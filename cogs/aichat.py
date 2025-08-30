import aiohttp
import discord
from discord.ext import commands

from discord import app_commands

from consts import badword
from models import command_disable

cooldown_mention_reply = {}

class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(AICog(bot))
