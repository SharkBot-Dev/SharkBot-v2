from datetime import datetime, timedelta
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import random

class AnimalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def one_kind_animal(self, user: discord.User):
        db = self.bot.async_db["Main"].Animals
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except Exception:
            return False
        return dbfind is not None

    async def add_level(self, user: discord.User, kinds: str, amount: int = 1):
        db = self.bot.async_db["Main"].Animals
        await db.update_one(
            {"User": user.id, "Kinds": kinds},
            {"$inc": {"Level": amount}},
        )

    async def add_xp(self, user: discord.User, kinds: str, amount: int = 1):
        db = self.bot.async_db["Main"].Animals
        await db.update_one(
            {"User": user.id, "Kinds": kinds},
            {"$inc": {"XP": amount}},
        )

    async def get_animal_status(self, user: discord.User, kinds: str):
        db = self.bot.async_db["Main"].Animals
        try:
            return await db.find_one({"User": user.id, "Kinds": kinds}, {"_id": False})
        except Exception:
            return None

    @commands.Cog.listener("on_message")
    async def on_message_animal(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        check = await self.one_kind_animal(message.author)
        if not check:
            return
        
        achi_db = self.bot.async_db["Main"].Animals
        async for animal in achi_db.find({"User": message.author.id}):
            try:
                status = await self.get_animal_status(message.author, animal.get('Kinds', "None"))
                await self.add_xp(message.author, animal.get('Kinds', "None"), 1)

                if status and status.get('XP', 0) >= status.get('IV', 60):
                    db = self.bot.async_db["Main"].Animals
                    await db.update_one(
                        {"User": message.author.id, "Kinds": animal.get('Kinds', "None")},
                        {"$set": {"XP": 0}}
                    )

                    await self.add_level(message.author, animal.get('Kinds', "None"), 1)
                    await message.reply(
                        embed=discord.Embed(
                            title=f"{status.get('Name', '名無し')}のレベルが上がったよ！",
                            description="やったね！",
                            color=discord.Color.green()
                        ).set_footer(text="このメッセージは5秒後に削除されます。"),
                        delete_after=5
                    )
                    await asyncio.sleep(1)
            except Exception:
                continue

    animal = app_commands.Group(
        name="animal", description="ペットを関連のコマンドです。"
    )

    async def is_keeping_animal(self, user: discord.User, kinds: str):
        db = self.bot.async_db["Main"].Animals
        try:
            dbfind = await db.find_one({"User": user.id, "Kinds": kinds}, {"_id": False})
        except Exception:
            return False
        return dbfind is not None

    @animal.command(
        name="keeping", description="ペットを新しく飼います。"
    )
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse")
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def animal_keeping(
        self, interaction: discord.Interaction, 種類: app_commands.Choice[str], 名前: str
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].Animals
        check = await self.is_keeping_animal(interaction.user, 種類.value)
        if not check:
            await db.replace_one(
                {"User": interaction.user.id, "Kinds": 種類.value},
                {
                    "User": interaction.user.id,
                    "Kinds": 種類.value,
                    "Name": 名前,
                    "Level": 0,
                    "XP": 0,
                    "Status": "いつも通り",
                    "IV": random.randint(50, 70)
                },
                upsert=True,
            )
            await interaction.followup.send(embed=discord.Embed(
                title="ペットを飼いました！",
                description=f"名前: {名前}\n種類: {種類.name}",
                color=discord.Color.green()
            ))
        else:
            await interaction.followup.send(embed=discord.Embed(
                title="すでにその種類のペットを飼っています！",
                color=discord.Color.red()
            ))

    @animal.command(
        name="status", description="ペットのステータスを確認します。"
    )
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse")
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def animal_status(
        self, interaction: discord.Interaction, 種類: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].Animals
        check = await self.is_keeping_animal(interaction.user, 種類.value)
        if not check:
            return await interaction.followup.send(embed=discord.Embed(
                title="まだそのペットを飼っていません！",
                description=f"/animal keeping で飼えます。",
                color=discord.Color.red()
            ))
        else:
            status = await self.get_animal_status(interaction.user, 種類.value)
            await interaction.followup.send(embed=discord.Embed(
                title=f"{status.get('Name', '名前')}のステータス",
                description=(
                    f"名前: {status.get('Name')}\n"
                    f"種類: {種類.name}\n"
                    f"レベル: {status.get('Level', 0)}\n"
                    f"XP: {status.get('XP', 0)}\n"
                    f"ステータス: {status.get('Status', 'いつも通り')}"
                ),
                color=discord.Color.blue()
            ))

    @animal.command(name="feed", description="ペットに餌をあげます。")
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse")
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def animal_feed(
        self, interaction: discord.Interaction, 種類: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].Animals

        status = await self.get_animal_status(interaction.user, 種類.value)
        if not status:
            return await interaction.followup.send(embed=discord.Embed(
                title="そのペットは飼っていません！",
                description="/animal keeping で飼えます。",
                color=discord.Color.red()
            ))

        now = datetime.utcnow()
        last_feed = status.get("LastFeed")

        if last_feed:
            elapsed = now - last_feed
            if elapsed < timedelta(hours=1):
                remaining = timedelta(hours=1) - elapsed
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                return await interaction.followup.send(embed=discord.Embed(
                    title="まだ餌をあげられません！",
                    description=f"次に餌をあげられるまで **{minutes}分{seconds}秒**",
                    color=discord.Color.orange()
                ))

        xp_gain = random.randint(5, 15)
        await self.add_xp(interaction.user, 種類.value, xp_gain)

        await db.update_one(
            {"User": interaction.user.id, "Kinds": 種類.value},
            {"$set": {"LastFeed": now}}
        )

        await interaction.followup.send(embed=discord.Embed(
            title=f"{status.get('Name', '名無し')}に餌をあげました！",
            description=f"XPが **+{xp_gain}** 増えたよ！",
            color=discord.Color.green()
        ))

async def setup(bot):
    await bot.add_cog(AnimalCog(bot))