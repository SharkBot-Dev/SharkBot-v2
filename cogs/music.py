from discord.ext import commands
import discord
from discord import app_commands

import yt_dlp
import asyncio

class YTDLSource:
    YTDL_OPTIONS = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        'quiet': True,
    }

    FFMPEG_OPTIONS = {
        'before_options': '-nostdin',
        'options': '-vn'
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @classmethod
    async def create_source(cls, search: str):
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(search, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        return {
            'title': data.get('title'),
            'url': data.get('url'),
            'webpage_url': data.get('webpage_url'),
        }

    @classmethod
    def create_ffmpeg_player(cls, url):
        return discord.FFmpegPCMAudio(url, **cls.FFMPEG_OPTIONS)

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_queues = {}
        self.db = self.bot.async_db["Main"]
        self.music_queue_collection = self.db["MusicQueue"]
        print(f"init -> MusicCog")

    async def get_queue(self, guild_id):
        doc = await self.music_queue_collection.find_one({"guild_id": guild_id})
        return doc["queue"] if doc else []

    async def add_to_queue(self, guild_id, item):
        await self.music_queue_collection.update_one(
            {"guild_id": guild_id},
            {"$push": {"queue": item}},
            upsert=True
        )

    async def pop_from_queue(self, guild_id):
        doc = await self.music_queue_collection.find_one({"guild_id": guild_id})
        if doc and doc["queue"]:
            first_item = doc["queue"][0]
            await self.music_queue_collection.update_one(
                {"guild_id": guild_id},
                {"$pop": {"queue": -1}}  # 先頭を削除
            )
            return first_item
        return None

    async def clear_queue(self, guild_id):
        await self.music_queue_collection.update_one(
            {"guild_id": guild_id},
            {"$set": {"queue": []}},
            upsert=True
        )

    async def now_play_set(self, guild, title):
        await self.db["NowPLay"].replace_one(
            {"Guild": guild}, 
            {"Guild": guild, "Title": title}, 
            upsert=True
        )

    async def play_next(self, interaction, guild_id):
        queue_item = await self.pop_from_queue(guild_id)
        if not queue_item:
            await self.db["NowPLay"].delete_one(
                {"Guild": interaction.guild.id})
            return

        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        def after_playing(error):
            fut = self.play_next(interaction, guild_id)
            asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

        await self.now_play_set(interaction.guild.id, queue_item["title"])
        audio = YTDLSource.create_ffmpeg_player(queue_item['url'])
        voice.play(audio, after=after_playing)
        await interaction.channel.send(f"再生中の曲: **{queue_item['title']}**")

    music = app_commands.Group(
        name="music", description="音楽関連のコマンドです。"
    )

    @music.command(name="play", description="音楽を再生します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_play(
        self, interaction: discord.Interaction, url: str
    ):
        if interaction.user.voice is None:
            return await interaction.response.send_message("ボイスチャンネルに参加してください。")

        if not "soundcloud.com" in url:
            return await interaction.response.send_message("SoundCloud以外に対応していません。")
        
        await interaction.response.defer()

        if interaction.guild.voice_client is None:
            await interaction.user.voice.channel.connect()

        source_info = await YTDLSource.create_source(url)
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if not voice.is_playing():
            audio = YTDLSource.create_ffmpeg_player(source_info['url'])
            voice.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction, interaction.guild.id), self.bot.loop))
            await self.now_play_set(interaction.guild.id, source_info["title"])
            await interaction.channel.send(f"再生中の曲: **{source_info['title']}**")
        else:
            await self.add_to_queue(interaction.guild.id, source_info)
            await interaction.channel.send(f"キューに追加: **{source_info['title']}**")

        await interaction.delete_original_response()

    @music.command(name="skip", description="音楽をスキップします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_skip(
        self, interaction: discord.Interaction
    ):
        await interaction.response.defer()
        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            voice.stop()
            await interaction.delete_original_response()
        else:
            await interaction.followup.send("現在再生中の音楽がありません。")

    @music.command(name="stop", description="音楽をストップします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_stop(
        self, interaction: discord.Interaction
    ):
        await interaction.response.defer()
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
        await self.db["NowPLay"].delete_one(
            {"Guild": interaction.guild.id})
        await interaction.followup.send("再生を停止し、キューをクリアしました。")

    @music.command(name="queue", description="キューを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_queue(
        self, interaction: discord.Interaction
    ):
        q_list = await self.get_queue(interaction.guild.id)
        if not q_list:
            await interaction.response.send_message("キューは空です。", ephemeral=True)
        else:
            desc = '\n'.join([f"{i+1}. {info['title']}" for i, info in enumerate(q_list)])
            await interaction.response.send_message(embed=discord.Embed(title="現在のキュー", description=desc, color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
