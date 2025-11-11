import ast
import datetime
import io
import json
from pathlib import Path
import random
from discord.ext import commands
import discord

from models import make_embed, save_commands, translate

from discord import app_commands

import asyncio

import discord.ext.tasks

from PIL import Image, ImageDraw

DIRECTIONS = [
    ("⬆️", 0),
    ("➡️", 270),
    ("⬇️", 180),
    ("⬅️", 90),
]

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

    @commands.command(name="task", hidden=True)
    async def task(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            value: dict[str, bool] = {}
            for c in self.bot.cogs.values():
                for a in filter(lambda a: not a.startswith("_"), dir(c)):
                    v = getattr(c, a)
                    if isinstance(v, discord.ext.tasks.Loop):
                        value[a] = v.is_running()
            value_max = len(max(value.keys(), key=len))
            res = ""
            for k, v in value.items():
                if v:
                    res += f"\n+ {k.ljust(value_max)}: Online"
                else:
                    res += f"\n- {k.ljust(value_max)}: Offline"

            await ctx.reply(embed=make_embed.success_embed(title="タスクの稼働状況", description="```diff" + res + "\n```"))

    @commands.command(name="send", hidden=True)
    async def send(self, ctx: commands.Context, text: str):
        if ctx.author.id == 1335428061541437531:
            att = ctx.message.attachments
            if len(att) != 0:
                io_ = io.BytesIO(await att[0].read())
                file = discord.File(io_, filename=att[0].filename)
                await ctx.channel.send(text, file=file)
                io_.close()
                return
            await ctx.channel.send(text)

    @commands.group(name="test", description="Bot管理者用コマンド。Bot管理者しか実行できません。")
    async def test_command(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            if not ctx.invoked_subcommand:
                await ctx.reply(embed=make_embed.success_embed(title="管理者のテスト用コマンド")
                                .add_field(name="!.test embed", value="埋め込みをJSONから送信します。", inline=False))
                
    @test_command.command(name="embed")
    async def test_command_embed_send(self, ctx: commands.Context, *, json_data: str):
        if ctx.author.id != 1335428061541437531:
            return
        
        await ctx.channel.send(embed=discord.Embed().from_dict(json.loads(json_data)))
        await ctx.message.add_reaction("✅")

    @test_command.command(name="tt")
    async def test_command_tt(self, ctx: commands.Context):
        if ctx.author.id != 1335428061541437531:
            return

        def generate_arrow_image(angle: int) -> io.BytesIO:
            size = (200, 200)
            img = Image.new("RGBA", size, (255, 255, 255, 255))
            draw = ImageDraw.Draw(img)
            cx, cy = size[0] // 2, size[1] // 2

            draw.line((cx, cy + 40, cx, cy - 40), fill=(0, 0, 0), width=8)
            draw.polygon([(cx - 15, cy - 40), (cx + 15, cy - 40), (cx, cy - 70)], fill=(0, 0, 0))

            rotated = img.rotate(angle, expand=True, fillcolor=(255, 255, 255, 255))

            buffer = io.BytesIO()
            rotated.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        
        correct_emoji, angle = random.choice(DIRECTIONS)
        img_buffer = await asyncio.to_thread(generate_arrow_image, angle)

        options = ["⬆️", "➡️", "⬇️", "⬅️"]

        view = discord.ui.View()

        for opt in options:
            async def callback(inter: discord.Interaction, opt=opt):
                if opt == correct_emoji:
                    await inter.response.edit_message(
                        content="✅ 正解！あなたはロボットではありません。",
                        attachments=[], view=None
                    )
                else:
                    await inter.response.edit_message(
                        content="❌ 不正解です。もう一度試してください。",
                        attachments=[], view=None
                    )

            btn = discord.ui.Button(emoji=opt, style=discord.ButtonStyle.primary)
            btn.callback = callback
            view.add_item(btn)

        file = discord.File(img_buffer, filename="arrow.png")
        embed = discord.Embed(title="この矢印の向きを選んでください。", color=discord.Color.blue())
        embed.set_image(url="attachment://arrow.png")

        await ctx.reply(embed=embed, file=file, view=view)

        img_buffer.close()

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