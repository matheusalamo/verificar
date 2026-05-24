from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from database import init_db, add_verificacao_web, add_verificacao, update_status, get_verificacao_por_telefone
from webhook import enviar_webhook


class VerificacaoRequest(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    idade: int = Field(ge=1, le=150)
    telefone: str = Field(min_length=10, max_length=20)
    discord_id: int = Field(ge=1000, le=999999999999999999)


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

    if data.idade < 13:
        await add_verificacao(discord_id=data.discord_id, nome=data.nome, idade=data.idade, telefone=telefone, origem="web")
        await update_status(data.discord_id, "banido", 0)

    existing = await get_verificacao_por_telefone(telefone)
    if existing and existing["status"] == "aprovado":
        return {"status": "ja_verificado", "message": "Este telefone já foi verificado."}

    if data.idade >= 13:
        await add_verificacao_web(nome=data.nome, idade=data.idade, telefone=telefone, discord_id=data.discord_id)

    await enviar_webhook(data.nome, data.idade, telefone, data.discord_id)

    return {"status": "pendente", "message": "Dados enviados para verificação. Aguarde aprovação."}


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
            else "🚫 Banido (menor de 13 anos)." if record["status"] == "banido"
            else "⏳ Pendente de aprovação."
        ),
    }
