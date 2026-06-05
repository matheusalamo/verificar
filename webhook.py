import aiohttp
from config import DISCORD_TOKEN, GUILD_ID, LOG_CHANNEL_ID


async def enviar_webhook(nome: str, idade: int, telefone: str, discord_id: int):
    if not DISCORD_TOKEN or not LOG_CHANNEL_ID:
        return False, "DISCORD_TOKEN ou LOG_CHANNEL_ID não configurados"

    discord_mention = f"<@{discord_id}>" if discord_id and discord_id > 0 else "Não informado"

    embed = {
        "title": "Nova verificação recebida",
        "color": 0x22c55e if idade >= 14 else 0xef4444,
        "fields": [
            {"name": "Nome", "value": nome, "inline": True},
            {"name": "Idade", "value": str(idade), "inline": True},
            {"name": "Telefone", "value": telefone, "inline": True},
            {"name": "Discord ID", "value": f"{discord_mention} (`{discord_id}`)", "inline": False},
            {"name": "Status", "value": "🚫 Banido (menor de 14)" if idade < 14 else "✅ Aprovado", "inline": False},
        ],
        "footer": {"text": f"Origem: Admin • ID: {discord_id}"},
    }

    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }

    url = f"https://discord.com/api/v10/channels/{LOG_CHANNEL_ID}/messages"

    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, json={"embeds": [embed]}, headers=headers) as resp:
                if resp.status == 429:
                    return False, "Rate limit da API do Discord. Aguarde e tente novamente."
                if resp.status >= 400:
                    body = await resp.text()
                    return False, f"API Discord {resp.status}: {body[:200]}"
                return True, "ok"
        except Exception as e:
            return False, f"Erro: {str(e)[:200]}"