import asyncio
from functools import partial
import io
import re
import socket
import textwrap
import time
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands
import discord

import uuid
import aiofiles.os

from html2image import Html2Image
import pyshorteners
from discord import app_commands
from consts import badword
from models import command_disable
import ipaddress
import socket
from urllib.parse import urlparse
import os
import yt_dlp

SOUNDCLOUD_REGEX = re.compile(
    r'^(https?://)?(www\.)?(soundcloud\.com|on\.soundcloud\.com)/.+'
)

IRASUTOTA_REGEX = re.compile(r'https://www\.irasutoya\.com/.+/.+/.+\.html')

ipv4_pattern = re.compile(
    r"^("
    r"(25[0-5]|"  # 250-255
    r"2[0-4][0-9]|"  # 200-249
    r"1[0-9]{2}|"  # 100-199
    r"[1-9][0-9]|"  # 10-99
    r"[0-9])"  # 0-9
    r"\.){3}"  # 繰り返し: 3回ドット付き
    r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])"  # 最後のオクテット
    r"$"
)

domain_regex = re.compile(r"^(?!\-)(?:[a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$")

is_url = re.compile(r"https?://[\w!\?/\+\-_~=;\.,\*&@#$%\(\)'\[\]]+")


def is_blocked_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return True

        if host in ("localhost",):
            return True

        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                return True
        except ValueError:
            try:
                resolved_ip = socket.gethostbyname(host)
                ip = ipaddress.ip_address(resolved_ip)
                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_reserved
                    or ip.is_link_local
                ):
                    return True
            except Exception:
                return True

        return False
    except Exception:
        return True


async def fetch_whois(target_domain):
    if not domain_regex.match(target_domain):
        return io.StringIO("Whoisに失敗しました。")

    def whois_query(domain: str, server="whois.iana.org") -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server, 43))
            s.sendall((domain + "\r\n").encode())
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
            return response.decode(errors="ignore")

    loop = asyncio.get_running_loop()
    res = await loop.run_in_executor(None, partial(whois_query, target_domain))
    return io.StringIO(res)


class EmbedMake(discord.ui.Modal, title="埋め込みを作成"):
    title_ = discord.ui.TextInput(
        label="タイトル",
        placeholder="タイトル！",
        style=discord.TextStyle.short,
    )

    desc = discord.ui.TextInput(
        label="説明",
        placeholder="説明！",
        style=discord.TextStyle.long,
    )

    color = discord.ui.TextInput(
        label="色",
        placeholder="#000000",
        style=discord.TextStyle.short,
        default="#000000",
    )

    button_label = discord.ui.TextInput(
        label="ボタンラベル",
        placeholder="Webサイト",
        style=discord.TextStyle.short,
        required=False,
    )

    button = discord.ui.TextInput(
        label="ボタンurl",
        placeholder="https://www.sharkbot.xyz/",
        style=discord.TextStyle.short,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            view = discord.ui.View()
            if self.button.value:
                if self.button_label.value:
                    view.add_item(
                        discord.ui.Button(
                            label=self.button_label.value, url=self.button.value
                        )
                    )
                else:
                    view.add_item(
                        discord.ui.Button(label="Webサイト", url=self.button.value)
                    )
            await interaction.channel.send(
                embed=discord.Embed(
                    title=self.title_.value,
                    description=self.desc.value,
                    color=discord.Color.from_str(self.color.value),
                )
                .set_author(
                    name=f"{interaction.user.name}",
                    icon_url=interaction.user.avatar.url
                    if interaction.user.avatar
                    else interaction.user.default_avatar.url,
                )
                .set_footer(
                    text=f"{interaction.guild.name} | {interaction.guild.id}",
                    icon_url=interaction.guild.icon.url
                    if interaction.guild.icon
                    else interaction.user.default_avatar.url,
                ),
                view=view,
            )
        except Exception as e:
            return await interaction.followup.send(
                "作成に失敗しました。",
                ephemeral=True,
                embed=discord.Embed(
                    title="エラー内容",
                    description=f"```{e}```",
                    color=discord.Color.red(),
                ),
            )


cooldown_afk = {}


class ToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ToolsCog")

    async def afk_mention_get(self, user: discord.User):
        try:
            database = self.bot.async_db["Main"].AFKMention
            m = [
                f"{self.bot.get_channel(b.get('Channel', 0)).mention if self.bot.get_channel(b.get('Channel', 0)) else b.get('Channel', 0)} - {self.bot.get_user(b.get('MentionUser')) if self.bot.get_user(b.get('MentionUser')) else b.get('MentionUser')}"
                async for b in database.find({"User": user.id})
            ]
            await database.delete_many(
                {
                    "User": user.id,
                }
            )
            return "\n".join(m)
        except Exception as e:
            return f"取得失敗！\n{e}"

    @commands.Cog.listener("on_message")
    async def on_message_afk(self, message: discord.Message):
        if message.author.bot:
            return
        db = self.bot.async_db["Main"].AFK
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        mens = await self.afk_mention_get(message.author)
        if mens == "":
            mens = "メンションなし"
        try:
            await message.reply(
                embed=discord.Embed(
                    title="AFKを解除しました。",
                    description=f"{dbfind['Reason']}",
                    color=discord.Color.green(),
                )
                .add_field(
                    name="今から何する？",
                    value=dbfind.get("End", "まだ予定がありません。"),
                    inline=False,
                )
                .add_field(name="メンション一覧", value=mens, inline=False)
            )
        except:
            pass
        await db.delete_one(
            {
                "User": message.author.id,
            }
        )

    @commands.Cog.listener("on_message")
    async def on_message_afk_mention(self, message):
        if message.author.bot:
            return
        if message.mentions:
            mentioned_users = [user.id for user in message.mentions]
            for m in mentioned_users:
                db = self.bot.async_db["Main"].AFK
                try:
                    dbfind = await db.find_one({"User": m}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                current_time = time.time()
                last_message_time = cooldown_afk.get(message.author.id, 0)
                if current_time - last_message_time < 5:
                    return
                cooldown_afk[message.author.id] = current_time
                await self.afk_mention_write(m, message)
                await message.reply(
                    embed=discord.Embed(
                        title="その人はAFKです。",
                        description=f"理由: {dbfind['Reason']}",
                        color=discord.Color.red(),
                    ).set_footer(text="このメッセージを5秒後に削除されます。"),
                    delete_after=5,
                )
                return

    tools = app_commands.Group(name="tools", description="ツール系のコマンドです。")

    @tools.command(name="embed", description="埋め込みを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tools_embed(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )
        await interaction.response.send_modal(EmbedMake())

    @tools.command(name="button", description="ボタンを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tools_button(
        self, interaction: discord.Interaction, ラベル: str, url: str
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        for b in badword.badwords:
            if b in ラベル:
                return await interaction.response.send_message(
                    ephemeral=True, content="不適切なワードが含まれています。"
                )

        if not is_url.search(url):
            return await interaction.response.send_message(
                ephemeral=True, content="URLを入力してください。"
            )

        await interaction.response.send_message(
            view=discord.ui.View().add_item(discord.ui.Button(label=ラベル, url=url))
        )

    @tools.command(name="invite", description="招待リンクを作成します。")
    @app_commands.checks.has_permissions(create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def invite(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if not interaction.guild.vanity_url:
            inv = await interaction.channel.create_invite()
            inv = inv.url
        else:
            inv = interaction.guild.vanity_url
        await interaction.response.send_message(
            f"サーバー名: {interaction.guild.name}\nサーバーの人数: {interaction.guild.member_count}\n招待リンク: {inv}"
        )

    @tools.command(name="uuid", description="uuidを作成します。")
    @app_commands.checks.has_permissions(create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def uuid(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.uuidtools.com/api/generate/v1"
            ) as response:
                jso = await response.json()
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="UUID生成",
                        description=f"{jso[0]}",
                        color=discord.Color.green(),
                    )
                )

    @tools.command(name="short", description="短縮urlを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ドメイン=[
            app_commands.Choice(name="tinyurl.com", value="tiny"),
            app_commands.Choice(name="urlc.net", value="urlc"),
            app_commands.Choice(name="oooooo.ooo", value="ooo"),
        ]
    )
    async def short_url(
        self,
        interaction: discord.Interaction,
        ドメイン: app_commands.Choice[str],
        url: str,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)
        if ドメイン.value == "tiny":
            loop = asyncio.get_running_loop()
            s = await loop.run_in_executor(None, partial(pyshorteners.Shortener))
            url_ = await loop.run_in_executor(None, partial(s.tinyurl.short, url))
        elif ドメイン.value == "urlc":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://urlc.net/", params={"url": url, "keyword": ""}
                ) as response:
                    soup = BeautifulSoup(await response.text(), "html.parser")
                    url_ = soup.find(
                        {"button": {"class": "short-url-button noselect"}}
                    )["data-clipboard-text"]
        elif ドメイン.value == "ooo":

            class OOO:
                enc = ["o", "ο", "о", "ᴏ"]
                curr_ver = "oooo"

                def encode_url(self, url: str) -> str:
                    utf8_bytes = url.encode("utf-8")
                    base4_digits = "".join(
                        format(byte, "04b").zfill(8) for byte in utf8_bytes
                    )

                    b4str = ""
                    for i in range(0, len(base4_digits), 2):
                        b4str += str(int(base4_digits[i : i + 2], 2))

                    oooified = "".join(self.enc[int(d)] for d in b4str)
                    return self.curr_ver + oooified

            url_ = "https://ooooooooooooooooooooooo.ooo/" + OOO().encode_url(url)
        await interaction.followup.send(
            embed=discord.Embed(
                title="短縮されたurl",
                description=f"{url_}",
                color=discord.Color.green(),
            ),
            ephemeral=True,
        )

    @tools.command(name="whois", description="Whoisします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def whois(self, interaction: discord.Interaction, ドメイン: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        data = await fetch_whois(ドメイン)
        return await interaction.followup.send(file=discord.File(data, "whois.txt"))

    @tools.command(name="nslookup", description="DNS情報を見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def nslookup(self, interaction: discord.Interaction, ドメイン: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        l = []
        domain = ドメイン
        json_data = {
            "domain": domain,
            "dnsServer": "cloudflare",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.nslookup.io/api/v1/records", json=json_data
            ) as response:
                js = await response.json()
                records_data = js.get("records", {})
                categorized_records = {}

                for record_type, record_info in records_data.items():
                    response = record_info.get("response", {})
                    answers = response.get("answer", [])

                    for answer in answers:
                        record_details = answer.get("record", {})
                        ip_info = answer.get("ipInfo", {})

                        record_entry = f"{record_details.get('raw', 'N/A')}"

                        if record_type not in categorized_records:
                            categorized_records[record_type] = []
                        categorized_records[record_type].append(record_entry)

                embed = discord.Embed(
                    title="NSLookup DNS情報", color=discord.Color.blue()
                )

                for record_type, entries in categorized_records.items():
                    value_text = "\n".join(entries)
                    embed.add_field(
                        name=record_type.upper(), value=value_text[:1024], inline=False
                    )

                await interaction.followup.send(embed=embed)

    @tools.command(name="iplookup", description="IP情報を見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def iplookup(self, interaction: discord.Interaction, ipアドレス: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if ipv4_pattern.match(ipアドレス):
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://ip-api.com/json/{ipアドレス}?lang=ja"
                ) as response:
                    try:
                        js = await response.json()
                        await interaction.response.send_message(
                            embed=discord.Embed(
                                title=f"IPアドレス情報 ({ipアドレス})",
                                description=f"""
    国名: {js.get("country", "不明")}
    都市名: {js.get("city", "不明")}
    プロバイダ: {js.get("isp", "不明")}
    緯度: {js.get("lat", "不明")}
    経度: {js.get("lon", "不明")}
    タイムゾーン: {js.get("timezone", "不明")}
    """,
                                color=discord.Color.green(),
                            )
                        )
                    except:
                        return await interaction.response.send_message(
                            embed=discord.Embed(
                                title="APIのレートリミットです。",
                                color=discord.Color.red(),
                            )
                        )
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="無効なIPアドレスです。", color=discord.Color.red()
                )
            )

    @tools.command(name="afk", description="AFKを設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def afk(
        self,
        interaction: discord.Interaction,
        理由: str,
        終わったらやること: str = "まだ予定がありません。",
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        database = self.bot.async_db["Main"].AFK
        await database.replace_one(
            {"User": interaction.user.id},
            {"User": interaction.user.id, "Reason": 理由, "End": 終わったらやること},
            upsert=True,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="AFKを設定しました。",
                description=f"{理由}",
                color=discord.Color.green(),
            )
        )

    @tools.command(name="timer", description="タイマーをセットします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def timer(self, interaction: discord.Interaction, 秒数: int):
        if 秒数 > 600:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="10分以上は計れません。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        db = self.bot.async_db["Main"].AlertQueue
        try:
            dbfind = await db.find_one(
                {"ID": f"timer_{interaction.user.id}"}, {"_id": False}
            )
        except:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="タイマーはすでにセットされています。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        if not dbfind is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="タイマーはすでにセットされています。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        await self.bot.alert_add(
            f"timer_{interaction.user.id}",
            interaction.channel.id,
            f"{interaction.user.mention}",
            f"{秒数}秒が経ちました。",
            "タイマーがストップされました。",
            秒数,
        )
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="タイマーをセットしました。",
                description=f"{秒数}秒です。",
                color=discord.Color.green(),
            )
        )

    @tools.command(name="qr", description="qrコードを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def qrcode_make(self, interaction: discord.Interaction, url: str):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="QRコード作成", color=discord.Color.green()
            ).set_image(
                url=f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={url}"
            )
        )

    @tools.command(name="weather", description="天気を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        場所=[
            app_commands.Choice(name="東京", value="130000"),
            app_commands.Choice(name="大阪", value="270000"),
        ]
    )
    async def weather(
        self, interaction: discord.Interaction, 場所: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{場所.value}.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                ts = data[0]["timeSeries"][0]
                time_defs = ts["timeDefines"]
                area = ts["areas"][0]
                weathers = area["weathers"]

                weather_info = []
                for dt, w in zip(time_defs, weathers):
                    weather_info.append((dt, w))

                embed = discord.Embed(
                    title=f"天気予報 ({場所.name})",
                    description="気象庁データを元にしています",
                    color=discord.Color.blue(),
                )

                for dt, w in weather_info:
                    embed.add_field(name=dt, value=w, inline=False)

                await interaction.followup.send(embed=embed)

    @tools.command(name="webshot", description="スクリーンショットを撮影します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def webshot(self, interaction: discord.Interaction, url: str):
        if not is_url.search(url):
            return await interaction.response.send_message(
                ephemeral=True, content="URLを入力してください。"
            )

        if await asyncio.to_thread(is_blocked_url, url):
            return await interaction.response.send_message(
                ephemeral=True, content="有効なURLを入力してください。"
            )

        await interaction.response.defer()

        hti = Html2Image(
            output_path=f"files/static/{interaction.user.id}/",
            custom_flags=[
                "--proxy-server=socks5://127.0.0.1:9050",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--headless=new",
                "--mute-audio",
                "--disable-geolocation",
                "--use-fake-device-for-media-stream",
                "--use-fake-ui-for-media-stream",
                "--deny-permission-prompts",
                "--log-level=3",
                "--disable-logging",
                "--disable-breakpad",
                "--disable-hang-monitor",
                "--disable-client-side-phishing-detection",
                "--disable-component-update",
                "--no-zygote",
            ],
        )

        filename = f"{uuid.uuid4()}.png"

        await asyncio.to_thread(
            hti.screenshot, url=url, size=(1280, 720), save_as=filename
        )

        filepath = f"https://file.sharkbot.xyz/static/{interaction.user.id}/{filename}"
        await interaction.followup.send(
            embed=discord.Embed(
                title="スクリーンショットを撮影しました。",
                description="一日の終わりにファイルが削除されます。",
                color=discord.Color.green(),
            ),
            view=discord.ui.View().add_item(
                discord.ui.Button(label="結果を確認する", url=filepath)
            ),
        )

    async def choice_download_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        choices = [
            app_commands.Choice(name=f, value=f)
            for f in ["いらすとや"] if current.lower() in f.lower()
        ]
        return choices[:25]

    @tools.command(name="download", description="ファイルをダウンロードします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.autocomplete(タイプ=choice_download_autocomplete)
    async def download(self, interaction: discord.Interaction, タイプ: str, url: str):
        await interaction.response.defer()

        if タイプ == "いらすとや":
            if not IRASUTOTA_REGEX.match(url):
                await interaction.followup.send(embed=discord.Embed(title="正しいURLを入力してください。", color=discord.Color.red()), ephemeral=True)
                return

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url
                ) as response:
                    bs4 = BeautifulSoup(await response.text(), "html.parser")
                    try:
                        img = bs4.select(".separator > a")[0]

                        class IrasutoyaView(discord.ui.LayoutView):
                            container = discord.ui.Container(
                                discord.ui.TextDisplay(
                                    f"### ダウンロード",
                                ),
                                discord.ui.Separator(),
                                discord.ui.MediaGallery(
                                    discord.MediaGalleryItem(img.get('href'))
                                ),
                                discord.ui.ActionRow(
                                    discord.ui.Button(
                                        label="ダウンロード",
                                        url=img.get('href'),
                                    )
                                ),
                                accent_colour=discord.Colour.green(),
                            )

                        await interaction.followup.send(view=IrasutoyaView())
                    except Exception as e:
                        return await interaction.followup.send(embed=discord.Embed(title="解析に失敗しました。", description=f"{e}", color=discord.Color.red()))
        else:
            embed = discord.Embed(
                title="タイプが見つかりません。",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ToolsCog(bot))
