import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from database import add_verificacao, get_verificacao, get_pendentes, get_banidos_pendentes, update_status, update_status_por_id
from config import ADMIN_ROLE_ID, LOG_CHANNEL_ID, GUILD_ID


class VerificacaoModal(discord.ui.Modal, title="Verificação"):
    nome = discord.ui.TextInput(label="Nome completo", placeholder="Seu nome completo", max_length=100)
    idade = discord.ui.TextInput(label="Idade", placeholder="Sua idade", max_length=3, min_length=1)
    telefone = discord.ui.TextInput(label="Telefone", placeholder="DDD + número (ex: 11999999999)", max_length=20)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            idade = int(self.idade.value)
        except ValueError:
            await interaction.response.send_message("Idade inválida. Digite apenas números.", ephemeral=True)
            return

        if idade < 1 or idade > 150:
            await interaction.response.send_message("Idade inválida.", ephemeral=True)
            return

        telefone = self.telefone.value.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not telefone.isdigit() or len(telefone) < 10:
            await interaction.response.send_message("Telefone inválido. Digite apenas números com DDD.", ephemeral=True)
            return

        if idade < 13:
            await add_verificacao(interaction.user.id, self.nome.value, idade, telefone, origem="discord")
            await update_status(interaction.user.id, "banido", 0)
            try:
                await interaction.user.ban(reason="Menor de 13 anos - verificação automática")
            except:
                pass
            await interaction.response.send_message("Dados enviados para verificação. Aguarde aprovação.", ephemeral=True)
            return

        await add_verificacao(interaction.user.id, self.nome.value, idade, telefone, origem="discord")

        embed = discord.Embed(
            title="Verificação enviada!",
            description=f"Olá {interaction.user.mention}, seus dados foram enviados para verificação.\nAguarde a aprovação de um administrador.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Nome", value=self.nome.value, inline=True)
        embed.add_field(name="Idade", value=str(idade), inline=True)
        embed.add_field(name="Telefone", value=telefone, inline=True)
        embed.add_field(name="Status", value="⏳ Pendente", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        guild = interaction.guild
        if guild and LOG_CHANNEL_ID:
            channel = guild.get_channel(LOG_CHANNEL_ID)
            if channel:
                log_embed = discord.Embed(
                    title="Nova verificação pendente",
                    description=f"{interaction.user.mention} ({interaction.user.id})",
                    color=discord.Color.orange(),
                )
                log_embed.add_field(name="Nome", value=self.nome.value, inline=True)
                log_embed.add_field(name="Idade", value=str(idade), inline=True)
                log_embed.add_field(name="Telefone", value=telefone, inline=True)
                log_embed.set_footer(text="Use /verificar_pendentes para aprovar ou rejeitar")
                await channel.send(embed=log_embed)


class VerificacaoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bg_task = bot.loop.create_task(self.ban_loop())

    async def cog_unload(self):
        self.bg_task.cancel()

    async def processar_bans_pendentes(self):
        banidos = await get_banidos_pendentes()
        if not banidos:
            return
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        for record in banidos:
            try:
                await guild.ban(discord.Object(id=record["discord_id"]), reason="Menor de 13 anos - verificação automática")
            except:
                pass

    async def ban_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.processar_bans_pendentes()
            await asyncio.sleep(15)

    @app_commands.command(name="verificar", description="Envie seus dados para verificação")
    async def verificar(self, interaction: discord.Interaction):
        existing = await get_verificacao(interaction.user.id)
        if existing and existing["status"] == "aprovado":
            await interaction.response.send_message("Você já está verificado!", ephemeral=True)
            return
        if existing and existing["status"] == "pendente":
            await interaction.response.send_message("Você já tem uma verificação pendente.", ephemeral=True)
            return
        if existing and existing["status"] == "banido":
            await interaction.response.send_message("🚫 Você foi banido deste servidor.", ephemeral=True)
            return
        await interaction.response.send_modal(VerificacaoModal())

    @app_commands.command(name="verificar_pendentes", description="Lista todas as verificações pendentes")
    @app_commands.default_permissions(administrator=True)
    async def pendentes(self, interaction: discord.Interaction):
        if ADMIN_ROLE_ID and ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message("Você não tem permissão.", ephemeral=True)
            return

        pendentes = await get_pendentes()
        if not pendentes:
            await interaction.response.send_message("Nenhuma verificação pendente.", ephemeral=True)
            return

        view = AprovacaoView(pendentes)
        await interaction.response.send_message(f"**{len(pendentes)} pendente(s)**", view=view, ephemeral=True)


class AprovacaoView(discord.ui.View):
    def __init__(self, pendentes):
        super().__init__(timeout=300)
        self.pendentes = pendentes
        self.index = 0
        self._update_buttons()

    def _update_buttons(self):
        self.clear_items()
        item = self.pendentes[self.index]
        label = f"{item['nome']} ({item['idade']} anos)"
        self.add_item(AprovarButton(item["discord_id"], item["id"]))
        self.add_item(ReprovarButton(item["discord_id"], item["id"]))
        if len(self.pendentes) > 1:
            self.add_item(NavegacaoButton("⬅️", -1))
            self.add_item(NavegacaoButton("➡️", 1))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True


class NavegacaoButton(discord.ui.Button):
    def __init__(self, label, delta):
        self.delta = delta
        super().__init__(label=label, style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view: AprovacaoView = self.view
        view.index = (view.index + self.delta) % len(view.pendentes)
        view._update_buttons()
        item = view.pendentes[view.index]
        user_info = f"<@{item['discord_id']}> ({item['discord_id']})" if item["discord_id"] else f"Web - ID não informado"
        embed = discord.Embed(
            title=f"Verificação #{item['id']}",
            description=f"Usuário: {user_info}",
            color=discord.Color.blue(),
        )
        embed.add_field(name="Nome", value=item["nome"], inline=True)
        embed.add_field(name="Idade", value=str(item["idade"]), inline=True)
        embed.add_field(name="Telefone", value=item["telefone"], inline=True)
        embed.add_field(name="Origem", value=item["origem"], inline=True)
        embed.set_footer(text=f"{view.index + 1} de {len(view.pendentes)}")
        await interaction.response.edit_message(embed=embed, view=view)


class AprovarButton(discord.ui.Button):
    def __init__(self, discord_id, record_id):
        self.target_id = discord_id
        self.record_id = record_id
        super().__init__(label="Aprovar", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        if self.target_id:
            await update_status(self.target_id, "aprovado", interaction.user.id)
            await interaction.response.edit_message(content=f"✅ <@{self.target_id}> foi **aprovado**!", view=None, embed=None)
            member = interaction.guild.get_member(self.target_id)
            if member:
                try:
                    await member.send("✅ **Você foi verificado com sucesso!**")
                except:
                    pass
        else:
            await update_status_por_id(self.record_id, "aprovado", interaction.user.id)
            await interaction.response.edit_message(content=f"✅ **Verificação #{self.record_id} aprovada!**", view=None, embed=None)


class ReprovarButton(discord.ui.Button):
    def __init__(self, discord_id, record_id):
        self.target_id = discord_id
        self.record_id = record_id
        super().__init__(label="Reprovar", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        if self.target_id:
            await update_status(self.target_id, "reprovado", interaction.user.id)
            await interaction.response.edit_message(content=f"❌ <@{self.target_id}> foi **reprovado**.", view=None, embed=None)
            member = interaction.guild.get_member(self.target_id)
            if member:
                try:
                    await member.send("❌ **Sua verificação foi reprovada.**")
                except:
                    pass
        else:
            await update_status_por_id(self.record_id, "reprovado", interaction.user.id)
            await interaction.response.edit_message(content=f"❌ **Verificação #{self.record_id} reprovada!**", view=None, embed=None)


async def setup(bot: commands.Bot):
    await bot.add_cog(VerificacaoCog(bot))
