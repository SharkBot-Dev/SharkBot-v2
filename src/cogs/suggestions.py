import asyncio
import time
import discord
from discord.ext import commands, tasks

from discord import app_commands

import aiohttp

from models import make_embed

import re

class SuggestionsSendModal(discord.ui.Modal, title="提案を送信する。"):
    title_ = discord.ui.Label(
        text="タイトル",
        description="タイトルを入力",
        component=discord.ui.TextInput(
            style=discord.TextStyle.short, required=True
        ),
    )

    text = discord.ui.Label(
        text="提案内容",
        description="提案内容を入力",
        component=discord.ui.TextInput(
            style=discord.TextStyle.long, required=True
        ),
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        assert isinstance(self.title_.component, discord.ui.TextInput)
        assert isinstance(self.text.component, discord.ui.TextInput)

        db = interaction.client.async_db["MainTwo"].Suggestions
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            return await interaction.followup.send(embed=make_embed.error_embed(title="提案チャンネルが見つかりません。", description="管理者に問い合わせください。"))
        
        channel = interaction.guild.get_channel(dbfind.get("Channel"))
        if not channel:
            return await interaction.followup.send(embed=make_embed.error_embed(title="提案チャンネルが見つかりません。", description="管理者に問い合わせください。"))
        
        msg = await channel.send(embed=discord.Embed(title=self.title_.component.value, description=self.text.component.value, color=discord.Color.blue())
                           .set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
                           .set_footer(
                                text=f"可決に必要な賛成数: {dbfind.get('MaxCount', 3)} | 否決に必要な反対数: {dbfind.get('MinCount', 3)}"
                            ))

        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await asyncio.sleep(1)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

class SuggestionsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> SuggestionsCog")

    @commands.Cog.listener("on_raw_reaction_add")
    async def on_reaction_add_suggestions(
        self, payload: discord.RawReactionActionEvent
    ):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = payload.member or guild.get_member(payload.user_id)
        if not member or member.bot:
            return

        db = self.bot.async_db["MainTwo"].Suggestions
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Channel": payload.channel_id},
                {"_id": False}
            )
        except Exception:
            return

        if not dbfind:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        if payload.message_author_id != self.bot.user.id:
            return

        try:
            msg = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not msg.embeds:
            return

        embed = msg.embeds[0]
        if not embed.footer or not embed.footer.text:
            return

        footer = embed.footer.text
        if not footer.startswith("可決に必要な賛成数:"):
            return

        for field in msg.embeds[0].fields:
            if field.name in ("この案は可決されました。", "この案は否決されました。"):
                return

        emoji = str(payload.emoji)

        if emoji in ("✅", "❌"):
            if not member.guild_permissions.administrator:
                await msg.remove_reaction(payload.emoji, member)
                return

            em = embed.copy()
            em.add_field(
                name="この案は可決されました。" if emoji == "✅" else "この案は否決されました。",
                value="👍" if emoji == "✅" else "❌"
            )
            await msg.edit(embed=em)
            await msg.clear_reactions()
            return

        footer = embed.footer.text

        match = re.search(
            r"可決に必要な賛成数:\s*(\d+).*否決に必要な反対数:\s*(\d+)",
            footer
        )
        if not match:
            return

        need_approve = int(match.group(1))
        need_reject = int(match.group(2))

        reaction_counts = {str(r.emoji): r.count for r in msg.reactions}

        approve_count = reaction_counts.get("👍", 0)
        reject_count = reaction_counts.get("👎", 0)

        if approve_count > need_approve:
            em = embed.copy()
            em.add_field(name="この案は可決されました。", value="👍")
            await msg.edit(embed=em)
            await msg.clear_reactions()
            return

        if reject_count > need_reject:
            em = embed.copy()
            em.add_field(name="この案は否決されました。", value="👎")
            await msg.edit(embed=em)
            await msg.clear_reactions()
            return

    suggestions = app_commands.Group(
        name="suggestions", description="提案関連のコマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @suggestions.command(name="send", description="提案を送信します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def suggestions_send(
        self,
        interaction: discord.Interaction
    ):
        db = interaction.client.async_db["MainTwo"].Suggestions
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            return await interaction.response.send_message(embed=make_embed.error_embed(title="提案チャンネルが見つかりません。", description="管理者に問い合わせください。"), ephemeral=True)

        await interaction.response.send_modal(SuggestionsSendModal())

    @suggestions.command(name="setting", description="提案関連のチャンネルをセットアップします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def suggestions_setting(
        self,
        interaction: discord.Interaction,
        可決されるのに必要な賛成数: int = 3,
        否決されるのに必要な賛成数: int = 3
    ):
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="テキストチャンネルのみを指定できます。",
                    description="指定できるのはテキストチャンネルのみです。",
                ),
            )

        db = self.bot.async_db["MainTwo"].Suggestions
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Channel": interaction.channel.id, "MaxCount": 可決されるのに必要な賛成数, "MinCount": 否決されるのに必要な賛成数}},
                upsert=True,
            )
            return await interaction.response.send_message(embed=make_embed.success_embed(title="提案関連のチャンネルをセットアップしました。"))
        else:
            await db.delete_one(
                {"Guild": interaction.guild.id}
            )
            return await interaction.response.send_message(embed=make_embed.success_embed(title="提案関連のチャンネルを無効化しました。"))

async def setup(bot):
    await bot.add_cog(SuggestionsCog(bot))
