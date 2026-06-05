import asyncio
import discord
import config


def normalizar_url(url: str) -> str:
    return url.replace("ptb.discord.com", "discord.com").replace("canary.discord.com", "discord.com")


async def enviar_webhook(nome: str, idade: int, telefone: str, discord_id: int):
    url = normalizar_url(config.WEBHOOK_URL)
    if not url:
        return False, "WEBHOOK_URL não configurada"

    discord_mention = f"<@{discord_id}>" if discord_id and discord_id > 0 else "Não informado"

    embed = discord.Embed(
        title="Nova verificação recebida",
        color=discord.Color.green() if idade >= 14 else discord.Color.red(),
    )
    embed.add_field(name="Nome", value=nome, inline=True)
    embed.add_field(name="Idade", value=str(idade), inline=True)
    embed.add_field(name="Telefone", value=telefone, inline=True)
    embed.add_field(name="Discord ID", value=f"{discord_mention} (`{discord_id}`)", inline=False)
    embed.add_field(name="Status", value="🚫 Banido (menor de 14)" if idade < 14 else "✅ Aprovado", inline=False)
    embed.set_footer(text=f"Origem: Admin • ID: {discord_id}")

    def send():
        wh = discord.SyncWebhook.from_url(url)
        wh.send(embed=embed, wait=True)

    try:
        await asyncio.to_thread(send)
        return True, "ok"
    except discord.NotFound:
        return False, "Webhook não encontrado (404). Crie um novo."
    except discord.Forbidden:
        return False, "Sem permissão para enviar (403)."
    except discord.HTTPException as e:
        return False, f"Discord {e.status}: {e.text[:200]}"
    except Exception as e:
        return False, f"Erro: {str(e)[:200]}"