from discord.ext import commands
import discord
from discord import app_commands

from models import make_embed

class BotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BotCog")

    bot = app_commands.Group(
        name="bot",
        description="Bot系のコマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    @bot.command(name="about", description="Botの情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def about_bot(self, interaction: discord.Interaction):
        await interaction.response.defer()

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="招待リンク",
                url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&integration_type=0&scope=bot+applications.commands",
            )
        )
        view.add_item(
            discord.ui.Button(
                label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"
            )
        )
        em = discord.Embed(title="SharkBotの情報", color=discord.Color.green())
        em.add_field(
            name="サーバー数", value=f"{len(self.bot.guilds)}サーバー"
        )

        em.set_thumbnail(url=self.bot.user.avatar.url)

        await interaction.followup.send(embeds=[em], view=view)

    @bot.command(name="ping", description="Pingを見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ping_bot(self, interaction: discord.Interaction):
        embed = make_embed.success_embed(
            title="Pingを測定しました。",
            description=f"DiscordAPI: {round(self.bot.latency * 1000)}ms",
        )
        await interaction.response.send_message(embed=embed)

    @bot.command(name="uptime", description="Botの起動した時刻を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_uptime(self, interaction: discord.Interaction):
        uptime = self.bot.extensions.get("jishaku").Feature.load_time.timestamp()
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="Botの起動した時刻を取得しました。",
                description=f"<t:{uptime:.0f}:R>",
            )
        )

async def setup(bot):
    await bot.add_cog(BotCog(bot))
