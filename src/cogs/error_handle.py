import traceback
from discord.ext import commands
import discord
from models import permissions_text

from models import make_embed


class ErrorHandleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        @bot.tree.error
        async def on_app_command_error(
            interaction: discord.Interaction,
            error: discord.app_commands.AppCommandError,
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
                embed = make_embed.error_embed(
                    title="コマンドを実行する権限がありません！",
                    description=f"不足している権限: {missing_perms_str}",
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True,
                    )
                return

            if isinstance(getattr(error, "original", error), discord.Forbidden):
                embed = make_embed.error_embed(
                    title="権限エラーが発生しました。",
                    description="Botにこの操作を行うための権限（ロールやチャンネル権限）がありません。",
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        embed=embed,
                        ephemeral=True,
                    )
                else:
                    await interaction.followup.send(embed=embed)
                return

            print("App command error:", error)
            embed = make_embed.error_embed(
                title="予期しないエラーが発生しました。",
                description=f"開発チームに報告してください。\n\nエラーコード```{error}```",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(embed=embed)

    @commands.Cog.listener("on_error")
    async def on_error(self, event: str, *args, **kwargs):
        error_text = traceback.format_exc()

        if "Unknown interaction" in error_text:
            print(f"Unknown interaction エラーが発生しました (event={event})")
        else:
            traceback.print_exc()


async def setup(bot):
    await bot.add_cog(ErrorHandleCog(bot))
