from codecs import encode
from functools import partial
import io
import json
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps
import unicodedata
import aiohttp
from discord.ext import commands
import discord

from cryptography.fernet import Fernet, InvalidToken
import pykakasi
from discord import app_commands
from models import command_disable
import asyncio
from deep_translator import GoogleTranslator

import urllib.parse

def text_len_sudden(text):
    count = 0
    for c in text:
        count += 2 if unicodedata.east_asian_width(c) in "FWA" else 1
    return count


def sudden_generator(msg):
    length = text_len_sudden(msg)
    generating = "＿人"
    for i in range(length // 2):
        generating += "人"
    generating += "人＿\n＞  " + msg + "  ＜\n￣^Y"
    for i in range(length // 2):
        generating += "^Y"
    generating += "^Y￣"
    return generating


async def fetch_avatar(user: discord.User):
    if user.avatar:
        url_a = f"https://cdn.discordapp.com/avatars/{user.id}/{user.avatar.key}"
    else:
        url_a = user.default_avatar.url
    async with aiohttp.ClientSession() as session:
        async with session.get(url_a, timeout=10) as resp:
            return await resp.read()


def wrap_text_with_ellipsis(text, font, draw, max_width, max_height, line_height):
    lines = []
    for raw_line in text.split("\n"):
        current_line = ""
        for char in raw_line:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char

            if len(lines) * line_height >= max_height - line_height * 2:
                ellipsis = "…"
                while True:
                    bbox = draw.textbbox((0, 0), current_line + ellipsis, font=font)
                    if bbox[2] - bbox[0] <= max_width:
                        break
                    if len(current_line) == 0:
                        break
                    current_line = current_line[:-1]
                lines.append(current_line + ellipsis)
                return lines

        if current_line:
            lines.append(current_line)

    return lines


def create_quote_image(
    author,
    text,
    avatar_bytes,
    background,
    textcolor,
    color: bool,
    negapoji: bool = False,
):
    width, height = 800, 400
    background_color = background
    text_color = textcolor

    img = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(img)

    avatar_size = (400, 400)
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize(avatar_size)

    mask = Image.new("L", avatar_size, 255)
    for x in range(avatar_size[0]):
        alpha = (
            255
            if x < avatar_size[0] // 2
            else int(255 * (1 - (x - avatar_size[0] // 2) / (avatar_size[0] / 2)))
        )
        for y in range(avatar_size[1]):
            mask.putpixel((x, y), alpha)
    avatar.putalpha(mask)

    img.paste(avatar, (0, height - avatar_size[1]), avatar)

    try:
        font = ImageFont.truetype("data/DiscordFont.ttf", 30)
        name_font = ImageFont.truetype("data/DiscordFont.ttf", 20)
    except:
        font = ImageFont.load_default()
        name_font = ImageFont.load_default()

    text_x = 420
    max_text_width = width - text_x - 50

    max_text_height = height - 80
    line_height = font.size + 10

    lines = wrap_text_with_ellipsis(
        text, font, draw, max_text_width, max_text_height, line_height
    )

    total_lines = len(lines)
    line_height = font.size + 10
    text_block_height = total_lines * line_height
    text_y = (height - text_block_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        draw.text(
            ((width + text_x - 50 - line_width) // 2, text_y + i * line_height),
            line,
            fill=text_color,
            font=font,
        )

    author_text = f"- {author}"
    bbox = draw.textbbox((0, 0), author_text, font=name_font)
    author_width = bbox[2] - bbox[0]
    author_x = (width + text_x - 50 - author_width) // 2
    author_y = text_y + len(lines) * line_height + 10

    draw.text((author_x, author_y), author_text, font=name_font, fill=text_color)

    draw.text((580, 0), "FakeQuote - SharkBot", font=name_font, fill=text_color)

    if negapoji:
        inverted_img = ImageOps.invert(img.convert("RGB"))
        return inverted_img

    if color:
        return img
    else:
        return img.convert("L")


class TextGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="text", description="テキスト系の面白いコマンド")

    @app_commands.command(name="suddendeath", description="突然の死を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def suddendeath(
        self, interaction: discord.Interaction, テキスト: str = "突然の死"
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"```{sudden_generator(テキスト)}```",
                title="突然の死",
                color=discord.Color.green(),
            )
        )

    @app_commands.command(name="retranslate", description="再翻訳します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def retranslate(self, interaction: discord.Interaction, テキスト: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()

        loop = asyncio.get_event_loop()

        desc = f"ja -> {テキスト}"
        msg = await interaction.followup.send(
            embed=discord.Embed(
                title="何回も翻訳 (ja)", description=desc, color=discord.Color.green()
            )
        )

        word = テキスト
        langs = ["en", "zh-CN", "ko", "ru", "ja"]

        for lang in langs:
            await asyncio.sleep(3)
            word_ = await loop.run_in_executor(
                None, partial(GoogleTranslator, source="auto", target=lang)
            )
            word = await loop.run_in_executor(None, partial(word_.translate, word))

            desc += f"\n{lang} -> {word}"
            await msg.edit(
                embed=discord.Embed(
                    title=f"何回も翻訳 ({lang})",
                    description=desc,
                    color=discord.Color.green(),
                )
            )

        await asyncio.sleep(3)
        await msg.edit(
            embed=discord.Embed(
                title="何回も翻訳",
                description=f"{desc}\n完了しました。",
                color=discord.Color.green(),
            )
        )

    @app_commands.command(
        name="text-to-emoji", description="テキストを絵文字化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def text_to_emoji(self, interaction: discord.Interaction, テキスト: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()

        async def text_emoji(text):
            kakasi = pykakasi.kakasi()
            result = kakasi.convert(text)

            def text_to_discord_emoji(text):
                emoji_map = {chr(97 + i): chr(0x1F1E6 + i) for i in range(26)}
                num_emoji_map = {str(i): f"{i}️⃣" for i in range(10)}
                return [
                    emoji_map[char.lower()]
                    if char.isalpha()
                    else num_emoji_map[char]
                    if char.isdigit()
                    else None
                    for char in text
                    if char.isalnum()
                ]

            romaji_text = "".join(item["kunrei"] for item in result if "kunrei" in item)
            emojis = text_to_discord_emoji(romaji_text)

            return emojis

        ems = await text_emoji(テキスト[:20])
        await interaction.followup.send(content=ems)

    @app_commands.command(name="reencode", description="文字化けを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def reencode(self, interaction: discord.Interaction, テキスト: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="文字化け",
                description=encode(テキスト).decode("sjis", errors="ignore"),
                color=discord.Color.green(),
            )
        )

    @app_commands.command(name="crypt", description="文字列を暗号化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def crypt_text(
        self,
        interaction: discord.Interaction,
        テキスト: str = None,
        暗号: str = None,
        暗号化キー: str = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if テキスト and not 暗号 and not 暗号化キー:
            key = Fernet.generate_key()
            f = Fernet(key)
            token = f.encrypt(テキスト.encode())
            embed = discord.Embed(title="暗号化完了", color=discord.Color.green())
            embed.add_field(name="暗号", value=token.decode(), inline=False)
            embed.add_field(name="暗号化キー", value=key.decode(), inline=False)
            await interaction.response.send_message(embed=embed)

        elif 暗号 and 暗号化キー and not テキスト:
            try:
                f = Fernet(暗号化キー.encode())
                decrypted = f.decrypt(暗号.encode())
                embed = discord.Embed(title="復号化完了", color=discord.Color.green())
                embed.add_field(name="復元結果", value=decrypted.decode(), inline=False)
                await interaction.response.send_message(embed=embed)
            except InvalidToken:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="復号エラー",
                        description="無効な暗号またはキーです。",
                        color=discord.Color.red(),
                    )
                )
            except Exception as e:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="エラー", description=str(e), color=discord.Color.red()
                    )
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="使用方法エラー",
                    description="暗号化には `テキスト` を、復号には `暗号` と `暗号化キー` を指定してください。",
                    color=discord.Color.orange(),
                )
            )

    @app_commands.command(name="number", description="進数を変更します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def number(self, interaction: discord.Interaction, 進数: int, 数字: str):
        if 進数 < 2 or 進数 > 16:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="対応していない進数です。",
                    description="2～16進数まで対応しています。",
                    color=discord.Color.red()
                )
            )
        
        try:
            result = int(数字, 進数)
        except ValueError:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="変換エラー",
                    description=f"入力 `{数字}` は {進数} 進数として無効です。",
                    color=discord.Color.red()
                )
            )
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="進数を変換しました。",
                description=f"`{数字}` ({進数}進数) → `{result}` (10進数)",
                color=discord.Color.green()
            )
        )

    @app_commands.command(name="arm", description="armのasmを、バイナリに変換します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def arm_byte(self, interaction: discord.Interaction):
        class SendModal(discord.ui.Modal, title="Armをバイナリに変換"):
            asm = discord.ui.TextInput(
                label="ASMを入力",
                style=discord.TextStyle.long,
                required=True
            )

            async def on_submit(self, interaction_: discord.Interaction) -> None:
                await interaction_.response.defer()
                try:
                    payload = {
                        "asm": self.asm.value,
                        "offset": "",
                        "arch": ["arm64", "arm", "thumb"]
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "https://armconverter.com/api/convert",
                            data=json.dumps(payload)
                        ) as response:
                            js = await response.json()

                            hex_list = js.get("hex", {}).get("arm", [])

                            if not hex_list:
                                await interaction_.followup.send(
                                    ephemeral=True,
                                    content="変換結果が取得できませんでした。"
                                )
                                return

                            result_lines = []
                            try:
                                for i, hex_result in enumerate(hex_list[1:], start=1):
                                    try:
                                        word = int(hex_result, 16) & 0xFFFFFFFF
                                        b = word.to_bytes(4, byteorder="little", signed=False)
                                        be = int.from_bytes(b, byteorder="big", signed=False)
                                        be_result = f"{be:08X}"
                                    except Exception:
                                        be_result = "変換失敗"

                                    result_lines.append(
                                        f"{i}. Little: {hex_result} | Big: {be_result}"
                                    )
                            except:
                                result_lines += "変換失敗"

                            embed = discord.Embed(
                                title="ARMのバイナリ変換結果",
                                description='```' + "\n".join(result_lines) + '```',
                                color=discord.Color.green()
                            )

                            await interaction_.followup.send(embed=embed)

                except Exception as e:
                    await interaction_.followup.send(
                        ephemeral=True,
                        content=f"エラーが発生しました: {e}"
                    )

        await interaction.response.send_modal(SendModal())

class NounaiGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="nounai", description="脳内メーカー系の面白いコマンド")

    @app_commands.command(name="nounai", description="脳内メーカーで遊びます")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def nounai(self, interaction: discord.Interaction, 名前: str):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="脳内メーカー", color=discord.Color.green()
            ).set_image(
                url=f"https://maker.usoko.net/nounai/img/{urllib.parse.quote(名前)}.gif"
            )
        )

    @app_commands.command(name="kakeizu", description="家系図メーカーで遊びます")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def kakeizu(self, interaction: discord.Interaction, 名前: str):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="家系図メーカー", color=discord.Color.green()
            ).set_image(
                url=f"https://usokomaker.com/kakeizu_fantasy/r/img/{urllib.parse.quote(名前)}.gif"
            )
        )


class ImageGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="image", description="画像系の面白いコマンド")

    @app_commands.command(name="cat", description="ネコの画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def cat(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search?size=med&mime_types=jpg&format=json&has_breeds=true&order=RANDOM&page=0&limit=1"
            ) as cat:
                msg = await interaction.response.send_message(
                    embed=discord.Embed(
                        title="猫の画像", color=discord.Color.green()
                    ).set_image(url=json.loads(await cat.text())[0]["url"])
                )

    @app_commands.command(name="dog", description="犬の画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dog(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as dog_:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="犬の画像", color=discord.Color.green()
                    ).set_image(url=f"{json.loads(await dog_.text())['message']}")
                )

    @app_commands.command(name="5000", description="5000兆円ほしい！")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def _5000(
        self,
        interaction: discord.Interaction,
        上: str,
        下: str,
        noアルファ: bool = None,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if noアルファ:
            if noアルファ == False:
                msg = await interaction.response.send_message(
                    embed=discord.Embed(
                        title="5000兆円ほしい！", color=discord.Color.green()
                    ).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}")
                )
            else:
                msg = await interaction.response.send_message(
                    embed=discord.Embed(
                        title="5000兆円ほしい！", color=discord.Color.green()
                    ).set_image(
                        url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}&noalpha=true"
                    )
                )
        else:
            msg = await interaction.response.send_message(
                embed=discord.Embed(
                    title="5000兆円ほしい！", color=discord.Color.green()
                ).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}")
            )

    @app_commands.command(name="textmoji", description="テキストを絵文字にします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        色=[
            app_commands.Choice(name="赤", value="FF0000"),
            app_commands.Choice(name="青", value="1111FF"),
            app_commands.Choice(name="黒", value="000000"),
        ]
    )
    async def textmoji(
        self,
        interaction: discord.Interaction,
        色: app_commands.Choice[str],
        テキスト: str,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://emoji-gen.ninja/emoji?align=center&back_color=00000000&color={色.value.upper()}FF&font=notosans-mono-bold&locale=ja&public_fg=true&size_fixed=true&stretch=true&text={テキスト}"
            ) as resp:
                i = io.BytesIO(await resp.read())
                await interaction.followup.send(file=discord.File(i, "emoji.png"))
                i.close()

    @app_commands.command(name="httpcat", description="httpキャットを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def httpcat(self, interaction: discord.Interaction, ステータスコード: int):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        embed = (
            discord.Embed(title="HTTPCat", color=discord.Color.blue())
            .set_image(url=f"https://http.cat/{ステータスコード}")
            .set_footer(text="Httpcat", icon_url="https://i.imgur.com/6mKRXgR.png")
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="miq", description="Make it a quoteを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        色=[
            app_commands.Choice(name="カラー", value="color"),
            app_commands.Choice(name="白黒", value="black"),
            app_commands.Choice(name="ネガポジ反転", value="negapoji"),
        ]
    )
    @app_commands.choices(
        背景色=[
            app_commands.Choice(name="黒", value="black"),
            app_commands.Choice(name="白", value="white"),
        ]
    )
    async def miq(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User,
        発言: str,
        色: app_commands.Choice[str],
        背景色: app_commands.Choice[str],
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        avatar = ユーザー
        av = await fetch_avatar(avatar)
        negapoji = False
        if 色.value == "color":
            color = True
        elif 色.value == "negapoji":
            color = True
            negapoji = True
        else:
            color = False
        if 背景色.value == "black":
            back = (0, 0, 0)
            text = (255, 255, 255)
        elif 背景色.value == "white":
            back = (255, 255, 255)
            text = (0, 0, 0)
        miq = create_quote_image(
            ユーザー.display_name, 発言, av, back, text, color, negapoji
        )
        image_binary = io.BytesIO()
        miq.save(image_binary, "PNG")
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="fake_quote.png")
        await interaction.followup.send(file=file)
        image_binary.close()


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> FunCog")

    fun = app_commands.Group(name="fun", description="面白いコマンドです。")

    fun.add_command(TextGroup())
    fun.add_command(ImageGroup())
    fun.add_command(NounaiGroup())

    @fun.command(name="janken", description="じゃんけんをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def janken(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        bot = random.choice(["ぐー", "ちょき", "ぱー"])

        def check(user: str, bot: str):
            if user == bot:
                return "あいこです\nもう一回やってみる？"
            if user == "ぐー" and bot == "ちょき":
                return "あなたの勝ち\nもう一回やってみる？"
            if user == "ちょき" and bot == "ぱー":
                return "あなたの勝ち\nもう一回やってみる？"
            if user == "ぱー" and bot == "ぐー":
                return "あなたの勝ち\nもう一回やってみる？"
            return "Botの勝ち\nもう一回チャレンジしてね！"

        class AnsView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

            @discord.ui.button(label="ぐー", style=discord.ButtonStyle.blurple)
            async def goo(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.defer(ephemeral=True)
                if interaction.user.id != interaction.user.id:
                    return await interaction.followup.send(
                        ephemeral=True, content="あなたのボタンではありません。"
                    )
                await interaction.message.edit(
                    view=None,
                    embed=discord.Embed(
                        title="じゃんけん",
                        description=f"あなた: {button.label}\nBot: {bot}\n\n"
                        + check(button.label, bot),
                        color=discord.Color.blue(),
                    ),
                )

            @discord.ui.button(label="ちょき", style=discord.ButtonStyle.blurple)
            async def choki(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.defer(ephemeral=True)
                if interaction.user.id != interaction.user.id:
                    return await interaction.followup.send(
                        ephemeral=True, content="あなたのボタンではありません。"
                    )
                await interaction.message.edit(
                    view=None,
                    embed=discord.Embed(
                        title="じゃんけん",
                        description=f"あなた: {button.label}\nBot: {bot}\n\n"
                        + check(button.label, bot),
                        color=discord.Color.blue(),
                    ),
                )

            @discord.ui.button(label="ぱー", style=discord.ButtonStyle.blurple)
            async def par(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.defer(ephemeral=True)
                if interaction.user.id != interaction.user.id:
                    return await interaction.followup.send(
                        ephemeral=True, content="あなたのボタンではありません。"
                    )
                await interaction.message.edit(
                    view=None,
                    embed=discord.Embed(
                        title="じゃんけん",
                        description=f"あなた: {button.label}\nBot: {bot}\n\n"
                        + check(button.label, bot),
                        color=discord.Color.blue(),
                    ),
                )

            @discord.ui.button(label="あきらめる", style=discord.ButtonStyle.red)
            async def exit(
                self, interaction: discord.Interaction, button: discord.ui.Button
            ):
                await interaction.response.defer(ephemeral=True)
                if interaction.user.id != interaction.user.id:
                    return await interaction.followup.send(
                        ephemeral=True, content="あなたのボタンではありません。"
                    )
                await interaction.message.edit(
                    view=None,
                    embed=discord.Embed(
                        title="じゃんけん",
                        description="Botの勝ち\nもう一回チャレンジしてね！",
                        color=discord.Color.blue(),
                    ),
                )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="じゃんけん",
                description="""
・グーはチョキに勝ち、パーに負けます
・チョキはパーに勝ち、グーに負けます
・パーはグーに勝ち、チョキに負けます
同じ手を両者が出した場合は、あいことなります。
""",
                color=discord.Color.blue(),
            ),
            view=AnsView(),
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
