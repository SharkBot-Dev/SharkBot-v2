from discord.ext import commands
import discord
from discord import app_commands

import yt_dlp
import asyncio

from urllib.parse import urlparse

class MusicView(discord.ui.LayoutView):
    container = discord.ui.Container(
        discord.ui.TextDisplay("### 操作パネル"),
        discord.ui.ActionRow(discord.ui.Button(emoji="💿", custom_id="music_add+"), discord.ui.Button(emoji="⏭️", custom_id="music_skip+"), discord.ui.Button(emoji="⏹️", custom_id="music_stop+"), discord.ui.Button(emoji="📝", custom_id="music_quote+"), discord.ui.Button(emoji="❓", custom_id="music_help+")),
        accent_colour=discord.Colour.green()
    )

class YTDLSource:
    YTDL_OPTIONS = {
        'format': 'bestaudio',
        "noplaylist": True,
        "playlist_items": "1",
        "quiet": True,
        "no_warnings": True,
    }

    BASE_FFMPEG = '-nostdin'
    BASE_OPTIONS = '-vn -ac 2'

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
    def create_ffmpeg_player(cls, url: str, boost: bool = False, volume: int = 70):
        vol = max(0, min(volume, 100)) / 100

        if boost:
            audio_filter = f"volume={vol},equalizer=f=80:width_type=h:width=200:g=8"
        else:
            audio_filter = f"volume={vol}"

        options = f"-vn -af \"{audio_filter}\""

        return discord.FFmpegPCMAudio(
            url,
            before_options=cls.BASE_FFMPEG,
            options=options
        )

class ShuugiinSource:
    YTDL_OPTIONS = {
        'format': 'bestaudio',
        "noplaylist": True,
        "playlist_items": "1",
        "quiet": True,
        "no_warnings": True,
    }

    BASE_FFMPEG = '-nostdin'
    BASE_OPTIONS = '-vn -ac 2'

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
    def create_ffmpeg_player(cls, url: str, boost: bool = False):
        if boost:
            options = f"{cls.BASE_OPTIONS} -b:a 128k -filter:a \"equalizer=f=80:width_type=h:width=200:g=8\""
        else:
            options = f"{cls.BASE_OPTIONS} -b:a 64k"
        return discord.FFmpegPCMAudio(url, before_options=cls.BASE_FFMPEG, options=options)

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

        guild_conf = await self.music_queue_collection.find_one({"guild_id": guild_id})
        boost_enabled = guild_conf and guild_conf.get("boost") == "true"
        vol_setting = guild_conf.get("volume", 70)

        await self.now_play_set(interaction.guild.id, queue_item["title"])
        audio = YTDLSource.create_ffmpeg_player(queue_item['url'], boost=boost_enabled, volume=vol_setting)
        voice.play(audio, after=after_playing)
        await interaction.channel.send(f"再生中の曲: **{queue_item['title']}**")

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id.startswith("music_skip+"):
                    await interaction.response.defer(ephemeral=True)
                    voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
                    if voice and voice.is_playing():
                        voice.stop()
                elif custom_id.startswith("music_stop+"):
                    await interaction.response.defer(ephemeral=True)
                    if interaction.guild.voice_client:
                        await interaction.guild.voice_client.disconnect()
                    await self.db["NowPLay"].delete_one(
                        {"Guild": interaction.guild.id})
                elif custom_id.startswith("music_quote+"):
                    q_list = await self.get_queue(interaction.guild.id)
                    if not q_list:
                        await interaction.response.send_message("キューは空です。", ephemeral=True)
                    else:
                        desc = '\n'.join([f"{i+1}. {info['title']}" for i, info in enumerate(q_list)])
                        await interaction.response.send_message(embed=discord.Embed(title="現在のキュー", description=desc, color=discord.Color.green()), ephemeral=True)
                elif custom_id.startswith("music_add+"):
                    class MusicAddModal(discord.ui.Modal):
                        def __init__(self_):
                            super().__init__(title="音楽をキューに追加 (SoundCloudのみ)", timeout=180)

                        musicurl = discord.ui.Label(
                            text="音楽のURL",
                            description="音楽のURLを入力してください。",
                            component=discord.ui.TextInput(
                                style=discord.TextStyle.short, required=True
                            ),
                        )

                        async def on_submit(self_, interaction: discord.Interaction):
                            assert isinstance(self_.musicurl.component, discord.ui.TextInput)

                            if interaction.user.voice is None:
                                return await interaction.response.send_message("ボイスチャンネルに参加してください。")

                            parsed_url = urlparse(self_.musicurl.component.value)
                            host = parsed_url.hostname
                            if not (host == "soundcloud.com" or (host and host.endswith(".soundcloud.com"))):
                                return await interaction.response.send_message("SoundCloud以外に対応していません。")
                            
                            await interaction.response.defer()

                            if interaction.guild.voice_client is None:
                                await interaction.user.voice.channel.connect()

                            guild_conf = await self.music_queue_collection.find_one({"guild_id": interaction.guild.id})
                            boost_enabled = guild_conf and guild_conf.get("boost") == "true"
                            vol_setting = guild_conf.get("volume", 70)

                            source_info = await YTDLSource.create_source(self_.musicurl.component.value)

                            voice = discord.utils.get(interaction.client.voice_clients, guild=interaction.guild)

                            async def add_to_queue(guild_id, item):
                                await interaction.client.async_db['Main'].MusicQueue.update_one(
                                    {"guild_id": guild_id},
                                    {"$push": {"queue": item}},
                                    upsert=True
                                )

                            if not voice.is_playing():
                                audio = YTDLSource.create_ffmpeg_player(source_info['url'], boost=boost_enabled, volume=vol_setting)
                                voice.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction, interaction.guild.id), interaction.client.loop))
                                await interaction.channel.send(f"再生中の曲: **{source_info['title']}**")
                            else:
                                await add_to_queue(interaction.guild.id, source_info)
                                await interaction.channel.send(f"キューに追加: **{source_info['title']}**")
                    await interaction.response.send_modal(MusicAddModal())
                elif custom_id.startswith('music_help+'):
                    await interaction.response.send_message(ephemeral=True, content="ボタンの説明\n> 💿 .. 音楽を追加する\n> ⏭️ .. 音楽をスキップする\n> ⏹️ .. 音楽をストップする\n> 📝 .. キューリストを取得する\n> ❓ .. ヘルプを表示する")
        except:
            return

    music = app_commands.Group(
        name="music", description="音楽関連のコマンドです。"
    )

    @music.command(name="play", description="音楽を再生します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_play(
        self, interaction: discord.Interaction, url: str = None, ファイル: discord.Attachment = None
    ):
        if interaction.user.voice is None:
            return await interaction.response.send_message("ボイスチャンネルに参加してください。")

        if interaction.guild.voice_client is None:
            await interaction.user.voice.channel.connect(self_deaf=True)

        voice = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)

        if ファイル:
            MAX_FILE_SIZE = 15 * 1024 * 1024
            if ファイル.size > MAX_FILE_SIZE:
                return await interaction.response.send_message(
                    f"ファイルサイズが大きすぎます。（上限 {MAX_FILE_SIZE // (1024*1024)}MB）"
                )
            
            if not ファイル.filename.endswith(('.mp3', '.wav', '.mp4')):
                return await interaction.response.send_message(content="そのファイルは対応していません。\n対応ファイル: `.mp3`, `.wav`, `.mp4`")

            await interaction.response.defer()

            item = {
                "title": ファイル.filename,
                "url": ファイル.url,
                "source": "file"
            }

            if not voice.is_playing():
                guild_conf = await self.music_queue_collection.find_one({"guild_id": interaction.guild.id})
                boost_enabled = guild_conf and guild_conf.get("boost") == "true"
                vol_setting = guild_conf.get("volume", 70)

                audio = YTDLSource.create_ffmpeg_player(item["url"], boost=boost_enabled, volume=vol_setting)
                voice.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction, interaction.guild.id), self.bot.loop))
                await self.now_play_set(interaction.guild.id, item["title"])
                await interaction.channel.send(f"再生中の曲: **{item['title']}**")
            else:
                await self.add_to_queue(interaction.guild.id, item)
                await interaction.channel.send(f"キューに追加: **{item['title']}**")

            return await interaction.followup.send(view=MusicView())

        if url:
            parsed_url = urlparse(url)
            host = parsed_url.hostname
            if (host == "soundcloud.com" or (host and host.endswith(".soundcloud.com"))):
                await interaction.response.defer()

                guild_conf = await self.music_queue_collection.find_one({"guild_id": interaction.guild.id})
                boost_enabled = guild_conf and guild_conf.get("boost") == "true"
                vol_setting = guild_conf.get("volume", 70)

                source_info = await YTDLSource.create_source(url)

                if not voice.is_playing():
                    audio = YTDLSource.create_ffmpeg_player(source_info['url'], boost=boost_enabled, volume=vol_setting)
                    voice.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction, interaction.guild.id), self.bot.loop))
                    await self.now_play_set(interaction.guild.id, source_info["title"])
                    await interaction.channel.send(f"再生中の曲: **{source_info['title']}**")
                else:
                    await self.add_to_queue(interaction.guild.id, source_info)
                    await interaction.channel.send(f"キューに追加: **{source_info['title']}**")

                return await interaction.followup.send(view=MusicView())
            elif (host == "shugiintv.go.jp" or (host and host.endswith(".shugiintv.go.jp"))):
                await interaction.response.defer()

                source_info = await ShuugiinSource.create_source(url)

                if not voice.is_playing():
                    audio = ShuugiinSource.create_ffmpeg_player(source_info['url'])
                    voice.play(audio, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(interaction, interaction.guild.id), self.bot.loop))
                    await self.now_play_set(interaction.guild.id, source_info["title"])
                    await interaction.channel.send(f"再生中の曲: **{source_info['title']}**")
                else:
                    await self.add_to_queue(interaction.guild.id, source_info)
                    await interaction.channel.send(f"キューに追加: **{source_info['title']}**")

                return await interaction.followup.send(view=MusicView())
            else:
                return await interaction.response.send_message("SoundCloud以外に対応していません。")

        return await interaction.response.send_message("URL または ファイルを指定してください。")

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

    @music.command(name="boost", description="低音ブーストをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_boost(
        self, interaction: discord.Interaction, 有効化するか: bool
    ):
        await self.music_queue_collection.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"boost": 'true' if 有効化するか else 'false'}},
            upsert=True
        )
        await interaction.response.send_message(embed=discord.Embed(title=f"低音ブーストを {'有効化' if 有効化するか else '無効化'} しました。", description="SoundCloudとファイルのみ適用されます。", color=discord.Color.green()))

    @music.command(name="volume", description="音量を設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        音量=[
            app_commands.Choice(name="30%", value="30"),
            app_commands.Choice(name="50%", value="50"),
            app_commands.Choice(name="70%", value="70"),
            app_commands.Choice(name="100%", value="100"),
        ]
    )
    async def music_volume(
        self, interaction: discord.Interaction, 音量: app_commands.Choice[str]
    ):
        await self.music_queue_collection.update_one(
            {"guild_id": interaction.guild.id},
            {"$set": {"volume": int(音量.value)}},
            upsert=True
        )
        await interaction.response.send_message(embed=discord.Embed(title=f"音量を {音量.value} にしました。", description="SoundCloudとファイルのみ適用されます。", color=discord.Color.green()))

    @music.command(name="source", description="対応ソースを表示します")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def music_source(
        self, interaction: discord.Interaction
    ):
        await interaction.response.send_message(embed=discord.Embed(title="対応ソース", color=discord.Color.green())
                                                .add_field(name="SoundCloud", value="音楽再生する用です。", inline=False)
                                                .add_field(name="衆議院配信", value="説明を忘れました。", inline=False)
                                                .add_field(name="ファイル", value=".mp3などが対応しています。", inline=False))

async def setup(bot):
    await bot.add_cog(MusicCog(bot))
