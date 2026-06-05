import aiohttp
import config


async def enviar_webhook(nome: str, idade: int, telefone: str, discord_id: int):
    url = config.WEBHOOK_URL
    if not url:
        return False

    discord_mention = f"<@{discord_id}> (`{discord_id}`)" if discord_id and discord_id > 0 else "Não informado"

    embed = {
        "title": "Nova verificação recebida",
        "color": 0x5865F2 if idade >= 13 else 0xED4245,
        "fields": [
            {"name": "Nome", "value": nome, "inline": True},
            {"name": "Idade", "value": str(idade), "inline": True},
            {"name": "Telefone", "value": telefone, "inline": True},
            {"name": "Discord ID", "value": discord_mention, "inline": False},
            {"name": "Status", "value": "🚫 Banido (menor de 14)" if idade < 14 else "✅ Aprovado", "inline": False},
        ],
        "footer": {"text": f"Origem: Admin • ID: {discord_id}"},
        "timestamp": None,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"embeds": [embed]}) as resp:
            if resp.status >= 400:
                body = await resp.text()
                print(f"[Webhook] Erro {resp.status}: {body[:200]}")
                return False
            return True
