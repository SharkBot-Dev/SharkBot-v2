from discord.ext import commands
import discord
from discord import app_commands

from models import command_disable, make_embed
import re


class ChannelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.timeout_pattern = re.compile(
            r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
        )
        print("init -> ChannelCog")

    channel = app_commands.Group(
        name="channel", description="チャンネル系のコマンドです。"
    )

    @channel.command(name="info", description="チャンネルの情報を表示するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_info(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channel = interaction.channel
        embed = make_embed.success_embed(title="チャンネルの情報")
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

    @channel.command(
        name="private", description="チャンネルをプライベートチャンネルにします。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def channel_private(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            overwrite = interaction.channel.overwrites_for(
                interaction.guild.default_role
            )
            overwrite.read_messages = False
            if type(interaction.channel) == discord.VoiceChannel:
                overwrite.connect = False
            await interaction.channel.set_permissions(
                interaction.guild.default_role, overwrite=overwrite
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="プライベートチャンネルにしました。"
                )
            )
        except discord.Forbidden as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="プライベートチャンネルにできませんでした。",
                    description="権限エラーです。",
                )
            )

    @channel.command(
        name="remove-private",
        description="チャンネルをプライベートチャンネルではなくします。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def remove_channel_private(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            overwrite = interaction.channel.overwrites_for(
                interaction.guild.default_role
            )
            overwrite.read_messages = True
            if type(interaction.channel) == discord.VoiceChannel:
                overwrite.connect = True
            await interaction.channel.set_permissions(
                interaction.guild.default_role, overwrite=overwrite
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="プライベートチャンネルを解除しました。"
                )
            )
        except discord.Forbidden as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="プライベートチャンネルを解除することに失敗しました。",
                    description="権限エラーです。",
                )
            )

    @channel.command(name="slowmode", description="低速モードを設定するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, 何秒か: int):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        try:
            await interaction.response.defer()
            await interaction.channel.edit(slowmode_delay=何秒か)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="スローモードを設定しました。"
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="スローモードを設定できませんでした。",
                    description="権限エラーです。",
                )
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="スローモードを設定できませんでした。",
                    description="6時間以上を設定しようとしているなら、\n`/channel long-slowmode`を使用してください。",
                )
            )

    @channel.command(
        name="long-slowmode",
        description="Botを使った長時間の低速モードを設定します。6時間以上も可能です。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode_bot(self, interaction: discord.Interaction, 時間: str):
        def parse_time_to_seconds(time_str: str) -> int:
            match = self.timeout_pattern.fullmatch(time_str)
            if not match:
                return None
            days, hours, minutes, seconds = match.groups()
            total_seconds = 0
            if days:
                total_seconds += int(days) * 86400
            if hours:
                total_seconds += int(hours) * 3600
            if minutes:
                total_seconds += int(minutes) * 60
            if seconds:
                total_seconds += int(seconds)
            return total_seconds

        delay_seconds = parse_time_to_seconds(時間)
        db = self.bot.async_db["Main"].SlowModeBot
        if delay_seconds == 0:
            await db.delete_one({"channel_id": interaction.channel.id})
            return await interaction.response.send_message(
                "Botを使ったスローモードを無効化しました。", ephemeral=True
            )

        if delay_seconds is None or delay_seconds < 0:
            await interaction.response.send_message(
                "無効な時間指定です。例: `1d2h30m`", ephemeral=True
            )
            return

        await db.update_one(
            {"channel_id": interaction.channel.id},
            {"$set": {"delay_seconds": delay_seconds}},
            upsert=True,
        )

        await interaction.response.send_message(
            "Botを使った低速モードを設定しました。", ephemeral=True
        )

    @channel.command(name="command-disable", description="このチャンネルではコマンドを無効化するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def command_disable(
        self, interaction: discord.Interaction, コマンドが使えるか: bool
    ):
        db = self.bot.async_db["Main"].CommandDisable
        if not コマンドが使えるか:
            await db.update_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
                {"$set": {"Guild": interaction.guild.id, "Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="このチャンネルではコマンドを使用できなくしました。"
                )
            )
        else:
            await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="このチャンネルではコマンドを使用できるようにしました。"
                )
            )


async def setup(bot):
    await bot.add_cog(ChannelCog(bot))
