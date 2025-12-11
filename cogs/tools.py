import asyncio
import calendar
import datetime
from functools import partial
import io
import json
import random
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
from PIL import Image
import pytesseract
from consts import badword
from models import command_disable, make_embed
import ipaddress
import socket
from urllib.parse import urlparse
import pyzbar.pyzbar
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
import aiohttp_socks

SOUNDCLOUD_REGEX = re.compile(
    r"^(https?://)?(www\.)?(soundcloud\.com|on\.soundcloud\.com)/.+"
)

IRASUTOTA_REGEX = re.compile(r"https://www\.irasutoya\.com/.+/.+/.+\.html")
X_REGEX = re.compile(r"https://x.com/.+/status/.+")

TIMESTAMP_REGEX = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")

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


COLOR_MAP = {
    "red": discord.Color.red(),
    "赤": discord.Color.red(),
    "blue": discord.Color.blue(),
    "青": discord.Color.red(),
    "green": discord.Color.green(),
    "緑": discord.Color.green(),
    "yellow": discord.Color.yellow(),
    "黄": discord.Color.yellow(),
    "pink": discord.Color.pink(),
    "ピンク": discord.Color.pink(),
    "white": discord.Color.from_str("#FFFFFF"),
    "白": discord.Color.from_str("#FFFFFF"),
    "black": discord.Color.from_str("#000000"),
    "黒": discord.Color.from_str("#000000"),
}


class EmbedBuilder(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="タイトル", style=discord.ButtonStyle.gray)
    async def title_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="タイトル編集"):
            text = discord.ui.Label(
                text="タイトルを入力",
                description="タイトルを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, max_length=30, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()

                em.title = self.text.component.value
                await ol_m.edit(embed=em)

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="説明", style=discord.ButtonStyle.gray)
    async def desc_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="説明編集"):
            text = discord.ui.Label(
                text="説明を入力",
                description="説明を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.long, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()

                em.description = self.text.component.value
                await ol_m.edit(embed=em)

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="画像", style=discord.ButtonStyle.gray)
    async def image_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="画像URLを追加"):
            text = discord.ui.Label(
                text="画像URL",
                description="画像URLを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    em.set_image(url=self.text.component.value)
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="サムネイル画像", style=discord.ButtonStyle.gray, emoji="🆕"
    )
    async def thum_image_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="サムネイル画像編集"):
            text = discord.ui.Label(
                text="サムネイル画像URL",
                description="サムネイル画像URLを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    em.set_thumbnail(url=self.text.component.value)
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="フィールド追加", style=discord.ButtonStyle.gray, emoji="🆕", row=2
    )
    async def field_add_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="フィールド追加"):
            title_ = discord.ui.Label(
                text="フィールド名",
                description="フィールド名を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            value = discord.ui.Label(
                text="フィールドの内容",
                description="フィールドの内容を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.long, required=True
                ),
            )

            # inl = discord.ui.Label(
            #     text="Inlineを有効化するか",
            #     description="Inlineを有効化するか",
            #     component=discord.ui.Select(
            #         options=[discord.SelectOption(label="はい", value="yes"), discord.SelectOption(label="いいえ", value="no")], required=True, max_values=1, min_values=1
            #     ),
            # )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.title_.component, discord.ui.TextInput)
                assert isinstance(self.value.component, discord.ui.TextInput)
                # assert isinstance(self.inl.component, discord.ui.Select)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    # inline_bool = (self.inl.component.options[0].value == "yes")

                    em.add_field(
                        name=self.title_.component.value,
                        value=self.value.component.value,
                    )
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="フィールド削除", style=discord.ButtonStyle.gray, emoji="🆕", row=2
    )
    async def field_remove_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="フィールド削除"):
            title_ = discord.ui.Label(
                text="削除するフィールド名",
                description="削除するフィールド名を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.title_.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    for _, mf in enumerate(em.fields):
                        if mf.name == self.title_.component.value:
                            em.remove_field(_)
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="色", style=discord.ButtonStyle.blurple, row=3)
    async def footer_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="色を入力"):
            text = discord.ui.Label(
                text="色",
                description="色を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True, default="#000000"
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    if not self.text.component.value.lower() in COLOR_MAP:
                        em.color = discord.Color.from_str(self.text.component.value)
                    else:
                        em.color = COLOR_MAP[self.text.component.value.lower()]
                    await ol_m.edit(embed=em)
                except:
                    return await interaction.followup.send(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="適切な色を入力してください。",
                            description="例: `#000000`",
                        ),
                    )

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="送信", style=discord.ButtonStyle.green, row=3)
    async def embed_send_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        ol_m = await interaction.original_response()
        try:
            await interaction.channel.send(embed=ol_m.embeds[0].copy())
        except Exception as e:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="埋め込み送信時にエラーが発生しました。",
                    description=f"```{e}```",
                ),
            )
            return


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


class CalcGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="calc", description="計算系のコマンドです。")

    @app_commands.command(name="calculator", description="電卓を使用します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def calculator_(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )
        def safe_calculator(expression: str):
            expression = expression.replace(" ", "")

            def check_number(n):
                if abs(n) > 10000:
                    return 0
                return n

            def parse_mul_div(tokens):
                result = float(tokens[0])
                i = 1
                while i < len(tokens):
                    op = tokens[i]
                    num = float(tokens[i + 1])
                    if op == "*":
                        result *= num
                    elif op == "/":
                        if num == 0:
                            return "0で割ることはできません。"
                        result /= num
                    i += 2
                return result

            def parse_add_sub(expression):
                tokens = re.findall(r"[+-]?\d+(?:\.\d+)?|[*/]", expression)
                new_tokens = []
                i = 0
                while i < len(tokens):
                    if tokens[i] in "*/":
                        a = new_tokens.pop()
                        op = tokens[i]
                        b = tokens[i + 1]
                        result = parse_mul_div([a, op, b])
                        new_tokens.append(str(result))
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1

                result = check_number(float(new_tokens[0]))
                i = 1
                while i < len(new_tokens):
                    op = new_tokens[i][0]
                    num_str = (
                        new_tokens[i][1:]
                        if len(new_tokens[i]) > 1
                        else new_tokens[i + 1]
                    )
                    num = check_number(float(num_str))
                    if op == "+":
                        result = check_number(result + num)
                    elif op == "-":
                        result = check_number(result - num)
                    i += 1 if len(new_tokens[i]) > 1 else 2
                return result

            try:
                return parse_add_sub(expression)
            except Exception:
                return f"エラー！"

        class CalculatorView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.calculator = "0"

            async def update_display(self, interaction: discord.Interaction):
                await interaction.response.edit_message(
                    content=self.calculator, view=self
                )

            # 数字ボタン
            @discord.ui.button(label="1", style=discord.ButtonStyle.secondary, row=1)
            async def one(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "1"
                await self.update_display(interaction)

            @discord.ui.button(label="2", style=discord.ButtonStyle.secondary, row=1)
            async def two(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "2"
                await self.update_display(interaction)

            @discord.ui.button(label="3", style=discord.ButtonStyle.secondary, row=1)
            async def three(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "3"
                await self.update_display(interaction)

            @discord.ui.button(label="4", style=discord.ButtonStyle.secondary, row=1)
            async def four(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "4"
                await self.update_display(interaction)

            @discord.ui.button(label="5", style=discord.ButtonStyle.secondary, row=2)
            async def five(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "5"
                await self.update_display(interaction)

            @discord.ui.button(label="6", style=discord.ButtonStyle.secondary, row=2)
            async def six(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "6"
                await self.update_display(interaction)

            @discord.ui.button(label="7", style=discord.ButtonStyle.secondary, row=2)
            async def seven(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "7"
                await self.update_display(interaction)

            @discord.ui.button(label="8", style=discord.ButtonStyle.secondary, row=2)
            async def eight(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "8"
                await self.update_display(interaction)

            @discord.ui.button(label="9", style=discord.ButtonStyle.secondary, row=3)
            async def nine(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = self.calculator.lstrip("0") + "9"
                await self.update_display(interaction)

            @discord.ui.button(label="0", style=discord.ButtonStyle.secondary, row=3)
            async def zero(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                if self.calculator != "0":
                    self.calculator += "0"
                await self.update_display(interaction)

            @discord.ui.button(label="00", style=discord.ButtonStyle.secondary, row=3)
            async def zerotwo(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                if self.calculator != "0":
                    self.calculator += "00"
                await self.update_display(interaction)

            # 演算子
            @discord.ui.button(label="+", style=discord.ButtonStyle.primary, row=4)
            async def plus(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator += "+"
                await self.update_display(interaction)

            @discord.ui.button(label="-", style=discord.ButtonStyle.primary, row=4)
            async def minus(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator += "-"
                await self.update_display(interaction)

            @discord.ui.button(label="=", style=discord.ButtonStyle.success, row=4)
            async def equal(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                result = safe_calculator(self.calculator)
                self.calculator = str(result)
                await self.update_display(interaction)

            @discord.ui.button(label="C", style=discord.ButtonStyle.red, row=4)
            async def clear(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                self.calculator = "0"
                await self.update_display(interaction)

        await interaction.response.send_message(content="0", view=CalculatorView())

    @app_commands.command(
        name="rule-calc", description="ある法則に基づいた計算をします。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        法則=[
            app_commands.Choice(name="114514になる計算式", value="homo"),
        ]
    )
    async def rule_calc(
        self,
        interaction: discord.Interaction,
        法則: app_commands.Choice[str],
        入力: str
    ):
        await interaction.response.defer()
        if 法則.value == "homo":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:3320/api/homo", params={
                        "input": int(入力)
                    }
                ) as response:
                    await interaction.followup.send(embed=make_embed.success_embed(title="変換しました。", description=f"```{await response.text()}```"))
            
    @app_commands.command(
        name="size-converter", description="ファイルの容量の単位を変換します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        単位=[
            app_commands.Choice(name="gb->mb", value="gm"),
            app_commands.Choice(name="mb->gb", value="mg"),
            app_commands.Choice(name="mb->kb", value="mk"),
            app_commands.Choice(name="kb->mb", value="km"),
        ]
    )
    async def size_converter(
        self,
        interaction: discord.Interaction,
        単位: app_commands.Choice[str],
        変換元: int,
    ):
        def gb_to_mb(gb):
            mb = gb * 1024
            return mb

        def mb_to_gb(mb):
            gb = mb / 1024
            return gb

        if 単位.value == "gm":
            mb = gb_to_mb(変換元)
            await interaction.response.send_message(
                embed=discord.Embed(title="変換結果", color=discord.Color.green())
                .add_field(name="GB", value=f"{変換元}", inline=False)
                .add_field(name="MB", value=f"{mb}", inline=False)
            )
        elif 単位.value == "mg":
            gb = mb_to_gb(変換元)
            await interaction.response.send_message(
                embed=discord.Embed(title="変換結果", color=discord.Color.green())
                .add_field(name="MB", value=f"{変換元}", inline=False)
                .add_field(name="GB", value=f"{gb}", inline=False)
            )
        elif 単位.value == "mk":
            kb = gb_to_mb(変換元)
            await interaction.response.send_message(
                embed=discord.Embed(title="変換結果", color=discord.Color.green())
                .add_field(name="MB", value=f"{変換元}", inline=False)
                .add_field(name="KB", value=f"{kb}", inline=False)
            )
        elif 単位.value == "km":
            mb = mb_to_gb(変換元)
            await interaction.response.send_message(
                embed=discord.Embed(title="変換結果", color=discord.Color.green())
                .add_field(name="KB", value=f"{変換元}", inline=False)
                .add_field(name="MB", value=f"{mb}", inline=False)
            )


class OcrGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="ocr", description="OCR系のコマンドです。")

    async def ocr_async(self, image_: io.BytesIO):
        image = await asyncio.to_thread(Image.open, image_)

        text = await asyncio.to_thread(pytesseract.image_to_string, image, lang="jpn")

        return text

    @app_commands.command(name="ocr", description="OCRをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ocr(self, interaction: discord.Interaction, 画像: discord.Attachment):
        await interaction.response.defer()

        if not 画像.filename.endswith((".png", ".jpg", ".jpeg")):
            return await interaction.followup.send(
                content="`.png`と`.jpg`のみ対応しています。"
            )
        i = io.BytesIO(await 画像.read())
        text_ocrd = await self.ocr_async(i)
        i.close()

        await interaction.followup.send(
            embed=discord.Embed(
                title="OCR結果",
                description=f"```{text_ocrd}```",
                color=discord.Color.green(),
            )
        )


class TwitterGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="twitter", description="ツイッター系のコマンドです。")

    @app_commands.command(name="info", description="そのツイートの情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tweet_info(self, interaction: discord.Interaction, tweet_url: str):
        tweet_id_match = re.search(r"status/(\d+)", tweet_url)
        if not tweet_id_match:
            return await interaction.response.send_message(
                "無効なURLです", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        tweet_id = tweet_id_match.group(1)
        API_BASE_URL = "https://api.fxtwitter.com/status/"
        api_url = f"{API_BASE_URL}{tweet_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(
                        "APIリクエストに失敗しました"
                    )
                data = await resp.json()

        tweet = data["tweet"]

        source = tweet.get("source", "取得失敗").replace("Twitter ", "")

        await interaction.followup.send(
            embed=discord.Embed(
                title="ツイートの情報を取得しました。",
                description=tweet.get("text", "なし"),
                color=discord.Color.green(),
                url=tweet["url"],
            )
            .set_author(
                name=tweet["author"]["name"], icon_url=tweet["author"]["avatar_url"]
            )
            .add_field(name="名前", value=tweet["author"]["name"])
            .add_field(name="スクリーン名前", value=tweet["author"]["screen_name"])
            .add_field(name="アバターの色", value=tweet["author"]["avatar_color"])
            .add_field(name="投稿日時", value=tweet.get("created_at", "取得失敗"))
            .add_field(name="リツイート回数", value=str(tweet["retweets"]) + "回")
            .add_field(name="いいね回数", value=str(tweet["likes"]) + "回")
            .add_field(name="表示回数", value=str(tweet["views"]) + "回")
            .add_field(name="返信回数", value=str(tweet["replies"]) + "回")
            .add_field(name="機種", value=source)
            .add_field(name="言語id", value=tweet["lang"])
            .add_field(name="ツイートの色", value=tweet["color"])
        )


class NetworkGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="network", description="ネットワークツール系コマンドです。"
        )

    @app_commands.command(name="whois", description="Whoisします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def whois(self, interaction: discord.Interaction, ドメイン: str):
        await interaction.response.defer()
        data = await fetch_whois(ドメイン)
        return await interaction.followup.send(file=discord.File(data, "whois.txt"))

    @app_commands.command(name="nslookup", description="DNS情報を見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def nslookup(self, interaction: discord.Interaction, ドメイン: str):
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

                embed = make_embed.success_embed(
                    title="NSLookupをしてDNS情報を取得しました。"
                )

                for record_type, entries in categorized_records.items():
                    value_text = "\n".join(entries)
                    embed.add_field(
                        name=record_type.upper(), value=value_text[:1024], inline=False
                    )

                await interaction.followup.send(embed=embed)

    @app_commands.command(name="iplookup", description="IP情報を見ます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def iplookup(self, interaction: discord.Interaction, ipアドレス: str):
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

    @app_commands.command(
        name="webshot", description="スクリーンショットを撮影します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def webshot(self, interaction: discord.Interaction, url: str):
        return await interaction.response.send_message(
            ephemeral=True, embed=make_embed.error_embed(title="現在は一時封鎖中です。")
        )
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
        embed = make_embed.success_embed(
            title="スクリーンショットを撮影しました。",
            description="一日の終わりにファイルが削除されます。",
        )
        await interaction.followup.send(
            embed=embed,
            view=discord.ui.View().add_item(
                discord.ui.Button(label="結果を確認する", url=filepath)
            ),
        )

    @app_commands.command(name="ping", description="ドメインにpingを送信します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ping_domein(
        self, interaction: discord.Interaction, ドメイン: str, ポート: int
    ):
        await interaction.response.defer()
        data = {
            "params": f"target_domain={ドメイン}&target_port={ポート}",
        }

        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://tech-unlimited.com",
            "priority": "u=1, i",
            "referer": "https://tech-unlimited.com/ping.html",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://tech-unlimited.com/proc/ping.php", data=data, headers=headers
            ) as response:
                text = await response.text()

                check = json.loads(text)
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="ドメインにPingを送信しました。"
                    )
                    .add_field(name="ステータス", value=check["result"], inline=False)
                    .add_field(
                        name="反応までかかった時間",
                        value=check["response_time"],
                        inline=False,
                    )
                )

    @app_commands.command(name="meta", description="サイトのメタデータを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def sites_meta(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        connector = aiohttp_socks.ProxyConnector("127.0.0.1", port=9050)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("https://rakko.tools/tools/34/") as response:
                regex = r"var (?:tokenId|token) = '([^']+)'"

                text = await response.text()

                match = re.findall(regex, text)

                data = {
                    "token_id": match[0],
                    "token": match[1],
                    "value": url,
                }

                headers = {
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "accept-language": "ja,en-US;q=0.9,en;q=0.8",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "origin": "https://rakko.tools",
                    "priority": "u=1, i",
                    "referer": "https://rakko.tools/tools/34/",
                    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                    "x-requested-with": "XMLHttpRequest",
                }

                async with session.post(
                    "https://rakko.tools/tools/34/urlToTitleController.php",
                    data=data,
                    headers=headers,
                ) as response_2:
                    js = json.loads(await response_2.text())

                    await interaction.followup.send(
                        embed=make_embed.success_embed(
                            title="サイトのメタデータを取得しました。"
                        )
                        .add_field(
                            name="サイト名",
                            value=js["result"][0].get("title", "取得失敗"),
                            inline=False,
                        )
                        .add_field(
                            name="サイト説明",
                            value=js["result"][0].get(
                                "metadata_description", "取得失敗"
                            ),
                            inline=False,
                        )
                        .add_field(
                            name="ロボット",
                            value=js["result"][0].get("metadata_robot", "取得失敗"),
                            inline=False,
                        )
                    )


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

    async def afk_mention_write(self, user: int, message: discord.Message):
        database = self.bot.async_db["Main"].AFKMention
        await database.replace_one(
            {
                "User": user,
                "Channel": message.channel.id,
                "MentionUser": message.author.id,
            },
            {
                "User": user,
                "MentionUser": message.author.id,
                "Channel": message.channel.id,
            },
            upsert=True,
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

    tools = app_commands.Group(name="tools", description="ツール系のコマンドです。", allowed_installs=app_commands.AppInstallationType(guild=True, user=True))

    tools.add_command(CalcGroup())
    tools.add_command(OcrGroup())
    tools.add_command(TwitterGroup())
    tools.add_command(NetworkGroup())

    @tools.command(name="embed", description="埋め込みを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        操作モード=[
            app_commands.Choice(name="PC・Web", value="pc"),
            app_commands.Choice(name="スマホ・タブレット", value="phone"),
        ]
    )
    async def tools_embed(
        self,
        interaction: discord.Interaction,
        操作モード: app_commands.Choice[str] = None,
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )
        async def send_pc_embed_builder():
            await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(
                    title="埋め込みタイトル",
                    description="埋め込み説明です",
                    color=discord.Color.green(),
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
                view=EmbedBuilder(),
            )

        if not 操作モード:
            is_pc = interaction.user.client_status.is_on_mobile()
            if not is_pc:
                await send_pc_embed_builder()
            else:
                await interaction.response.send_modal(EmbedMake())
            return

        if 操作モード.value == "pc":
            await send_pc_embed_builder()
        else:
            await interaction.response.send_modal(EmbedMake())

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_button_redirect(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "button_redirect+":
                    try:
                        await interaction.response.defer(ephemeral=True, thinking=True)
                        msg_id = interaction.message.id
                        db = interaction.client.async_db["MainTwo"].ButtonRedirect
                        docs = await db.find_one({"guild_id": interaction.guild_id, "message_id": msg_id})

                        view = discord.ui.View()
                        view.add_item(discord.ui.Button(label="アクセスする", url=docs.get('url', "https://example.com/")))

                        await interaction.followup.send(embed=discord.Embed(title="説明", description="以下のボタンを押すことで先ほどの\nボタンのページに飛ぶことができます。", color=discord.Color.green())
                                                        .add_field(name="ボタンのページのURL", value=docs.get('url', "https://example.com/"), inline=False), view=view)
                    except Exception as e:
                        return await interaction.followup.send(embed=make_embed.error_embed(title="エラーが発生しました。", description=f"```{e}```"))
        except:
            return

    @tools.command(name="button", description="ボタンを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ボタンの種類=[
            app_commands.Choice(name="URLボタン", value="url"),
            app_commands.Choice(name="グレーボタン", value="gray"),
            app_commands.Choice(name="緑ボタン", value="green"),
            app_commands.Choice(name="赤ボタン", value="red"),
            app_commands.Choice(name="青ボタン", value="blue"),
            app_commands.Choice(name="押せないボタン", value="none"),
        ]
    )
    async def tools_button(
        self, interaction: discord.Interaction, ラベル: str, url: str, ボタンの種類: app_commands.Choice[str]
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
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

        view = discord.ui.View()
        if ボタンの種類.value == "url":
            view.add_item(discord.ui.Button(label=ラベル, url=url))
        elif ボタンの種類.value == "gray":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.gray))
        elif ボタンの種類.value == "green":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.green))
        elif ボタンの種類.value == "red":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.red))
        elif ボタンの種類.value == "blue":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.blurple))
        elif ボタンの種類.value == "none":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.gray, disabled=True))

        await interaction.response.send_message(
            view=view
        )

        if ボタンの種類.value != "url":

            fet_message = await interaction.original_response()
            await interaction.client.async_db["MainTwo"].ButtonRedirect.update_one(
                {"guild_id": interaction.guild.id, "channel_id": interaction.channel_id, "message_id": fet_message.id},
                {'$set': {"guild_id": interaction.guild.id, "channel_id": interaction.channel_id, "message_id": fet_message.id, "url": url}},
                upsert=True,
            )

    @tools.command(
        name="choice", description="自分だけが見えるようにBotが選んでくれます。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tools_choice(
        self,
        interaction: discord.Interaction,
        選択肢1: str,
        選択肢2: str,
        選択肢3: str = None,
        選択肢4: str = None,
        選択肢5: str = None,
    ):
        choices = [
            c for c in [選択肢1, 選択肢2, 選択肢3, 選択肢4, 選択肢5] if c != None
        ]
        choiced = random.choice(choices)
        await interaction.response.send_message(
            ephemeral=True,
            embed=make_embed.success_embed(
                title="Botが選びました。", description=choiced
            ),
        )

    @tools.command(name="timestamp", description="タイムスタンプを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tools_timestamp(self, interaction: discord.Interaction, 時間: str):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )
        def parse_time(timestr: str):
            match = TIMESTAMP_REGEX.fullmatch(timestr.strip().lower())
            if not match:
                raise ValueError("時間の形式が正しくありません")

            days, hours, minutes, seconds = match.groups(default="0")
            return datetime.timedelta(
                days=int(days),
                hours=int(hours),
                minutes=int(minutes),
                seconds=int(seconds),
            )

        try:
            timed = parse_time(時間)
        except ValueError:
            return await interaction.response.send_message(
                ephemeral=True,
                content="時間の形式が正しくありません。\nサンプル: `2h3m`",
            )
        text = ""
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 't')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "t")
            + "\n"
        )
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 'T')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "T")
            + "\n"
        )
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 'd')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "d")
            + "\n"
        )
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 'D')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "D")
            + "\n"
        )
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 'f')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "f")
            + "\n"
        )
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 'F')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "F")
            + "\n"
        )
        text += (
            f"`{discord.utils.format_dt(discord.utils.utcnow() + timed, 'R')}` -> "
            + discord.utils.format_dt(discord.utils.utcnow() + timed, "R")
            + "\n"
        )
        await interaction.response.send_message(content=text)

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_todo_(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "todo_add+":

                    class TodoAddModal(discord.ui.Modal):
                        def __init__(self):
                            super().__init__(title="Todoに追加", timeout=180)

                        text = discord.ui.Label(
                            text="やることを入力",
                            description="やることを入力してください。",
                            component=discord.ui.TextInput(
                                style=discord.TextStyle.short,
                                max_length=30,
                                required=True,
                            ),
                        )

                        async def on_submit(self, interaction: discord.Interaction):
                            await interaction.response.defer(
                                ephemeral=True, thinking=False
                            )

                            assert isinstance(self.text.component, discord.ui.TextInput)

                            msg = interaction.message.embeds[0].description
                            if interaction.message.embeds[0].description:
                                count = (
                                    len(
                                        interaction.message.embeds[0].description.split(
                                            "\n"
                                        )
                                    )
                                    + 1
                                )
                                msg = (
                                    msg
                                    + f"\n{count}. {self.text.component.value.replace('.', '')} .. ❌"
                                )
                            else:
                                msg = f"\n1. {self.text.component.value.replace('.', '')} .. ❌\n"
                            em = discord.Embed(
                                title=interaction.message.embeds[0].title,
                                description=msg,
                                color=interaction.message.embeds[0].color,
                            )
                            await interaction.message.edit(embed=em)

                    await interaction.response.send_modal(TodoAddModal())
                elif custom_id == "todo_end+":
                    if interaction.message.embeds[0].description:
                        todo_s = [
                            discord.SelectOption(
                                label=t.split(" .. ")[0].split(". ")[1],
                                value=t.split(" .. ")[0].split(". ")[1],
                            )
                            for t in interaction.message.embeds[0].description.split(
                                "\n"
                            )
                            if t.split(" .. ")[1] == "❌"
                        ]
                        await interaction.response.send_message(
                            ephemeral=True,
                            content=f"どれを終了させる？\n{interaction.message.id}",
                            view=discord.ui.View().add_item(
                                discord.ui.Select(
                                    custom_id="todo_end_select+",
                                    placeholder="終了させるTodoを選択",
                                    options=todo_s,
                                )
                            ),
                        )
                    else:
                        return await interaction.response.send_message(
                            ephemeral=True, content="まだTodoがありません。"
                        )
                elif custom_id == "todo_delete+":
                    embed = interaction.message.embeds[0]
                    if embed.description:
                        todo_s = [
                            discord.SelectOption(
                                label=t.split(" .. ")[0].split(". ")[1],
                                value=t.split(" .. ")[0].split(". ")[1],
                            )
                            for t in embed.description.split("\n")
                        ]

                        if not todo_s:
                            return await interaction.response.send_message(
                                ephemeral=True, content="削除できるTodoはありません。"
                            )

                        view = discord.ui.View()
                        view.add_item(
                            discord.ui.Select(
                                custom_id=f"todo_delete_select+",
                                placeholder="削除するTodoを選択",
                                options=todo_s,
                            )
                        )

                        await interaction.response.send_message(
                            ephemeral=True,
                            content=f"どれを削除する？\n{interaction.message.id}",
                            view=view,
                        )
                    else:
                        return await interaction.response.send_message(
                            ephemeral=True, content="まだTodoがありません。"
                        )
            elif interaction.data["component_type"] == 3:
                custom_id = interaction.data.get("custom_id")
                if not custom_id:
                    return

                if custom_id.startswith("todo_end_select+"):
                    await interaction.response.defer(ephemeral=True)
                    original_msg_id = int(interaction.message.content.split("\n")[1])
                    msg = await interaction.channel.fetch_message(original_msg_id)

                    embed = msg.embeds[0]
                    desc = embed.description

                    for t in desc.split("\n"):
                        if (
                            t.split(" .. ")[0].split(". ")[1]
                            == interaction.data["values"][0]
                        ):
                            new_line = t.replace("❌", "✅")
                            desc = desc.replace(t, new_line)
                            break

                    em = discord.Embed(
                        title=embed.title,
                        description=desc,
                        color=embed.color,
                    )
                    await msg.edit(embed=em)

                    await interaction.followup.send(
                        ephemeral=True, content="Todoを完了しました"
                    )
                elif custom_id.startswith("todo_delete_select+"):
                    original_msg_id = int(interaction.message.content.split("\n")[1])
                    msg = await interaction.channel.fetch_message(original_msg_id)

                    embed = msg.embeds[0]
                    desc = embed.description

                    new_lines = []
                    for t in desc.split("\n"):
                        if (
                            t.split(" .. ")[0].split(". ")[1]
                            != interaction.data["values"][0]
                        ):
                            new_lines.append(t)

                    new_desc = "\n".join(
                        [
                            f"{i + 1}. {line.split('. ', 1)[1]}"
                            for i, line in enumerate(new_lines)
                        ]
                    )

                    em = discord.Embed(
                        title=embed.title,
                        description=new_desc,
                        color=embed.color,
                    )
                    await msg.edit(embed=em)

                    await interaction.response.send_message(
                        ephemeral=True, content="Todoを削除しました"
                    )
        except:
            return

    @tools.command(name="todo", description="Todoパネルを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def todo(self, interaction: discord.Interaction, タイトル: str):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )
        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="追加", style=discord.ButtonStyle.blurple, custom_id="todo_add+"
            )
        )
        view.add_item(
            discord.ui.Button(
                label="完了", style=discord.ButtonStyle.green, custom_id="todo_end+"
            )
        )
        view.add_item(
            discord.ui.Button(
                label="削除", style=discord.ButtonStyle.red, custom_id="todo_delete+"
            )
        )
        await interaction.response.send_message(
            embed=discord.Embed(title=タイトル, color=discord.Color.blue()), view=view
        )

    @tools.command(name="invite", description="招待リンクを作成します。")
    @app_commands.checks.has_permissions(create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def invite(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
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
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.uuidtools.com/api/generate/v1"
            ) as response:
                jso = await response.json()
                embed = make_embed.success_embed(
                    title="UUIDを生成しました。", description=jso[0]
                )
                await interaction.followup.send(embed=embed)

    @tools.command(name="short", description="短縮urlを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ドメイン=[
            app_commands.Choice(name="shb.red", value="shb"),
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
        if not is_url.search(url):
            return await interaction.response.send_message(
                ephemeral=True, content="URLを入力してください。"
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
        elif ドメイン.value == "shb":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://shb.red/shorten", params={"url": url}
                ) as response:
                    url_ = await response.json()
                    url_ = url_["short_url"]
        embed = make_embed.success_embed(title="URLを短縮しました。", description=url_)
        await interaction.followup.send(
            embed=embed,
            ephemeral=True,
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
        await interaction.response.defer()
        database = self.bot.async_db["Main"].AFK
        await database.update_one(
            {"User": interaction.user.id},
            {'$set': {"User": interaction.user.id, "Reason": 理由, "End": 終わったらやること}},
            upsert=True,
        )
        embed = make_embed.success_embed(title="AFKを設定しました。", description=理由)
        await interaction.followup.send(embed=embed)

    @tools.command(name="timer", description="タイマーをセットします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def timer(self, interaction: discord.Interaction, 秒数: int):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )
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

    @tools.command(name="qr", description="qrコードを作成・読み取りをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="作成", value="create"),
            app_commands.Choice(name="読み取り", value="read"),
        ]
    )
    async def qrcode_make(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        qrコード: discord.Attachment = None,
    ):
        if 操作.value == "create":

            class CreateModal(discord.ui.Modal, title="QRコード作成"):
                url = discord.ui.TextInput(
                    label="URLを入力",
                    required=True,
                    style=discord.TextStyle.short,
                )

                async def on_submit(self, interaction_: discord.Interaction):
                    await interaction_.response.defer()
                    embed = make_embed.success_embed(title="QRコードを作成しました。")
                    embed.set_image(
                        url=f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={self.url.value}"
                    )
                    await interaction_.followup.send(embed=embed)

            await interaction.response.send_modal(CreateModal())
        elif 操作.value == "read":
            if not qrコード:
                return await interaction.response.send_message(
                    ephemeral=True, content="Qrコードを添付してください。"
                )
            await interaction.response.defer()
            i_ = io.BytesIO(await qrコード.read())
            img = await asyncio.to_thread(Image.open, i_)
            decoded_objects = await asyncio.to_thread(pyzbar.pyzbar.decode, img)
            if not decoded_objects:
                await interaction.followup.send("QRコードが見つかりませんでした。")
                return
            results = "\n".join([obj.data.decode("utf-8") for obj in decoded_objects])
            embed = make_embed.success_embed(
                title="QRコード読み取りました。", description=f"```{results}```"
            )
            await interaction.followup.send(embed=embed)
            i_.close()
            await asyncio.to_thread(img.close)

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

                embed = make_embed.success_embed(
                    title=f"{場所.name} の天気を取得しました。",
                    description="気象庁データを元にしています",
                )

                for dt, w in weather_info:
                    embed.add_field(name=dt, value=w, inline=False)

                await interaction.followup.send(embed=embed)

    @tools.command(name="reminder", description="リマインダーを設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True, manage_guild=True)
    async def reminder(self, interaction: discord.Interaction, 要件: str, 時間: str):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        def parse_time(timestr: str) -> int:
            pattern = r"((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?"
            match = re.fullmatch(pattern, timestr)
            if not match:
                return None
            time_params = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
            return (
                time_params["days"] * 86400
                + time_params["hours"] * 3600
                + time_params["minutes"] * 60
                + time_params["seconds"]
            )

        seconds = parse_time(時間)
        if seconds is None or seconds <= 0:
            embed = discord.Embed(
                title="時間の指定が正しくありません。",
                description="例: `1d2h3m4s`",
                color=discord.Color.red(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await self.bot.reminder_create(
            datetime.timedelta(seconds=seconds),
            "reminder_sendtime",  # イベント名
            interaction.user.id,  # args
            interaction.guild.id,  # args
            channel_id=interaction.channel_id,
            reason=要件,
        )

        embed = make_embed.success_embed(
            title="リマインダーをセットしました。",
            description=f"{seconds}秒後に通知します。",
        )

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener("on_reminder_sendtime")
    async def on_reminder_sendtime_main(self, user_id: int, guild_id: int, **kwargs):
        channel_id = kwargs.get("channel_id")
        reason = kwargs.get("reason")
        print(f"リマインダーの時間になりました: {user_id}")
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.send(
                    embed=make_embed.success_embed(
                        title="リマインダーのセットされた時間になりました。",
                        description=reason,
                    ),
                    content=f"<@{user_id}>",
                )
            except:
                return

    @tools.command(name="calendar", description="カレンダーを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def calendar(self, interaction: discord.Interaction):
        await interaction.response.defer()

        def make_image():
            today = datetime.date.today()
            year, month, day_today = today.year, today.month, today.day
            cell_w, cell_h = 100, 80
            font_size = 24
            title_font_size = 36

            cal = calendar.Calendar(firstweekday=6)
            month_days = cal.monthdayscalendar(year, month)

            img_w = cell_w * 7
            img_h = cell_h * (len(month_days) + 2)
            img = Image.new("RGB", (img_w, img_h), "white")
            draw = ImageDraw.Draw(img)

            try:
                font = ImageFont.truetype("data/DiscordFont.ttf", font_size)
                title_font = ImageFont.truetype("data/DiscordFont.ttf", title_font_size)
            except:
                font = ImageFont.load_default()
                title_font = font

            title = f"{year}年 {month}月"
            bbox = draw.textbbox((0, 0), title, font=title_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text(((img_w - tw) // 2, 10), title, font=title_font, fill="black")

            weekdays = ["日", "月", "火", "水", "木", "金", "土"]
            for i, wd in enumerate(weekdays):
                x = i * cell_w + cell_w // 3
                y = cell_h + 10
                color = "red" if i == 0 else "blue" if i == 6 else "black"
                draw.text((x, y), wd, font=font, fill=color)

            for row, week in enumerate(month_days):
                for col, day in enumerate(week):
                    if day != 0:
                        x = col * cell_w + 10
                        y = (row + 2) * cell_h + 10

                        if day == day_today:
                            x0, y0 = col * cell_w, (row + 2) * cell_h
                            x1, y1 = x0 + cell_w, y0 + cell_h
                            draw.rectangle(
                                [x0, y0, x1, y1], fill="#ffe5e5", outline="red", width=3
                            )

                        draw.text((x, y), str(day), font=font, fill="black")

                    x0, y0 = col * cell_w, (row + 2) * cell_h
                    x1, y1 = x0 + cell_w, y0 + cell_h
                    draw.rectangle([x0, y0, x1, y1], outline="gray")

            i = io.BytesIO()

            img.save(i, "png")

            i.seek(0)

            return i

        img = await asyncio.to_thread(make_image)

        await interaction.followup.send(file=discord.File(img, filename="calendar.png"))

        img.close()

    async def choice_download_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ):
        choices = [
            app_commands.Choice(name=f, value=f)
            for f in ["いらすとや", "X(Twitter)"]
            if current.lower() in f.lower()
        ]
        return choices[:25]

    @tools.command(name="download", description="ファイルをダウンロードします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.autocomplete(タイプ=choice_download_autocomplete)
    async def download(self, interaction: discord.Interaction, タイプ: str, url: str):
        if タイプ == "いらすとや":
            await interaction.response.defer()

            if not IRASUTOTA_REGEX.match(url):
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="正しいURLを入力してください。", color=discord.Color.red()
                    ),
                    ephemeral=True,
                )
                return

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    bs4 = BeautifulSoup(await response.text(), "html.parser")
                    try:
                        img = bs4.select(".separator > a")[0]

                        class IrasutoyaView(discord.ui.LayoutView):
                            container = discord.ui.Container(
                                discord.ui.TextDisplay(
                                    f"### いらすとやのダウンロード",
                                ),
                                discord.ui.Separator(),
                                discord.ui.MediaGallery(
                                    discord.MediaGalleryItem(img.get("href"))
                                ),
                                discord.ui.ActionRow(
                                    discord.ui.Button(
                                        label="ダウンロード",
                                        url=img.get("href"),
                                    )
                                ),
                                accent_colour=discord.Colour.green(),
                            )

                        await interaction.followup.send(view=IrasutoyaView())
                    except Exception as e:
                        return await interaction.followup.send(
                            embed=discord.Embed(
                                title="解析に失敗しました。",
                                description=f"{e}",
                                color=discord.Color.red(),
                            )
                        )
        elif タイプ == "X(Twitter)":
            tweet_id_match = re.search(r"status/(\d+)", url)
            if not tweet_id_match:
                return await interaction.response.send_message(
                    "無効なURLです", ephemeral=True
                )

            await interaction.response.defer(ephemeral=True)

            tweet_id = tweet_id_match.group(1)
            API_BASE_URL = "https://api.fxtwitter.com/status/"
            api_url = f"{API_BASE_URL}{tweet_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(
                            "APIリクエストに失敗しました"
                        )
                    data = await resp.json()

            tweet = data["tweet"]

            if (
                "media" not in tweet
                or "videos" not in tweet["media"]
                or not tweet["media"]["videos"]
            ):
                return await interaction.followup.send(
                    "このツイートには動画がありません"
                )

            videos_under_1080p = [
                v for v in tweet["media"]["videos"] if v.get("height", 9999) <= 1080
            ]

            if not videos_under_1080p:
                return await interaction.followup.send(
                    "1080p以下の動画が見つかりませんでした"
                )

            embeds = []
            buttons = []

            for index, video in enumerate(videos_under_1080p, start=1):
                embed = discord.Embed(
                    title="X(Twitter)にある動画のダウンロード",
                    url=tweet["url"],
                    description=tweet.get("text", ""),
                    color=discord.Color.green(),
                )
                embed.set_author(
                    name=tweet["author"]["name"], icon_url=tweet["author"]["avatar_url"]
                )
                embed.set_image(url=video["thumbnail_url"])

                button = discord.ui.Button(
                    label=f"動画{index}",
                    style=discord.ButtonStyle.link,
                    url=video["url"],
                )

                embeds.append(embed)
                buttons.append(button)

            await interaction.followup.send(
                embeds=embeds, view=discord.ui.View().add_item(*buttons), ephemeral=True
            )
        else:
            embed = discord.Embed(
                title="タイプが見つかりません。", color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(ToolsCog(bot))
