from discord.ext import commands, tasks
import discord
from datetime import datetime, timedelta
from consts import mongodb
import asyncio

class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> DashboardCog")

    async def cog_load(self):
        self.dashboard_sendembed.start()

    async def cog_unload(self):
        self.dashboard_sendembed.stop()

    @tasks.loop(seconds=10)
    async def dashboard_sendembed(self):
        db = self.bot.async_db["DashboardBot"].SendEmbedQueue
        async for doc in db.find({}):
            guild_id = int(doc["Guild"])
            channel_id = int(doc.get("Channel", 0))
            
            g = self.bot.get_guild(guild_id)
            if not g:
                await db.delete_one({"Guild": guild_id})
                continue

            ch = g.get_channel(channel_id)
            if ch:
                embed = discord.Embed(
                    title=doc.get("Title", "タイトルです"),
                    description=doc.get("Description", "説明です"),
                    color=discord.Color.green()
                )
                await ch.send(embed=embed)

            await db.delete_one({"Guild": guild_id, "Channel": channel_id})
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(DashboardCog(bot))