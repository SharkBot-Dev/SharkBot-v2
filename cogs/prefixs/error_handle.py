import traceback
from discord.ext import commands
import discord
from models import permissions_text

from models import make_embed

class Prefixs_ErrorHandleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # error_details = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a
        elif isinstance(error, commands.NotOwner):
            a = None
            return a
        else:
            print(f"Prefix Command error: {error}")
            return await ctx.reply(embed=make_embed.error_embed(title="予期しないエラーが発生しました。", description=f"開発チームに報告してください。\n\nエラーコード\n```{error}```"))

async def setup(bot):
    await bot.add_cog(Prefixs_ErrorHandleCog(bot))
