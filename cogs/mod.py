from discord.ext import commands, tasks
import discord
import datetime
from consts import settings
from discord import app_commands
from models import command_disable
import asyncio

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

async def setup(bot):
    await bot.add_cog(ModCog(bot))