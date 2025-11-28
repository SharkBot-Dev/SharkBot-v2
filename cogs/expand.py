from discord.ext import commands
import discord
import time
import re

COOLDOWN_TIME_EXPAND = 5
cooldown_expand_time = {}

URL_REGEX = re.compile(r"https://discord.com/channels/(\d+)/(\d+)/(\d+)")


class ExpandCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ExpandCog")

    async def is_outside_enbaled(self, guild_id: int):
        db = self.bot.async_db["Main"].ExpandSettings
        try:
            dbfind = await db.find_one({"Guild": guild_id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        return dbfind.get("Outside", False)

    @commands.Cog.listener("on_message")
    async def on_message_expand(self, message: discord.Message):
        if message.author.bot:
            return  # ボットのメッセージは無視
        if not message.content:
            return  # からのメッセージなら無視
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].ExpandSettings
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        if not dbfind:
            return
        if not dbfind.get("Enabled", True):
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
            guild_id, channel_id, message_id = (
                int(guild_id),
                int(channel_id),
                int(message_id),
            )
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            if guild_id != message.guild.id:
                if not await self.is_outside_enbaled(guild_id):
                    return

            try:
                channel = await guild.fetch_channel(channel_id)
            except discord.NotFound:
                return await message.add_reaction("❌")

            if getattr(channel, "nsfw", False) and not getattr(
                message.channel, "nsfw", False
            ):
                return await message.add_reaction("❌")

            try:
                msg = await channel.fetch_message(message_id)
            except discord.NotFound:
                return await message.add_reaction("❌")

            embed = discord.Embed(
                description=msg.content[:1500] if msg.content else "[メッセージなし]",
                color=discord.Color.green(),
                timestamp=msg.created_at,
            )
            embed.set_author(
                name=msg.author.display_name,
                icon_url=msg.author.display_avatar.url,
                url=f"https://discord.com/users/{msg.author.id}",
            )
            embed.add_field(
                name="元のメッセージ",
                value=f"[リンクを開く]({msg.jump_url})",
                inline=False,
            )
            embed.set_footer(
                text=f"{msg.guild.name} | {msg.channel.name}",
                icon_url=msg.guild.icon.url if msg.guild.icon else None,
            )

            embeds = [embed]
            if msg.embeds:
                embeds.append(msg.embeds[0])

            await message.channel.send(embeds=embeds)
            return


async def setup(bot):
    await bot.add_cog(ExpandCog(bot))
