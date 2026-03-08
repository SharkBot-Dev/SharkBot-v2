import asyncio
from discord.ext import commands
import discord
import aiohttp
from discord import Webhook
import datetime


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.join_cache = {}
        print("init -> WelcomeCog")

    @commands.Cog.listener("on_member_join")
    async def on_member_join_welcome_card(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].WelcomeCard
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        async def rep_name(msg: str, member: discord.Member):
            return (
                msg.replace("<name>", member.name)
                .replace("<count>", f"{member.guild.member_count}")
                .replace("<guild>", member.guild.name)
                .replace("<createdat>", f"{member.created_at}")
            )

        try:
            wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
            webhooks = discord.utils.get(wb, name="SharkBot")
            if webhooks is None:
                webhooks = await self.bot.get_channel(dbfind["Channel"]).create_webhook(
                    name="SharkBot"
                )
            color = dbfind.get("Color", "66, 135, 245").split(", ")
            r, g, b = map(int, color)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3001/welcome_card",
                    json={
                        "Text": await rep_name(dbfind.get("Message"), member),
                        "Avatar": member.avatar.url
                        if member.avatar
                        else member.default_avatar.url,
                        "WebHook": webhooks.url,
                        "Color": [r, g, b, 255],
                        "Image": dbfind.get(
                            "Image", "http://192.168.11.2:5002/static/welcome_card.png"
                        ),
                    },
                ) as resp:
                    return
        except Exception:
            return

    @commands.Cog.listener("on_member_join")
    async def on_member_join_rta_cache(self, member: discord.Member):
        db = self.bot.async_db["Main"].FastGoodByeRTAMessage
        dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        
        if not dbfind:
            return

        self.join_cache[member.id] = member.joined_at or datetime.datetime.now(datetime.timezone.utc)

    @commands.Cog.listener("on_member_remove")
    async def on_member_remove_rta(self, member: discord.Member):
        g = member.guild
        
        db = self.bot.async_db["Main"].FastGoodByeRTAMessage
        dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        
        if not dbfind or not (ch := g.get_channel(dbfind.get("Channel", 0))):
            return

        join_time = self.join_cache.pop(member.id, member.joined_at)
        
        if not join_time:
            return

        now = datetime.datetime.now(datetime.timezone.utc)
        duration = now - join_time
        seconds = duration.total_seconds()

        if seconds > 60:
            return

        embed = discord.Embed(
            title=f"{member.name} さんが即抜けしました。",
            color=discord.Color.yellow(),
            description=f"**{seconds:.2f}** 秒で即抜けしました。",
        ).set_thumbnail(url=member.display_avatar.url)
        
        await ch.send(embed=embed)

    @commands.Cog.listener("on_member_join")
    async def on_member_join_welcome(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].WelcomeMessage
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        async def rep_name(msg: str, member: discord.Member):
            return (
                msg.replace("<name>", member.name)
                .replace("<count>", f"{member.guild.member_count}")
                .replace("<guild>", member.guild.name)
                .replace("<createdat>", f"{member.created_at}")
            )

        try:
            if not dbfind.get("Webhook"):
                wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
                webhooks = discord.utils.get(wb, name="SharkBot")
                if webhooks is None:
                    webhooks = await self.bot.get_channel(
                        dbfind["Channel"]
                    ).create_webhook(name="SharkBot")

                webhooks = webhooks.url

                await db.update_one({"Guild": g.id}, {"$set": {"Webhook": webhooks}})
            else:
                webhooks = dbfind.get("Webhook")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks, session=session)
                try:
                    if dbfind.get('Mention'):
                        await webhook.send(
                            embed=discord.Embed(
                                title=f"{await rep_name(dbfind['Title'], member=member)}",
                                description=f"{await rep_name(dbfind['Description'], member=member)}",
                                color=discord.Color.green(),
                            ),
                            username="SharkBot Welcome",
                            avatar_url=self.bot.user.avatar.url,
                            content=member.mention
                        )
                    else:
                        await webhook.send(
                            embed=discord.Embed(
                                title=f"{await rep_name(dbfind['Title'], member=member)}",
                                description=f"{await rep_name(dbfind['Description'], member=member)}",
                                color=discord.Color.green(),
                            ),
                            username="SharkBot Welcome",
                            avatar_url=self.bot.user.avatar.url
                        )
                except:
                    return
        except:
            return

    @commands.Cog.listener("on_member_remove")
    async def on_member_remove(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].GoodByeMessage
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        async def rep_name(msg: str, member: discord.Member):
            return (
                msg.replace("<name>", member.name)
                .replace("<count>", f"{member.guild.member_count}")
                .replace("<guild>", member.guild.name)
                .replace("<createdat>", f"{member.created_at}")
            )

        try:
            if not dbfind.get("Webhook"):
                wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
                webhooks = discord.utils.get(wb, name="SharkBot")
                if webhooks is None:
                    webhooks = await self.bot.get_channel(
                        dbfind["Channel"]
                    ).create_webhook(name="SharkBot")

                webhooks = webhooks.url

                await db.update_one({"Guild": g.id}, {"$set": {"Webhook": webhooks}})
            else:
                webhooks = dbfind.get("Webhook")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks, session=session)
                try:
                    await webhook.send(
                        embed=discord.Embed(
                            title=f"{await rep_name(dbfind['Title'], member=member)}",
                            description=f"{await rep_name(dbfind['Description'], member=member)}",
                            color=discord.Color.red(),
                        ),
                        username="SharkBot Goodbye",
                        avatar_url=self.bot.user.avatar.url,
                    )
                except:
                    return
        except:
            return

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, member: discord.Member):
        g = self.bot.get_guild(guild.id)
        db = self.bot.async_db["Main"].BanMessage
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        async def rep_name(msg: str, member: discord.User):
            m = msg.replace("<name>", member.name).replace(
                "<createdat>", f"{member.created_at}"
            )
            return m

        try:
            if not dbfind.get("Webhook"):
                wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
                webhooks = discord.utils.get(wb, name="SharkBot")
                if webhooks is None:
                    webhooks = await self.bot.get_channel(
                        dbfind["Channel"]
                    ).create_webhook(name="SharkBot")

                webhooks = webhooks.url

                await db.update_one(
                    {"Guild": guild.id}, {"$set": {"Webhook": webhooks}}
                )
            else:
                webhooks = dbfind.get("Webhook")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks, session=session)
                try:
                    await webhook.send(
                        embed=discord.Embed(
                            title=f"{await rep_name(dbfind['Title'], member=member)}",
                            description=f"{await rep_name(dbfind['Description'], member=member)}",
                            color=discord.Color.yellow(),
                        ),
                        username="SharkBot Ban",
                        avatar_url=self.bot.user.avatar.url,
                    )
                except:
                    return
        except:
            return


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
