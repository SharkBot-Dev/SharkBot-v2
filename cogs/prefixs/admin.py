import ast
import datetime
from pathlib import Path
from discord.ext import commands
import discord

from models import make_embed, save_commands, translate

from discord import app_commands

import asyncio

class Prefix_AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> Prefix_AdminCog")

    @commands.command(name="reload", aliases=["r"], hidden=True)
    async def reload(self, ctx: commands.Context, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")

    @commands.command(name="load", hidden=True)
    async def load_admin(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.load_extension(f"cogs.{cogname}")
            await ctx.reply(f"LoadOK .. `cogs.{cogname}`")

    @commands.command(name="sync_slash", aliases=["sy"], hidden=True)
    async def sync_slash(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            await self.bot.tree.sync()
            await ctx.reply("スラッシュコマンドを同期しました。")

    @commands.command(name="reload_lang", hidden=True)
    async def reload_lang(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            await translate.load()
            await ctx.message.add_reaction('✅')

    @commands.command(name="save", hidden=True)
    async def save(self, ctx):
        if ctx.author.id == 1335428061541437531:
            await save_commands.clear_commands()

            count = 0
            for cmd in self.bot.tree.get_commands():
                await save_commands.save_command(cmd)
                count += 1

            for g in self.bot.guilds:
                await self.bot.async_db["DashboardBot"].bot_joind_guild.replace_one(
                    {"Guild": g.id}, {"Guild": g.id}, upsert=True
                )

            await ctx.reply(f"コマンドをセーブしました。\n{count}件。")

async def setup(bot):
    await bot.add_cog(Prefix_AdminCog(bot))