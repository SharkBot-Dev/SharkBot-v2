import io
import aiohttp
from discord.ext import commands
import discord
import time
import time

cooldown_announce_pub = {}
cooldown_announce_arr = {}


class AnnounceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> AnnounceCog")

    async def announce_pun_set_setting(
        self, guild: discord.Guild, channel: discord.TextChannel, tf=False
    ):
        db = self.bot.async_db["Main"].AnnouncePun
        if not tf:
            return await db.delete_one({"Guild": guild.id})
        else:
            await db.update_one(
                {"Guild": guild.id, "Channel": channel.id},
                {"$set": {"Guild": guild.id, "Channel": channel.id}},
                upsert=True,
            )

    async def announce_pun_get(self, guild: discord.Guild, ch: discord.TextChannel):
        db = self.bot.async_db["Main"].AnnouncePun
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Channel": ch.id}, {"_id": False}
            )
        except:
            return None
        if not dbfind is None:
            return self.bot.get_channel(dbfind["Channel"])
        return None

    @commands.Cog.listener("on_message")
    async def on_message_publish(self, message: discord.Message):
        if message.author.bot or message.author == self.bot.user:
            return

        check = await self.announce_pun_get(message.guild, message.channel)
        if (
            not check
            or not isinstance(check, discord.TextChannel)
            or check.id != message.channel.id
        ):
            return

        current_time = time.time()
        last_message_time = cooldown_announce_pub.get(message.guild.id, 0)
        if current_time - last_message_time < 5:
            return

        cooldown_announce_pub[message.guild.id] = current_time

        try:
            await message.publish()
        except discord.Forbidden as e:
            db = self.bot.async_db["Main"].AnnouncePun
            await db.delete_one(
                {"Guild": message.guild.id, "Channel": message.channel.id}
            )
            await message.add_reaction("❌")

    async def announce_arr_set_setting(
        self, guild: discord.Guild, channel: discord.TextChannel, tf=False
    ):
        db = self.bot.async_db["MainTwo"].AnnounceAutoReplace
        if not tf:
            return await db.delete_one({"Guild": guild.id, "Channel": channel.id})
        else:
            await db.update_one(
                {"Guild": guild.id, "Channel": channel.id},
                {"$set": {"Guild": guild.id, "Channel": channel.id}},
                upsert=True,
            )

    async def announce_arr_get(self, guild: discord.Guild, ch: discord.TextChannel):
        db = self.bot.async_db["MainTwo"].AnnounceAutoReplace
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Channel": ch.id}, {"_id": False}
            )
        except:
            return None
        if not dbfind is None:
            return guild.get_channel(dbfind["Channel"])
        return None

    @commands.Cog.listener("on_message")
    async def on_message_autoreplyreplace(self, message: discord.Message):
        if message.author.bot or message.author == self.bot.user:
            return

        try:
            check = await self.announce_arr_get(message.guild, message.channel)
            if (
                not check
                or not isinstance(check, discord.TextChannel)
                or check.id != message.channel.id
            ):
                return
        except:
            return

        reply = message.reference

        if not reply:
            return

        current_time = time.time()
        last_message_time = cooldown_announce_arr.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return

        cooldown_announce_arr[message.guild.id] = current_time

        try:
            msg = await message.channel.fetch_message(reply.message_id)

            webhooks = await message.channel.webhooks()

            webhook = None
            for wh in webhooks:
                if wh.name == "SharkBot-ReplyReplace":
                    webhook = wh
                    break

            if webhook is None:
                webhook = await message.channel.create_webhook(
                    name="SharkBot-ReplyReplace"
                )

            if msg.application_id != self.bot.user.id:
                embed = discord.Embed(
                    description=message.content, color=discord.Color.blue()
                )
                embed.add_field(
                    name=f"返信先 ({msg.author.__str__()})",
                    value=msg.content,
                    inline=False,
                )
                embed.set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar.url
                    if message.author.avatar
                    else message.author.default_avatar.url,
                )
            elif msg.application_id == self.bot.user.id:
                embed = discord.Embed(
                    description=message.content, color=discord.Color.blue()
                )
                embed.add_field(
                    name=f"返信先 ({msg.embeds[0].author.name})",
                    value=msg.embeds[0].description,
                    inline=False,
                )
                embed.set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar.url
                    if message.author.avatar
                    else message.author.default_avatar.url,
                )

            if not message.attachments == []:
                at = message.attachments[0]
                for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                    if kaku in at.filename:
                        embed.set_image(url=f"attachment://image.{kaku}")

                        rd = io.BytesIO(await at.read())

                        async with aiohttp.ClientSession() as session:
                            webhook_ = discord.Webhook.from_url(
                                webhook.url, session=session
                            )
                            try:
                                await webhook_.send(
                                    embed=embed,
                                    username="SharkBot-ReplyReplace",
                                    avatar_url=self.bot.user.avatar.url,
                                    file=discord.File(rd, filename=f"image.{kaku}"),
                                )
                            except:
                                pass
                        rd.close()
                        await message.delete()
                        return

                async with aiohttp.ClientSession() as session:
                    webhook_ = discord.Webhook.from_url(webhook.url, session=session)
                    await webhook_.send(
                        embed=embed,
                        username="SharkBot-ReplyReplace",
                        avatar_url=self.bot.user.avatar.url,
                    )
            else:
                async with aiohttp.ClientSession() as session:
                    webhook_ = discord.Webhook.from_url(webhook.url, session=session)
                    await webhook_.send(
                        embed=embed,
                        username="SharkBot-ReplyReplace",
                        avatar_url=self.bot.user.avatar.url,
                    )

            await message.delete()
        except Exception as e:
            # print(e)
            return


async def setup(bot):
    await bot.add_cog(AnnounceCog(bot))
