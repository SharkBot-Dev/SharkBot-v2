import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient

intent = discord.Intents.all()


class NewSharkBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=os.environ.get("PREFIX"),
            help_command=None,
            intents=intent
        )
        print("InitDone")
        self.async_db = AsyncIOMotorClient(os.environ.get('MONGO_URI'))[os.environ.get('DB_NAME')]

bot = NewSharkBot()


@bot.event
async def on_ready():
    await bot.load_extension("jishaku")
    await bot.change_presence(
        activity=discord.CustomActivity(
            name=f"/help | {len(bot.guilds)}鯖 | {bot.shard_count}Shard | {round(bot.latency * 1000)}ms"
        )
    )
    os.system("clear")
    print("---[Logging]-------------------------------")
    print(f"BotName: {bot.user.name}")
    print("Ready.")


@bot.event
async def on_message(message):
    await bot.process_commands(message)
    return


async def load_cogs(bot: commands.Bot, base_folder="cogs"):
    for root, dirs, files in os.walk(base_folder):
        for file in files:
            if file.endswith(".py") and not file.startswith("_"):
                relative_path = os.path.relpath(os.path.join(root, file), base_folder)
                module = relative_path.replace(os.sep, ".")[:-3]
                module = f"{base_folder}.{module}"
                try:
                    await bot.load_extension(module)
                except Exception as e:
                    print(f"❌ Failed to load {module}: {e}")


@bot.event
async def setup_hook() -> None:
    await load_cogs(bot)
    try:
        await bot.tree.sync()
    except Exception as e:
        print(f"スラッシュコマンドの同期に失敗しました。: {e}")


if os.environ.get(f"Token") is not None:
    bot.run(os.environ.get(f"Token"))
else:
    raise ValueError("No Token")
