import datetime
from discord.ext import commands, tasks
import discord
import asyncio
from discord import app_commands
from consts import mongodb
from models import make_embed


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
                await db.update_one(
                    {"Guild": ch_.guild.id, "Channel": ch_.id},
                    {'$set': {"Guild": ch_.guild.id, "Channel": ch_.id}},
                    upsert=True,
                )
                await asyncio.sleep(1)
                await ch_.edit(position=ch.position + 1)
                await asyncio.sleep(1)
                await ch.delete()
                await ch_.send(
                    embed=make_embed.success_embed(
                        title="チャンネルがリセットされました。"
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

    @commands.Cog.listener()
    async def on_auto_reset_event(
        self,
        guild_id: int,
        channel_id: int,
        hour: int
    ):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        
        db = self.bot.async_db["MainTwo"].AutoResetChannelBeta

        exists = await db.find_one(
            {"Guild": guild_id, "Channel": channel_id, "Reminder": hour}
        )
        if not exists:
            return

        new_ch = await channel.clone(reason="Auto reset")
        await new_ch.edit(position=channel.position + 1)
        await channel.delete(reason="Auto reset")

        await new_ch.send(
            embed=make_embed.success_embed(
                title="チャンネルがリセットされました。",
                description="これは定期リセットです。"
            )
        )

        await db.update_one(
            {"Guild": guild.id, "Channel": channel_id},
            {"$set": {"Guild": guild.id, "Channel": new_ch.id, "Reminder": hour}},
        )

        await self.bot.loop_create(
            datetime.timedelta(minutes=hour),
            "auto_reset_event",
            guild_id,
            channel_id,
            hour
        )

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
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel, 何時間間隔か: int = 3
    ):
        await interaction.response.defer()
        if 何時間間隔か < 1:
            return await interaction.followup.send(embed=make_embed.error_embed(title="時間指定は1以上でお願いします。"))

        db = self.bot.async_db["MainTwo"].AutoResetChannelBeta
        await db.update_one(
            {"Guild": interaction.guild.id, "Channel": チャンネル.id},
            {'$set': {"Guild": interaction.guild.id, "Channel": チャンネル.id, "Reminder": 何時間間隔か}},
            upsert=True,
        )
        await interaction.client.loop_create(
            datetime.timedelta(hours=何時間間隔か),
            "auto_reset_event",
            interaction.guild.id,
            チャンネル.id,
            何時間間隔か
        )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"チャンネルの自動リセットを{何時間間隔か}時間ごとに設定しました。"
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

        db = self.bot.async_db["MainTwo"].AutoResetChannelBeta
        await db.delete_one({"Guild": interaction.guild.id, "Channel": チャンネル.id})

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="自動リセットを無効化しました。"
            )
        )

async def setup(bot):
    await bot.add_cog(AutoResetCog(bot))
