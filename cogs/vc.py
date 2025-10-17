import asyncio
import time
from discord.ext import commands
import discord

from discord import app_commands

from models import make_embed

cooldown_tempvc = {}
cooldown_alert = {}


class VCCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> VCCog")

    vc = app_commands.Group(name="vc", description="vc管理系のコマンドです。")

    @vc.command(name="move", description="VCにメンバーを移動させます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def vc_move_(
        self,
        interaction: discord.Interaction,
        メンバー: discord.Member,
        チャンネル: discord.VoiceChannel = None,
    ):
        try:
            await interaction.response.defer()
            if not チャンネル:
                if not interaction.user.voice:
                    return await interaction.followup.send(
                        embed=discord.Embed(
                            title="移動させる先が見つかりません。",
                            color=discord.Color.green(),
                        )
                    )
                await メンバー.edit(voice_channel=interaction.user.voice.channel)
            else:
                await メンバー.edit(voice_channel=チャンネル)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="メンバーを移動しました。"
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="メンバーを移動できませんでした。",
                    description="権限エラーです。",
                )
            )

    @vc.command(name="leave", description="VCからメンバーを退出させます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def vc_leave_(
        self, interaction: discord.Interaction, メンバー: discord.Member
    ):
        try:
            await interaction.response.defer()
            await メンバー.edit(voice_channel=None)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="メンバーを退出させました。"
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="メンバーを退出させれませんでした。",
                    description="権限エラーです。",
                )
            )

    @vc.command(name="bomb", description="VCからメンバーを退出させます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def vc_bomb_(
        self,
        interaction: discord.Interaction,
        ボイスチャンネル: discord.VoiceChannel = None,
    ):
        try:
            await interaction.response.defer()
            if not ボイスチャンネル:
                if not interaction.user.voice:
                    return await interaction.followup.send(
                        embed=make_embed.error_embed(
                            title="解散させるvcが見つかりません。"
                        )
                    )
                for chm in interaction.user.voice.channel.members:
                    await chm.edit(voice_channel=None)
                    await asyncio.sleep(1)
            else:
                for chm in ボイスチャンネル.members:
                    await chm.edit(voice_channel=None)
                    await asyncio.sleep(1)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="VCを解散させました。"
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="VCを解散できませんでした。",
                    description="権限エラーです。",
                )
            )

    @vc.command(name="gather", description="VCに参加している全員を特定のVCに集めます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def vc_gather_(
        self,
        interaction: discord.Interaction,
        ボイスチャンネル: discord.VoiceChannel = None,
    ):
        try:
            await interaction.response.defer()
            if not ボイスチャンネル:
                if not interaction.user.voice:
                    return await interaction.followup.send(
                        embed=make_embed.error_embed(
                            title="集めたいVCが見つかりません。",
                            color=discord.Color.green(),
                        )
                    )
                for vc in interaction.guild.voice_channels:
                    for vm in vc.members:
                        await vm.edit(voice_channel=interaction.user.voice.channel)
                        await asyncio.sleep(1)
            else:
                for vc in interaction.guild.voice_channels:
                    for vm in vc.members:
                        await vm.edit(voice_channel=ボイスチャンネル)
                        await asyncio.sleep(1)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="VCに集めました。"
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="VCに集められませんでした。",
                    description="権限エラーです。",
                )
            )

    async def set_tempvc(self, guild: discord.Guild, vc: discord.VoiceChannel = None):
        db = self.bot.async_db["Main"].TempVCBeta
        if not vc:
            await db.delete_one({"Guild": guild.id})
            return True
        await db.update_one(
            {"Guild": guild.id}, {'$set': {"Guild": guild.id, "Channel": vc.id}}, upsert=True
        )
        return True

    @vc.command(
        name="temp",
        description="一時的なボイスチャンネルを作成するボイスチャンネルを作成します。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def vc_temp(
        self, interaction: discord.Interaction, チャンネル: discord.VoiceChannel = None
    ):
        await interaction.response.defer()
        await self.set_tempvc(interaction.guild, チャンネル)
        if not チャンネル:
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="一時的なVCを削除しました。"
                )
            )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="一時的なVCを設定しました。"
            )
        )

    @vc.command(
        name="alert", description="ボイスチャンネルに参加・退出したときに通知をします。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def vc_alert(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].VoiceAlert
        if チャンネル:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id, "Channel": チャンネル.id}},
                upsert=True,
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="ボイスチャンネル通知を有効化しました。"
                )
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="ボイスチャンネル通知を無効化しました。"
                )
            )

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_alert(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return
        db = self.bot.async_db["Main"].VoiceAlert
        try:
            dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            channel = after.channel or before.channel
            if before.channel is None and after.channel is not None:
                msg = f"{member.mention}が「{after.channel.mention}」に参加しました。"
                color = discord.Color.green()
                title = "参加"
            elif before.channel is not None and after.channel is None:
                msg = (
                    f"{member.mention} が「{before.channel.mention}」から退出しました。"
                )
                color = discord.Color.red()
                title = "退出"
            current_time = time.time()
            last_message_time = cooldown_alert.get(member.guild.id, 0)
            if current_time - last_message_time < 5:
                return
            cooldown_alert[member.guild.id] = current_time
            if member.guild.get_channel(dbfind.get("Channel", None)):
                await member.guild.get_channel(dbfind.get("Channel", None)).send(
                    embed=discord.Embed(
                        title=f"ボイスチャンネル{title}通知",
                        description=msg,
                        color=color,
                    )
                )
        except:
            return

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_temp(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.bot:
            return
        db = self.bot.async_db["Main"].TempVCBeta
        try:
            dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            if not after.channel.id == dbfind.get("Channel", 0):
                return
            current_time = time.time()
            last_message_time = cooldown_tempvc.get(member.guild.id, 0)
            if current_time - last_message_time < 5:
                return
            cooldown_tempvc[member.guild.id] = current_time
            if after.channel.category:
                vc = await after.channel.category.create_voice_channel(
                    name=f"tempvc-{member.name}"
                )
            else:
                vc = await member.guild.create_voice_channel(
                    name=f"tempvc-{member.name}"
                )
            await asyncio.sleep(0.5)
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    emoji="🗑️",
                    style=discord.ButtonStyle.red,
                    custom_id="tempvc_remove",
                )
            )
            view.add_item(
                discord.ui.Button(
                    emoji="🖊️",
                    style=discord.ButtonStyle.green,
                    custom_id="tempvc_edit",
                )
            )
            view.add_item(
                discord.ui.Button(
                    emoji="❓",
                    style=discord.ButtonStyle.blurple,
                    custom_id="tempvc_help",
                )
            )
            await vc.send(
                embed=make_embed.success_embed(
                    title="一時的なVCの管理パネル"
                ),
                view=view,
            )
            await member.edit(voice_channel=vc)
        except:
            return

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel_vc(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "tempvc_remove":
                    await interaction.response.defer(ephemeral=True)
                    await interaction.channel.delete(
                        reason="一時的なVCチャンネルの削除のため。"
                    )
                elif custom_id == "tempvc_edit":
                    class EditNameModal(discord.ui.Modal, title="チャンネルの変更"):
                        ch_name = discord.ui.TextInput(
                            label='チャンネル名を入力',
                            required=True,
                            style=discord.TextStyle.short,
                        )

                        async def on_submit(self, interaction_modal: discord.Interaction):
                            await interaction_modal.response.defer(ephemeral=True)

                            await interaction_modal.channel.edit(name=self.ch_name.value)

                            await interaction.channel.send(content=f"{interaction_modal.user.mention} がチャンネル名を変更しました。")
                    await interaction.response.send_modal(EditNameModal())
                elif custom_id == "tempvc_help":
                    await interaction.response.send_message(ephemeral=True, embed=make_embed.success_embed(title="VC作成のヘルプ", description="""
> ❓ .. このヘルプを表示します。
> 🖊️ .. VC名を変更します。
> 🗑️ .. VCを削除します。
"""))
        except:
            return


async def setup(bot):
    await bot.add_cog(VCCog(bot))
