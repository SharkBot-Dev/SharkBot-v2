import time
from discord.ext import commands, tasks
import discord
import asyncio

cooldown_dm_time = {}


class DMCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> DMCog")


async def setup(bot):
    await bot.add_cog(DMCog(bot))
