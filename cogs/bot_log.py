from discord.ext import commands, tasks
import discord
import datetime
from consts import mongodb

class BotLogCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> BotLogCog")

    async def update_guild_channels(self, guild: discord.Guild):
        text_channels = [
            {"id": ch.id, "name": ch.name}
            for ch in guild.text_channels
        ]
        await mongodb.mongo["DashboardBot"].guild_channels.update_one(
            {"Guild": guild.id},
            {"$set": {"Channels": text_channels}},
            upsert=True
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.update_guild_channels(channel.guild)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.update_guild_channels(channel.guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        await mongodb.mongo["DashboardBot"].bot_joind_guild.replace_one({
            "Guild": guild.id
        }, {"Guild": guild.id}, upsert=True)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        await mongodb.mongo["DashboardBot"].bot_joind_guild.delete_one({
            "Guild": guild.id
        })

async def setup(bot):
    await bot.add_cog(BotLogCog(bot))