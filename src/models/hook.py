import discord
import functools
import copy
from motor.motor_asyncio import AsyncIOMotorClient
from models import make_embed

def hook_embed(bot: discord.Client, db_client: AsyncIOMotorClient):
    db = db_client["DashboardBot"]
    settings_col = db["Embed"]

    original_send_message = bot.http.send_message

    # メッセージ系
    @functools.wraps(original_send_message)
    async def hooked_send_message(channel_id, *, params, **kwargs):
        guild_id = None
        
        channel = bot.get_channel(int(channel_id))
        if channel and hasattr(channel, 'guild') and channel.guild:
            guild_id = str(channel.guild.id)

        if guild_id and params.payload and params.payload.get('embeds'):
            try:
                config = await settings_col.find_one({"guild_id": guild_id})
                
                if config:
                    
                    new_payload = copy.deepcopy(params.payload)
                    modified = False

                    for embed_dict in new_payload["embeds"]:
                        author_data = embed_dict.get('author', {})
                        current_icon = author_data.get('icon_url')
                        
                        if not current_icon:
                            continue
                        
                        if current_icon == make_embed.SUCCESS_EMOJI:
                            type_key = "success"
                        elif current_icon == make_embed.ERROR_EMOJI:
                            type_key = "error"
                        elif current_icon == make_embed.LOADING_EMOJI:
                            type_key = "loading"
                        else:
                            continue

                        type_config = config.get(type_key)
                        if type_config:
                            if "color" in type_config:
                                embed_dict['color'] = type_config["color"]
                            
                            if "icon" in type_config:
                                if 'author' not in embed_dict:
                                    embed_dict['author'] = {}
                                embed_dict['author']['icon_url'] = type_config["icon"]
                            modified = True

                    if modified:
                        params = params._replace(payload=new_payload)

            except Exception as e:
                pass

        return await original_send_message(channel_id, params=params, **kwargs)

    hooked_send_message.__hooked__ = True
    bot.http.send_message = hooked_send_message