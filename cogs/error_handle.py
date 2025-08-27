from discord.ext import commands, tasks
import discord
import datetime
import random
from models import permissions_text

class ErrorHandleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ErrorHandleCog")

    @commands.Cog.listener("on_app_command_error")
    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            e = 0
            return e
        
        if isinstance(error, discord.app_commands.CommandNotFound):
            e = 0
            return e

        if isinstance(error, discord.app_commands.MissingPermissions):
            missing_perms = [
                permissions_text.PERMISSION_TRANSLATIONS.get(perm, perm)
                for perm in error.missing_permissions
            ]
            missing_perms_str = ", ".join(missing_perms)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="コマンドを実行する権限がありません！",
                        description=f"不足している権限: {missing_perms_str}",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
            return

        print("App command error:", error)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "予期しないエラーが発生しました。開発者に報告してください。",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ErrorHandleCog(bot))