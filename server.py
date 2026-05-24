import aiohttp
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from database import init_db, add_verificacao_web, add_verificacao, update_status, get_verificacao_por_telefone
from webhook import enviar_webhook
from config import DISCORD_TOKEN, GUILD_ID


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
        await enviar_webhook(data.nome, data.idade, telefone, discord_id_int)
        return {"status": "pendente", "message": "Dados enviados para verificação. Aguarde aprovação."}

    if existing and existing["status"] == "aprovado":
        return {"status": "ja_verificado", "message": "Este telefone já foi verificado."}

    await add_verificacao_web(nome=data.nome, idade=data.idade, telefone=telefone, discord_id=discord_id_int)
    await update_status(discord_id_int, "aprovado", 0)
    await adicionar_cargo(discord_id_int)
    await remover_cargo(discord_id_int)
    await enviar_webhook(data.nome, data.idade, telefone, discord_id_int)

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
