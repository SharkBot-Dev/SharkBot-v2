from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import aiohttp
from discord import Webhook
import io

class SettingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> SettingCog")


async def setup(bot):
    await bot.add_cog(SettingCog(bot))