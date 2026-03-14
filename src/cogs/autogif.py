from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
from discord import app_commands
import time
import aiohttp
from consts import settings
import asyncio

from models import make_embed, translate, web_translate

cooldown_autogif = {}


class AutoGifAddChannelGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="autogif-channel",
            description="自動gif返信するチャンネルを指定します。",
        )

    @app_commands.command(
        name="add", description="自動gif返信のチャンネルを追加します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_add_autogif(self, interaction: discord.Interaction):
        db = interaction.client.async_db["Main"].AutoGif
        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$addToSet": {"Channel": interaction.channel.id}},
            upsert=True,
        )
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(
                title=translate.get(
                    interaction.extras["lang"],
                    "autogif",
                    "自動gif返信のチャンネルを追加しました。",
                ),
                color=discord.Color.green(),
            ),
        )

    @app_commands.command(
        name="remove", description="自動gif返信のチャンネルを削除します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_remove_autogif(self, interaction: discord.Interaction):
        db = interaction.client.async_db["Main"].AutoGif
        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$pull": {"Channel": interaction.channel.id}},
            upsert=True,
        )
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(
                title=translate.get(
                    interaction.extras["lang"],
                    "autogif",
                    "自動gif返信のチャンネルを削除しました。",
                ),
                color=discord.Color.green(),
            ),
        )


async def reply_gif(message: discord.Message):
    if message.content == "":
        return

    text = await web_translate.translate("ja", "en", message.clean_content)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.imgur.com/3/gallery/search",
            params={"q": text['text']},
            headers={"Authorization": f"Client-ID {settings.IMGUR_CLIENTID}"},
        ) as resp:
            data = await resp.json()
            if data and "data" in data:
                for item in data["data"]:
                    if item.get("animated"):
                        return await message.reply(item["link"])
                            
                    if "images" in item:
                        for image in item["images"]:
                            if image.get("animated"):
                                return await message.reply(image["link"])
                            
            await message.reply("🤔")


class AutoGifCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoGifCog")

    gif = app_commands.Group(name="gif", description="gif関連のコマンドです。")

    gif.add_command(AutoGifAddChannelGroup())

    @gif.command(name="search", description="gifを検索します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def gif_search(self, interaction: discord.Interaction, 検索ワード: str):
        await interaction.response.defer()

        text = await web_translate.translate("ja", "en", 検索ワード)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.imgur.com/3/gallery/search",
                    params={"q": text['text']},
                    headers={"Authorization": f"Client-ID {settings.IMGUR_CLIENTID}"},
                ) as resp:
                    data = await resp.json()

                    if data and "data" in data:
                        for item in data["data"]:
                            if item.get("animated"):
                                return await interaction.followup.send(item["link"])
                            
                            if "images" in item:
                                for image in item["images"]:
                                    if image.get("animated"):
                                        return await interaction.followup.send(image["link"])

                    return await interaction.followup.send(embed=make_embed.error_embed(title="Gifが見つかりませんでした。"))
        except Exception as e:
            print(f"Error: {e}")
            return await interaction.followup.send(embed=make_embed.error_embed(title="Gifが見つかりませんでした。"))

    @commands.Cog.listener("on_message")
    async def on_message_channel_autogif(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return
        db = self.bot.async_db["Main"].AutoGif
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        check = dbfind.get("Channel", None)
        if not check:
            return

        for c in check:
            if c == message.channel.id:
                current_time = time.time()
                last_message_time = cooldown_autogif.get(message.guild.id, 0)
                if current_time - last_message_time < 3:
                    return
                cooldown_autogif[message.guild.id] = current_time
                await reply_gif(message)
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoGifCog(bot))
