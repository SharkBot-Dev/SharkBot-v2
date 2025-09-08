import time
from discord.ext import commands
import discord

from discord import app_commands
from models import command_disable

cooldown_reaction = {}


class StarBoardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> StarBoardCog")

    async def get_reaction_channel(self, guild: discord.Guild, emoji: str):
        db = self.bot.async_db["Main"].ReactionBoard
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Emoji": emoji}, {"_id": False}
            )
        except:
            return None
        if dbfind is None:
            return None
        return self.bot.get_channel(dbfind["Channel"])

    async def get_channel(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].ReactionBoard
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return self.bot.get_channel(dbfind["Channel"])

    async def save_message(self, message: discord.Message, msg: discord.Message):
        db = self.bot.async_db["Main"].ReactionBoardMessage
        await db.replace_one(
            {"Guild": message.guild.id},
            {"Guild": message.guild.id, "ID": message.id, "ReactMessageID": msg.id},
            upsert=True,
        )

    async def read_message(self, message: discord.Message):
        db = self.bot.async_db["Main"].ReactionBoardMessage
        try:
            dbfind = await db.find_one(
                {"Guild": message.guild.id, "ReactMessageID": message.id},
                {"_id": False},
            )
        except:
            return None
        if dbfind is None:
            return None
        return dbfind["ID"]

    async def reaction_add(self, message: discord.Message, emoji_: str):
        reaction_counts = {}
        for reaction in message.reactions:
            emoji = reaction.emoji
            count = reaction.count
            reaction_counts[emoji] = count
        if reaction_counts:
            for emoji, count in reaction_counts.items():
                if emoji == emoji_:
                    if count == 1:
                        cha = await self.get_reaction_channel(message.guild, emoji_)
                        msg = await cha.send(
                            embed=discord.Embed(
                                title=f"{emoji}x1",
                                description=f"{message.content}",
                                color=discord.Color.blue(),
                            ).set_author(
                                name=message.author.name,
                                icon_url=message.author.avatar.url
                                if message.author.avatar
                                else message.author.default_avatar.url,
                            ),
                            view=discord.ui.View().add_item(
                                discord.ui.Button(
                                    label="メッセージに飛ぶ", url=message.jump_url
                                )
                            ),
                        )
                        await self.save_message(msg, message)
                    else:
                        cha = await self.get_channel(message.guild)
                        msg = await self.read_message(message)
                        try:
                            m = await cha.fetch_message(msg)
                        except:
                            return
                        msg = await m.edit(
                            embed=discord.Embed(
                                title=f"{emoji}x{count}",
                                description=f"{message.content}",
                                color=discord.Color.blue(),
                            ).set_author(
                                name=message.author.name,
                                icon_url=message.author.avatar.url
                                if message.author.avatar
                                else message.author.default_avatar.url,
                            )
                        )
                    return

    async def reaction_add_2(self, message: discord.Message, emoji_: str):
        reaction_counts = {}
        for reaction in message.reactions:
            emoji = reaction.emoji
            count = reaction.count
            reaction_counts[emoji] = count
        if reaction_counts:
            for emoji, count in reaction_counts.items():
                if emoji == emoji_:
                    cha = await self.get_channel(message.guild)
                    msg = await self.read_message(message)
                    try:
                        m = await cha.fetch_message(msg)
                    except:
                        return
                    msg = await m.edit(
                        embed=discord.Embed(
                            title=f"{emoji}x{count}",
                            description=f"{message.content}",
                            color=discord.Color.blue(),
                        ).set_author(
                            name=message.author.name,
                            icon_url=message.author.avatar.url
                            if message.author.avatar
                            else message.author.default_avatar.url,
                        )
                    )
                    return

    @commands.Cog.listener("on_raw_reaction_add")
    async def on_reaction_add_reaction_board(
        self, payload: discord.RawReactionActionEvent
    ):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        if not payload.member or payload.member.bot:
            return

        check = await self.get_reaction_channel(guild, payload.emoji)
        if check:
            current_time = time.time()
            last_message_time = cooldown_reaction.get(payload.guild_id, 0)
            if current_time - last_message_time < 1:
                return

            cooldown_reaction[payload.guild_id] = current_time
            channel = guild.get_channel(payload.channel_id)
            if not channel:
                return

            message = await channel.fetch_message(payload.message_id)
            await self.reaction_add(message, payload.emoji)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def on_reaction_remove_reaction_board(
        self, payload: discord.RawReactionActionEvent
    ):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        check = await self.get_reaction_channel(guild, payload.emoji)
        if check:
            current_time = time.time()
            last_message_time = cooldown_reaction.get(payload.guild_id, 0)
            if current_time - last_message_time < 1:
                return

            cooldown_reaction[payload.guild_id] = current_time
            channel = guild.get_channel(payload.channel_id)
            if not channel:
                return

            message = await channel.fetch_message(payload.message_id)
            await self.reaction_add_2(message, payload.emoji)

    async def set_reaction_board(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.TextChannel,
        絵文字: str,
    ):
        db = self.bot.async_db["Main"].ReactionBoard
        await db.replace_one(
            {"Guild": interaction.guild.id, "Emoji": 絵文字, "Channel": チャンネル.id},
            {"Guild": interaction.guild.id, "Channel": チャンネル.id, "Emoji": 絵文字},
            upsert=True,
        )

    async def delete_reaction_board(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].ReactionBoard
        await db.delete_one({"Guild": interaction.channel.id})

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
        絵文字: str,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        try:
            await interaction.response.defer()
            await self.set_reaction_board(interaction, チャンネル, 絵文字)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="リアクションボードをセットアップしました。",
                    color=discord.Color.green(),
                    description=f"{チャンネル.mention}",
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="リアクションボードをセットアップできませんでした。",
                    color=discord.Color.red(),
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
                embed=discord.Embed(
                    title="リアクションボードを無効にしました。",
                    color=discord.Color.green(),
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="リアクションボードを無効にできませんでした。",
                    color=discord.Color.red(),
                    description="権限エラーです。",
                )
            )


async def setup(bot):
    await bot.add_cog(StarBoardCog(bot))
