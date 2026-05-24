import os
import aiosqlite
from config import DB_PATH


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS verificacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER UNIQUE,
                discord_tag TEXT,
                nome TEXT NOT NULL,
                idade INTEGER NOT NULL,
                telefone TEXT NOT NULL,
                origem TEXT NOT NULL DEFAULT 'discord',
                status TEXT NOT NULL DEFAULT 'pendente',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewed_by INTEGER
            )
        """)
        await db.commit()


async def add_verificacao(discord_id: int, nome: str, idade: int, telefone: str, origem: str = "discord", discord_tag: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO verificacoes (discord_id, discord_tag, nome, idade, telefone, origem, status) VALUES (?, ?, ?, ?, ?, ?, 'pendente')",
            (discord_id, discord_tag, nome, idade, telefone, origem),
        )
        await db.commit()


async def add_verificacao_web(nome: str, idade: int, telefone: str, discord_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO verificacoes (discord_id, nome, idade, telefone, origem, status) VALUES (?, ?, ?, ?, 'web', 'pendente')",
            (discord_id, nome, idade, telefone),
        )
        await db.commit()


async def get_verificacao(discord_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM verificacoes WHERE discord_id = ?", (discord_id,)
        )
        return await cursor.fetchone()


async def get_verificacao_por_telefone(telefone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM verificacoes WHERE telefone = ? ORDER BY created_at DESC LIMIT 1",
            (telefone,),
        )
        return await cursor.fetchone()


async def get_banidos_pendentes():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM verificacoes WHERE status = 'banido' AND discord_id IS NOT NULL ORDER BY created_at ASC"
        )
        return await cursor.fetchall()


async def get_pendentes():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM verificacoes WHERE status = 'pendente' ORDER BY created_at ASC"
        )
        return await cursor.fetchall()


async def update_status(discord_id: int, status: str, reviewed_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE verificacoes SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP WHERE discord_id = ?",
            (status, reviewed_by, discord_id),
        )
        await db.commit()


async def update_status_por_id(record_id: int, status: str, reviewed_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE verificacoes SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, reviewed_by, record_id),
        )
        await db.commit()
