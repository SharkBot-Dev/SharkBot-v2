from discord.ext import commands
import discord
import random
from discord import app_commands
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import asyncio
import aiohttp


def generate_tree_image(length_cm: int):
    hour = datetime.utcnow().hour + 9
    if hour >= 24:
        hour -= 24

    width, height = 400, 600

    if 6 <= hour < 18:
        bg_color = (135, 206, 235)
    else:
        bg_color = (25, 25, 112)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    if not (6 <= hour < 18):
        for _ in range(50):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 150)
            r = random.randint(1, 3)
            draw.ellipse([x, y, x + r, y + r], fill=(255, 255, 200))

    draw.rectangle([0, height - 100, width, height], fill=(34, 139, 34))

    trunk_height = min(int(length_cm * 2), height - 150)
    trunk_width = 40
    trunk_x = width // 2 - trunk_width // 2
    trunk_y1 = height - 100
    trunk_y0 = trunk_y1 - trunk_height
    draw.rectangle(
        [trunk_x, trunk_y0, trunk_x + trunk_width, trunk_y1], fill=(139, 69, 19)
    )

    leaf_radius = max(50, trunk_height // 2)
    leaf_x0 = width // 2 - leaf_radius
    leaf_y0 = trunk_y0 - leaf_radius
    leaf_x1 = width // 2 + leaf_radius
    leaf_y1 = trunk_y0 + leaf_radius
    draw.ellipse([leaf_x0, leaf_y0, leaf_x1, leaf_y1], fill=(34, 139, 34))

    font = ImageFont.load_default(30)
    if not (6 <= hour < 18):
        draw.text(
            (10, 10), f"Tree Height: {length_cm} cm", fill=(255, 255, 255), font=font
        )
    else:
        draw.text((10, 10), f"Tree Height: {length_cm} cm", fill=(0, 0, 0), font=font)

    return img


class TreeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> TreeCog")

    tree = app_commands.Group(name="tree", description="みんなで木を育てるゲームです")

    async def check_tree_time(self, user: discord.User):
        db = self.bot.async_db["Main"].GlobalTree
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except Exception:
            return False, 0, 0

        if not dbfind:
            return False, 0, 0

        now = datetime.utcnow()
        last_feed = dbfind.get("LastTime")

        if last_feed and isinstance(last_feed, datetime):
            elapsed = now - last_feed
            if elapsed < timedelta(hours=1):
                remaining = timedelta(hours=1) - elapsed
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                return True, minutes, seconds
        return False, 0, 0

    @tree.command(name="watering", description="木に水をまきます。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def tree_watering(self, interaction: discord.Interaction):
        await interaction.response.defer()

        cm = random.randint(1, 3)

        db = self.bot.async_db["Main"].GlobalTree

        b, m, s = await self.check_tree_time(interaction.user)
        if b:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="まだ水をまけません！",
                    description=f"次に水をまけるまで **{m}分{s}秒**",
                    color=discord.Color.orange(),
                )
            )

        now = datetime.utcnow()
        await db.update_one(
            {"User": interaction.user.id},
            {"$inc": {"Length": cm}, "$set": {"LastTime": now}},
            upsert=True,
        )

        await interaction.followup.send(
            embed=discord.Embed(
                title="木に水をまきました。",
                description=f"{cm}cm育ちました。",
                color=discord.Color.green(),
            )
        )

    @tree.command(name="status", description="木のステータスを確認します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def tree_status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].GlobalTree

        cm = 0
        async for t in db.find({}):
            cm += t.get("Length", 0)

        await interaction.followup.send(
            embed=discord.Embed(
                title="現在の木のステータスです。",
                description=f"育てた木の大きさ: {cm / 100:.2f}m",
                color=discord.Color.green(),
            )
        )

    @tree.command(name="mystatus", description="自分のステータスを確認します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def tree_mystatus(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].GlobalTree

        try:
            dbfind = await db.find_one({"User": interaction.user.id}, {"_id": False})
        except Exception:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="まだ一度も水をまいたことがないようです",
                    color=discord.Color.red(),
                )
            )

        if not dbfind:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="まだ一度も水をまいたことがないようです",
                    color=discord.Color.red(),
                )
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{interaction.user.name}のステータスです。",
                description=f"木の大きさ: {dbfind.get('Length', 0)}cm",
                color=discord.Color.green(),
            )
        )

    @tree.command(name="image", description="木の画像を確認します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def tree_image(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = self.bot.async_db["Main"].GlobalTree

        cm = 0
        async for t in db.find({}):
            cm += t.get("Length", 0)

        c = 0
        while True:
            if c > 8:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="予期しないエラーが発生しました。",
                        color=discord.Color.red(),
                    )
                )

            f = await asyncio.to_thread(generate_tree_image, cm)

            i = io.BytesIO()

            await asyncio.to_thread(f.save, i, format="png")

            i.seek(0)

            try:
                await interaction.followup.send(
                    file=discord.File(i, filename="tree.png")
                )

            except aiohttp.ClientOSError:
                c += 1
                i.close()
                await asyncio.sleep(0.5)
                continue

            i.close()
            return


async def setup(bot):
    await bot.add_cog(TreeCog(bot))
