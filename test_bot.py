import discord
from discord.ext import commands
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import dotenv
from models import custom_tree, translate

dotenv.load_dotenv()

intent = discord.Intents.all()


class NewSharkBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self.ChangePrefix,
            help_command=None,
            intents=intent,
            tree_cls=custom_tree.CustomTree,
        )
        print("InitDone")
        self.async_db = AsyncIOMotorClient("mongodb://localhost:27017")
        self.sync_db = MongoClient("mongodb://localhost:27017")

    def ChangePrefix(self, bot, message):
        pdb = self.sync_db["DashboardBot"].CustomPrefixBot
        try:
            dbfind = pdb.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return ["!/", "?/"]
        if dbfind is None:
            return ["!/", "?/"]
        return [dbfind["Prefix"], "!/", "?/"]


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
    await translate.load()
    await load_cogs(bot)
    try:
        await bot.tree.sync()
    except:
        print("スラッシュコマンドの同期に失敗しました。")


if os.environ.get("Token") is not None:
    bot.run(os.environ.get("Token"))
else:
    raise ValueError("No Token")
