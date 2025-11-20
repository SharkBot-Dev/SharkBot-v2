import datetime
from discord.ext import commands, tasks
import discord
import aiohttp
from discord import Webhook
import asyncio
from discord import app_commands

from models import make_embed

class ServerStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.batch_update_stat_channel.start()
        print("init -> ServerStats")

    @tasks.loop(minutes=5)
    async def batch_update_stat_channel(self):
        db = self.bot.async_db["MainTwo"].ServerStatus
        async for db_find in db.find({}):
            guild = self.bot.get_guild(db_find.get('Guild', 0))
            if not guild:
                continue
            member_channel = db_find.get('Members', None)
            humans_channel = db_find.get('Humans', None)
            if member_channel:
                channel = guild.get_channel(member_channel)
                if channel:
                    if type(channel) != discord.VoiceChannel:
                        continue
                    await channel.edit(name=f"メンバー数: {guild.member_count}人")
            if humans_channel:
                channel = guild.get_channel(humans_channel)
                if channel:
                    if type(channel) != discord.VoiceChannel:
                        continue
                    await channel.edit(name=f"人間数: {len(list(filter(lambda m: not m.bot, guild.members)))}人")
            await asyncio.sleep(1)

    server_status = app_commands.Group(
        name="server-status", description="サーバーのステータスを表示する設定をします。"
    )

    @server_status.command(
        name="create", description="サーバーステータスを表示するチャンネルを作成します。"
    )
    @app_commands.choices(
        何を表示するか=[
            app_commands.Choice(name="メンバー数", value="members"),
            app_commands.Choice(name="人間数", value="humans"),
            app_commands.Choice(name="招待リンク", value="invite"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def status_create_category(
        self, interaction: discord.Interaction, カテゴリー: discord.CategoryChannel, 何を表示するか: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        db = self.bot.async_db["MainTwo"].ServerStatus
        if 何を表示するか.value == "members":
            ch = await カテゴリー.create_voice_channel(name=f"メンバー数: {interaction.guild.member_count}人")
            await db.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id, "Members": ch.id}},
                upsert=True,
            )
        elif 何を表示するか.value == "humans":
            ch = await カテゴリー.create_voice_channel(name=f"人間数: {len(list(filter(lambda m: not m.bot, interaction.guild.members)))}人")
            await db.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id, "Humans": ch.id}},
                upsert=True,
            )
        elif 何を表示するか.value == "invite":
            inv = await interaction.channel.create_invite()
            await カテゴリー.create_voice_channel(name=inv.url)
        await interaction.followup.send(embed=make_embed.success_embed(title="ステータスチャンネルを作成しました。", description=f"{何を表示するか.name}を作成しました。"))

    @server_status.command(
        name="disable", description="サーバーステータスを無効化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_status(
        self, interaction: discord.Interaction
    ):
        await interaction.response.defer()
        db = self.bot.async_db["MainTwo"].ServerStatus
        await db.delete_one({"Guild": interaction.guild.id})
        await interaction.followup.send(embed=make_embed.success_embed(title="すべてのステータスチャンネルを無効化しました。"))

async def setup(bot):
    await bot.add_cog(ServerStats(bot))
