from datetime import datetime, timedelta
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from models import make_embed


def get_vc_member_count(channel: discord.VoiceChannel) -> int:
    return len([m for m in channel.members if not m.bot])


class AutoTextCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------
    # Text channel name helper
    # -------------------------
    def default_text_name(self, vc: discord.VoiceChannel):
        return f"{vc.name}-聞き専".lower()

    autotext = app_commands.Group(
        name="autotext", description="自動聞き専作成機能です。"
    )

    @autotext.command(name="setting", description="自動聞き専作成機能を設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autotext_setting(
        self,
        interaction: discord.Interaction,
        ボイスチャンネル: discord.VoiceChannel,
        有効化するか: bool
    ):
        if not ボイスチャンネル.category:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(title="指定するVCはカテゴリに入っている必要があります。")
            )
        await interaction.response.defer()

        db = self.bot.async_db["MainTwo"].AutoText

        if 有効化するか:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$addToSet": {"Channels": ボイスチャンネル.id}},
                upsert=True
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="自動聞き専機能を有効化しました。")
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$pull": {"Channels": ボイスチャンネル.id}},
                upsert=True
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="自動聞き専機能を無効化しました。")
            )

    @autotext.command(name="textname", description="聞き専チャンネルの名前を設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autotext_textname(
        self,
        interaction: discord.Interaction,
        ボイスチャンネル: discord.VoiceChannel,
        チャンネル名: str
    ):
        if not ボイスチャンネル.category:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(title="指定するVCはカテゴリに入っている必要があります。")
            )
        await interaction.response.defer()

        db = self.bot.async_db["MainTwo"].AutoText

        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$pull": {"TextName": {"Channel": ボイスチャンネル.id}}}
        )

        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$addToSet": {"TextName": {"Channel": ボイスチャンネル.id, "Name": チャンネル名}}},
            upsert=True
        )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="聞き専の名前を変更しました。",
                description=f"```{チャンネル名}```"
            )
        )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        db = self.bot.async_db["MainTwo"].AutoText

        try:
            guild_id = after.channel.guild.id if after.channel else before.channel.guild.id
            data = await db.find_one({"Guild": guild_id}, {"_id": False})
        except:
            return

        if not data:
            return

        target_channels = data.get("Channels", [])
        name_settings = data.get("TextName", [])

        guild = member.guild

        if before.channel is None and after.channel is not None:
            if after.channel.id not in target_channels:
                return

            vc = after.channel
            member_count = get_vc_member_count(vc)

            if member_count == 1:
                category = vc.category

                tname = None
                for entry in name_settings:
                    if entry.get("Channel") == vc.id:
                        tname = entry.get("Name")
                        break

                if tname is None:
                    tname = self.default_text_name(vc)

                existing = discord.utils.get(guild.text_channels, name=tname)
                if existing is None:
                    vc_text = await guild.create_text_channel(
                        name=tname,
                        category=category,
                        reason="VCを始めたので聞き専チャットを自動作成"
                    )

                    await db.update_one(
                        {"Guild": guild.id},
                        {"$addToSet": {"NowText": vc_text.id}},
                        upsert=True
                    )

                    await vc_text.send(content=member.mention, embed=make_embed.success_embed(title="聞き専チャンネルが作成されました。", description=f"このチャンネルは{after.channel.mention}に\n誰もいなくなったら自動的に消去されます。"))

        if before.channel is not None and after.channel is None:
            if before.channel.id not in target_channels:
                return

            vc = before.channel
            member_count = get_vc_member_count(vc)

            if member_count == 0:
                tname = None
                for entry in name_settings:
                    if entry.get("Channel") == vc.id:
                        tname = entry.get("Name")
                        break

                if tname is None:
                    tname = self.default_text_name(vc)

                target = discord.utils.get(guild.text_channels, name=tname)
                if target is not None:
                    await db.update_one(
                        {"Guild": guild.id},
                        {"$pull": {"NowText": target.id}},
                        upsert=True
                    )
                    vc_text = await target.delete(reason="VCが空になったため聞き専チャンネルを削除")

async def setup(bot):
    await bot.add_cog(AutoTextCog(bot))