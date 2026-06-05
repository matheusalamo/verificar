import aiohttp
import config


def normalizar_url(url: str) -> str:
    return url.replace("ptb.discord.com", "discord.com").replace("canary.discord.com", "discord.com")


async def enviar_webhook(nome: str, idade: int, telefone: str, discord_id: int):
    url = normalizar_url(config.WEBHOOK_URL)
    if not url:
        return False, "WEBHOOK_URL não configurada"

    discord_mention = f"<@{discord_id}> (`{discord_id}`)" if discord_id and discord_id > 0 else "Não informado"

    payload = {
        "embeds": [{
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
        }],
    }

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.post(url, json=payload) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    return False, f"Discord {resp.status}: {body[:200]}"
                return True, "ok"
        except Exception as e:
            return False, f"Erro na conexão: {str(e)[:200]}"
