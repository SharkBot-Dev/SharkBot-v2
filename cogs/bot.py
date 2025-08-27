from discord.ext import commands, tasks
import discord
from discord import app_commands

from models import command_disable

class BotCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> BotCog")

    bot = app_commands.Group(name="bot", description="Bot系のコマンドです。")

    @bot.command(name="about", description="Botの情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def about_bot(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="招待リンク", url="https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands"))
        view.add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"))
        em = discord.Embed(title="`SharkBot`の情報", color=discord.Color.green())
        em.add_field(name="サーバー数", value=f"{len(self.bot.guilds)}サーバー").add_field(name="ユーザー数", value=f"{len(self.bot.users)}人")
        em.add_field(name="サブ管理者", value=f"3人")
        em.add_field(name="モデレーター", value=f"8人")
        await interaction.response.send_message(embed=em)

    @bot.command(name="ping", description="Pingを見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def ping_bot(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.send_message(embed=discord.Embed(title="Pingを測定しました。", description=f"DiscordAPI: {round(self.bot.latency * 1000)}ms", color=discord.Color.green()))

    @bot.command(name="invite", description="Botの招待リンクを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def invite_bot(self, interaction: discord.Interaction, botのid: discord.User):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()

        gu = interaction.guild.default_role
        mem_kengen = discord.utils.oauth_url(botのid.id, permissions=gu.permissions)

        embed=discord.Embed(title=f"{botのid}を招待する。", description=f"""# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)
# [🖊️権限を選んで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands)
# [✅メンバーの権限で招待]({mem_kengen})
# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)""", color=discord.Color.green())

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotCog(bot))