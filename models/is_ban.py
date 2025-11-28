from discord import Interaction, Message
from consts import mongodb


async def user_block_check(user: int):
    db = mongodb.mongo["Main"].BlockUser
    try:
        dbfind = await db.find_one({"User": user}, {"_id": False})
    except:
        return True
    if dbfind is not None:
        return False
    return True


async def guild_block_check(guild: int):
    db = mongodb.mongo["Main"].BlockGuild
    try:
        dbfind = await db.find_one({"Guild": guild}, {"_id": False})
    except:
        return True
    if dbfind is not None:
        return False
    return True


async def is_blockd_by_message(message: Message):
    if not await user_block_check(message.author.id):
        return False
    if message.guild:
        if not await guild_block_check(message.guild.id):
            return False
    return True
