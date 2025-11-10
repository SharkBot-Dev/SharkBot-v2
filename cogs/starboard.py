import time
from discord.ext import commands
import discord

from discord import app_commands
from models import command_disable, make_embed

cooldown_reaction = {}


class StarBoardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> StarBoardCog")

    async def get_reaction_channel(
        self, guild: discord.Guild, emoji: discord.PartialEmoji
    ):
        db = self.bot.async_db["Main"].ReactionBoard
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Emoji": emoji.__str__()}, {"_id": False}
            )
        except Exception:
            return None
        if not dbfind:
            return None
        return self.bot.get_channel(dbfind["Channel"])

    async def get_channel(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].ReactionBoard
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except Exception:
            return None
        if not dbfind:
            return None
        return self.bot.get_channel(dbfind["Channel"])

    async def save_message(self, original: discord.Message, board_msg: discord.Message):
        db = self.bot.async_db["Main"].ReactionBoardMessage
        await db.update_one(
            {"Guild": original.guild.id},
            {'$set': {
                "Guild": original.guild.id,
                "ID": original.id,
                "ReactMessageID": board_msg.id,
            }},
            upsert=True,
        )

    async def read_message(self, original: discord.Message):
        db = self.bot.async_db["Main"].ReactionBoardMessage
        try:
            dbfind = await db.find_one(
                {"Guild": original.guild.id, "ID": original.id},
                {"_id": False},
            )
        except Exception:
            return None
        if not dbfind:
            return None
        return dbfind["ReactMessageID"]

    async def reaction_add(self, message: discord.Message, emoji_: str):
        """リアクション追加時の処理"""
        reaction_counts = {r.emoji: r.count for r in message.reactions}

        if emoji_ not in reaction_counts:
            return

        count = reaction_counts[emoji_]
        cha = await self.get_reaction_channel(message.guild, emoji_)
        if not cha:
            return

        if count == 1:
            board_msg = await cha.send(
                embed=discord.Embed(
                    title=f"{emoji_}x1",
                    description=message.content,
                    color=discord.Color.blue(),
                ).set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar.url
                    if message.author.avatar
                    else message.author.default_avatar.url,
                ).set_image(url=message.attachments[0].url if message.attachments else None),
                view=discord.ui.View().add_item(
                    discord.ui.Button(label="メッセージに飛ぶ", url=message.jump_url)
                ),
            )
            await self.save_message(message, board_msg)
        else:
            cha = await self.get_channel(message.guild)
            msg_id = await self.read_message(message)
            if not msg_id:
                return
            try:
                m = await cha.fetch_message(msg_id)
            except discord.NotFound:
                return
            await m.edit(
                embed=discord.Embed(
                    title=f"{emoji_}x{count}",
                    description=message.content,
                    color=discord.Color.blue(),
                ).set_author(
                    name=message.author.name,
                    icon_url=message.author.avatar.url
                    if message.author.avatar
                    else message.author.default_avatar.url,
                ).set_image(url=message.attachments[0].url if message.attachments else None)
            )

    async def reaction_add_2(self, message: discord.Message, emoji_: str):
        """リアクション削除時の処理"""
        reaction_counts = {r.emoji: r.count for r in message.reactions}

        if emoji_ not in reaction_counts:
            cha = await self.get_channel(message.guild)
            msg_id = await self.read_message(message)
            if not msg_id:
                return
            try:
                m = await cha.fetch_message(msg_id)
            except discord.NotFound:
                return
            await m.delete()
            return

        count = reaction_counts[emoji_]
        cha = await self.get_channel(message.guild)
        msg_id = await self.read_message(message)
        if not msg_id:
            return
        try:
            m = await cha.fetch_message(msg_id)
        except discord.NotFound:
            return
        await m.edit(
            embed=discord.Embed(
                title=f"{emoji_}x{count}",
                description=message.content,
                color=discord.Color.blue(),
            ).set_author(
                name=message.author.name,
                icon_url=message.author.avatar.url
                if message.author.avatar
                else message.author.default_avatar.url,
            ).set_image(url=message.attachments[0].url if message.attachments else None)
        )

    @commands.Cog.listener("on_raw_reaction_add")
    async def on_reaction_add_reaction_board(
        self, payload: discord.RawReactionActionEvent
    ):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        check = await self.get_reaction_channel(guild, payload.emoji)
        if not check:
            return

        current_time = time.time()
        last_message_time = cooldown_reaction.get(payload.guild_id, 0)
        if current_time - last_message_time < 1:
            return
        cooldown_reaction[payload.guild_id] = current_time

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        message = await channel.fetch_message(payload.message_id)
        await self.reaction_add(message, payload.emoji.__str__())

    @commands.Cog.listener("on_raw_reaction_remove")
    async def on_reaction_remove_reaction_board(
        self, payload: discord.RawReactionActionEvent
    ):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        check = await self.get_reaction_channel(guild, payload.emoji)
        if not check:
            return

        current_time = time.time()
        last_message_time = cooldown_reaction.get(payload.guild_id, 0)
        if current_time - last_message_time < 1:
            return
        cooldown_reaction[payload.guild_id] = current_time

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        message = await channel.fetch_message(payload.message_id)
        await self.reaction_add_2(message, payload.emoji.__str__())

    async def set_reaction_board(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.TextChannel,
        絵文字: str,
    ):
        db = self.bot.async_db["Main"].ReactionBoard
        await db.update_one(
            {"Guild": interaction.guild.id, "Channel": チャンネル.id},
            {'$set': {"Guild": interaction.guild.id, "Channel": チャンネル.id, "Emoji": 絵文字}},
            upsert=True,
        )

    async def delete_reaction_board(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].ReactionBoard
        await db.delete_one({"Channel": interaction.channel.id})

    starboard = app_commands.Group(
        name="starboard", description="スターボードのコマンドです。"
    )

    @starboard.command(name="setup", description="スターボードをセットアップします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def reactionboard_setup(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.TextChannel,
        絵文字: str = "⭐",
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        try:
            await interaction.response.defer()
            await self.set_reaction_board(interaction, チャンネル, 絵文字)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="スターボードをセットアップしました。",
                    description=f"{チャンネル.mention}",
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="スターボードをセットアップできませんでした。",
                    description="権限エラーです。",
                )
            )

    @starboard.command(name="disable", description="スターボードを無効化します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def reation_board_disable(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        try:
            await interaction.response.defer()
            await self.delete_reaction_board(interaction)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="スターボードを無効にしました。"
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="スターボードを無効にできませんでした。",
                    description="権限エラーです。",
                )
            )


async def setup(bot):
    await bot.add_cog(StarBoardCog(bot))
