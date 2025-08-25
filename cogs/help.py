from discord.ext import commands, tasks
import discord
import datetime
from consts import settings
from discord import app_commands
from models import command_disable

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> HelpCog")

    @app_commands.command(name="help", description="ヘルプを表示します")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def help(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.send_message(embed=discord.Embed(title="ヘルプ", description="/help .. このメッセージを表示します。\n/dashboard .. ダッシュボードのリンクを取得します。", color=discord.Color.blue()), ephemeral=True)

    @app_commands.command(name="dashboard", description="ダッシュボードのリンクを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def dashboard(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.send_message(f"以下のリンクからアクセスできます。\n{settings.DASHBOARD_URL}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))