from discord.ext import commands
import discord
from discord import Webhook
import time
import asyncio
import aiohttp

user_last_message_time_pgc = {}


class PrivateGlobalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> PrivateGlobalCog")

    async def check_channel_message(self, message: discord.Message):
        db = self.bot.async_db["Main"].PrivateGlobal
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return dbfind.get("Name", None)
        except Exception:
            return False

    async def user_block(self, message: discord.Message):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return False
        if dbfind is not None:
            return True
        return False

    async def badge_build(self, message: discord.Message):
        if message.author.id == 1335428061541437531:
            return "👑"

        try:
            if (
                self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
                in self.bot.get_guild(1343124570131009579)
                .get_member(message.author.id)
                .roles
            ):
                return "🛠️"
        except:
            return "😀"

        return "😀"

    def filter_global(self, message: discord.Message) -> bool:
        blocked_words = [
            "discord.com",
            "discord.gg",
            "x.gd",
            "shorturl.asia",
            "tiny.cc",
            "<sound:",
            "niga",
            "everyone",
            "here",
        ]
        return not any(word in message.content for word in blocked_words)

    async def get_guild_emoji(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].NewGlobalChatEmoji
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            if dbfind is None:
                return "😎"
            return dbfind.get("Emoji", "😎")
        except Exception:
            return "😎"

    async def send_one_globalchat(
        self, webhook: str, message: discord.Message, ref_msg: discord.Message = None
    ):
        if not self.filter_global(message):
            return

        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                description=message.content, color=discord.Color.blue()
            )
            em = await self.get_guild_emoji(message.guild)
            embed.set_footer(text=f"[{em}] {message.guild.name}/{message.guild.id}")

            bag = await self.badge_build(message)

            if message.author.avatar:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.avatar.url,
                )
            else:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.default_avatar.url,
                )
            if not message.attachments == []:
                embed.add_field(name="添付ファイル", value=message.attachments[0].url)
                for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                    if message.attachments[0].filename.endswith(kaku):
                        embed.set_image(url=message.attachments[0].url)
                        break

            if ref_msg:
                wh = ref_msg.webhook_id
                embed_ = ref_msg.embeds
                if wh:
                    try:
                        name = (
                            embed_[0]
                            .author.name.replace("[👑]", "")
                            .replace("[😀]", "")
                            .replace("[🛠️]", "")
                            .split("/")[0]
                        )
                        value = embed_[0].description
                    except:
                        name = ref_msg.author.name
                        value = ref_msg.content
                else:
                    name = ref_msg.author.name
                    value = ref_msg.content
                embed.add_field(name=name, value=value)
            try:
                await webhook_.send(
                    embed=embed,
                    avatar_url=self.bot.user.avatar.url,
                    username="SharkBot-PrivateGlobal",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except:
                return

    async def send_global_chat(
        self, room: str, message: discord.Message, ref_msg: discord.Message = None
    ):
        db = self.bot.async_db["Main"].PrivateGlobal
        channels = db.find({"Name": room})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                if not ref_msg:
                    await self.send_one_globalchat(channel["Webhook"], message)
                else:
                    await self.send_one_globalchat(channel["Webhook"], message, ref_msg)
            else:
                continue

            await asyncio.sleep(1)

    @commands.Cog.listener("on_message")
    async def on_message_private_global(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if "!." in message.content:
            return

        check = await self.check_channel_message(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            return

        current_time = time.time()
        last_message_time = user_last_message_time_pgc.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        user_last_message_time_pgc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat(check, message, rmsg)
        else:
            await self.send_global_chat(check, message)

        await message.remove_reaction("🔄", self.bot.user)

        await message.add_reaction("✅")
        await asyncio.sleep(3)
        await message.remove_reaction("✅", message.guild.me)


async def setup(bot):
    await bot.add_cog(PrivateGlobalCog(bot))
