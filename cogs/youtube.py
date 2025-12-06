import re
from discord.ext import commands
import discord
import random
import time
from discord import app_commands
from models import make_embed
import aiohttp
from youtube import settings

CHANNEL_REGEX = re.compile(r"^UC[0-9A-Za-z_-]{22}$")

async def subscribe_channel(channel_id, callback_url):
    topic = f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"

    data = {
        "hub.mode": "subscribe",
        "hub.topic": topic,
        "hub.callback": callback_url,
        "hub.verify": "async",
        "hub.secret": settings.HMAC_SECRET
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://pubsubhubbub.appspot.com/subscribe", data=data) as response:
            return response.status
        
class YoutubeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> YoutubeCog")

    youtube = app_commands.Group(
        name="youtube", description="Youtube関連のコマンドです。", allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @youtube.command(
        name="add", description="Youtube通知に追加します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def youtube_add_alert(self, interaction: discord.Interaction, youtubeチャンネルid: str, メンション: discord.Role = None):
        if not CHANNEL_REGEX.match(youtubeチャンネルid):
            return await interaction.response.send_message(embed=make_embed.error_embed(title="不正なYoutubeチャンネルidです。", description="正しいYoutubeチャンネルIDを入れてください。"))

        db = interaction.client.async_db["MainTwo"].YoutubeAlert
        if await db.find_one({"channel_id": youtubeチャンネルid, "guild_id": interaction.guild.id}):
            return await interaction.response.send_message(embed=make_embed.error_embed(title="すでに登録されています。"))
        
        await interaction.response.defer()

        count = await db.count_documents({"guild_id": interaction.guild_id})
        if count >= 3:
            return await interaction.followup.send(embed=make_embed.error_embed(title="三つまでしか登録できません。", description="不要なYoutube通知を削除してください。"))

        wh = await interaction.channel.create_webhook(name="SharkBot-Youtube")

        if メンション:
            await db.insert_one({
                "channel_id": youtubeチャンネルid,
                "guild_id": interaction.guild_id,
                "webhook_url": wh.url,
                "role_mention": メンション.mention
            })
        else:
            await db.insert_one({
                "channel_id": youtubeチャンネルid,
                "guild_id": interaction.guild_id,
                "webhook_url": wh.url
            })

        res = await subscribe_channel(youtubeチャンネルid, settings.CALLBACK)

        await interaction.followup.send(
            embed=make_embed.success_embed(title="登録しました。", description=f"ステータスコード: {res}")
        )

    @youtube.command(
        name="remove", description="Youtube通知から削除します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def youtube_remove_alert(self, interaction: discord.Interaction, youtubeチャンネルid: str):
        db = interaction.client.async_db["MainTwo"].YoutubeAlert
        await interaction.response.defer()

        data = await db.find_one({"channel_id": youtubeチャンネルid, "guild_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send(embed=make_embed.error_embed(title="そのチャンネルは登録されていません。"))

        await db.delete_one({"channel_id": youtubeチャンネルid, "guild_id": interaction.guild.id})

        # res = await unsubscribe_channel(youtubeチャンネルid, settings.CALLBACK)

        await interaction.followup.send(
            embed=make_embed.success_embed(title="登録を解除しました。")
        )

    @youtube.command(
        name="list", description="Youtube通知をリスト化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def youtube_list_alert(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].YoutubeAlert
        items = await db.find({"guild_id": interaction.guild.id}).to_list(length=None)
        text = "\n".join(f"- {item['channel_id']}" for item in items) or "なし"
        await interaction.response.send_message(embed=make_embed.success_embed(title="登録チャンネル一覧", description=text))

async def setup(bot):
    await bot.add_cog(YoutubeCog(bot))
