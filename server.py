import aiohttp
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from database import init_db, add_verificacao_web, add_verificacao, update_status, update_status_por_id, get_verificacao_por_telefone, get_pendentes, get_aprovados, get_all_verificacoes, get_verificacao_por_id
from webhook import enviar_webhook
from config import DISCORD_TOKEN, GUILD_ID, ADMIN_PASSWORD, WEBHOOK_URL


HEADERS = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
CARGO_ADICIONAR = 886623918767616031
CARGO_REMOVER = 1211125285752410112


async def api_discord(method: str, path: str, json_data: dict = None):
    url = f"https://discord.com/api/v10{path}"
    async with aiohttp.ClientSession() as s:
        async with s.request(method, url, headers=HEADERS, json=json_data) as r:
            return r.status


async def banir(discord_id: int):
    await api_discord("PUT", f"/guilds/{GUILD_ID}/bans/{discord_id}", {"delete_message_days": 0})


async def adicionar_cargo(discord_id: int):
    await api_discord("PUT", f"/guilds/{GUILD_ID}/members/{discord_id}/roles/{CARGO_ADICIONAR}")


async def remover_cargo(discord_id: int):
    await api_discord("DELETE", f"/guilds/{GUILD_ID}/members/{discord_id}/roles/{CARGO_REMOVER}")


class VerificacaoRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    idade: int = Field(ge=1, le=150)
    telefone: str = Field(min_length=10, max_length=20)
    discord_id: str = Field(min_length=10, max_length=30, pattern=r"^\d+$")


class StatusRequest(BaseModel):
    telefone: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Sistema de Verificação", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="web"), name="web")


@app.get("/")
async def index():
    return FileResponse("web/index.html")

@app.get("/admin")
async def admin_page():
    return FileResponse("web/admin.html")


@app.post("/api/verificar")
async def verificar(data: VerificacaoRequest):
    telefone = data.telefone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    if not telefone.isdigit() or len(telefone) < 10:
        raise HTTPException(status_code=400, detail="Telefone inválido")

    existing = await get_verificacao_por_telefone(telefone)
    if existing and existing["status"] in ("banido", "reprovado"):
        return {"status": "bloqueado", "message": "Este telefone está bloqueado."}

    discord_id_int = int(data.discord_id)

    if data.idade < 14:
        await add_verificacao(discord_id=discord_id_int, nome=data.nome, idade=data.idade, telefone=telefone, origem="web")
        await update_status(discord_id_int, "banido", 0)
        await banir(discord_id_int)
        return {"status": "pendente", "message": "Dados enviados para verificação. Aguarde aprovação."}

    if existing and existing["status"] == "aprovado":
        return {"status": "ja_verificado", "message": "Este telefone já foi verificado."}

    await add_verificacao_web(nome=data.nome, idade=data.idade, telefone=telefone, discord_id=discord_id_int)
    await update_status(discord_id_int, "aprovado", 0)
    await adicionar_cargo(discord_id_int)
    await remover_cargo(discord_id_int)

    return {"status": "aprovado", "message": "✅ Verificado com sucesso!"}


@app.post("/api/status")
async def status(data: StatusRequest):
    telefone = data.telefone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    record = await get_verificacao_por_telefone(telefone)
    if not record:
        return {"status": "nao_encontrado", "message": "Nenhum registro encontrado para este telefone."}
    return {
        "status": record["status"],
        "nome": record["nome"],
        "created_at": record["created_at"],
        "message": (
            "✅ Verificado!" if record["status"] == "aprovado"
            else "❌ Reprovado." if record["status"] == "reprovado"
            else "🚫 Banido." if record["status"] == "banido"
            else "⏳ Pendente de aprovação."
        ),
    }


class AdminLoginRequest(BaseModel):
    password: str

class AdminStatusRequest(BaseModel):
    status: str

def admin_required(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Senha incorreta")

@app.post("/api/admin/login")
async def admin_login(data: AdminLoginRequest):
    if data.password == ADMIN_PASSWORD:
        return {"status": "ok"}
    raise HTTPException(status_code=401, detail="Senha incorreta")

@app.get("/api/admin/verificacoes")
async def admin_verificacoes(password: str = Query(...)):
    admin_required(password)
    pendentes = await get_pendentes()
    return [dict(r) for r in pendentes]

@app.get("/api/admin/logs")
async def admin_logs(password: str = Query(...)):
    admin_required(password)
    logs = await get_all_verificacoes()
    return [dict(r) for r in logs]

@app.post("/api/admin/verificacoes/{id}/status")
async def admin_update_status(id: int, data: AdminStatusRequest, password: str = Query(...)):
    admin_required(password)
    await update_status_por_id(id, data.status, 0)
    return {"status": "ok"}

@app.post("/api/admin/webhook/{id}")
async def admin_webhook_resend(id: int, password: str = Query(...)):
    admin_required(password)
    if not WEBHOOK_URL:
        raise HTTPException(status_code=400, detail="WEBHOOK_URL não configurada")
    record = await get_verificacao_por_id(id)
    if not record:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    ok = await enviar_webhook(record["nome"], record["idade"], record["telefone"], record["discord_id"] or 0)
    if not ok:
        raise HTTPException(status_code=502, detail="Erro ao enviar webhook")
    return {"status": "ok"}

@app.get("/api/admin/webhook/status")
async def admin_webhook_status(password: str = Query(...)):
    admin_required(password)
    return {"configurado": bool(WEBHOOK_URL)}

@app.post("/api/reset")
async def reset():
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM verificacoes")
        await db.commit()
    return {"status": "ok", "message": "Banco resetado."}
