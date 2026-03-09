from discord import Embed, Color

SUCCESS_EMOJI = "https://cdn.discordapp.com/emojis/1419898127975972937.png?format=webp&quality=lossless&width=85&height=81"
ERROR_EMOJI = "https://cdn.discordapp.com/emojis/1419898620530004140.png?format=webp&quality=lossless&width=84&height=79"
LOADING_EMOJI = "https://cdn.discordapp.com/emojis/1480529495114121279.gif"

def success_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.green(), description=description)
    embed.set_author(name=title, icon_url=SUCCESS_EMOJI, url=url)
    return embed


def error_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.red(), description=description)
    embed.set_author(name=title, icon_url=ERROR_EMOJI, url=url)
    return embed

def loading_embed(title: str, description: str = None, url: str = None):
    embed = Embed(color=Color.blue(), description=description)
    embed.set_author(name=title, icon_url=LOADING_EMOJI, url=url)
    return embed