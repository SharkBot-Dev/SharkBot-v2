import asyncio
import datetime
import os
import re
import time
import aiohttp
import discord
from discord.ext import commands

from discord import app_commands

from consts import badword, settings
from models import command_disable, is_ban, make_embed

from google.genai.client import Client
from google.genai.types import GenerateContentConfig

cooldown_aichat = {}


class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def is_premium(self, user: discord.User):
        db = self.bot.async_db["Main"].PremiumUser

        user_data = await db.find_one({"User": user.id})

        if not user_data:
            return False
        else:
            return True

    async def add_cooldown(
        self,
        author: discord.User,
        cooldown_type: str,
        cooldown: int = 3600,
    ):
        db = self.bot.async_db["MainTwo"].AICooldown
        key = f"{author.id}-{cooldown_type}"
        current_time = time.time()

        user_data = await db.find_one({"_id": key})

        if user_data:
            last_time = user_data.get("last_time", 0)
            elapsed = current_time - last_time

            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                return False, remaining

            await db.update_one(
                {"_id": key},
                {"$set": {"last_time": current_time}},
            )

        else:
            await db.insert_one(
                {
                    "_id": key,
                    "User": author.id,
                    "last_time": current_time,
                    "type": cooldown_type,
                }
            )

        return True, 0

    aichat = app_commands.Group(
        name="ai",
        description="寄付者限定のAI機能を使用します。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    @aichat.command(name="keigo", description="AIで敬語を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def aichat_keigo(self, interaction: discord.Interaction, 口語: str):
        await interaction.response.defer(ephemeral=True)

        a_c, ti = await self.add_cooldown(interaction.user, "keigo", 15)
        if not a_c:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="クールダウン中です。",
                    description=f"あと{ti}秒お待ちください。",
                )
            )

        json_data = {
            "kougo_writing": 口語,
            "mode": "direct",
            "translation_id": "",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://y026dvhch0.execute-api.ap-northeast-1.amazonaws.com/translate",
                json=json_data,
            ) as response:
                response_data = await response.json()
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="敬語を生成しました。",
                        description=response_data.get(
                            "content", "敬語に変換できませんでした。"
                        ),
                    )
                )
                
async def setup(bot):
    await bot.add_cog(AICog(bot))
