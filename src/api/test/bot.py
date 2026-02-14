import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

import sharkapi

load_dotenv()

bot = commands.Bot(command_prefix="a!", intents=discord.Intents.all())
client = sharkapi.SharkBot()

@bot.group(name="economy")
async def economy(ctx: commands.Context):
    if not ctx.invoked_subcommand is None:
        return

    guildId = ctx.guild.id

    data = await client.fetchEconomy(str(guildId))

    await ctx.reply(f"コイン名: {data.currency}")

@economy.command(name="member")
async def economy(ctx: commands.Context, user: discord.User = None):
    guildId = ctx.guild.id
    userId = user.id if user else ctx.author.id

    data = await client.fetchEconomyMember(str(guildId), str(userId))

    await ctx.reply(f"手持ち: {data.money}\n銀行預金: {data.bank}")

bot.run(os.environ.get('TOKEN'))