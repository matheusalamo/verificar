import discord
from discord.ext import commands
from config import DISCORD_TOKEN, GUILD_ID
from database import init_db


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="*", intents=intents)

    async def setup_hook(self):
        await init_db()
        await self.load_extension("cogs.verification")
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

    async def on_ready(self):
        print(f"Bot logado como {self.user} (ID: {self.user.id})")
        print("-" * 40)


if __name__ == "__main__":
    bot = Bot()
    bot.run(DISCORD_TOKEN)
