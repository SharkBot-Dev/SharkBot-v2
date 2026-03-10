from datetime import datetime, timedelta
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import random
from models import make_embed

from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorCollection

class AnimalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = self.bot.async_db["DashboardBot"].Account

    animal = app_commands.Group(
        name="animal", description="ペット関連のコマンドです。"
    )

    @animal.command(name="keeping", description="ペットを飼います。(1000コイン)")
    async def animal_keeping(self, interaction: discord.Interaction, 名前: str):
        db = self.db

        if not isinstance(db, AsyncIOMotorCollection):
            return
        
        check = await db.find_one({
            "user_id": interaction.user.id
        })

        if not check:
            await interaction.response.send_message(embed=make_embed.error_embed(title="アカウントが存在しません。", description="/account create で作成可能"), ephemeral=True)
            return
        
        if check.get("money", 0) < 1000:
            await interaction.response.send_message(embed=make_embed.error_embed(title="コインが足りません。", description="/account work or daily で稼げます。"), ephemeral=True)
            return

        await interaction.response.defer()

        new_pet = {
            "name": 名前,
            "items": [],
            "value": 500,
            "last_train": datetime.fromtimestamp(0)
        }

        await db.update_one({
            "user_id": interaction.user.id
        }, {
            "$push": {"pets": new_pet},
            "$inc": {"money": -1000}
        })

        await interaction.followup.send(embed=make_embed.success_embed(title=f"「{名前}」を飼い始めました！"))

    async def choice_animal_names_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        db = self.db
        check = await db.find_one({"user_id": interaction.user.id})
        
        if not check or "pets" not in check:
            return []

        return [
            app_commands.Choice(name=p["name"], value=p["name"])
            for p in check["pets"] if current.lower() in p["name"].lower()
        ][:25]

    @animal.command(name="status", description="ペットのステータスを確認します。")
    @app_commands.autocomplete(名前=choice_animal_names_autocomplete)
    async def animal_status(self, interaction: discord.Interaction, 名前: str):
        db = self.db
        check = await db.find_one({"user_id": interaction.user.id})

        pet = next((p for p in check.get("pets", []) if p["name"] == 名前), None)

        if not pet:
            await interaction.response.send_message("その名前のペットは見つかりませんでした。", ephemeral=True)
            return

        await interaction.response.send_message(embed=make_embed.success_embed(title=f"{名前}のステータス").add_field(name="名前", value=pet["name"], inline=False).add_field(name="価値", value=pet["value"], inline=False))

    @animal.command(name="feed", description="ペットに餌をあげます。(50コイン / 価値+50)")
    @app_commands.autocomplete(名前=choice_animal_names_autocomplete)
    async def animal_feed(self, interaction: discord.Interaction, 名前: str):
        db = self.db
        user_id = interaction.user.id

        user_data = await db.find_one({"user_id": user_id})
        if not user_data:
            await interaction.response.send_message(embed=make_embed.error_embed(title="アカウントが存在しません。", description="/account create で作成可能"), ephemeral=True)
            return
        
        if user_data.get("money", 0) < 50:
            await interaction.response.send_message(embed=make_embed.error_embed(title="コインが足りません。", description="50コイン必要です。"), ephemeral=True)
            return

        result = await db.update_one(
            {"user_id": user_id, "pets.name": 名前},
            {
                "$inc": {
                    "money": -50, 
                    "pets.$.value": 50
                }
            }
        )

        if result.modified_count == 0:
            await interaction.response.send_message(f"「{名前}」というペットは見つかりませんでした。", ephemeral=True)
            return

        await interaction.response.send_message(embed=make_embed.success_embed(title=f"「{名前}」に餌をあげました！", description="価値が50上がりました。"))

    @animal.command(name="train", description="ペットを訓練します。")
    @app_commands.autocomplete(名前=choice_animal_names_autocomplete)
    async def animal_train(self, interaction: discord.Interaction, 名前: str):
        db = self.db
        user_id = interaction.user.id
        now = datetime.now()
        cooldown_seconds = 3600

        user_data = await db.find_one({"user_id": user_id})
        pet = next((p for p in user_data.get("pets", []) if p["name"] == 名前), None)

        if not pet:
            await interaction.response.send_message(f"「{名前}」は見つかりませんでした。", ephemeral=True)
            return

        last_train = pet.get("last_train")
        if isinstance(last_train, datetime):
            elapsed = (now - last_train).total_seconds()
            if elapsed < cooldown_seconds:
                remaining = int((cooldown_seconds - elapsed) / 60)
                await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="まだ訓練できません。",
                        description=f"あと {remaining}分 休憩が必要です。"
                    ), ephemeral=True
                )
                return

        value = random.randint(50, 150)

        await db.update_one(
            {"user_id": user_id, "pets.name": 名前},
            {
                "$inc": {"pets.$.value": value},
                "$set": {"pets.$.last_train": now}
            }
        )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"「{名前}」を訓練しました！",
                description=f"価値が{value}上昇しました。"
            )
        )

    @animal.command(name="sell", description="ペットを売却してコインにします。")
    @app_commands.autocomplete(名前=choice_animal_names_autocomplete)
    async def animal_sell(self, interaction: discord.Interaction, 名前: str):
        db = self.db
        user_id = interaction.user.id

        user_data = await db.find_one({"user_id": user_id})
        if not user_data or "pets" not in user_data:
            await interaction.response.send_message(embed=make_embed.error_embed(title="ペットを飼っていません。"), ephemeral=True)
            return

        pet = next((p for p in user_data["pets"] if p["name"] == 名前), None)

        if not pet:
            await interaction.response.send_message(f"「{名前}」というペットは見つかりませんでした。", ephemeral=True)
            return

        sell_price = pet.get("value", 0)

        await db.update_one({
            "user_id": user_id
        }, {
            "$pull": {"pets": {"name": 名前}},
            "$inc": {"money": sell_price} 
        })

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="ペットを売却しました。",
                description=f"「{名前}」を売却し、{sell_price}コイン を受け取りました。"
            )
        )

async def setup(bot):
    await bot.add_cog(AnimalCog(bot))
