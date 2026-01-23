from datetime import datetime, timedelta
import asyncio
import discord
from discord.ext import commands, tasks


class AlertCheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_alert.start()
        self.bot.alert_add = self.alert_add

    def cog_unload(self):
        self.check_alert.cancel()

    async def alert_add(
        self,
        id: str,
        channelid: int,
        text: str,
        title: str,
        description: str,
        time: int,
    ):
        notify_time = datetime.now() + timedelta(seconds=time)

        db = self.bot.async_db["Main"].AlertQueue

        await db.update_one(
            {"Channel": channelid, "ID": id},
            {
                "$set": {
                    "NotifyAt": notify_time,
                    "Text": text,
                    "Title": title,
                    "Description": description,
                    "ID": id,
                }
            },
            upsert=True,
        )

        return True

    @tasks.loop(seconds=30)
    async def check_alert(self):
        db = self.bot.async_db["Main"].AlertQueue
        now = datetime.now()
        async for doc in db.find({"NotifyAt": {"$lte": now}}):
            ch = self.bot.get_channel(doc["Channel"])
            if ch:
                try:
                    await ch.send(
                        content=doc.get("Text", "メンションするロールがありません。"),
                        embed=discord.Embed(
                            title=doc.get("Title", "タイトルです"),
                            description=doc.get("Description", "説明です"),
                            color=discord.Color.green(),
                        ),
                    )
                except:
                    pass
            await db.delete_one(
                {"Channel": doc["Channel"], "ID": doc.get("ID", "none")}
            )
            await asyncio.sleep(1)


async def setup(bot):
    await bot.add_cog(AlertCheckCog(bot))
