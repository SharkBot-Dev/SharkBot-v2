import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import yt_dlp
import re
import os
import dotenv

from discord import Embed, Color

SUCCESS_EMOJI = "https://cdn.discordapp.com/emojis/1419898127975972937.png?format=webp&quality=lossless&width=85&height=81"
ERROR_EMOJI = "https://cdn.discordapp.com/emojis/1419898620530004140.png?format=webp&quality=lossless&width=84&height=79"

def success_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.green(), description=description, url=url)
    embed.set_author(name=title, icon_url=SUCCESS_EMOJI)
    return embed


def error_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.red(), description=description, url=url)
    embed.set_author(name=title, icon_url=ERROR_EMOJI)
    return embed

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
            "default_search": "ytsearch1" if search else None,
            'noplaylist': True,
            "no_warnings": True,
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


@tasks.loop(seconds=10)
async def loop_pres():
    try:
        await bot.change_presence(
            activity=discord.CustomActivity(
                name=f"/help | {len(bot.guilds)}鯖"
            )
        )
    except:
        pass

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    await bot.tree.sync()
    print("Commands synced.")

    loop_pres.start()

@bot.tree.command(name="play", description="音楽を再生します")
@app_commands.describe(query="URL または検索語句")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()

    vc = interaction.guild.voice_client
    if not vc:
        if not interaction.user.voice:
            return await interaction.followup.send(embed=error_embed(title="まずボイスチャンネルに参加してください。"))
        vc = await interaction.user.voice.channel.connect()

    if "list=" in query:
        return await interaction.followup.send(embed=error_embed(title="プレイリストには対応してません。"))

    try:

        if not re.match(YOUTUBE_RE, query):
            info = await yt_extract_async(query, search=True)
            query = info["entries"][0]["webpage_url"]

        queue = get_queue(interaction.guild.id)
        await queue.put(query)
    except:
        return await interaction.followup.send(embed=error_embed(title="エラーが発生しました。", description="プレイリストには対応してません。"))

    await interaction.followup.send(embed=success_embed(title="キューに追加しました。", description=query))

    if not vc.is_playing():
        await play_next(vc, interaction.guild.id)

@bot.tree.command(name="skip", description="曲をスキップします")
async def skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or not vc.is_playing():
        return await interaction.response.send_message(embed=error_embed(title="再生中ではありません。"))

    vc.stop()
    await interaction.response.send_message(embed=success_embed(title="スキップしたよ！"))

@bot.tree.command(name="queue", description="再生キューを表示します")
async def queue_cmd(interaction: discord.Interaction):
    queue = get_queue(interaction.guild.id)

    if queue.empty():
        return await interaction.response.send_message(embed=error_embed(title="キューは空です。"))

    items = list(queue._queue)
    text = "\n".join(f"{i+1}. {v}" for i, v in enumerate(items[:10]))

    await interaction.response.send_message(embed=success_embed(title="現在のキュー", description=text))

@bot.tree.command(name="stop", description="停止して切断します")
async def stop(interaction: discord.Interaction):
    await interaction.response.defer()
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()

    get_queue(interaction.guild.id)._queue.clear()
    await interaction.followup.send(embed=success_embed(title="停止しました。"))

@bot.tree.command(name="help", description="ヘルプを表示します。")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=error_embed(
        title="Shark DJのヘルプ",
        description="""
/play 音楽を再生します。
/stop 音楽をストップします。
/skip 音楽をスキップします。
/queue 再生キューを表示します。
/help ヘルプを表示します。
"""
    ).set_thumbnail(url=bot.user.avatar.url), ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))