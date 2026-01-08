import discord
from discord.ext import commands

from models import make_embed

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AdminCog")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # error_details = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a
        elif isinstance(error, commands.NotOwner):
            a = None
            return a
        elif isinstance(error, commands.CommandOnCooldown):
            a = None
            return a
        elif isinstance(error, commands.NoPrivateMessage):
            a = None
            return a
        elif isinstance(error, commands.BadArgument):
            a = None
            return a
        elif isinstance(error, commands.MissingRequiredArgument):
            a = None
            return a
        else:
            print(f"Prefix Command error: {error}")
            return await ctx.reply(
                embed=make_embed.error_embed(
                    title="予期しないエラーが発生しました。",
                    description=f"開発チームに報告してください。\n\nエラーコード\n```{error}```",
                )
            )

    @commands.command(name="upload")
    @commands.is_owner()
    async def uploader(self, ctx: commands.Context):
        attatch = ctx.message.attachments
        if attatch == []:
            return await ctx.reply("添付ファイルが見つかりません。")
        if attatch[0].filename.endswith(".py"):
            return await ctx.reply("添付ファイルは.pyで終わる必要があります。")
        await attatch[0].save(f"cogs/{attatch[0].filename}")
        await ctx.reply('保存しました。')

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, cog_name: str):
        await self.bot.reload_extension(f"cogs.{cog_name}")
        await ctx.reply('Reloaded!')

    @commands.command(name="load")
    @commands.is_owner()
    async def load(self, ctx: commands.Context, cog_name: str):
        await self.bot.load_extension(f"cogs.{cog_name}")
        await ctx.reply('Loaded!')

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
        await ctx.reply('Synced!')

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
