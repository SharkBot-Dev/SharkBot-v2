from datetime import datetime, timedelta, timezone
import asyncio
from typing import Any
import discord
from discord.ext import commands, tasks

class ReminderCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.reminder_create = self.reminder_create
        self.check_alert.start()

    async def cog_unload(self):
        self.check_alert.cancel()

    async def reminder_create(self, time: timedelta, event: str, /, *args: Any, **kwargs: Any):
        notify_time = datetime.now(timezone.utc) + time
        db = self.bot.async_db["MainTwo"].ReminderQueue

        await db.update_one(
            {"Event": event, "Args": args},
            {
                "$set": {
                    "NotifyAt": notify_time,
                    "Event": event,
                    "Args": args,
                    "Kwargs": kwargs
                }
            },
            upsert=True,
        )

    @tasks.loop(seconds=15)
    async def check_alert(self):
        db = self.bot.async_db["MainTwo"].ReminderQueue
        now = datetime.now(timezone.utc)

        async for doc in db.find({"NotifyAt": {"$lte": now}}):
            event = doc.get("Event")
            args = doc.get("Args", [])
            kwargs = doc.get("Kwargs", {})

            self.bot.dispatch(event, *args, **kwargs)

            await db.delete_one({"_id": doc["_id"]})

    @check_alert.before_loop
    async def before_check_alert(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderCog(bot))