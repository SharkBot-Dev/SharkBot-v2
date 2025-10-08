import asyncio
import traceback
from discord.ext import commands
import discord
import aiohttp
from discord import app_commands

from models import make_embed

class ChangeToView:
    def tsunami(self, warning):
        return {
            "Warning": "警報が発表されている地域があります",
            "Unknown": "不明",
            "None": "なし",
            "Checking": "調査中",
            "NonEffective": "若干の海面変動"
        }.get(warning, "情報のフォーマットに失敗。")

    def shindo(self, sindo):
        return {
            10: "1",
            20: "2",
            30: "3",
            40: "4",
            45: "5弱",
            50: "5強",
            55: "6弱",
            60: "6強",
            70: "7",
            -1: "[不明]"
        }.get(sindo, "[不明]")

    def icon(self, sindo):
        return {
            "5弱": "5m",
            "5強": "5p",
            "6弱": "6m",
            "6強": "6p"
        }.get(sindo, sindo)

    def depth(self, depth):
        return "ごく浅い" if str(depth) == "0" else str(depth)

class EEWCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    eew = app_commands.Group(name="eew", description="地震系のコマンドです。")

    @eew.command(name="start", description="地震速報の受信を開始します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def eew_start(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].EEWAlert

        web = await interaction.channel.create_webhook(name="SharkBot-EEW")

        await db.update_one({
            "Guild": interaction.guild.id
        }, {
            '$set': {
                "Guild": interaction.guild.id,
                "Channel": interaction.channel.id,
                "WebHook": web.url
            }
        })

        await interaction.response.send_message(embed=make_embed.success_embed(title="地震速報の受信を開始しました。"))

    @eew.command(name="end", description="地震速報の受信を終了します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def eew_end(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].EEWAlert

        await db.delete_one({"Guild": interaction.guild.id})

        await interaction.response.send_message(embed=make_embed.success_embed(title="地震速報の受信を終了しました。"))

    @commands.Cog.listener('on_ready')
    async def on_ready_start_ws(self):
        asyncio.create_task(self.p2pquake_ws())

    async def p2pquake_ws(self):
        c = ChangeToView()

        db = self.bot.async_db["Main"].EEWAlert

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('wss://api.p2pquake.net/v2/ws') as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        o = msg.json()

                        if o.get("code") == 551:
                            eq = o.get("earthquake", {})
                            msindo = c.shindo(eq.get("maxScale", -1))
                            atime = eq.get("time")
                            domesticTsunami = eq.get("domesticTsunami")
                            depth = eq.get("hypocenter", {}).get("depth", -1)
                            magnitude = eq.get("hypocenter", {}).get("magnitude", -1)
                            hyposentername = eq.get("hypocenter", {}).get("name", "[不明]")

                            tsunamiwarning = "現在、津波警報が発表されています。" if domesticTsunami == "Warning" else "この地震による津波の心配はありません。"

                            maxscaleplace = ""
                            for i in o.get("points", []):
                                if i.get("scale") == eq.get("maxScale"):
                                    maxscaleplace += f"**{i.get('addr')}**\n"

                            title = f"EarthQuakeInfo - 最大震度{msindo}"
                            placedescription = f"最大震度{msindo}を\n{maxscaleplace}で観測しています。"
                            if eq.get("maxScale", -1) == -1 and maxscaleplace == "":
                                title = "EarthQuakeInfo - 震源情報"
                                placedescription = ""

                            embed = discord.Embed(
                                title=title,
                                description=f"〈震源と大きさ〉\n{hyposentername} M{magnitude} 最大震度{msindo}\n・震源の深さ : {depth}km\n・発生時刻 : {atime}\n\n{placedescription}\n**{tsunamiwarning}**",
                                color=discord.Color.yellow()
                            )
                            embed.set_footer(text=f"id : {o.get('_id')}")

                            channels = db.find({})

                            async for channel in channels:

                                try:

                                    webhook_ = discord.Webhook.from_url(channel.get('WebHook', None), session=session)

                                    await webhook_.send(embed=embed)
                                except:
                                    continue

                        elif o.get("code") == 554:
                            embed = discord.Embed(
                                title="緊急地震速報 - (警報)",
                                description="緊急地震速報です。強い揺れに警戒して下さい。\n緊急地震速報が発令された地域では、震度5弱以上の揺れが来るかもしれません。\n落ち着いて、身の安全を図ってください。",
                                color=discord.Color.red()
                            )
                            embed.set_footer(text=f"id : {o.get('_id')}")

                            channels = db.find({})

                            async for channel in channels:

                                try:

                                    webhook_ = discord.Webhook.from_url(channel.get('WebHook', None), session=session)

                                    await webhook_.send(embed=embed)
                                except:
                                    continue

async def setup(bot):
    await bot.add_cog(EEWCog(bot))
