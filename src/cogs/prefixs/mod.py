import datetime
import io
from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed, pages
import aiohttp


class Prefixs_ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefixs_ModCog")

    @commands.command(
        name="clear", description="メッセージを一斉削除します。"
    )
    @commands.cooldown(2, 5, type=commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    @commands.guild_only()
    async def clear_prefix(self, ctx: commands.Context, count: int, user: discord.User = None):
        if not await command_disable.command_enabled_check_by_cmdname(
            "moderation clear", ctx.guild
        ):
            return
        
        await ctx.message.delete()

        now = discord.utils.utcnow()
        two_weeks = datetime.timedelta(days=14)

        def check(msg: discord.Message):
            if (now - msg.created_at) > two_weeks:
                return False
            if user is not None and msg.author.id != user.id:
                return False
            return True

        deleted = await ctx.channel.purge(limit=count, check=check)

        if len(deleted) == 0:
            await ctx.send(embed=make_embed.error_embed(title="メッセージを削除できませんでした。").set_footer(text="このメッセージは5秒後に削除されます。"), delete_after=5)

        await ctx.send(embed=make_embed.success_embed(title=f"{len(deleted)}個のメッセージを削除しました。").set_footer(text="このメッセージは5秒後に削除されます。"), delete_after=5)

async def setup(bot):
    await bot.add_cog(Prefixs_ModCog(bot))
