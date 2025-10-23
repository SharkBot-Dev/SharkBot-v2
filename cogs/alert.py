import time
import discord
from discord.ext import commands, tasks

from discord import app_commands

import aiohttp
from bs4 import BeautifulSoup
import ssl

from models import make_embed

cooldown_eventalert = {}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class AlertCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_news_alert.start()

    async def get_mention(self, guild: discord.Guild, channel_id: int):
        db = self.bot.async_db["Main"].AlertMention
        try:
            dbfind = await db.find_one({"Channel": channel_id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return guild.get_role(dbfind.get("Role")).mention

    @tasks.loop(hours=3)
    async def check_news_alert(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://mainichi.jp/", ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                title = soup.find_all("div", class_="toppickup")[0]
                url = title.find_all("a")[0]

                news_db = self.bot.async_db["Main"].NewsAlert
                async for n in news_db.find({}):
                    guild= self.bot.get_guild(n.get('Guild', 0))
                    if guild:
                        channel = guild.get_channel(n.get('Channel', 0))
                        if channel:
                            mention = await self.get_mention(guild, channel.id)
                            mention = mention if mention else ""
                            await channel.send(f"{mention}\nhttps:{url['href']}")

    async def cog_unload(self):
        self.check_news_alert.stop()

    @commands.Cog.listener("on_scheduled_event_create")
    async def on_scheduled_event_create_alert(self, event: discord.ScheduledEvent):
        db = self.bot.async_db["Main"].EventAlert
        try:
            dbfind = await db.find_one({"Guild": event.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_eventalert.get(event.guild.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_eventalert[event.guild.id] = current_time
        try:
            ch = await event.guild.fetch_channel(dbfind.get("Channel"))
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="確認する", url=event.url))
            men = await self.get_mention(event.guild, ch.id)
            if not men:
                await ch.send(
                    embed=discord.Embed(
                        title="イベントが作成されました！",
                        description=f"{event.name}",
                        color=discord.Color.green(),
                    )
                    .add_field(
                        name="開始時刻",
                        value=f"{event.start_time.strftime('%Y年%m月%d日 %H時%M分%S秒')}",
                    )
                    .set_footer(
                        text=f"{event.guild.name} / {event.guild.id}",
                        icon_url=event.guild.icon.url
                        if event.guild.icon
                        else self.bot.user.avatar.url,
                    ),
                    view=view,
                )
                return
            await ch.send(
                content=men,
                embed=discord.Embed(
                    title="イベントが作成されました！",
                    description=f"{event.name}",
                    color=discord.Color.green(),
                )
                .add_field(
                    name="開始時刻",
                    value=f"{event.start_time.strftime('%Y年%m月%d日 %H時%M分%S秒')}",
                )
                .set_footer(
                    text=f"{event.guild.name} / {event.guild.id}",
                    icon_url=event.guild.icon.url
                    if event.guild.icon
                    else self.bot.user.avatar.url,
                ),
                view=view,
            )
        except:
            return

    alert = app_commands.Group(
        name="alert", description="様々な通知を設定するコマンドです。"
    )

    @alert.command(
        name="event", description="イベントを通知するチャンネルを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def alert_event(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None
    ):
        db = self.bot.async_db["Main"].EventAlert
        if チャンネル:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id, "Channel": チャンネル.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="イベント作成時に通知するチャンネルを設定しました。",
                    description="`/alert event`で、チャンネルを指定しなければ無効化できます。"
                ),
                ephemeral=True,
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="イベント作成時に通知するチャンネルを削除しました。"
                ),
                ephemeral=True,
            )

    @alert.command(
        name="news", description="ニュースを通知するチャンネルを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def alert_news(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None
    ):
        db = self.bot.async_db["Main"].NewsAlert
        if チャンネル:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {'$set': {"Guild": interaction.guild.id, "Channel": チャンネル.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="ニュースを通知するチャンネルを設定しました。",
                    description="`/alert news`で、チャンネルを指定しなければ無効化できます。"
                ),
                ephemeral=True,
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="ニュースを通知するチャンネルを削除しました。"
                ),
                ephemeral=True,
            )

    @alert.command(
        name="mention", description="アラート時にメンションするロールを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def alert_mention(
        self, interaction: discord.Interaction, ロール: discord.Role = None
    ):
        db = self.bot.async_db["Main"].AlertMention
        if ロール:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"Channel": interaction.channel.id, "Role": ロール.id},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="アラート時にメンションするようにしました。",
                    description=f"{ロール.mention}"
                ),
                ephemeral=True,
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="アラート時にメンションしなくしました。"
                ),
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(AlertCog(bot))
