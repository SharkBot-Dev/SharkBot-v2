from discord.ext import commands
import discord
from discord import app_commands

import asyncio


class BulkChannelGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="channel", description="チャンネル系のコマンドです。")

    @app_commands.command(
        name="delete", description="同じ名前のチャンネルを削除します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bulk_channel_delete(
        self, interaction: discord.Interaction, チャンネル名: str
    ):
        await interaction.response.defer()

        c = 0

        for ch in interaction.guild.channels:
            if ch.name == チャンネル名:
                try:
                    await ch.delete()
                except:
                    continue
                c += 1
                await asyncio.sleep(0.5)

        await interaction.followup.send(
            embed=discord.Embed(
                title="同じ名前のチャンネルを一括削除しました。",
                description=f"{c}個チャンネルを削除しました。",
                color=discord.Color.green(),
            )
        )


class BulkRoleGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="role", description="ロール系のコマンドです。")

    @app_commands.command(name="delete", description="同じ名前のロールを削除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bulk_role_delete(
        self, interaction: discord.Interaction, ロール名: discord.Role
    ):
        await interaction.response.defer()

        c = 0
        f = 0

        for ch in interaction.guild.roles:
            if ch.name == ロール名.name:
                try:
                    await ch.delete()
                except:
                    f += 1
                    await asyncio.sleep(0.5)
                    continue
                c += 1
                await asyncio.sleep(0.5)

        await interaction.followup.send(
            embed=discord.Embed(
                title="同じ名前のロールを一括削除しました。",
                description=f"{c}個ロールを削除しました。\n{f}個削除できませんでした。",
                color=discord.Color.green(),
            )
        )


class BulkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> BulkCog")

    bulk = app_commands.Group(name="bulk", description="様々な物事を一斉にこなします。")

    bulk.add_command(BulkChannelGroup())
    bulk.add_command(BulkRoleGroup())


async def setup(bot):
    await bot.add_cog(BulkCog(bot))
