import asyncio
import os
import re
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

    aichat = app_commands.Group(
        name="ai",
        description="寄付者限定のAI機能を使用します。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    @aichat.command(name="name", description="ユーザーの新しい名前を考えてもらいます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
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
