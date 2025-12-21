import asyncio
import io
import re
import traceback
import aiohttp
from discord.ext import commands
import discord
from models import permissions_text

from models import make_embed
from discord import app_commands

from PIL import Image, ImageDraw, ImageFont, ImageOps

def edit_emoji(byte: io.BytesIO):
    image = Image.open(byte, "r")
    i = io.BytesIO()
    image = image.resize((128, 128))
    image.save(i, format="png")
    i.seek(0)
    image.close()
    return i

EMOJI_RE = re.compile(r"(<a?:(\w+):(\d+?)>)")

def extract_discord_emoji_info(text):
    matches = EMOJI_RE.findall(text)

    results = []
    for full_emoji, name, emoji_id in matches:
        is_animated = full_emoji.startswith("<a:")

        results.append((name, emoji_id, is_animated))

    return results

allowed_content_types = [
    "image/jpeg",
    "image/png",
]

class EmojisCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> EmojisCog")

    emojis = app_commands.Group(
        name="emojis",
        description="絵文字を作成&編集します。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @emojis.command(name="copy", description="絵文字をコピーします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True, create_expressions=True)
    async def emojis_copy(self, interaction: discord.Interaction, 絵文字: str):
        await interaction.response.defer()
        extracted_info = extract_discord_emoji_info(絵文字)
        for name, emoji_id, is_animated in extracted_info:
            if is_animated:
                url=f"https://cdn.discordapp.com/emojis/{emoji_id}.gif"
            else:
                url=f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    i = io.BytesIO(await resp.read())
                    b = i.read()
                    em = await interaction.guild.create_custom_emoji(name=name, image=b)
                    i.close()
                    await interaction.followup.send(embed=make_embed.success_embed(title="絵文字をコピーしました。", description=em.__str__()))
            return

    @emojis.command(name="create", description="絵文字を作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True, create_expressions=True)
    async def emojis_create(self, interaction: discord.Interaction, 名前: str, ファイル: discord.Attachment):
        if ファイル.content_type not in allowed_content_types:
            return await interaction.response.send_message(ephemeral=True, embed=make_embed.error_embed(title="絵文字を追加できませんでした。", description="画像タイプはpngかjpgである必要があります。"))
        await interaction.response.defer()
        name = 名前.lower()
        if not name.islower():
            return await interaction.followup.send(embed=make_embed.error_embed(title="絵文字を追加できませんでした。", description="絵文字を追加するには、名前を小文字で、\nかつ英語で入力する必要があります。"))
        i = io.BytesIO(await ファイル.read())
        image = await asyncio.to_thread(edit_emoji, i)
        b = image.read()
        em = await interaction.guild.create_custom_emoji(name=name, image=b)
        i.close()
        image.close()
        await interaction.followup.send(embed=make_embed.success_embed(title="絵文字を追加しました。", description=em.__str__()))

    @emojis.command(name="list", description="絵文字をリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def emojis_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        em_ls = []
        for e in interaction.guild.emojis:
            em_ls.append(e.__str__())
        await interaction.followup.send(" ".join(em_ls), ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmojisCog(bot))
