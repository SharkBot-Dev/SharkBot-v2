import aiohttp
import discord
from discord.ext import commands

from discord import app_commands

import yt_dlp
import asyncio

class RadioCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    """

    def get_radio_url(self):
        radiko_url = "https://radiko.jp/#!/live/RN1"
        ydl_opts = {"quiet": True, "no_warnings": True, "format": "bestaudio"}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(radiko_url, download=False)
            return info["url"]

    radio = app_commands.Group(name="radio", description="ラジオ関連のコマンドです。")

    @radio.command(name="play", description="ラジオを再生します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def _radio_start(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="ラジオ接続に失敗しました。",
                    description="まずボイスチャンネルに参加してから実行してください。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        await interaction.response.defer()

        try:
            vc = interaction.guild.voice_client
            if not vc:
                vc = await interaction.user.voice.channel.connect()

            stream_url = await asyncio.to_thread(self.get_radio_url)

            ffmpeg_options = {
                'before_options': '-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            audio_source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_options)

            if vc.is_playing():
                vc.stop()
            vc.play(audio_source)

            await interaction.followup.send(
                embed=discord.Embed(title="ラジオを再生しました。", color=discord.Color.green())
            )

        except Exception as e:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="エラーが発生しました。",
                    description=f"```{e}```",
                    color=discord.Color.red(),
                )
            )

    @radio.command(name="stop", description="ラジオを停止します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def _radio_stop(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="ラジオ停止に失敗しました。",
                    description="まずボイスチャンネルに参加してから実行してください。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await interaction.response.defer()

        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()
            return await interaction.followup.send(embed=discord.Embed(title="ラジオをストップしました。", color=discord.Color.green()))
        
        await interaction.followup.send(embed=discord.Embed(title="まだラジオを再生していないようです。", color=discord.Color.green()))

    """
    
async def setup(bot):
    await bot.add_cog(RadioCog(bot))
