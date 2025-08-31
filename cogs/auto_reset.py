from discord.ext import commands, tasks
import discord
import asyncio
from discord import app_commands
from consts import mongodb


class AutoResetCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> AutoResetCog")

    @tasks.loop(hours=3)
    async def auto_reset_loop(self):
        db = self.bot.async_db["Main"].AutoResetChannel
        async for channel in db.find():
            try:
                ch = self.bot.get_channel(channel.get("Channel", None))
                if not ch:
                    continue
                ch_ = await ch.clone()
                await db.replace_one(
                    {"Guild": ch_.guild.id},
                    {"Guild": ch_.guild.id, "Channel": ch_.id},
                    upsert=True,
                )
                await asyncio.sleep(1)
                await ch_.edit(position=ch.position + 1)
                await asyncio.sleep(1)
                await ch.delete()
                await ch_.send(
                    embed=discord.Embed(
                        title="チャンネルがリセットされました。",
                        color=discord.Color.red(),
                    )
                )
                await asyncio.sleep(1)
            except:
                continue

    async def cog_load(self):
        self.auto_reset_loop.start()
        return

    async def cog_unload(self):
        self.auto_reset_loop.stop()
        return

    autoreset = app_commands.Group(
        name="autoreset", description="チャンネルの自動リセット関連のコマンドです。"
    )

    @autoreset.command(
        name="setting", description="チャンネルの自動リセットを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def _auto_reset_setting(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].AutoResetChannel
        await db.replace_one(
            {"Guild": interaction.guild.id, "Channel": チャンネル.id},
            {"Guild": interaction.guild.id, "Channel": チャンネル.id},
            upsert=True,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="自動リセットするチャンネルを設定しました。",
                color=discord.Color.green(),
            )
        )

    @autoreset.command(
        name="disable", description="チャンネルの自動リセットを無効化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def _auto_reset_disable(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel
    ):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].AutoResetChannel
        await db.delete_one({"Guild": interaction.guild.id, "Channel": チャンネル.id})
        await interaction.followup.send(
            embed=discord.Embed(
                title="自動リセットを無効化しました。", color=discord.Color.green()
            )
        )

    @autoreset.command(
        name="now", description="チャンネルの自動リセットを今実行します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def _auto_reset_now(self, interaction: discord.Interaction):
        await interaction.response.defer()
        channels = [
            b
            async for b in self.bot.async_db["Main"].AutoResetChannel.find(
                {"Guild": interaction.guild.id}
            )
        ]
        for ch in channels:
            channel = interaction.guild.get_channel(ch.get("Channel"))
            if channel.id == interaction.channel.id:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="自動リセットの設定されているチャンネルでは\nリセットコマンドを実行できません。",
                        color=discord.Color.red(),
                    )
                )
            ch_ = await channel.clone()
            await self.bot.async_db["Main"].AutoResetChannel.replace_one(
                {"Guild": interaction.guild.id, "Channel": ch.get("Channel")},
                {"Guild": interaction.guild.id, "Channel": ch_.id},
                upsert=True,
            )
            await asyncio.sleep(1)
            await ch.edit(position=channel.position + 1)
            await asyncio.sleep(1)
            await channel.delete()
            await ch.send(
                embed=discord.Embed(
                    title="チャンネルがリセットされました。", color=discord.Color.red()
                )
            )
        await interaction.followup.send(
            embed=discord.Embed(title="リセットしました。", color=discord.Color.green())
        )


async def setup(bot):
    await bot.add_cog(AutoResetCog(bot))
