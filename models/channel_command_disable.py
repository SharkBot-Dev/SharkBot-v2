from discord import Interaction


async def disable_channel(interaction: Interaction):
    db = interaction.client.async_db["Main"].CommandDisable
    try:
        dbfind = await db.find_one({"Channel": interaction.channel.id}, {"_id": False})
    except:
        return True
    if dbfind is not None:
        try:
            if interaction.user.guild_permissions.manage_guild:
                return True
        except:
            return True
        return False
    return True
