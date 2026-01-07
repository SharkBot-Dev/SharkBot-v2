from discord import Embed, Color

SUCCESS_EMOJI = "https://cdn.discordapp.com/emojis/1419898127975972937.png?format=webp&quality=lossless&width=85&height=81"
ERROR_EMOJI = "https://cdn.discordapp.com/emojis/1419898620530004140.png?format=webp&quality=lossless&width=84&height=79"


def success_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.green(), description=description, url=url)
    embed.set_author(name=title, icon_url=SUCCESS_EMOJI)
    return embed


def error_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.red(), description=description, url=url)
    embed.set_author(name=title, icon_url=ERROR_EMOJI)
    return embed