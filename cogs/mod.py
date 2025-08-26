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
            return await interaction.response.send_message(embed=discord.Embed(title=f"自分自身はタイムアウトできません。", color=discord.Color.red()), ephemeral=True)
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(embed=discord.Embed(title=f"このサーバーにいないメンバーはタイムアウトできません。", color=discord.Color.red()))
        await interaction.response.defer()
        try:
            duration = parse_time(時間)
            await interaction.guild.get_member(ユーザー.id).edit(timeout=discord.utils.utcnow() + duration, reason=理由)
        except:
            return await interaction.followup.send(embed=discord.Embed(title="タイムアウトに失敗しました。", description="権限が足りないかも！？", color=discord.Color.red()))
        return await interaction.followup.send(embed=discord.Embed(title=f"{ユーザー.name}をタイムアウトしました。", color=discord.Color.green()))
    
    @moderation.command(name="max-timeout", description="最大までタイムアウトします。")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def max_timeout(self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(embed=discord.Embed(title=f"自分自身はタイムアウトできません。", color=discord.Color.red()), ephemeral=True)
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(embed=discord.Embed(title=f"このサーバーにいないメンバーはタイムアウトできません。", color=discord.Color.red()))
        await interaction.response.defer()
        try:
            await interaction.guild.get_member(ユーザー.id).edit(timeout=discord.utils.utcnow() + datetime.datetime(day=28), reason=理由)
        except:
            return await interaction.followup.send(embed=discord.Embed(title="タイムアウトに失敗しました。", description="権限が足りないかも！？", color=discord.Color.red()))
        return await interaction.followup.send(embed=discord.Embed(title=f"{ユーザー.name}を最大までタイムアウトしました。", color=discord.Color.green()))
    
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

    @moderation.command(name="warn", description="メンバーを警告します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def warn(self, interaction: discord.Interaction, メンバー: discord.User, 理由: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        if interaction.guild.get_member(メンバー.id) is None:
            return await interaction.response.send_message(embed=discord.Embed(title=f"このサーバーにいないメンバーは警告できません。", color=discord.Color.red()))
        
        await メンバー.send(embed=discord.Embed(title=f"あなたは`{interaction.guild.name}`\nで警告されました。", color=discord.Color.yellow(), description=f"理由: {理由}"))

        await interaction.followup.send(ephemeral=True, embed=discord.Embed(title="警告しました。", color=discord.Color.green()))

    @moderation.command(name="lock", description="チャンネルをロックします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def lock(self, interaction: discord.Interaction, スレッド作成可能か: bool = False, リアクション可能か: bool = False):
        await interaction.response.defer()
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        overwrite.create_polls = False
        overwrite.use_application_commands = False
        overwrite.attach_files = False
        if スレッド作成可能か:
            overwrite.create_public_threads = True
            overwrite.create_private_threads = True
        else:
            overwrite.create_public_threads = False
            overwrite.create_private_threads = False
        if リアクション可能か:
            overwrite.add_reactions = True
        else:
            overwrite.add_reactions = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.followup.send(content="🔒チャンネルをロックしました。")

    @moderation.command(name="unlock", description="チャンネルを開放します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.response.defer()
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        overwrite.create_polls = True
        overwrite.use_application_commands = True
        overwrite.attach_files = True
        overwrite.create_public_threads = True
        overwrite.create_private_threads = True
        overwrite.add_reactions = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.followup.send(content="🔓チャンネルを開放しました。")

    @moderation.command(name="report", description="レポートチャンネルをセットアップします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def report_channel(self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer(ephemeral=True)
        db = self.bot.async_db["Main"].ReportChannel
        if チャンネル:
            await db.replace_one(
                {"Guild": interaction.guild.id}, 
                {"Guild": interaction.guild.id, "Channel": チャンネル.id}, 
                upsert=True
            )
            await interaction.followup.send(embed=discord.Embed(title="通報チャンネルをセットアップしました。", color=discord.Color.green()))
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.followup.send(embed=discord.Embed(title="通報チャンネルを無効化しました。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(ModCog(bot))