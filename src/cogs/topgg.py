from discord.ext import commands, tasks
import topgg

from models.topgg import TOPGG_TOKEN

class TopGGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.topgg_client = topgg.DBLClient(self.bot, TOPGG_TOKEN)

    async def cog_load(self):
        self.update_stats.start()

    async def cog_unload(self):
        self.update_stats.stop()

    @tasks.loop(minutes=30)
    async def update_stats(self):
        try:
            await self.topgg_client.post_guild_count()
        except Exception as e:
            print(f"[TopGGError] {e}")

async def setup(bot):
    await bot.add_cog(TopGGCog(bot))