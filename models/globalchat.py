import aiohttp
import discord
from discord.ext import commands

async def badge_build(bot: commands.Bot, message: discord.Message):
    if message.author.id == 1335428061541437531:
        return "👑"

    try:
        if (
            bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            in bot.get_guild(1343124570131009579)
            .get_member(message.author.id)
            .roles
        ):
            return "🛠️"
    except:
        return "😀"

    return "😀"

def filter_global(message: discord.Message) -> bool:
    blocked_words = [
        "discord.com",
        "discord.gg",
        "x.gd",
        "shorturl.asia",
        "tiny.cc",
        "<sound:",
        "niga",
        "everyone",
        "here",
    ]
    return not any(word in message.content for word in blocked_words)

async def get_guild_emoji(bot: commands.Bot, guild: discord.Guild):
    db = bot.async_db["Main"].NewGlobalChatEmoji
    try:
        dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        if dbfind is None:
            return "😎"
        return dbfind.get("Emoji", "😎")
    except Exception:
        return "😎"

async def send_one_global(bot: commands.Bot, webhook: str, message: discord.Message, ref_msg: discord.Message = None, is_ad: bool = False):
    if not is_ad:
        if not filter_global(message):
            return
    async with aiohttp.ClientSession() as session:
        webhook_object = discord.Webhook.from_url(webhook, session=session)

        bag = await badge_build(bot, message)
        em = await get_guild_emoji(bot, message.guild)
        user_name = f"[{bag}] {message.author.name} | [{em}] {message.guild.name.replace('discord', 'disc**d')} | ({message.author.id})"

        if not message.attachments == [] or ref_msg:

            embed = discord.Embed(color=discord.Color.dark_gray())

            if not message.attachments == []:
                if message.stickers == []:
                    embed.add_field(
                        name="添付ファイル", value=message.attachments[0].url
                    )
                    for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                        if message.attachments[0].filename.endswith(kaku):
                            embed.set_image(url=message.attachments[0].url)
                            break

            if ref_msg:
                embed.add_field(name=f"返信: {ref_msg.author.display_name.split(' | ')[0]}", value=ref_msg.content, inline=False)

            try:
                msg = await webhook_object.send(content=message.clean_content, username=user_name, avatar_url=message.author.display_avatar.url, embed=embed, allowed_mentions=discord.AllowedMentions.none(), wait=True)
            except:
                return
        else:
            try:
                msg = await webhook_object.send(content=message.clean_content, username=user_name, avatar_url=message.author.display_avatar.url, allowed_mentions=discord.AllowedMentions.none(), wait=True)
            except:
                return