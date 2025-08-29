from discord import Interaction

async def ban_user_block(interaction: Interaction):
    db = interaction.client.async_db["Main"].BlockUser
    try:
        dbfind = await db.find_one({"User": interaction.user.id}, {"_id": False})
    except:
        return True
    if not dbfind is None:
        return False
    return True
    
async def ban_guild_block(interaction: Interaction):
    db = interaction.client.async_db["Main"].BlockGuild
    try:
        dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
    except:
        return True
    if not dbfind is None:
        return False
    return True