from discord.ext import commands, tasks
import discord
import datetime
from consts import mongodb
from discord import app_commands

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> AdminCog")

    @commands.command(name="reload", aliases=["r"], hidden=True)
    async def reload(self, ctx: commands.Context, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")

    @commands.command(name="sync_slash", aliases=["sy"], hidden=True)
    async def sync_slash(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            await self.bot.tree.sync()
            await ctx.reply("スラッシュコマンドを同期しました。")

    @commands.command(name="load", hidden=True)
    async def load_admin(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.load_extension(f"cogs.{cogname}")
            await ctx.reply(f"LoadOK .. `cogs.{cogname}`")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))