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

    @aichat.command(name="name", description="ユーザーの新しい名前を考えてもらいます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def aichat_name(
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
ユーザー名の人に合う新しい名前を三つ考えてください。
名前を出力する際は、必ず「」で囲むようにしてください。
ユーザー名: {user}
"""

        try:

            name = await client.aio.models.generate_content(
                model="gemma-3-27b-it",
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

    @aichat.command(name="keigo", description="AIで敬語を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def aichat_keigo(
        self,
        interaction: discord.Interaction,
        口語: str
    ):
        await interaction.response.defer(ephemeral=True)

        a_c, ti = await self.add_cooldown(interaction.user, "keigo", 15)
        if not a_c:
            return await interaction.followup.send(embed=make_embed.error_embed(title="クールダウン中です。", description=f"あと{ti}秒お待ちください。"))

        json_data = {
            'kougo_writing': 口語,
            'mode': 'direct',
            'translation_id': '',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://y026dvhch0.execute-api.ap-northeast-1.amazonaws.com/translate",
                json=json_data,
            ) as response:
                response_data = await response.json()
                await interaction.followup.send(embed=make_embed.success_embed(title="敬語を生成しました。", description=response_data.get("content", "敬語に変換できませんでした。")))

    @commands.Cog.listener("on_message")
    async def on_message_aichat(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        db = self.bot.async_db["MainTwo"].AIChat

        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return

        if dbfind is None:
            return
        
        if not dbfind.get("Enabled"):
            return
        
        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = cooldown_aichat.get(message.channel.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_aichat[message.channel.id] = current_time

        try:
            webhooks = await message.channel.webhooks()

            webhook = None
            for wh in webhooks:
                if wh.name == "SharkBot-AIChat":
                    webhook = wh
                    break

            if webhook is None:
                webhook = await message.channel.create_webhook(name="SharkBot-AIChat")
        except:
            return

        check = await self.is_premium(message.author)
        if not check:
            a_c, ti = await self.add_cooldown(message.author, "aichat", 1800)
            if not a_c:
                return await message.reply(embed=make_embed.error_embed(title="AIChatは一人当たり30分当たり1回までです！"))

        api_key = settings.GEMINI_APIKEY
        if not api_key:
            return

        client = await asyncio.to_thread(Client, api_key=api_key)

        prompt = f"""
# Context Information
現在、以下の状況でユーザーと対話しています。これらの情報を踏まえた回答をしてください。
- ユーザー名: {message.author.name}
- 現在時刻: {datetime.datetime.now().strftime("%d年%m月%Y日, %H時%M分%S秒")}
- サーバー/プラットフォーム名: {message.guild.name}

以下は、ユーザーからのプロンプトです。
「{message.clean_content}」
"""

        try:

            text = await client.aio.models.generate_content(
                model="gemma-3-27b-it",
                contents=prompt
            )

            chunks = []
            for i in range(0, len(text.text), 1000):
                chunks.append(text.text[i:i+1000])

            for c in chunks:
                await webhook.send(content=c, username="GoogleのAI", avatar_url=self.bot.user.avatar.url)
                await asyncio.sleep(2)
        except Exception as e:
            # print(f"AIChatError: {e}")
            return await message.reply(embed=make_embed.error_embed(title="エラーが発生しました。", description="レートリミットである可能性があります。"))

    @aichat.command(name="chat", description="AIに質問できるチャンネルを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def aichat_chat(
        self,
        interaction: discord.Interaction
    ):
        db = interaction.client.async_db["MainTwo"].AIChat
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Enabled": True, "Channel": interaction.channel.id}},
                upsert=True,
            )
            return await interaction.response.send_message(embed=make_embed.success_embed(title="AIチャットを有効化しました。"))
        else:
            if not dbfind.get('Enabled'):
                await db.update_one(
                    {"Guild": interaction.guild.id},
                    {"$set": {"Enabled": True, "Channel": interaction.channel.id}},
                    upsert=True,
                )
                return await interaction.response.send_message(embed=make_embed.success_embed(title="AIチャットを有効化しました。"))
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Enabled": False}},
                upsert=True,
            )
            return await interaction.response.send_message(embed=make_embed.success_embed(title="AIチャットを無効化しました。"))

async def setup(bot):
    await bot.add_cog(AICog(bot))
