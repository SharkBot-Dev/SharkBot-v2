from discord.ext import commands
import discord
import random
from discord import app_commands
from datetime import datetime, timedelta


class TreeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> TreeCog")

    tree = app_commands.Group(
        name="tree", description="みんなで木を育てるゲームです"
    )

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

async def setup(bot):
    await bot.add_cog(TreeCog(bot))