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
        self.create_automod.start()

    async def cog_unload(self):
        self.dashboard_sendembed.stop()
        self.create_automod.stop()

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

            user = g.get_member(doc.get("User", 0))

            ch = g.get_channel(channel_id)
            if ch:
                embed = (
                    discord.Embed(
                        title=doc.get("Title", "タイトルです"),
                        description=doc.get("Description", "説明です"),
                        color=discord.Color.green(),
                    )
                    .set_author(
                        name=user.name,
                        icon_url=user.avatar.url
                        if user.avatar
                        else user.default_avatar.url,
                    )
                    .set_footer(text=g.name, icon_url=g.icon.url if g.icon else None)
                )
                await ch.send(embed=embed)

            await db.delete_one({"Guild": guild_id, "Channel": channel_id})
            await asyncio.sleep(1)

    @tasks.loop(seconds=10)
    async def create_automod(self):
        db = self.bot.async_db["DashboardBot"].CreateAutoModQueue
        async for doc in db.find({}):
            guild_id = int(doc["Guild"])

            g = self.bot.get_guild(guild_id)
            if not g:
                await db.delete_one({"Guild": guild_id})
                continue

            if doc.get("Name", "不明") == "招待リンク":
                await g.create_automod_rule(
                    name="招待リンク対策",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModRuleTriggerType.keyword,
                        regex_patterns=[
                            r"(discord\.(gg|com/invite|app\.com/invite)[/\\][\w-]+)",
                            r"\b\<(\n*)?h(\n*)?t(\n*)?t(\n*)?p(\n*)?s?(\n*)?:(\n*)?\/(\n*)?\/(\n*)?(([dｄⓓᵈᴰⅮ𝒹ⅾⅮ𝔻𝕕%％𝓓]{1,}|[^\p{sc=latin}]*)(\n*)([iｉⓘsｓⓢ𝖎𝖘ɪꜱᴵⁱˢ𝓘𝓢\n]{1,}|[\p{sc=latin}\n]*)([\p{sc=latin}\nº]*|[^\p{sc=latin}\n]*)[\/\\](\n*)[^\s]*)+\b",
                        ],
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        )
                    ],
                    enabled=True,
                )

            elif doc.get("Name", "不明") == "Token":
                dbs = self.bot.async_db["Main"].TokenBlock
                await dbs.replace_one({"Guild": g.id}, {"Guild": g.id}, upsert=True)

            elif doc.get("Name", "不明") == "EveryoneとHere":
                await g.create_automod_rule(
                    name="everyoneとhere対策",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModRuleTriggerType.keyword,
                        regex_patterns=[r"@everyone", r"@here"],
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        )
                    ],
                    enabled=True,
                )

            elif doc.get("Name", "不明") == "メールアドレス":
                await g.create_automod_rule(
                    name="メールアドレス対策",
                    event_type=discord.AutoModRuleEventType.message_send,
                    trigger=discord.AutoModTrigger(
                        type=discord.AutoModRuleTriggerType.keyword,
                        regex_patterns=[
                            r"^[a-zA-Z0-9_+-]+(.[a-zA-Z0-9_+-]+)*@([a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.)+[a-zA-Z]{2,}$"
                        ],
                    ),
                    actions=[
                        discord.AutoModRuleAction(
                            type=discord.AutoModRuleActionType.block_message
                        )
                    ],
                    enabled=True,
                )

            elif doc.get("Name", "不明") == "メッセージスパム":
                dbs = self.bot.async_db["Main"].SpamBlock
                await dbs.replace_one({"Guild": g.id}, {"Guild": g.id}, upsert=True)

            elif doc.get("Name", "不明") == "スラッシュコマンドスパム":
                dbs = self.bot.async_db["Main"].UserApplicationSpamBlock
                await dbs.replace_one({"Guild": g.id}, {"Guild": g.id}, upsert=True)

            await db.delete_one({"Guild": guild_id})
            await asyncio.sleep(1)


async def setup(bot):
    await bot.add_cog(DashboardCog(bot))
