import asyncio
import traceback
from discord.ext import commands
import discord
import aiohttp
from discord import app_commands

from models import make_embed

# -----------------------------
# 地域ID → 地名変換テーブル
# 出典: P2PQuake Area Code List
# https://api.p2pquake.net/v2/area
# -----------------------------
AREA_ID_MAP = {
    10: "北海道地方",
    15: "東北地方北部",
    20: "東北地方南部",
    25: "関東地方北部",
    30: "関東地方南部",
    35: "中部地方北部",
    45: "中部地方南部",
    50: "近畿地方北部",
    55: "近畿地方南部",
    60: "中国地方北部",
    65: "中国地方南部",
    70: "四国地方",
    100: "福岡県",
    105: "佐賀県",
    110: "長崎県",
    115: "熊本県",
    120: "大分県",
    125: "宮崎県",
    130: "鹿児島県",
    135: "沖縄県",
    250: "東京都",
    270: "神奈川県",
    275: "埼玉県",
    280: "千葉県",
    300: "新潟県",
    310: "富山県",
    315: "石川県",
    320: "福井県",
    325: "山梨県",
    330: "長野県",
    335: "岐阜県",
    340: "静岡県",
    345: "愛知県",
    350: "三重県",
    400: "滋賀県",
    405: "京都府",
    410: "大阪府",
    415: "兵庫県",
    420: "奈良県",
    425: "和歌山県",
    460: "広島県",
    465: "山口県",
    475: "徳島県",
    480: "香川県",
    485: "愛媛県",
    490: "高知県",
    900: "不明地域",
}


# -----------------------------
# 各種変換クラス
# -----------------------------
class ChangeToView:
    def tsunami(self, warning):
        return {
            "Warning": "警報が発表されている地域があります",
            "Unknown": "不明",
            "None": "なし",
            "Checking": "調査中",
            "NonEffective": "若干の海面変動",
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
            -1: "[不明]",
        }.get(sindo, "[不明]")

    def depth(self, depth):
        return "ごく浅い" if str(depth) == "0" else str(depth)


class EEWCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.c = ChangeToView()

    eew = app_commands.Group(name="eew", description="地震系のコマンドです。")

    @eew.command(name="start", description="地震速報の受信を開始します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def eew_start(self, interaction: discord.Interaction):
        db = self.bot.async_db["MainTwo"].EEWAlert
        try:
            web = await interaction.channel.create_webhook(name="SharkBot-EEW")
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="Webhookを作成できませんでした。権限を確認してください。"
                ),
                ephemeral=True,
            )
            return

        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "WebHook": web.url,
                }
            },
            upsert=True,
        )

        await interaction.response.send_message(
            embed=make_embed.success_embed(title="地震速報の受信を開始しました。")
        )

    @eew.command(name="end", description="地震速報の受信を終了します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def eew_end(self, interaction: discord.Interaction):
        db = self.bot.async_db["MainTwo"].EEWAlert
        await db.delete_one({"Guild": interaction.guild.id})
        await interaction.response.send_message(
            embed=make_embed.success_embed(title="地震速報の受信を終了しました。")
        )

    @commands.Cog.listener("on_ready")
    async def on_ready_start_ws(self):
        asyncio.create_task(self.p2pquake_ws())

    async def p2pquake_ws(self):
        db = self.bot.async_db["MainTwo"].EEWAlert
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect("wss://api.p2pquake.net/v2/ws") as ws:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    o = msg.json()
                                    await self.handle_message(o, db, session)
                                except Exception:
                                    traceback.print_exc()
            except Exception:
                traceback.print_exc()
                await asyncio.sleep(5)

    async def handle_message(self, o, db, session):
        code = o.get("code")

        if code == 551:
            await self.handle_earthquake_info(o, db, session)

        elif code == 554:
            await self.handle_eew_alert(o, db, session)

        elif code == 555:
            await self.handle_sensed_report(o, db, session)

    async def handle_earthquake_info(self, o, db, session):
        eq = o.get("earthquake", {})
        msindo = self.c.shindo(eq.get("maxScale", -1))
        atime = eq.get("time")
        domesticTsunami = eq.get("domesticTsunami")
        depth = eq.get("hypocenter", {}).get("depth", -1)
        magnitude = eq.get("hypocenter", {}).get("magnitude", -1)
        hyposentername = eq.get("hypocenter", {}).get("name", "[不明]")

        tsunamiwarning = (
            "現在、津波警報が発表されています。"
            if domesticTsunami == "Warning"
            else "この地震による津波の心配はありません。"
        )

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
            color=discord.Color.yellow(),
        )
        embed.set_footer(text=f"id : {o.get('_id')}")

        async for channel in db.find({}):
            try:
                webhook_ = discord.Webhook.from_url(
                    channel.get("WebHook", None), session=session
                )
                await webhook_.send(embed=embed)
            except Exception:
                continue

    async def handle_eew_alert(self, o, db, session):
        embed = discord.Embed(
            title="緊急地震速報 - (警報)",
            description="緊急地震速報です。強い揺れに警戒して下さい。\n震度5弱以上の揺れが来るおそれがあります。\n落ち着いて、身の安全を確保してください。",
            color=discord.Color.red(),
        )
        embed.set_footer(text=f"id : {o.get('_id')}")

        async for channel in db.find({}):
            try:
                webhook_ = discord.Webhook.from_url(
                    channel.get("WebHook", None), session=session
                )
                await webhook_.send(embed=embed)
            except Exception:
                continue

    async def handle_sensed_report(self, o, db, session):
        areas = o.get("areas", [])
        if not areas:
            return

        sorted_areas = sorted(areas, key=lambda x: x.get("peer", 0), reverse=True)[:10]

        description = ""
        for a in sorted_areas:
            name = AREA_ID_MAP.get(a["id"], f"地域ID {a['id']}")
            description += f"・{name}：{a['peer']}人が揺れを感知\n"

        embed = discord.Embed(
            title="地震感知情報（体感報告）",
            description=f"ユーザーから揺れの報告が届いています。\n\n{description}",
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"id : {o.get('_id')}")

        async for channel in db.find({}):
            try:
                webhook_ = discord.Webhook.from_url(
                    channel.get("WebHook", None), session=session
                )
                await webhook_.send(embed=embed)
            except Exception:
                continue


async def setup(bot):
    await bot.add_cog(EEWCog(bot))
