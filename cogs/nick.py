from discord.ext import commands, tasks
import discord
from discord import app_commands
import datetime
import random

from models import command_disable


class NickNameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> NickNameCog")

    nick = app_commands.Group(name="nick", description="ニックネーム関連のコマンドです。")

    @nick.command(name="edit", description="ニックネームを編集します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick_edit(self, interaction: discord.Interaction, メンバー: discord.Member, 名前: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")
        try:
            await interaction.response.defer()
            await メンバー.edit(nick=名前)
            await interaction.followup.send(embed=discord.Embed(title="ニックネームを編集しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await interaction.followup.send(embed=discord.Embed(title="ニックネームを編集できませんでした。", color=discord.Color.red(), description="権限エラーです。"))

    @nick.command(name="reset", description="ニックネームをリセットします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick_reset(self, interaction: discord.Interaction, メンバー: discord.Member):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")
        try:
            await interaction.response.defer()
            await メンバー.edit(nick=None)
            await interaction.followup.send(embed=discord.Embed(title="ニックネームをリセットしました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await interaction.followup.send(embed=discord.Embed(title="ニックネームをリセットできませんでした。", color=discord.Color.red(), description="権限エラーです。"))


async def setup(bot):
    await bot.add_cog(NickNameCog(bot))
