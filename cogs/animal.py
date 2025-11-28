from datetime import datetime, timedelta
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import random
from models import make_embed


class AnimalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def one_kind_animal(self, user: discord.User):
        db = self.bot.async_db["Main"].Animals
        try:
            return await db.find_one({"User": user.id}, {"_id": False}) is not None
        except Exception:
            return False

    async def is_keeping_animal(self, user: discord.User, kinds: str):
        db = self.bot.async_db["Main"].Animals
        try:
            return (
                await db.find_one({"User": user.id, "Kinds": kinds}, {"_id": False})
                is not None
            )
        except Exception:
            return False

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
        # レベルアップ判定
        await self.check_level_up(user, kinds)

    async def get_animal_status(self, user: discord.User, kinds: str):
        db = self.bot.async_db["Main"].Animals
        try:
            return await db.find_one({"User": user.id, "Kinds": kinds}, {"_id": False})
        except Exception:
            return None

    async def change_status(self, user: discord.User, kinds: str, message: str):
        db = self.bot.async_db["Main"].Animals
        await db.update_one(
            {"User": user.id, "Kinds": kinds}, {"$set": {"Status": message}}
        )

    async def check_level_up(self, user: discord.User, kinds: str):
        db = self.bot.async_db["Main"].Animals
        status = await self.get_animal_status(user, kinds)
        if status and status.get("XP", 0) >= status.get("IV", 60):
            await db.update_one({"User": user.id, "Kinds": kinds}, {"$set": {"XP": 0}})
            await self.add_level(user, kinds, 1)

    @commands.Cog.listener("on_message")
    async def on_message_animal(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not await self.one_kind_animal(message.author):
            return

        achi_db = self.bot.async_db["Main"].Animals
        async for animal in achi_db.find({"User": message.author.id}):
            try:
                kinds = animal.get("Kinds", "None")
                status = await self.get_animal_status(message.author, kinds)

                await self.add_xp(message.author, kinds, 1)

                now = datetime.utcnow()
                last_feed = status.get("LastFeed")

                if last_feed and isinstance(last_feed, datetime):
                    if now - last_feed >= timedelta(hours=1):
                        await self.change_status(
                            message.author,
                            animal.get("Kinds", "None"),
                            "餌をほしがっている・・",
                        )

            except Exception:
                continue

    animal = app_commands.Group(
        name="animal", description="ペットを関連のコマンドです。"
    )

    @animal.command(name="keeping", description="ペットを新しく飼います。")
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse"),
            app_commands.Choice(name="牛", value="caw"),
            app_commands.Choice(name="ハムスター", value="hamster"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def animal_keeping(
        self,
        interaction: discord.Interaction,
        種類: app_commands.Choice[str],
        名前: str,
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].Animals
        if not await self.is_keeping_animal(interaction.user, 種類.value):
            await db.update_one(
                {"User": interaction.user.id, "Kinds": 種類.value},
                {
                    "$set": {
                        "User": interaction.user.id,
                        "Kinds": 種類.value,
                        "Name": 名前,
                        "Level": 0,
                        "XP": 0,
                        "Status": "いつも通り",
                        "IV": random.randint(100, 130),
                        "LastFeed": None,
                    }
                },
                upsert=True,
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="ペットを飼いました！",
                    description=f"名前: {名前}\n種類: {種類.name}",
                )
            )
        else:
            await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="すでにその種類のペットを飼っています！"
                )
            )

    @animal.command(name="status", description="ペットのステータスを確認します。")
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse"),
            app_commands.Choice(name="牛", value="caw"),
            app_commands.Choice(name="ハムスター", value="hamster"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def animal_status(
        self,
        interaction: discord.Interaction,
        種類: app_commands.Choice[str],
        ユーザー: discord.User = None,
    ):
        await interaction.response.defer()
        target = ユーザー or interaction.user

        if not await self.is_keeping_animal(target, 種類.value):
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="まだそのペットを飼っていません！",
                    description="/animal keeping で飼えます。",
                )
            )

        status = await self.get_animal_status(target, 種類.value)

        now = datetime.utcnow()
        last_feed = status.get("LastFeed")

        if last_feed and isinstance(last_feed, datetime):
            if now - last_feed >= timedelta(hours=1):
                await self.change_status(target, 種類.value, "餌をほしがっている・・")

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{status.get('Name', '名前')}のステータス",
                description=(
                    f"名前: {status.get('Name')}\n"
                    f"種類: {種類.name}\n"
                    f"レベル: {status.get('Level', 0)}\n"
                    f"XP: {status.get('XP', 0)} / {status.get('IV', 60)}\n"
                    f"ステータス: {status.get('Status', 'いつも通り')}"
                ),
            )
        )

    @animal.command(name="feed", description="ペットに餌をあげます。")
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse"),
            app_commands.Choice(name="牛", value="caw"),
            app_commands.Choice(name="ハムスター", value="hamster"),
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
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="そのペットは飼っていません！",
                    description="/animal keeping で飼えます。",
                )
            )

        now = datetime.utcnow()
        last_feed = status.get("LastFeed")

        if last_feed and isinstance(last_feed, datetime):
            elapsed = now - last_feed
            if elapsed < timedelta(hours=1):
                remaining = timedelta(hours=1) - elapsed
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="まだ餌をあげられません！",
                        description=f"次に餌をあげられるまで **{minutes}分{seconds}秒**",
                    )
                )

        xp_gain = random.randint(5, 15)
        await self.add_xp(interaction.user, 種類.value, xp_gain)

        await db.update_one(
            {"User": interaction.user.id, "Kinds": 種類.value},
            {"$set": {"LastFeed": now}},
        )
        await self.change_status(interaction.user, 種類.value, "いつも通り")

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{status.get('Name', '名無し')}に餌をあげました！",
                description=f"XPが **+{xp_gain}** 増えたよ！",
            )
        )

    @animal.command(name="train", description="ペットをしつけ（訓練）します。")
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="犬", value="dog"),
            app_commands.Choice(name="猫", value="cat"),
            app_commands.Choice(name="馬", value="horse"),
            app_commands.Choice(name="牛", value="caw"),
            app_commands.Choice(name="ハムスター", value="hamster"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def animal_train(
        self, interaction: discord.Interaction, 種類: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].Animals

        status = await self.get_animal_status(interaction.user, 種類.value)
        if not status:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="そのペットは飼っていません！",
                    description="/animal keeping で飼えます。",
                )
            )

        now = datetime.utcnow()
        last_feed = status.get("LastTrain")

        if last_feed and isinstance(last_feed, datetime):
            elapsed = now - last_feed
            if elapsed < timedelta(hours=1):
                remaining = timedelta(hours=1) - elapsed
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="まだ訓練できません！",
                        description=f"次に訓練ができるまで **{minutes}分{seconds}秒**",
                    )
                )

        success = random.random() < 0.7
        if success:
            xp_gain = random.randint(10, 20)
            await self.add_xp(interaction.user, 種類.value, xp_gain)
            result_text = f"訓練に成功しました！ \nXPが **+{xp_gain}** 増えたよ！"
        else:
            xp_gain = random.randint(0, 5)
            await self.add_xp(interaction.user, 種類.value, xp_gain)
            result_text = (
                f"訓練に失敗しました… \nXPが **+{xp_gain}** しか増えなかった。"
            )

        await self.change_status(interaction.user, 種類.value, "訓練中…")

        await db.update_one(
            {"User": interaction.user.id, "Kinds": 種類.value},
            {"$set": {"LastTrain": now}},
        )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{status.get('Name', '名無し')}の訓練結果",
                description=result_text,
            )
        )


async def setup(bot):
    await bot.add_cog(AnimalCog(bot))
