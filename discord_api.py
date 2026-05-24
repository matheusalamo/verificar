import aiohttp
import config


async def banir_membro(discord_id: int, motivo: str = "Menor de 13 anos - verificação automática") -> bool:
    headers = {
        "Authorization": f"Bot {config.DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"https://discord.com/api/v10/guilds/{config.GUILD_ID}/bans/{discord_id}"
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json={"delete_message_days": 0, "reason": motivo}) as resp:
            return resp.status == 204 or resp.status == 201
