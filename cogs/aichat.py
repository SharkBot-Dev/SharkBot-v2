from datetime import datetime, timedelta
import asyncio
import time
import aiohttp
import discord
from discord.ext import commands, tasks

from discord import app_commands

from consts import badword

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    ai = app_commands.Group(name="ai", description="aiを使用します。")

    @ai.command(name="write", description="AIを使って文章を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ai_write(self, interaction: discord.Interaction, お題: str):
        await interaction.response.defer()

        headers = {
            'Content-Type': 'application/json',
        }

        json_data = {
            'prompt': お題,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:6000/generate", headers=headers, json=json_data) as cat:
                j = await cat.json()

                text = f"{お題}{j.get("generated_text", "生成に失敗しました。")}"

                for n in badword.badwords:
                    if n in text:
                        return await interaction.followup.send(embed=discord.Embed(title="生成に失敗しました。", color=discord.Color.red()))

                await interaction.followup.send(embed=discord.Embed(title="AIの回答", description=f"```{text}```"))

async def setup(bot):
    await bot.add_cog(AICog(bot))