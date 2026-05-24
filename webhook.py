import aiohttp
import config


async def enviar_webhook(nome: str, idade: int, telefone: str, discord_id: int):
    url = config.WEBHOOK_URL
    if not url:
        return

    embed = {
        "title": "Nova verificação recebida",
        "color": 0x5865F2 if idade >= 13 else 0xED4245,
        "fields": [
            {"name": "Nome", "value": nome, "inline": True},
            {"name": "Idade", "value": str(idade), "inline": True},
            {"name": "Telefone", "value": telefone, "inline": True},
            {"name": "Discord ID", "value": f"<@{discord_id}> (`{discord_id}`)", "inline": False},
            {"name": "Status", "value": "🚫 Banido (menor de 13)" if idade < 13 else "⏳ Pendente", "inline": False},
        ],
        "footer": {"text": f"Origem: Web • ID: {discord_id}"},
        "timestamp": None,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"embeds": [embed]}) as resp:
            if resp.status >= 400:
                print(f"[Webhook] Erro: {resp.status}")
