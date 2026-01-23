from discord.ext import commands
import discord
from consts import mongodb


class BotLogCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BotLogCog")

    # 不要なので削除
    
async def setup(bot):
    await bot.add_cog(BotLogCog(bot))
