import re
from discord.ext import commands
import discord
import time
import asyncio
import io
import aiohttp
import urllib.parse
from discord import app_commands

from models import tts_dict

cooldown_autojoin = {}
cooldown_tts = {}


class DictGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="dict", description="読み上げ辞書を設定します。")

    @app_commands.command(name="add", description="読み上げ辞書を追加します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def dict_add(
        self, interaction: discord.Interaction, ワード: str, 置き換えるワード: str
    ):
        ttsdict = self.bot.async_db["Main"].TTSWord
        await ttsdict.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Word": ワード,
                    "ReplaceWord": 置き換えるワード,
                }
            },
            upsert=True,
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="置き換えるワードを追加しました。", color=discord.Color.green()
            )
        )

    @app_commands.command(name="remove", description="読み上げの辞書から削除します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def dict_remove(self, interaction: discord.Interaction, ワード: str):
        ttsdict = self.bot.async_db["Main"].TTSWord
        await ttsdict.delete_one({"Guild": interaction.guild.id, "Word": ワード})
        await interaction.response.send_message(
            embed=discord.Embed(
                title="置き換えるワードを削除しました。", color=discord.Color.green()
            )
        )

    @app_commands.command(name="list", description="読み上げの辞書をリスト化します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def dict_list(self, interaction: discord.Interaction, ワード: str):
        ttsdict = self.bot.async_db["Main"].TTSWord
        r = (
            await ttsdict.find({"Guild": interaction.guild.id})
            .limit(30)
            .to_list(length=30)
        )

        if not r:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="辞書がありません。", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        await interaction.response.defer()

        description = "\n".join(
            [f"{entry.get('Word')} = {entry.get('ReplaceWord')}" for entry in r]
        )

        embed = discord.Embed(
            title="読み上げの辞書", description=description, color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)


class TTSCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.guild_queues: dict[int, asyncio.Queue] = {}
        self.guild_tasks: dict[int, asyncio.Task] = {}
        print("init -> TTSCog")

    tts = app_commands.Group(name="tts", description="読み上げ関連のコマンドです。")

    @tts.command(name="start", description="読み上げをします。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def _tts_start(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="読み上げ接続に失敗しました。",
                    description="まずボイスチャンネルに参加してから実行してください。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        try:
            await interaction.user.voice.channel.connect(self_deaf=True)
        except Exception as e:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="エラーが発生しました。",
                    description=f"```{e}```",
                    color=discord.Color.red(),
                )
            )
            return
        ttscheck = self.bot.async_db["Main"].TTSCheckBeta
        await ttscheck.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Channel": interaction.channel.id,
                    "Guild": interaction.guild.id,
                }
            },
            upsert=True,
        )
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="接続しました。",
                description="この機能はベータ版です。\n不具合があったらサポートサーバーに来てください。",
                color=discord.Color.green(),
            )
        )

    @tts.command(name="end", description="読み上げを終了します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tts_end(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            await interaction.guild.voice_client.disconnect()
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="読み上げ退出に失敗しました。",
                    color=discord.Color.red(),
                    description="まだボイスチャンネルに接続されていません。",
                )
            )
        ttscheck = self.bot.async_db["Main"].TTSCheckBeta
        await ttscheck.delete_one({"Guild": interaction.guild.id})
        return await interaction.followup.send(
            embed=discord.Embed(title="退出しました。", color=discord.Color.green())
        )

    @tts.command(name="voice", description="読み上げの声を変更します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tts_voice(self, interaction: discord.Interaction, 声: str = None):
        if not 声:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="読み上げの声一覧",
                    description="""
ID | 説明
ミク 初音ミクの声で読み上げます
緋惺 緋惺の声で読み上げます。
句音 句音コノの声で読み上げます。
霊夢 霊夢の声で読み上げます。
""",
                    color=discord.Color.green(),
                )
            )
            return
        else:
            ttscheck = self.bot.async_db["Main"].TTSVoiceBeta
            if 声 == "ミク":
                await ttscheck.update_one(
                    {"User": interaction.user.id},
                    {"$set": {"User": interaction.user.id, "Voice": "miku"}},
                    upsert=True,
                )
                await interaction.response.send_message(
                    content=f"声を {声} に変更しました。", ephemeral=True
                )
            elif 声 == "緋惺":
                await ttscheck.update_one(
                    {"User": interaction.user.id},
                    {"$set": {"User": interaction.user.id, "Voice": "akesato"}},
                    upsert=True,
                )
                await interaction.response.send_message(
                    content=f"声を {声} に変更しました。", ephemeral=True
                )
            elif 声 == "句音":
                await ttscheck.update_one(
                    {"User": interaction.user.id},
                    {"$set": {"User": interaction.user.id, "Voice": "kuon"}},
                    upsert=True,
                )
                await interaction.response.send_message(
                    content=f"声を {声} に変更しました。", ephemeral=True
                )
            elif 声 == "霊夢":
                await ttscheck.update_one(
                    {"User": interaction.user.id},
                    {"$set": {"User": interaction.user.id, "Voice": "reimu"}},
                    upsert=True,
                )
                await interaction.response.send_message(
                    content=f"声を {声} に変更しました。", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    content="指定した声が存在しません。", ephemeral=True
                )

    async def tts_guilds(self):
        db = self.bot.async_db["Main"].TTSCheckBeta
        return await db.count_documents({})

    def get_guild_queue_status(self, guild_id: int):
        queue = self.guild_queues.get(guild_id)
        if not queue:
            return 0, 20
        return queue.qsize(), queue.maxsize

    @tts.command(name="info", description="読み上げしているサーバー数を取得します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tts_info(self, interaction: discord.Interaction):
        g_c = await self.tts_guilds()
        remaining, total = self.get_guild_queue_status(interaction.guild.id)
        if g_c < 3:
            return await interaction.response.send_message(
                embeds=[
                    discord.Embed(
                        title="読み上げを使用しているサーバー数",
                        description=f"{g_c}サーバー\n読み上げは快適だと思います。",
                        color=discord.Color.blue(),
                    ),
                    discord.Embed(
                        title="読み上げの残りキューリソース",
                        description=f"```{remaining}/{total}```",
                        color=discord.Color.blue(),
                    ),
                ]
            )
        return await interaction.response.send_message(
            embeds=[
                discord.Embed(
                    title="読み上げを使用しているサーバー数",
                    description=f"{g_c}サーバー\n読み上げは重いかもしれないです。",
                    color=discord.Color.blue(),
                ),
                discord.Embed(
                    title="読み上げの残りキューリソース",
                    description=f"```{remaining}/{total}```",
                    color=discord.Color.blue(),
                ),
            ]
        )

    @tts.command(name="autojoin", description="読み上げの自動接続を設定します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def tts_autojoin(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.VoiceChannel,
        有効化するか: bool,
    ):
        await interaction.response.defer()
        ttscheck = self.bot.async_db["Main"].TTSAutoJoin
        if 有効化するか:
            await ttscheck.update_one(
                {"Channel": チャンネル.id, "Guild": interaction.guild.id},
                {"$set": {"Channel": チャンネル.id, "Guild": interaction.guild.id}},
                upsert=True,
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="自動接続を有効化しました。", color=discord.Color.green()
                )
            )
        else:
            await ttscheck.delete_one(
                {"Channel": チャンネル.id, "Guild": interaction.guild.id}
            )
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="自動接続を無効化しました。", color=discord.Color.red()
                )
            )

    tts.add_command(DictGroup())

    async def replace_word(self, word: str, guild: discord.Guild):
        w = word
        ttsdict = self.bot.async_db["Main"].TTSWord
        r = await ttsdict.find({"Guild": guild.id}, {}).limit(30).to_list(length=30)
        for r_ in r:
            if r_.get("Word") in word:
                w = word.replace(r_.get("Word"), r_.get("ReplaceWord"))
        return w

    async def autojoin_channel(self, channel: discord.VoiceChannel):
        ttscheck = self.bot.async_db["Main"].TTSCheckBeta
        await ttscheck.update_one(
            {"Guild": channel.guild.id},
            {"$set": {"Channel": channel.id, "Guild": channel.guild.id}},
            upsert=True,
        )

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_autojoin(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        try:
            if after.channel:
                ttscheck = self.bot.async_db["Main"].TTSAutoJoin

                try:
                    ttscheckfind = await ttscheck.find_one(
                        {"Channel": after.channel.id}, {"_id": False}
                    )
                except:
                    return
                if ttscheckfind is None:
                    return

                channel = after.channel
                non_bot_members = [m for m in channel.members if not m.bot]

                if len(non_bot_members) == 1:
                    if not channel.guild.voice_client:
                        current_time = time.time()
                        last_message_time = cooldown_autojoin.get(member.guild.id, 0)
                        if current_time - last_message_time < 5:
                            return
                        cooldown_autojoin[member.guild.id] = current_time

                        await channel.connect(self_deaf=True)
                        await self.autojoin_channel(channel)
        except:
            return

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_tts(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.id == self.bot.user.id:
            if before.channel and not after.channel:
                ttscheck = self.bot.async_db["Main"].TTSCheckBeta
                await ttscheck.delete_one({"Guild": member.guild.id})
                print("BotがVCからキックされました！")
            return

    async def make_text(self, message: discord.Message):
        if "http" in message.content:
            return "URL"
        if "@" in message.content:
            return "メンション"
        if "#" in message.content:
            return "チャンネル"
        if len(message.content) > 50:
            return "省略しました。"
        r_w = await self.replace_word(message.content, message.guild)
        em_repd = re.sub(r"<:([a-zA-Z0-9_]+):(\d+)>", r"絵文字", r_w)
        for k, v in tts_dict.TTSDICTS.items():
            em_repd = em_repd.replace(k, v)
        return em_repd

    async def get_voice_file(self, author: discord.User):
        voices = {
            "miku": "htsvoice/miku.htsvoice",
            "akesato": "htsvoice/akesato.htsvoice",
            "kuon": "htsvoice/kono.htsvoice",
            "reimu": "reimu",
        }

        ttscheck = self.bot.async_db["Main"].TTSVoiceBeta
        try:
            ttscheckfind = await ttscheck.find_one({"User": author.id}, {"_id": False})
        except:
            return "htsvoice/miku.htsvoice"
        if ttscheckfind is None:
            return "htsvoice/miku.htsvoice"
        v = ttscheckfind.get("Voice", None)
        if v is None:
            return "htsvoice/miku.htsvoice"
        return voices.get(v, "htsvoice/miku.htsvoice")

    async def generate_voice_bytes(self, author: discord.User, text: str) -> bytes:
        v = await self.get_voice_file(author)
        if v == "reimu":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://www.yukumo.net/api/v2/aqtk1/koe.mp3?type=f1&kanji={urllib.parse.quote(text)}"
                ) as response:
                    return await response.read()
        process = await asyncio.create_subprocess_exec(
            "open_jtalk",
            "-x",
            "/var/lib/mecab/dic/open-jtalk/naist-jdic",
            "-m",
            v,
            "-ow",
            "/dev/stdout",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(input=text.replace("\n", "").encode("utf-8")),
                timeout=10,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return None
        return stdout

    async def process_guild_queue(self, guild: discord.Guild):
        queue = self.guild_queues[guild.id]

        while True:
            try:
                try:
                    author, text = await asyncio.wait_for(queue.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    continue

                wav_bytes = await self.generate_voice_bytes(author, text)
                if wav_bytes is None:
                    queue.task_done()
                    continue

                vc = guild.voice_client
                if vc is None or not vc.is_connected():
                    queue.task_done()
                    continue

                finished = asyncio.Event()

                def after_playing(_):
                    finished.set()

                with io.BytesIO(wav_bytes) as bio:
                    vc.play(discord.FFmpegPCMAudio(bio, pipe=True), after=after_playing)
                    await finished.wait()

                queue.task_done()

            except Exception as e:
                print(f"[TTS Error] {e}")
                queue.task_done()

    @commands.Cog.listener(name="on_message")
    async def on_message_tts(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return
        if not message.content:
            return
        if not message.author.voice:
            return
        if not message.guild.voice_client:
            return
        try:
            ttscheck = self.bot.async_db["Main"].TTSCheckBeta
            try:
                ttscheckfind = await ttscheck.find_one(
                    {"Channel": message.channel.id}, {"_id": False}
                )
            except:
                return
            if ttscheckfind is None:
                return

            text = await self.make_text(message)

            if message.guild.id not in self.guild_queues:
                self.guild_queues[message.guild.id] = asyncio.Queue(maxsize=20)
                self.guild_tasks[message.guild.id] = self.bot.loop.create_task(
                    self.process_guild_queue(message.guild)
                )

            try:
                self.guild_queues[message.guild.id].put_nowait((message.author, text))
            except asyncio.QueueFull:
                return

        except discord.ClientException:
            return
        except Exception as e:
            await message.channel.send(
                embed=discord.Embed(
                    title="エラーが発生しました。",
                    description=f"```{e}```",
                    color=discord.Color.red(),
                )
            )
            ttscheck = self.bot.async_db["Main"].TTSCheckBeta
            await ttscheck.delete_one({"Guild": message.guild.id})
            return await message.guild.voice_client.disconnect()


async def setup(bot):
    await bot.add_cog(TTSCog(bot))
