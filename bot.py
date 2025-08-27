import discord
from discord.ext import commands, tasks
import os
import asyncio
import logging
import sys
import json
from motor.motor_asyncio import AsyncIOMotorClient
import sqlite3
import aiofiles
from pymongo import MongoClient
import dotenv

dotenv.load_dotenv()

intent = discord.Intents.all()

class NewSharkBot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self.ChangePrefix,
            help_command=None,
            intents=intent
        )
        print("InitDone")
        self.async_db = AsyncIOMotorClient("mongodb://localhost:27017")
        self.sync_db = MongoClient("mongodb://localhost:27017")

    def ChangePrefix(self, bot, message):
        pdb = self.sync_db["DashboardBot"].CustomPrefixBot
        try:
            dbfind = pdb.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return ["!.", "?."]
        if dbfind is None:
            return ["!.", "?."]
        return [dbfind["Prefix"], "!.", "?."]
    
bot = NewSharkBot()

@bot.event
async def on_ready():
    await bot.load_extension('jishaku')
    await bot.change_presence(activity=discord.CustomActivity(name=f"/help | {len(bot.guilds)}鯖 | {bot.shard_count}Shard | {round(bot.latency * 1000)}ms"))
    os.system("clear")
    print("---[Logging]-------------------------------")
    print(f"BotName: {bot.user.name}")
    print("Ready.")

@bot.event
async def on_message(message):
    return

@bot.event
async def setup_hook() -> None:
    for cog in os.listdir("cogs"):
        if cog.endswith(".py"):
            await bot.load_extension(f"cogs.{cog[:-3]}")
    try:
        await bot.tree.sync()
    except:
        print("スラッシュコマンドの同期に失敗しました。")

bot.run(os.environ.get("Token"))