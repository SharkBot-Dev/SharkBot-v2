from datetime import datetime, timedelta
import asyncio
import time
import discord
from discord.ext import commands, tasks

from discord import app_commands

cooldown_eventalert = {}

class AlertCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_mention(self, guild: discord.Guild, channel_id: int):
        db = self.bot.async_db["Main"].AlertMention
        try:
            dbfind = await db.find_one({"Channel": channel_id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return guild.get_role(dbfind.get("Role")).mention

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
                await ch.send(embed=discord.Embed(title="イベントが作成されました！", description=f"{event.name}", color=discord.Color.green())
                          .add_field(name="開始時刻", value=f"{event.start_time.strftime('%Y年%m月%d日 %H時%M分%S秒')}").set_footer(text=f"{event.guild.name} / {event.guild.id}", icon_url=event.guild.icon.url if event.guild.icon else self.bot.user.avatar.url), view=view)
                return
            await ch.send(content=men, embed=discord.Embed(title="イベントが作成されました！", description=f"{event.name}", color=discord.Color.green())
                          .add_field(name="開始時刻", value=f"{event.start_time.strftime('%Y年%m月%d日 %H時%M分%S秒')}").set_footer(text=f"{event.guild.name} / {event.guild.id}", icon_url=event.guild.icon.url if event.guild.icon else self.bot.user.avatar.url), view=view)
        except:
            return
        
    alert = app_commands.Group(name="alert", description="様々な通知を設定するコマンドです。")

    @alert.command(name="event", description="イベントを通知するチャンネルを設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def alert_event(self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None):
        db = self.bot.async_db["Main"].EventAlert
        if  チャンネル:
            await db.replace_one(
                {"Guild": interaction.guild.id}, 
                {"Guild": interaction.guild.id, "Channel": チャンネル.id}, 
                upsert=True
            )
            await interaction.response.send_message(embed=discord.Embed(title="イベント作成時に通知するチャンネルを設定しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await db.delete_one(
                {"Guild": interaction.guild.id}
            )
            await interaction.response.send_message(embed=discord.Embed(title="イベント作成時に通知するチャンネルを削除しました。", color=discord.Color.red()), ephemeral=True)

    @alert.command(name="mention", description="アラート時にメンションするロールを設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def alert_mention(self, interaction: discord.Interaction, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].AlertMention
        if  ロール:
            await db.replace_one(
                {"Channel": interaction.channel.id}, 
                {"Channel": interaction.channel.id, "Role": ロール.id}, 
                upsert=True
            )
            await interaction.response.send_message(embed=discord.Embed(title="アラート時にメンションするようにしました。", description=f"{ロール.mention}", color=discord.Color.green()), ephemeral=True)
        else:
            await db.delete_one(
                {"Channel": interaction.channel.id}
            )
            await interaction.response.send_message(embed=discord.Embed(title="アラート時にメンションしなくしました。", color=discord.Color.red()), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AlertCog(bot))