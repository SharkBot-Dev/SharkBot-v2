import discord
from discord.ext import commands

async def is_enabled(bot: commands.Bot, guild: discord.Guild, module_name: str):
    db = bot.async_db["Bot"].Modules
    setting = await db.find_one({"guild_id": guild.id})

    if not setting:
        return True
    
    disabled_modules = setting.get('disabled_modules')
    if module_name in disabled_modules:
        return False
    
    return True