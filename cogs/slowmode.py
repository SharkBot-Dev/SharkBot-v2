import datetime
from discord.ext import commands
import discord
import aiohttp
from discord import Webhook
import asyncio


class SlowModeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.working = set()
        print("init -> SlowModeCog")

    @commands.Cog.listener("on_message")
    async def on_message_slowmode(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if message.author.guild_permissions.manage_channels:
            return

        db = self.bot.async_db["Main"].SlowModeBot
        record = await db.find_one({"channel_id": message.channel.id})
        if record:
            delay = record["delay_seconds"]
            last_msg = await db.find_one(
                {"channel_id": message.channel.id, "user_id": message.author.id}
            )

            now = datetime.datetime.utcnow()
            if last_msg:
                last_time = last_msg["last_sent"]
                elapsed = (now - last_time).total_seconds()
                if elapsed < delay:
                    if message.channel.id in self.working:
                        return

                    self.working.add(message.channel.id)

                    try:
                        remain = int(delay - elapsed)
                        await message.delete()

                        overwrite = message.channel.overwrites_for(message.author)

                        overwrite.send_messages = False
                        overwrite.create_polls = False
                        overwrite.use_application_commands = False
                        overwrite.attach_files = False
                        overwrite.create_public_threads = False
                        overwrite.create_private_threads = False

                        await message.channel.set_permissions(
                            message.author, overwrite=overwrite
                        )

                        await asyncio.sleep(1)

                        await message.channel.send(
                            f"{message.author.mention}、スローモード中です。あと {remain} 秒待ってください。",
                            delete_after=5,
                        )

                        await asyncio.sleep(10)

                        overwrite = message.channel.overwrites_for(message.author)

                        overwrite.send_messages = True
                        overwrite.create_polls = True
                        overwrite.use_application_commands = True
                        overwrite.attach_files = True
                        overwrite.create_public_threads = True
                        overwrite.create_private_threads = True

                        await message.channel.set_permissions(
                            message.author, overwrite=overwrite
                        )
                    except:
                        pass
                    finally:
                        self.working.remove(message.channel.id)

                    return

            await db.update_one(
                {"channel_id": message.channel.id, "user_id": message.author.id},
                {"$set": {"last_sent": now}},
                upsert=True,
            )


async def setup(bot):
    await bot.add_cog(SlowModeCog(bot))
