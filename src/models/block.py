from discord.ext import commands

SETTINDS_LIST = ["Miq機能", "恋愛度計算機"]

async def is_blocked_func(bot: commands.Bot, user_id, func_name: str):
    db = bot.async_db["MainTwo"].UserBlockSetting
    setting = await db.find_one({
        "user_id": user_id
    })

    if not setting:
        return False

    if func_name in setting.get("blockd_func", []):
        return True
    
    return False