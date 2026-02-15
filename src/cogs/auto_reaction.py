from discord.ext import commands
import discord
import random
import time
from discord import app_commands
from models import make_embed

cooldown_auto_reaction = {}


class AutoReactionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoReactionCog")

    async def add_reactions_from_string(self, message: discord.Message, emoji_str: str):
        if emoji_str == "random":
            if message.guild.emojis:
                try:
                    r_em = random.choice(message.guild.emojis)
                    await message.add_reaction(r_em)
                except discord.HTTPException:
                    pass
            return

        emojis = set(emoji_str.split("|"))
        for e in emojis:
            try:
                e = e.strip()
                if e:
                    await message.add_reaction(e)
            except discord.HTTPException:
                continue

    @commands.Cog.listener("on_message")
    async def on_message_auto_reaction(self, message: discord.Message):
        if message.author.bot or not message.guild or not message.content:
            return

        current_time = time.time()
        last_time = cooldown_auto_reaction.get(message.author.id, 0)
        if current_time - last_time < 3:
            return

        db_main = self.bot.async_db["Main"]
        
        channel_data = await db_main.AutoReactionChannel.find_one(
            {"Guild": message.guild.id, "Channel": message.channel.id},
            {"_id": False}
        )

        word_data = await db_main.AutoReactionWord.find_one(
            {"Guild": message.guild.id, "Word": message.content},
            {"_id": False}
        )

        if not channel_data and not word_data:
            return

        cooldown_auto_reaction[message.author.id] = current_time

        if channel_data and (em := channel_data.get("Emoji")):
            await self.add_reactions_from_string(message, em)

        if word_data and (em := word_data.get("Emoji")):
            await self.add_reactions_from_string(message, em)

    autoreact = app_commands.Group(
        name="autoreact", description="自動リアクション関連の設定です。"
    )

    @autoreact.command(
        name="channel", description="自動リアクションをするチャンネルを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreact_channel(self, interaction: discord.Interaction, 絵文字: str):
        db = self.bot.async_db["Main"].AutoReactionChannel
        await db.update_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "Emoji": 絵文字,
                }
            },
            upsert=True,
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="自動リアクションを設定しました。",
                description=f"絵文字: {絵文字}\nチャンネル: {interaction.channel.mention}",
            )
        )

    @autoreact.command(
        name="word", description="自動リアクションをするワードを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreact_word(
        self, interaction: discord.Interaction, 言葉: str, 絵文字: str
    ):
        db = self.bot.async_db["Main"].AutoReactionWord
        await db.update_one(
            {"Guild": interaction.guild.id, "Word": 言葉},
            {"$set": {"Guild": interaction.guild.id, "Word": 言葉, "Emoji": 絵文字}},
            upsert=True,
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="自動リアクションを設定しました。",
                description=f"絵文字: {絵文字}",
            )
        )

    @autoreact.command(name="remove", description="自動リアクションを削除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreact_remove(
        self, interaction: discord.Interaction, ワード: str = None
    ):
        db = self.bot.async_db["Main"].AutoReactionChannel
        await db.delete_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
        )
        if ワード:
            db_word = self.bot.async_db["Main"].AutoReactionWord
            await db_word.delete_one({"Guild": interaction.guild.id, "Word": ワード})
        await interaction.response.send_message(
            embed=make_embed.success_embed(title="自動リアクションを削除しました。")
        )

    @autoreact.command(name="list", description="自動リアクションをリスト化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreact_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].AutoReactionWord
        word_list = [
            f"{b.get('Word')} - {b.get('Emoji')}"
            async for b in db.find({"Guild": interaction.guild.id})
        ]
        db_channel = self.bot.async_db["Main"].AutoReactionChannel
        channel_list = [
            f"{interaction.guild.get_channel(b.get('Channel')).mention if interaction.guild.get_channel(b.get('Channel')) else '不明'} - {b.get('Emoji')}"
            async for b in db_channel.find({"Guild": interaction.guild.id})
        ]
        await interaction.followup.send(
            embed=make_embed.success_embed(title="自動リアクションのリスト")
            .add_field(name="特定のワードに対して", value="\n".join(word_list))
            .add_field(name="チャンネルに対して", value="\n".join(channel_list))
        )


async def setup(bot):
    await bot.add_cog(AutoReactionCog(bot))
