import asyncio
import os
import re
import time
import aiohttp
import discord
from discord.ext import commands

from discord import app_commands

from consts import badword, settings
from models import command_disable, make_embed

from google.genai.client import Client

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

    @aichat.command(name="name", description="ユーザーの新しい名前を考えてもらいます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def cogs_setting(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User = None
    ):
        user = ユーザー.display_name if ユーザー else interaction.user.display_name

        check = await self.is_premium(interaction.user)
        if not check:
            return await interaction.response.send_message(ephemeral=True, embed=make_embed.error_embed(title="あなたは寄付者ではありません！", description="この機能は寄付者のみ使用できます。\n現在寄付は受け付けておりません。"))

        await interaction.response.defer()

        a_c, ti = await self.add_cooldown(interaction.user, "name", 60)
        if not a_c:
            return await interaction.followup.send(embed=make_embed.error_embed(title="クールダウン中です。", description=f"あと{ti}秒お待ちください。"))

        api_key = settings.GEMINI_APIKEY
        if not api_key:
            return

        client = await asyncio.to_thread(Client, api_key=api_key)

        prompt = f"""
        以下のユーザー名の人に合う新しい名前を三つ考えてください。
        名前を出力する際は、必ず「」で囲むようにしてください。
        ユーザー名: {user}
        """

        try:

            name = await client.aio.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
        except:
            return await interaction.followup.send(embed=make_embed.error_embed(title="エラーが発生しました。", description="レートリミットである可能性があります。"))

        names = re.findall(r'「.+」', name.text)

        if not names:
            embed = make_embed.error_embed(
                title="名前の生成に失敗しました", 
                description=f"AIが名前を生成できませんでした。"
            )
            await interaction.followup.send(embed=embed)
            return

        embed = make_embed.success_embed(title=f"「{user}」さんに合う新しい名前を考えました。")
        for i, n in enumerate(names):
            embed.add_field(name=f"候補 {i+1}", value=n, inline=False)
                
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AICog(bot))
