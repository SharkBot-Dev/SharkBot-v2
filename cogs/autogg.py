from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
from discord import app_commands
import time
import aiohttp
from consts import settings
import asyncio

from models import make_embed, translate

class AutoGGCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoGGCog")

    @commands.Cog.listener("on_presence_update")
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.bot or not after.guild:
            return

        db = self.bot.async_db["MainTwo"].AutoGG
        settings = await db.find_one({"Guild": after.guild.id})
        
        if not settings or not settings.get("Enabled"):
            return

        old_game = discord.utils.find(lambda a: a.type == discord.ActivityType.playing, before.activities)

        is_now_playing = any(a.type == discord.ActivityType.playing for a in after.activities)

        if old_game and not is_now_playing:
            game_name = old_game.name
            webhook_url = settings.get("WebHook")
            
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    try:
                        webhook = discord.Webhook.from_url(webhook_url, session=session)

                        await webhook.send(
                            content=f"GG!", 
                            username=after.display_name, 
                            avatar_url=after.display_avatar.url,
                            embed=discord.Embed(title="プレイしていたゲーム", color=discord.Color.blue()).add_field(name="ゲーム名", value=game_name)
                        )
                    except (discord.NotFound, discord.Forbidden):
                        await db.update_one({"Guild": after.guild.id}, {"$set": {"Enabled": False}})

    autogg = app_commands.Group(name="autogg", description="ゲームをやめた際にggと送信します。")

    @autogg.command(name="setup", description="AutoGGのON/OFFを切り替え、現在のチャンネルに設定します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True, manage_channels=True, manage_webhooks=True)
    async def autogg_channel(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        db = self.bot.async_db["MainTwo"].AutoGG
        settings = await db.find_one({"Guild": interaction.guild.id})
        
        is_enabling = not (settings and settings.get("Enabled", False))

        if is_enabling:
            webhook = await interaction.channel.create_webhook(name="SharkBot-AutoGG")
            update_data = {
                "WebHook": webhook.url,
                "Enabled": True,
                "ChannelID": interaction.channel.id
            }
            msg = make_embed.success_embed(title="AutoGGを ON にしました。")
        else:
            update_data = {
                "Enabled": False
            }
            msg = make_embed.success_embed(title="AutoGGを OFF にしました。")

        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$set": update_data},
            upsert=True
        )

        await interaction.followup.send(embed=msg)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoGGCog(bot))
