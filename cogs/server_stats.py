from discord.ext import commands, tasks
import discord
import asyncio
from discord import app_commands

from models import make_embed


class ServerStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.batch_update_stat_channel.start()
        print("init -> ServerStats")

    async def get_messages(self, guild: discord.Guild):
        db = self.bot.async_db["MainTwo"].ServerStat
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            return False
        if not dbfind.get('Enabled'):
            return False
        message = dbfind.get('Message')
        return message
    
    async def get_now_messages(self, guild: discord.Guild):
        db = self.bot.async_db["MainTwo"].ServerStat
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            return False
        if not dbfind.get('Enabled'):
            return False
        message = dbfind.get('NowMessage')
        return message

    @tasks.loop(minutes=5)
    async def batch_update_stat_channel(self):
        db = self.bot.async_db["MainTwo"].ServerStatus
        async for db_find in db.find({}):
            guild = self.bot.get_guild(db_find.get("Guild", 0))
            if not guild:
                continue
            member_channel = db_find.get("Members", None)
            humans_channel = db_find.get("Humans", None)
            messages_channel = db_find.get("Messages", None)
            now_messages_channel = db_find.get("NowMessages", None)
            if member_channel:
                channel = guild.get_channel(member_channel)
                if channel:
                    if type(channel) != discord.VoiceChannel:
                        continue
                    new_name = f"メンバー数: {guild.member_count}人"
                    if channel.name != new_name:
                        await channel.edit(name=new_name)
            if humans_channel:
                channel = guild.get_channel(humans_channel)
                if channel:
                    if type(channel) != discord.VoiceChannel:
                        continue
                    new_name = f"人間数: {len(list(filter(lambda m: not m.bot, guild.members)))}人"
                    if channel.name != new_name:
                        await channel.edit(
                            name=new_name
                        )
            await asyncio.sleep(1)
            if messages_channel:
                channel = guild.get_channel(messages_channel)
                if channel:
                    if type(channel) != discord.VoiceChannel:
                        continue
                    msg = await self.get_messages(guild)
                    if msg:
                        new_name = f"メッセージ数: {msg}個"
                        if channel.name != new_name:
                            await channel.edit(
                                name=new_name
                            )
            if now_messages_channel:
                channel = guild.get_channel(now_messages_channel)
                if channel:
                    if type(channel) != discord.VoiceChannel:
                        continue
                    nmsg = await self.get_now_messages(guild)
                    if nmsg:
                        new_name = f"今日のメッセージ数: {nmsg}個"
                        if channel.name != new_name:
                            await channel.edit(
                                name=new_name
                            )

    server_status = app_commands.Group(
        name="server-status",
        description="サーバーのステータスを表示する設定をします。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @server_status.command(
        name="create",
        description="サーバーステータスを表示するチャンネルを作成します。",
    )
    @app_commands.choices(
        何を表示するか=[
            app_commands.Choice(name="メンバー数", value="members"),
            app_commands.Choice(name="人間数", value="humans"),
            app_commands.Choice(name="今までのメッセージ数", value="messages"),
            app_commands.Choice(name="今日のメッセージ数", value="now_messages"),
            app_commands.Choice(name="招待リンク", value="invite"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def status_create_category(
        self,
        interaction: discord.Interaction,
        カテゴリー: discord.CategoryChannel,
        何を表示するか: app_commands.Choice[str],
    ):
        await interaction.response.defer()
        db = self.bot.async_db["MainTwo"].ServerStatus
        if 何を表示するか.value == "members":
            ch = await カテゴリー.create_voice_channel(
                name=f"メンバー数: {interaction.guild.member_count}人"
            )
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id, "Members": ch.id}},
                upsert=True,
            )
        elif 何を表示するか.value == "humans":
            ch = await カテゴリー.create_voice_channel(
                name=f"人間数: {len(list(filter(lambda m: not m.bot, interaction.guild.members)))}人"
            )
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id, "Humans": ch.id}},
                upsert=True,
            )
        elif 何を表示するか.value == "messages":
            msg = await self.get_messages(interaction.guild)
            if not msg:
                return await interaction.followup.send(embed=make_embed.error_embed(title="統計情報の収集が無効化されています。", description="/settings stat setting で有効にして下さい。"))
            ch = await カテゴリー.create_voice_channel(
                name=f"メッセージ数: {msg}個"
            )
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id, "Messages": ch.id}},
                upsert=True,
            )
        elif 何を表示するか.value == "now_messages":
            nmsg = await self.get_now_messages(interaction.guild)
            if not nmsg:
                return await interaction.followup.send(embed=make_embed.error_embed(title="統計情報の収集が無効化されています。", description="/settings stat setting で有効にして下さい。"))
            ch = await カテゴリー.create_voice_channel(
                name=f"今日のメッセージ数: {nmsg}個"
            )
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id, "NowMessages": ch.id}},
                upsert=True,
            )
        elif 何を表示するか.value == "invite":
            inv = await interaction.channel.create_invite()
            await カテゴリー.create_voice_channel(name=inv.url)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ステータスチャンネルを作成しました。",
                description=f"{何を表示するか.name}を作成しました。",
            )
        )

    @server_status.command(
        name="disable", description="サーバーステータスを無効化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["MainTwo"].ServerStatus
        await db.delete_one({"Guild": interaction.guild.id})
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="すべてのステータスチャンネルを無効化しました。"
            )
        )


async def setup(bot):
    await bot.add_cog(ServerStats(bot))
