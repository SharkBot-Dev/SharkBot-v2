from datetime import datetime, timedelta, timezone
import asyncio
from typing import Any
import discord
from discord.ext import commands, tasks


class LoopCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop_create = self.loop_create
        self.bot.loop_delete = self.loop_delete
        self.check_loop.start()

    async def cog_unload(self):
        self.check_loop.cancel()

    async def loop_create(
        self,
        time: timedelta,
        event: str,
        /,
        *args: Any,
        **kwargs: Any
    ):
        notify_time = datetime.now(timezone.utc) + time
        db = self.bot.async_db["MainTwo"].LoopQueue

        if event == "auto_reset_event":
            guild_id = args[0]
            channel_id = args[1]
            hour = args[2]

            new_doc = {
                "NotifyAt": notify_time,
                "Event": event,
                "Guild": guild_id,
                "Channel": channel_id,
                "Hour": hour,
                "Args": [],
                "Kwargs": {},
            }

            await db.update_one(
                {"Event": event, "Guild": guild_id, "Channel": channel_id},
                {"$set": new_doc},
                upsert=True,
            )
            return

        await db.update_one(
            {"Event": event, "Args": args},
            {
                "$set": {
                    "NotifyAt": notify_time,
                    "Event": event,
                    "Args": args,
                    "Kwargs": kwargs,
                }
            },
            upsert=True,
        )

    async def loop_delete(self, event: str, /, *args: Any, **kwargs: Any):
        db = self.bot.async_db["MainTwo"].LoopQueue

        if event == "auto_reset_event":
            guild_id = args[0]
            await db.delete_many({"Event": event, "Guild": guild_id, "Channel": args[1]})
            return

        await db.delete_many({"Event": event, "Args": args})

    @tasks.loop(seconds=15)
    async def check_loop(self):
        db = self.bot.async_db["MainTwo"].LoopQueue
        now = datetime.now(timezone.utc)

        async for doc in db.find({"NotifyAt": {"$lte": now}}):
            event = doc.get("Event")
            args = doc.get("Args", [])
            kwargs = doc.get("Kwargs", {})

            if event == "auto_reset_event":
                guild_id = doc.get("Guild")
                channel_id = doc.get("Channel")
                hour = doc.get("Hour")

                args = [guild_id, channel_id, hour]

            self.bot.dispatch(event, *args, **kwargs)

            # await db.delete_one({"_id": doc["_id"]})

    @check_loop.before_loop
    async def before_check_alert(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopCog(bot))