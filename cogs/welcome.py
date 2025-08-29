from discord.ext import commands
import discord
import aiohttp
from discord import Webhook


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> WelcomeCog")

    async def get_user_color_welcome(self, user: discord.User):
        db = self.bot.async_db["Main"].UserColor
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return discord.Color.green()
        if dbfind is None:
            return discord.Color.green()
        if dbfind["Color"] == "red":
            return discord.Color.red()
        elif dbfind["Color"] == "yellow":
            return discord.Color.yellow()
        elif dbfind["Color"] == "blue":
            return discord.Color.blue()
        elif dbfind["Color"] == "random":
            return discord.Color.random()
        return discord.Color.green()

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
            wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
            webhooks = discord.utils.get(wb, name="SharkBot")
            if webhooks is None:
                webhooks = await self.bot.get_channel(dbfind["Channel"]).create_webhook(
                    name="SharkBot"
                )
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks.url, session=session)
                try:
                    col = await self.get_user_color_welcome(member)
                    await webhook.send(
                        embed=discord.Embed(
                            title=f"{await rep_name(dbfind['Title'], member=member)}",
                            description=f"{await rep_name(dbfind['Description'], member=member)}",
                            color=col,
                        ),
                        username="SharkBot Welcome",
                        avatar_url=self.bot.user.avatar.url,
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
            wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
            webhooks = discord.utils.get(wb, name="SharkBot")
            if webhooks is None:
                webhooks = await self.bot.get_channel(dbfind["Channel"]).create_webhook(
                    name="SharkBot"
                )
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks.url, session=session)
                try:
                    col = await self.get_user_color_welcome(member)
                    await webhook.send(
                        embed=discord.Embed(
                            title=f"{await rep_name(dbfind['Title'], member=member)}",
                            description=f"{await rep_name(dbfind['Description'], member=member)}",
                            color=col,
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
            wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
            webhooks = discord.utils.get(wb, name="SharkBot")
            if webhooks is None:
                webhooks = await self.bot.get_channel(dbfind["Channel"]).create_webhook(
                    name="SharkBot"
                )
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks.url, session=session)
                try:
                    col = await self.get_user_color_welcome(member)
                    await webhook.send(
                        embed=discord.Embed(
                            title=f"{await rep_name(dbfind['Title'], member=member)}",
                            description=f"{await rep_name(dbfind['Description'], member=member)}",
                            color=col,
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
