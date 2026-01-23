import datetime
import re
import time
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

# import TagScriptEngine as tse
from consts import badword
import io

from models import make_embed


class TimerSetModal(discord.ui.Modal):
    def __init__(self, time: int):
        super().__init__(title="タイマーをセットする", timeout=180)
        self.time = time

    text = discord.ui.TextInput(
        label="投稿するメッセージ",
        placeholder="こんにちは！これはタイマーのメッセージです！",
        style=discord.TextStyle.long,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        channel: discord.TextChannel = interaction.channel
        webhooks = await channel.webhooks()

        webhook = None
        for wh in webhooks:
            if wh.name == "SharkBot-Timer":
                webhook = wh
                break

        if webhook is None:
            webhook = await channel.create_webhook(name="SharkBot-Timer")

        doc = {
            "guild_id": interaction.guild_id,
            "channel_id": interaction.channel_id,
            "message": self.text.value,
            "interval": self.time,
            "webhook_url": webhook.url,
        }

        await interaction.client.async_db["MainTwo"].ServerTimer.update_one(
            {"guild_id": interaction.guild.id, "channel_id": interaction.channel_id},
            {"$set": doc},
            upsert=True,
        )

        await interaction.client.loop_create(
            datetime.timedelta(minutes=self.time),
            "timer_event",
            interaction.guild.id,
            interaction.channel_id,
            webhook.url,
            self.text.value,
            self.time,
        )

        embed = make_embed.success_embed(
            title="定期的に投稿するメッセージを設定しました。",
            description=f"{self.time}分ごとに送信します。",
        )

        await interaction.followup.send(embed=embed)


class TimerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> TimerCog")

    timer = app_commands.Group(
        name="timer",
        description="定期的に投稿するメッセージを設定します。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @timer.command(name="create", description="タイマーを作成します。")
    @app_commands.checks.has_permissions(manage_channels=True, manage_webhooks=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def timer_create(self, interaction: discord.Interaction, 間隔_分: int):
        count = await interaction.client.async_db[
            "MainTwo"
        ].ServerTimer.count_documents({"guild_id": interaction.guild_id})
        if count >= 3:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="タイマーは3個までしか作成できません！",
                    description="先にいらないタイマーを削除してから実行してください！",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )

        if 間隔_分 < 3:
            embed = discord.Embed(
                title="時間の指定が正しくありません。",
                description="3分以上にしてください。",
                color=discord.Color.red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_modal(TimerSetModal(間隔_分))

    @timer.command(name="delete", description="タイマーを削除します。")
    @app_commands.checks.has_permissions(manage_channels=True, manage_webhooks=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def timer_create(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].ServerTimer

        doc = await db.find_one(
            {"guild_id": interaction.guild_id, "channel_id": interaction.channel_id}
        )

        if not doc:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="このチャンネルにはタイマーはありません！"
                ),
                ephemeral=True,
            )

        await db.delete_one({"_id": doc["_id"]})

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="タイマーを削除しました。", description="このチャンネルのタイマーが削除されました。"
            ),
            ephemeral=True,
        )

    @timer.command(name="list", description="タイマーの一覧を表示します。")
    @app_commands.checks.has_permissions(manage_channels=True, manage_webhooks=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def timer_list(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].ServerTimer

        docs = db.find({"guild_id": interaction.guild_id})

        embed = make_embed.success_embed(title="定期投稿一覧")
        count = 0

        async for doc in docs:
            count += 1
            interval = doc.get("interval")
            message = doc.get("message")
            channel_id = doc.get("channel_id")
            embed.add_field(
                name=f"{count}. チャンネル: <#{channel_id}> / {interval}分間隔",
                value=f"メッセージ: {message}",
                inline=False,
            )

        if count == 0:
            embed.description = "このサーバーには定期投稿はありません。"

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_timer_event(
        self,
        guild_id: int,
        channel_id: int,
        webhook_url: str,
        message: str,
        interval: int,
    ):
        exists = await self.bot.async_db["MainTwo"].ServerTimer.find_one(
            {"guild_id": guild_id, "channel_id": channel_id, "message": message}
        )
        if not exists:
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json={
                    "content": message,
                    "username": "SharkBot Timer",
                    "avatar_url": self.bot.user.avatar.url,
                },
            ):
                pass

        await self.bot.loop_create(
            datetime.timedelta(minutes=interval),
            "timer_event",
            guild_id,
            channel_id,
            webhook_url,
            message,
            interval,
        )


async def setup(bot):
    await bot.add_cog(TimerCog(bot))
