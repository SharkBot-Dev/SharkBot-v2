from discord.ext import commands, tasks
import discord
import datetime
from consts import mongodb
from discord import app_commands
import random
import time
import re

COOLDOWN_TIME_EXPAND = 5
cooldown_expand_time = {}

URL_REGEX = re.compile(r"https://discord.com/channels/(\d+)/(\d+)/(\d+)")


class ExpandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ExpandCog")

    @commands.Cog.listener("on_message")
    async def on_message_expand(self, message: discord.Message):
        if message.author.bot:
            return  # ボットのメッセージは無視
        if not message.content:
            return  # ボットのメッセージは無視
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].ExpandSettings
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_expand_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_EXPAND:
            return
        cooldown_expand_time[message.guild.id] = current_time
        urls = URL_REGEX.findall(message.content)
        if not urls:
            return

        for guild_id, channel_id, message_id in urls:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue

            channel = await guild.fetch_channel(int(channel_id))
            if not channel:
                continue

            if not type(channel) == discord.Thread:

                if channel.nsfw:
                    if message.channel.nsfw:
                        msg = await channel.fetch_message(int(message_id))
                        embed = discord.Embed(
                            description=msg.content[:1500] if msg.content else "[メッセージなし]",
                            color=discord.Color.green(),
                            timestamp=msg.created_at
                        )
                        embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url,
                                         url=f"https://discord.com/users/{msg.author.id}")
                        embed.add_field(
                            name="元のメッセージ", value=f"[リンクを開く]({msg.jump_url})", inline=False)
                        embed.set_footer(text=f"{msg.guild.name} | {msg.channel.name}",
                                         icon_url=msg.guild.icon if msg.guild.icon else None)

                        await message.channel.send(embed=embed)

                        return
                    else:
                        return await message.add_reaction("❌")

            try:
                msg = await channel.fetch_message(int(message_id))
                embed = discord.Embed(
                    description=msg.content[:1500] if msg.content else "[メッセージなし]",
                    color=discord.Color.green(),
                    timestamp=msg.created_at
                )
                embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url if msg.author.avatar else msg.author.default_avatar.url,
                                 url=f"https://discord.com/users/{msg.author.id}")
                embed.add_field(
                    name="元のメッセージ", value=f"[リンクを開く]({msg.jump_url})", inline=False)
                embed.set_footer(text=f"{msg.guild.name} | {msg.channel.name}",
                                 icon_url=msg.guild.icon if msg.guild.icon else None)

                await message.channel.send(embed=embed)

                return
            except Exception as e:
                return await message.add_reaction("❌")


async def setup(bot):
    await bot.add_cog(ExpandCog(bot))
