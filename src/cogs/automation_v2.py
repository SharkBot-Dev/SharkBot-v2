import asyncio
import time
import discord
from discord.ext import commands

cooldown_automation = {}

class AutoMationV2Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = self.bot.async_db["MainTwo"]
        self.collection = self.db["AutoMationV2"]
        print("init -> AutoMationV2Cog")

    async def check_condition(self, condition: dict, message: discord.Message) -> bool:
        c_type = condition.get("type")
        c_value = condition.get("value")

        if c_type == "if_included":
            return c_value in message.content
        elif c_type == "if_equal":
            return c_value == message.content
        elif c_type == "is_channel":
            return str(message.channel.id) == str(c_value)
        
        return False

    async def execute_action(self, action: dict, message: discord.Message):
        a_type = action.get("type")
        a_value = action.get("value")

        try:
            if a_type == "sendmsg":
                await message.channel.send(f"{a_value}\n-# このメッセージは自動化機能によるメッセージです。")
            elif a_type == "add_reaction":
                await message.add_reaction(a_value)
            elif a_type == "delmsg":
                await message.delete()
            elif a_type == "reply":
                await message.reply(f"{a_value}\n-# このメッセージは自動化機能によるメッセージです。")
        except Exception as e:
            return

    async def run_automation_on_message(self, message: discord.Message):
        if not message.guild:
            return

        cursor = self.collection.find({"Guild": message.guild.id})
        
        async for setting in cursor:
            if setting.get("Trigger") != "on_message":
                continue

            conditions = setting.get("Conditions", [])
            if not conditions:
                continue

            match = all([await self.check_condition(c, message) for c in conditions])

            if match:
                current_time = time.time()
                last_message_time = cooldown_automation.get(message.author.id, 0)
                if current_time - last_message_time < 2:
                    return
                cooldown_automation[message.author.id] = current_time

                for action in setting.get("Actions", []):
                    await self.execute_action(action, message)
                    await asyncio.sleep(0.5)

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        if not message.guild:
            return
        
        await self.run_automation_on_message(message)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMationV2Cog(bot))