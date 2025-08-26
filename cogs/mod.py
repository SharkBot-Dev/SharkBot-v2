from discord.ext import commands, tasks
import discord
import datetime
from consts import settings
from discord import app_commands
from models import command_disable
import asyncio
import re

timeout_pattern = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")

def parse_time(timestr: str):
    match = timeout_pattern.fullmatch(timestr.strip().lower())
    if not match:
        raise ValueError("時間の形式が正しくありません")

    days, hours, minutes, seconds = match.groups(default="0")
    return datetime.timedelta(
        days=int(days),
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds),
    )

class ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ModCog")

    moderation = app_commands.Group(name="moderation", description="モデレーション系のコマンドです。")

    @moderation.command(name="kick", description="メンバーをキックします。")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def kick(self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(embed=discord.Embed(title=f"自分自身はキックできません。", color=discord.Color.red()), ephemeral=True)
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(embed=discord.Embed(title=f"このサーバーにいないメンバーはキックできません。", color=discord.Color.red()))
        await interaction.response.defer()
        try:
            await interaction.guild.kick(ユーザー, reason=理由)
        except:
            return await interaction.followup.send(embed=discord.Embed(title="キックに失敗しました。", description="権限が足りないかも！？", color=discord.Color.red()))
        return await interaction.followup.send(embed=discord.Embed(title=f"{ユーザー.name}をKickしました。", color=discord.Color.green()))
    
    @moderation.command(name="ban", description="ユーザーをBanします。")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def ban(self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(embed=discord.Embed(title=f"自分自身はBanできません。", color=discord.Color.red()), ephemeral=True)
        await interaction.response.defer()
        try:
            await interaction.guild.ban(ユーザー, reason=理由)
        except:
            return await interaction.followup.send(embed=discord.Embed(title="Banに失敗しました。", description="権限が足りないかも！？", color=discord.Color.red()))
        return await interaction.followup.send(embed=discord.Embed(title=f"{ユーザー.name}をBanしました。", color=discord.Color.green()))
    
    @moderation.command(name="softban", description="ユーザーをSoftBanします。")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def softban(self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(embed=discord.Embed(title=f"自分自身はSoftBanできません。", color=discord.Color.red()), ephemeral=True)
        await interaction.response.defer()
        try:
            await interaction.guild.ban(ユーザー, reason=理由)

            await asyncio.sleep(2)
            await interaction.guild.unban(ユーザー, reason=理由)
        except:
            return await interaction.followup.send(embed=discord.Embed(title="SoftBanに失敗しました。", description="権限が足りないかも！？", color=discord.Color.red()))
        return await interaction.followup.send(embed=discord.Embed(title=f"{ユーザー.name}をSoftBanしました。", color=discord.Color.green()))
    
    @moderation.command(name="timeout", description="メンバーをタイムアウトします。")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def timeout(self, interaction: discord.Interaction, ユーザー: discord.User, 時間: str, 理由: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(embed=discord.Embed(title=f"自分自身はSoftBanできません。", color=discord.Color.red()), ephemeral=True)
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(embed=discord.Embed(title=f"このサーバーにいないメンバーはタイムアウトできません。", color=discord.Color.red()))
        await interaction.response.defer()
        try:
            duration = parse_time(時間)
            await interaction.guild.get_member(ユーザー.id).edit(timeout=discord.utils.utcnow() + duration, reason=理由)
        except:
            return await interaction.followup.send(embed=discord.Embed(title="タイムアウトに失敗しました。", description="権限が足りないかも！？", color=discord.Color.red()))
        return await interaction.followup.send(embed=discord.Embed(title=f"{ユーザー.name}をタイムアウトしました。", color=discord.Color.green()))
    
    @moderation.command(name="clear", description="メッセージを一斉削除します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def clear(self, interaction: discord.Interaction, メッセージ数: int):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer(ephemeral=True)

        now = discord.utils.utcnow()
        two_weeks = datetime.timedelta(days=14)

        def check(msg: discord.Message):
            return (now - msg.created_at) < two_weeks

        deleted = await interaction.channel.purge(limit=メッセージ数, check=check)
        await interaction.followup.send(ephemeral=True, content=f"{len(deleted)} 件のメッセージを削除しました")

async def setup(bot):
    await bot.add_cog(ModCog(bot))