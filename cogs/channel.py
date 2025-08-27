from discord.ext import commands, tasks
import discord
import datetime
import random
from discord import app_commands

from models import command_disable

class ChannelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ChannelCog")

    channel = app_commands.Group(name="channel", description="チャンネル系のコマンドです。")

    @channel.command(name="info", description="チャンネルの情報を表示するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_info(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        channel = interaction.channel
        embed = discord.Embed(title="チャンネルの情報", color=discord.Color.green())
        embed.add_field(name="名前", value=channel.name, inline=False)
        embed.add_field(name="ID", value=str(channel.id), inline=False)
        if channel.category:
            embed.add_field(name="カテゴリ", value=channel.category.name, inline=False)
        else:
            embed.add_field(name="カテゴリ", value="なし", inline=False)
        embed.add_field(name="位置", value=str(channel.position), inline=False)
        embed.add_field(name="メンション", value=channel.mention, inline=False)
        embed.set_footer(text=f"{channel.guild.name} / {channel.guild.id}")
        await interaction.followup.send(embed=embed)

    @channel.command(name="slowmode", description="低速モードを設定するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, 何秒か: int):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        try:
            await interaction.response.defer()
            await interaction.channel.edit(slowmode_delay=何秒か)
            await interaction.followup.send(embed=discord.Embed(title="スローモードを設定しました。", color=discord.Color.green()))
        except discord.Forbidden as e:
            return await interaction.followup.send(embed=discord.Embed(title="スローモードを設定できませんでした。", color=discord.Color.red(), description="権限エラーです。"))
        
    @channel.command(name="command-disable", description="低速モードを設定するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def command_disable(self, interaction: discord.Interaction, コマンドが使えるか: bool):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        db = self.bot.async_db["Main"].CommandDisable
        if not コマンドが使えるか:
            await db.replace_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}, 
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}, 
                upsert=True
            )
            await interaction.response.send_message(embed=discord.Embed(title="このチャンネルではコマンドを使用できなくしました。", color=discord.Color.green()))
        else:
            await db.delete_one({
                "Guild": interaction.guild.id, "Channel": interaction.channel.id
            })
            await interaction.response.send_message(embed=discord.Embed(title="このチャンネルではコマンドを使用できるようにしました。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(ChannelCog(bot))