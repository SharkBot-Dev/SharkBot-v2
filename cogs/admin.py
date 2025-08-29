from discord.ext import commands, tasks
import discord
import datetime
from consts import mongodb
from discord import app_commands

from models import save_commands

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

    @commands.command(name="save", hidden=True)
    async def save(self, ctx):
        if ctx.author.id == 1335428061541437531:
            await save_commands.clear_commands()

            count = 0
            for cmd in self.bot.tree.get_commands():
                await save_commands.save_command(cmd)
                count += 1

            await ctx.reply(f"コマンドをセーブしました。\n{count}件。")

    @commands.command(name="ban_user", hidden=True)
    async def banuser(self, ctx, user: discord.User):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            if user.id == 1335428061541437531:
                return
            db = self.bot.async_db["Main"].BlockUser
            await db.replace_one(
                {"User": user.id}, 
                {"User": user.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{user.name}をBotからBANしました。", color=discord.Color.red()))

    @commands.command(name="unban_user", hidden=True)
    async def unban_user(self, ctx, user: discord.User):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            if user.id == 1335428061541437531:
                return
            db = self.bot.async_db["Main"].BlockUser
            await db.delete_one({
                "User": user.id
            })
            await ctx.reply(embed=discord.Embed(title=f"{user.name}のBotからのBANを解除しました。", color=discord.Color.red()))

    @commands.command(name="ban_guild", hidden=True)
    async def ban_guild(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].BlockGuild
            await db.replace_one(
                {"Guild": guild.id}, 
                {"Guild": guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}をBotからBANしました。", color=discord.Color.red()))

    @commands.command(name="unban_guild", hidden=True)
    async def unban_guild(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].BlockGuild
            await db.delete_one({
                "Guild": guild.id
            })
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}のBotからのBANを解除しました。", color=discord.Color.red()))

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        # await guild.leave()
        db = self.bot.async_db["Main"].BlockUser
        try:
            profile = await db.find_one({"User": guild.owner.id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                return
        except:
            return

async def setup(bot):
    await bot.add_cog(AdminCog(bot))