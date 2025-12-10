import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import yt_dlp
import re
import os
import dotenv

dotenv.load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

YOUTUBE_RE = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"

guild_queues = {}


def get_queue(gid: int):
    if gid not in guild_queues:
        guild_queues[gid] = asyncio.Queue()
    return guild_queues[gid]

async def yt_extract_async(url: str, search: bool = False):
    def run():
        ydl_opts = {
            "quiet": True,
            "default_search": "ytsearch1" if search else None
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    return await asyncio.to_thread(run)


async def yt_get_audio_url(info):
    formats = info["formats"]

    audio = next(
        (f for f in formats if f.get("acodec") != "none" and f.get("abr", 999) <= 64),
        None
    )

    if audio is None:
        audio = next((f for f in formats if f.get("acodec") != "none"), None)

    return audio["url"]

async def play_next(vc, guild_id):
    queue = get_queue(guild_id)

    if queue.empty():
        await vc.disconnect()
        return

    url = await queue.get()

    info = await yt_extract_async(url)
    audio_url = await yt_get_audio_url(info)

    ffmpeg_opts = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    vc.play(
        discord.FFmpegPCMAudio(audio_url, **ffmpeg_opts),
        after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(vc, guild_id), bot.loop
        )
    )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Commands synced.")

@bot.tree.command(name="play", description="YouTubeの音楽を再生します")
@app_commands.describe(query="URL または検索語句")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    vc = interaction.guild.voice_client
    if not vc:
        if not interaction.user.voice:
            return await interaction.followup.send("ボイスチャンネルに入ってね！")
        vc = await interaction.user.voice.channel.connect()

    if "list=" in query:
        return await interaction.followup.send("プレイリストには対応していません。")

    if not re.match(YOUTUBE_RE, query):
        info = await yt_extract_async(query, search=True)
        query = info["entries"][0]["webpage_url"]

    queue = get_queue(interaction.guild.id)
    await queue.put(query)

    await interaction.followup.send(f"キューに追加 ✔\n{query}")

    if not vc.is_playing():
        await play_next(vc, interaction.guild.id)

@bot.tree.command(name="skip", description="曲をスキップします")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        return await interaction.response.send_message("再生中じゃないよ？")

    vc.stop()
    await interaction.response.send_message("スキップしたよ！")

@bot.tree.command(name="queue", description="再生キューを表示します")
async def queue_cmd(interaction: discord.Interaction):
    queue = get_queue(interaction.guild.id)

    if queue.empty():
        return await interaction.response.send_message("キューは空だよ！")

    items = list(queue._queue)
    text = "\n".join(f"{i+1}. {v}" for i, v in enumerate(items[:10]))

    await interaction.response.send_message(f"**現在のキュー:**\n{text}")

@bot.tree.command(name="stop", description="停止して切断します")
async def stop(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()

    get_queue(interaction.guild.id)._queue.clear()
    await interaction.response.send_message("停止しました！")

bot.run(os.getenv("DISCORD_TOKEN"))