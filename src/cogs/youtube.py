import json
import re
from discord.ext import commands
import discord
import random
import time
from discord import app_commands
from models import make_embed
import aiohttp
from youtube import settings
from yt_dlp import YoutubeDL

CHANNEL_REGEX = re.compile(r"^UC[0-9A-Za-z_-]{22}$")
YOUTUBE_ID_REGEX = re.compile(r".*(?:youtu\.be\/|v\/|vi\/|e\/|embed\/|watch\?v=|watch\?.+&v=)([^#&?]{11}).*")

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

        channel: discord.TextChannel = interaction.channel
        webhooks = await channel.webhooks()

        webhook = None
        for wh in webhooks:
            if wh.name == "SharkBot-Youtube":
                webhook = wh
                break

        if webhook is None:
            webhook = await channel.create_webhook(name="SharkBot-Youtube")

        if メンション:
            await db.insert_one({
                "channel_id": youtubeチャンネルid,
                "guild_id": interaction.guild_id,
                "webhook_url": webhook.url,
                "role_mention": メンション.mention
            })
        else:
            await db.insert_one({
                "channel_id": youtubeチャンネルid,
                "guild_id": interaction.guild_id,
                "webhook_url": webhook.url
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

    @youtube.command(
        name="thumbnail", description="Youtube動画のサムネを取得します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def youtube_thumbnail(self, interaction: discord.Interaction, 動画のurl: str):
        await interaction.response.defer()
        match = YOUTUBE_ID_REGEX.search(動画のurl)
        v_id = match.group(1)
        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.youtube.com/youtubei/v1/player', headers={
                "Content-Type": "application/json"
            }, data=json.dumps({
                "context":{
                    "client":{
                    "clientName": "WEB",
                    "clientVersion": "2.20210721.00.00",
                    }
                },
                "videoId": v_id
            })) as response:
                data = await response.json()

        try:
            thumbnails = data["videoDetails"]["thumbnail"]["thumbnails"]
        except KeyError:
            return await interaction.followup.send("サムネイル情報を取得できませんでした。")

        best_thumb = thumbnails[-1]["url"]

        embed = make_embed.success_embed(
            title="サムネイルを取得しました。",
            description=f"動画ID: `{v_id}`"
        ).set_image(url=best_thumb)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(YoutubeCog(bot))
