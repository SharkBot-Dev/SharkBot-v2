import asyncio
from functools import partial
import io
import re
import socket
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
import discord
import datetime

import pyshorteners
from consts import mongodb
from discord import app_commands
from models import command_disable

ipv4_pattern = re.compile(
    r'^('
    r'(25[0-5]|'        # 250-255
    r'2[0-4][0-9]|'     # 200-249
    r'1[0-9]{2}|'       # 100-199
    r'[1-9][0-9]|'      # 10-99
    r'[0-9])'           # 0-9
    r'\.){3}'           # 繰り返し: 3回ドット付き
    r'(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])'  # 最後のオクテット
    r'$'
)

domain_regex = re.compile(
    r"^(?!\-)(?:[a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,}$"
)

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

class EmbedMake(discord.ui.Modal, title='埋め込みを作成'):
    title_ = discord.ui.TextInput(
        label='タイトル',
        placeholder='タイトル！',
        style=discord.TextStyle.short,
    )

    desc = discord.ui.TextInput(
        label='説明',
        placeholder='説明！',
        style=discord.TextStyle.long,
    )

    color = discord.ui.TextInput(
        label='色',
        placeholder='#000000',
        style=discord.TextStyle.short,
        default="#000000"
    )

    button_label = discord.ui.TextInput(
        label='ボタンラベル',
        placeholder='Webサイト',
        style=discord.TextStyle.short,
        required=False
    )

    button = discord.ui.TextInput(
        label='ボタンurl',
        placeholder='https://www.sharkbot.xyz/',
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            view = discord.ui.View()
            if self.button.value:
                if self.button_label.value:
                    view.add_item(discord.ui.Button(label=self.button_label.value, url=self.button.value))
                else:
                    view.add_item(discord.ui.Button(label="Webサイト", url=self.button.value))
            await interaction.channel.send(embed=discord.Embed(title=self.title_.value, description=self.desc.value, color=discord.Color.from_str(self.color.value)).set_author(name=f"{interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url).set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.user.default_avatar.url), view=view)
        except Exception as e:
            return await interaction.followup.send("作成に失敗しました。", ephemeral=True, embed=discord.Embed(title="エラー内容", description=f"```{e}```", color=discord.Color.red()))

class ToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ToolsCog")

    tools = app_commands.Group(name="tools", description="ツール系のコマンドです。")

    @tools.command(name="embed", description="埋め込みを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def tools_embed(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")
        await interaction.response.send_modal(EmbedMake())

    @tools.command(name="invite", description="招待リンクを作成します。")
    @app_commands.checks.has_permissions(create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def invite(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if not interaction.guild.vanity_url:
            inv = await interaction.channel.create_invite()
            inv = inv.url
        else:
            inv = interaction.guild.vanity_url
        await interaction.response.send_message(f"サーバー名: {interaction.guild.name}\nサーバーの人数: {interaction.guild.member_count}\n招待リンク: {inv}")

    @tools.command(name="uuid", description="uuidを作成します。")
    @app_commands.checks.has_permissions(create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def uuid(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.uuidtools.com/api/generate/v1") as response:
                jso = await response.json()
                await interaction.followup.send(embed=discord.Embed(title="UUID生成", description=f"{jso[0]}", color=discord.Color.green()))

    @tools.command(name="short", description="短縮urlを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @app_commands.choices(ドメイン=[
        app_commands.Choice(name='tinyurl.com',value="tiny"),
        app_commands.Choice(name='urlc.net',value="urlc"),
        app_commands.Choice(name='oooooo.ooo',value="ooo")
    ])
    async def short_url(self, interaction: discord.Interaction, ドメイン: app_commands.Choice[str], url: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer(ephemeral=True)
        if ドメイン.value == "tiny":
            loop = asyncio.get_running_loop()
            s = await loop.run_in_executor(None, partial(pyshorteners.Shortener))
            url_ = await loop.run_in_executor(None, partial(s.tinyurl.short, url))
        elif ドメイン.value == "urlc":
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://urlc.net/', params={'url': url,'keyword': ''}) as response:
                    soup = BeautifulSoup(await response.text(), 'html.parser')
                    url_ = soup.find({"button": {"class": "short-url-button noselect"}})["data-clipboard-text"]
        elif ドメイン.value == "ooo":
            class OOO:
                enc = ["o", "ο", "о", "ᴏ"]
                curr_ver = "oooo"

                def encode_url(self, url: str) -> str:
                    utf8_bytes = url.encode("utf-8")
                    base4_digits = ''.join(format(byte, '04b').zfill(8) for byte in utf8_bytes)
                    
                    b4str = ''
                    for i in range(0, len(base4_digits), 2):
                        b4str += str(int(base4_digits[i:i+2], 2))

                    oooified = ''.join(self.enc[int(d)] for d in b4str)
                    return self.curr_ver + oooified
            url_ = "https://ooooooooooooooooooooooo.ooo/" + OOO().encode_url(url)
        await interaction.followup.send(embed=discord.Embed(title="短縮されたurl", description=f"{url_}", color=discord.Color.green()), ephemeral=True)

    @tools.command(name="whois", description="Whoisします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def whois(self, interaction: discord.Interaction, ドメイン: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        data = await fetch_whois(ドメイン)
        return await interaction.followup.send(file=discord.File(data, "whois.txt"))
    
    @tools.command(name="nslookup", description="DNS情報を見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def nslookup(self, interaction: discord.Interaction, ドメイン: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        l = []
        domain = ドメイン
        json_data = {
            'domain': domain,
            'dnsServer': 'cloudflare',
        }
        async with aiohttp.ClientSession() as session:
            async with session.post("https://www.nslookup.io/api/v1/records", json=json_data) as response:
                js = await response.json()
                records_data = js.get("records", {})
                categorized_records = {}

                for record_type, record_info in records_data.items():
                    response = record_info.get("response", {})
                    answers = response.get("answer", [])
                    
                    for answer in answers:
                        record_details = answer.get("record", {})
                        ip_info = answer.get("ipInfo", {})
                        
                        record_entry = (
                            f"{record_details.get('raw', 'N/A')}"
                        )
                        
                        if record_type not in categorized_records:
                            categorized_records[record_type] = []
                        categorized_records[record_type].append(record_entry)

                embed = discord.Embed(title="NSLookup DNS情報", color=discord.Color.blue())
                
                for record_type, entries in categorized_records.items():
                    value_text = "\n".join(entries)
                    embed.add_field(name=record_type.upper(), value=value_text[:1024], inline=False)
                
                await interaction.followup.send(embed=embed)

    @tools.command(name="iplookup", description="IP情報を見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def iplookup(self, interaction: discord.Interaction, ipアドレス: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        if ipv4_pattern.match(ipアドレス):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ip-api.com/json/{ipアドレス}?lang=ja") as response:
                    try:
                        js = await response.json()
                        await interaction.response.send_message(embed=discord.Embed(title=f"IPアドレス情報 ({ipアドレス})", description=f"""
    国名: {js.get("country", "不明")}
    都市名: {js.get("city", "不明")}
    プロバイダ: {js.get("isp", "不明")}
    緯度: {js.get("lat", "不明")}
    経度: {js.get("lon", "不明")}
    タイムゾーン: {js.get("timezone", "不明")}
    """, color=discord.Color.green()))
                    except:
                        return await interaction.response.send_message(embed=discord.Embed(title="APIのレートリミットです。", color=discord.Color.red()))
        else:
            return await interaction.response.send_message(embed=discord.Embed(title="無効なIPアドレスです。", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(ToolsCog(bot))