from codecs import encode
import datetime
from functools import partial
import io
import json
import random
import re
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps
import unicodedata
import aiohttp
from discord.ext import commands
import discord

from cryptography.fernet import Fernet, InvalidToken
import pykakasi
from discord import app_commands
import requests
from consts import settings
from models import block, command_disable, make_embed, miq, markov, miq_china
from models.markov import HIROYUKI_TEXT
import asyncio
import uuid
from deep_translator import GoogleTranslator
import aiofiles.os

import urllib.parse

from models import quest

import cowsay

cooldown_hiroyuki = {}


class EditImageView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=180)
        self.user = user

    @discord.ui.button(label="ネガポジ反転", style=discord.ButtonStyle.blurple)
    async def negapoji(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            return

        await interaction.response.defer(ephemeral=True)
        file = io.BytesIO(await interaction.message.attachments[0].read())
        image = await asyncio.to_thread(Image.open, file)
        image = await asyncio.to_thread(image.convert, "RGB")
        imv = await asyncio.to_thread(ImageOps.invert, image)
        i = io.BytesIO()
        await asyncio.to_thread(imv.save, i, format="png")
        i.seek(0)
        await interaction.message.edit(attachments=[discord.File(i, "emoji.png")])
        file.close()
        i.close()

    @discord.ui.button(emoji="💾", style=discord.ButtonStyle.blurple)
    async def save(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            return

        await interaction.response.defer(ephemeral=True)
        await interaction.message.edit(view=None)


ASCII_CHARS = "@%#*+=-:. "


def resize_image(image, new_width=40, new_height=40):
    return image.resize((new_width, new_height))


def grayify(image):
    return image.convert("L")


def pixels_to_ascii(image):
    pixels = image.getdata()
    ascii_str = ""
    for pixel in pixels:
        ascii_str += ASCII_CHARS[pixel * len(ASCII_CHARS) // 256]
    return ascii_str


def image_to_ascii(image_path):
    try:
        image = Image.open(image_path)
    except Exception as e:
        return "変換エラー"

    image = resize_image(image)
    image = grayify(image)

    ascii_str = pixels_to_ascii(image)

    ascii_art = "\n".join(ascii_str[i : i + 40] for i in range(0, len(ascii_str), 40))
    return ascii_art


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


class BirthdayGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="birthday", description="誕生日を設定&祝ってもらうためのコマンドです。"
        )

    @app_commands.command(name="set", description="誕生日を設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def birthday_set(self, interaction: discord.Interaction, 月: int, 日: int):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        if 月 < 1 or 月 > 12:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="月の値が不正です。",
                    description="1～12の間で指定してください。",
                ),
                ephemeral=True,
            )
        if 日 < 1 or 日 > 31:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="日の値が不正です。",
                    description="1～31の間で指定してください。",
                ),
                ephemeral=True,
            )
        if 月 == 2 and 日 > 29:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="日の値が不正です。",
                    description="2月は29日までしかありません。",
                ),
                ephemeral=True,
            )
        if 月 in [4, 6, 9, 11] and 日 > 30:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="日の値が不正です。",
                    description=f"{月}月は30日までしかありません。",
                ),
                ephemeral=True,
            )

        db = interaction.client.async_db["Main"].Birthdays
        await db.update_one(
            {"user_id": interaction.user.id, "guild_id": interaction.guild_id},
            {"$set": {"month": 月, "day": 日}},
            upsert=True,
        )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="誕生日を設定しました。",
                description=f"{月}月{日}日 が誕生日に設定されました。",
            ),
            ephemeral=True,
        )

    @app_commands.command(name="get", description="ほかの人の誕生日を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def birthday_get(
        self, interaction: discord.Interaction, メンバー: discord.User = None
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        if interaction.guild.get_member(interaction.user.id) is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="サーバーに参加していません。",
                    description="このコマンドではサーバーに参加している人の誕生日のみ取得できます。",
                ),
                ephemeral=True,
            )

        if not メンバー:
            メンバー = interaction.user

        db = interaction.client.async_db["Main"].Birthdays
        data = await db.find_one(
            {"user_id": メンバー.id, "guild_id": interaction.guild_id}
        )

        if not data:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="誕生日が設定されていません。",
                    description=f"{メンバー} さんは誕生日を設定していません。",
                ),
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"{メンバー.name} さんの誕生日",
                description=f"{メンバー.name} さんの誕生日は {data['month']}月{data['day']}日 です。",
            )
        )

    @app_commands.command(name="list", description="今月が誕生日の人を表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def birthday_list(self, interaction: discord.Interaction, 月: int = None):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        db = interaction.client.async_db["Main"].Birthdays
        data = db.find(
            {
                "guild_id": interaction.guild_id,
                "month": 月 if 月 else interaction.created_at.month,
            }
        )

        members = []
        async for d in data:
            member = interaction.guild.get_member(d["user_id"])
            if member:
                members.append(f"{member.name} さん - {d['month']}月{d['day']}日")

        if not members:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title=f"{月 if 月 else interaction.created_at.month}月 が誕生日の人はいません。"
                ),
                ephemeral=True,
            )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"{月 if 月 else interaction.created_at.month}月 が誕生日の人を表示しています。",
                description="\n".join(members[:30]),
            ).set_footer(text="30人までしか表示されません。")
        )


class SayGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="say", description="いろいろなキャラクターに発言させます。"
        )

    @app_commands.command(name="caw", description="牛にしゃべらせます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def say_cow(self, interaction: discord.Interaction, テキスト: str):
        text = cowsay.get_output_string("cow", テキスト)
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(
                title="牛が発言しました。",
                description=f"```{text}```",
                color=discord.Color.green(),
            ).set_footer(text="コピーして貼り付けると会話中にしようできます。"),
        )

    @app_commands.command(name="dragon", description="ドラゴンにしゃべらせます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def say_dragon(self, interaction: discord.Interaction, テキスト: str):
        text = cowsay.get_output_string("dragon", テキスト)
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(
                title="ドラゴンが発言しました。",
                description=f"```{text}```",
                color=discord.Color.green(),
            ).set_footer(text="コピーして貼り付けると会話中にしようできます。"),
        )

    @app_commands.command(name="penguin", description="ペンギンにしゃべらせます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def say_tux(self, interaction: discord.Interaction, テキスト: str):
        text = cowsay.get_output_string("tux", テキスト)
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(
                title="ペンギンが発言しました。",
                description=f"```{text}```",
                color=discord.Color.green(),
            ).set_footer(text="コピーして貼り付けると会話中にしようできます。"),
        )

class TextGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="text", description="テキスト系の面白いコマンド")

    @app_commands.command(name="suddendeath", description="突然の死を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def suddendeath(
        self, interaction: discord.Interaction, テキスト: str = "突然の死"
    ):
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                description=f"```{sudden_generator(テキスト)}```", title="突然の死"
            )
        )

    @app_commands.command(name="retranslate", description="再翻訳します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def retranslate(self, interaction: discord.Interaction, テキスト: str):
        await interaction.response.defer()

        loop = asyncio.get_event_loop()

        desc = f"ja -> {テキスト}"
        msg = await interaction.followup.send(
            embed=make_embed.success_embed(title="何回も翻訳 (ja)", description=desc)
        )

        word = テキスト
        langs = ["en", "zh-CN", "ko", "ru", "ja"]

        for lang in langs:
            await asyncio.sleep(1)
            word_ = await loop.run_in_executor(
                None, partial(GoogleTranslator, source="auto", target=lang)
            )
            word = await loop.run_in_executor(None, partial(word_.translate, word))

            desc += f"\n{lang} -> {word}"
            await interaction.edit_original_response(
                embed=make_embed.success_embed(
                    title=f"何回も翻訳 ({lang})", description=desc
                )
            )

        await asyncio.sleep(1)
        await interaction.edit_original_response(
            embed=make_embed.success_embed(
                title="何回も翻訳", description=f"{desc}\n完了しました。"
            )
        )

    @app_commands.command(
        name="text-to-emoji", description="テキストを絵文字化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def text_to_emoji(self, interaction: discord.Interaction, テキスト: str):
        await interaction.response.defer()

        try:

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

                romaji_text = "".join(
                    item["kunrei"] for item in result if "kunrei" in item
                )
                emojis = text_to_discord_emoji(romaji_text)

                return emojis

            ems = await text_emoji(テキスト[:20])
            await interaction.followup.send(content=" ".join(ems))
        except KeyError:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="特殊文字や絵文字、記号などは使用できません。"
                )
            )

    @app_commands.command(name="reencode", description="文字化けを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def reencode(self, interaction: discord.Interaction, テキスト: str):
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="文字化け",
                description=encode(テキスト).decode("sjis", errors="ignore"),
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
        if テキスト and not 暗号 and not 暗号化キー:
            key = Fernet.generate_key()
            f = Fernet(key)
            token = f.encrypt(テキスト.encode())
            embed = make_embed.success_embed(title="暗号化完了")
            embed.add_field(name="暗号", value=token.decode(), inline=False)
            embed.add_field(name="暗号化キー", value=key.decode(), inline=False)
            await interaction.response.send_message(embed=embed)

        elif 暗号 and 暗号化キー and not テキスト:
            try:
                f = Fernet(暗号化キー.encode())
                decrypted = f.decrypt(暗号.encode())
                embed = make_embed.success_embed(title="復号化完了")
                embed.add_field(name="復元結果", value=decrypted.decode(), inline=False)
                await interaction.response.send_message(embed=embed)
            except InvalidToken:
                await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="復号エラー", description="無効な暗号またはキーです。"
                    )
                )
            except Exception as e:
                await interaction.response.send_message(
                    embed=make_embed.error_embed(title="エラー", description=str(e))
                )
        else:
            await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="使用方法エラー",
                    description="暗号化には `テキスト` を、復号には `暗号` と `暗号化キー` を指定してください。",
                )
            )

    @app_commands.command(name="number", description="進数を変更します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def number(self, interaction: discord.Interaction, 進数: int, 数字: str):
        if 進数 < 2 or 進数 > 16:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="対応していない進数です。",
                    description="2～16進数まで対応しています。",
                )
            )

        try:
            result = int(数字, 進数)
        except ValueError:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="変換エラー",
                    description=f"入力 `{数字}` は {進数} 進数として無効です。",
                )
            )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="進数を変換しました。",
                description=f"`{数字}` ({進数}進数) → `{result}` (10進数)",
            )
        )

    @app_commands.command(name="unicode", description="テキストをUnicodeに変換します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def unicode_python(self, interaction: discord.Interaction, テキスト: str):
        raw_text = ""
        text = ""
        for t in テキスト:
            ord_str = f"{ord(t)}"
            raw_text += t.center(len(ord_str) + 1)
            text += ord_str + " "
        await interaction.response.send_message(
            f"```{raw_text}\n{text}```", ephemeral=True
        )

    @app_commands.command(name="arm", description="armのasmを、バイナリに変換します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def arm_byte(self, interaction: discord.Interaction):
        class send(discord.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="Armをバイナリに変換", timeout=None)

            asm = discord.ui.TextInput(
                label="ASMを入力", style=discord.TextStyle.long, required=True
            )

            async def on_submit(self, interaction_: discord.Interaction) -> None:
                await interaction_.response.defer()
                try:
                    payload = {
                        "asm": self.asm.value,
                        "offset": "",
                        "arch": ["arm64", "arm", "thumb"],
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            "https://armconverter.com/api/convert",
                            data=json.dumps(payload),
                        ) as response:
                            js = await response.json()
                            hex_list = js.get("hex", {}).get("arm", [])
                            hex_result = (
                                hex_list[1]
                                if len(hex_list) > 1
                                else "取得できませんでした"
                            )
                            await interaction_.followup.send(
                                embed=make_embed.success_embed(
                                    title="ARMのバイナリ",
                                    description=f"```{hex_result}```",
                                )
                            )
                except Exception as e:
                    await interaction_.followup.send(
                        ephemeral=True, content=f"エラーが発生しました: {e}"
                    )

        await interaction.response.send_modal(send())

    @app_commands.command(name="oldtext", description="文字列を旧字体に変換します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        変換方法=[
            app_commands.Choice(name="新しくする", value="new"),
            app_commands.Choice(name="古くする", value="old"),
        ]
    )
    async def oldtext_convert(
        self,
        interaction: discord.Interaction,
        テキスト: str,
        変換方法: app_commands.Choice[str],
    ):
        New = "亜悪圧囲為医壱逸稲飲隠羽営栄衛益駅悦謁円園縁艶塩奥応横欧殴鴎黄温穏仮価禍画会回壊悔懐海絵慨概拡殻覚学岳楽喝渇褐勧巻寛歓漢缶観間関陥館巌顔器既帰気祈亀偽戯犠却糾旧拠挙虚峡挟教狭郷響尭暁勤謹区駆駆勲薫群径恵掲携渓経継茎蛍軽鶏芸撃欠倹券剣圏検権献研県険顕験厳効広恒晃鉱高号国穀黒済砕斎剤冴崎桜冊殺雑参惨桟蚕賛残祉糸視飼歯児辞湿実舎写煮社者釈寿収臭従渋獣縦祝粛処暑渚緒署諸叙奨将床渉焼祥称証乗剰壌嬢条浄状畳穣譲醸嘱触寝慎晋真神刃尽図粋酔随髄数枢瀬晴清精声青静斉跡摂窃節専戦浅潜繊践銭禅曽祖僧双壮層捜挿巣争痩窓総聡荘装騒増憎臓蔵贈即属続堕体対帯滞台滝択沢琢単嘆担胆団壇弾断痴遅昼虫鋳猪著庁徴懲聴勅鎮塚禎逓鉄転点伝都党島盗灯当祷闘闘徳独読突届縄難弐妊祢粘悩脳覇廃拝杯梅売麦発髪抜繁飯晩蛮卑碑秘桧浜賓頻敏瓶富侮福払仏併塀並変辺辺勉弁弁弁舗歩穂宝峰萌褒豊墨没翻毎槙万満免麺黙餅戻野弥薬訳薮祐予余与誉揺様謡遥欲来頼乱欄覧略隆竜虜両涼猟緑隣塁涙類励礼隷霊齢暦歴恋練錬炉労廊朗楼郎禄録亘湾渕瑶凜閲鎌強呉娯歳産姉尚税説絶痩双脱彦姫"

        Old = "亞惡壓圍爲醫壹逸稻飮隱羽營榮衞益驛悅謁圓薗緣艷鹽奧應橫歐毆鷗黃溫穩假價禍畫會囘壞悔懷海繪慨槪擴殼覺學嶽樂喝渴褐勸卷寬歡漢罐觀閒關陷館巖顏器既歸氣祈龜僞戲犧卻糺舊據擧虛峽挾敎狹鄕響堯曉勤謹區驅駈勳薰羣徑惠揭攜溪經繼莖螢輕鷄藝擊缺儉劵劍圈檢權獻硏縣險顯驗嚴效廣恆晄鑛髙號國穀黑濟碎齋劑冱﨑櫻册殺雜參慘棧蠶贊殘祉絲視飼齒兒辭濕實舍寫煮社者釋壽收臭從澁獸縱祝肅處暑渚緖署諸敍奬將牀涉燒祥稱證乘剩壤孃條淨狀疊穰讓釀囑觸寢愼晉眞神刄盡圖粹醉隨髓數樞瀨晴淸精聲靑靜齊蹟攝竊節專戰淺潛纖踐錢禪曾祖僧雙壯層搜插巢爭瘦窗總聰莊裝騷增憎臟藏贈卽屬續墮體對帶滯臺瀧擇澤琢單嘆擔膽團檀彈斷癡遲晝蟲鑄猪著廳徵懲聽敕鎭塚禎遞鐵轉點傳都黨嶋盜燈當禱鬪鬭德獨讀突屆繩難貳姙禰黏惱腦霸廢拜盃梅賣麥發髮拔繁飯晚蠻卑碑祕檜濱賓頻敏甁冨侮福拂佛倂塀竝變邊邉勉辨辯瓣舖步穗寶峯萠襃豐墨沒飜毎槇萬滿免麵默餠戾埜彌藥譯藪祐豫餘與譽搖樣謠遙慾來賴亂欄覽畧隆龍虜兩凉獵綠鄰壘淚類勵禮隸靈齡曆歷戀練鍊爐勞廊朗樓郞祿錄亙灣淵瑤凛閱鐮强吳娛歲產姊尙稅說絕瘦雙脫彥姬"

        def N2O(text, flag):
            result = ""
            for ch in text:
                found = False
                code = ord(ch)

                if 0x4E00 <= code <= 0x9FFF:
                    for j in range(len(New)):
                        if flag:
                            if ch == New[j]:
                                result += Old[j]
                                found = True
                                break
                        else:
                            if ch == Old[j]:
                                result += New[j]
                                found = True
                                break

                if not found:
                    result += ch

            return result

        if 変換方法.value == "old":
            result = N2O(テキスト, True)
            await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="旧字体に変換しました。", description=result
                ),
            )
        else:
            result = N2O(テキスト, False)
            await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="新字体に変換しました。", description=result
                ),
            )

    @app_commands.command(
        name="parse", description="かっこが閉じられているかを検証します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def text_parse(self, interaction: discord.Interaction, テキスト: str):
        def check_brackets(text):
            mapping = {")": "(", "]": "[", "}": "{"}
            stack = []

            for index, char in enumerate(text, start=1):
                if char in mapping.values():
                    stack.append((char, index))

                elif char in mapping.keys():
                    if not stack:
                        return (
                            f"{index}文字目の '{char}' に対応する開き括弧がありません。",
                            True,
                        )

                    last_bracket, last_index = stack.pop()
                    if last_bracket != mapping[char]:
                        return (
                            f"{index}文字目の '{char}' は、{last_index}文字目の '{last_bracket}' と一致しません。",
                            True,
                        )

            if stack:
                last_bracket, last_index = stack.pop()
                return (
                    f"{last_index}文字目の '{last_bracket}' が閉じられていません。",
                    True,
                )

            return "すべての括弧が正しく閉じられています。", False

        text, is_error = check_brackets(テキスト)

        if is_error:
            embed = make_embed.error_embed(title="検証しました。", description=text)
        else:
            embed = make_embed.success_embed(title="検証しました。", description=text)

        await interaction.response.send_message(ephemeral=True, embed=embed)

    @app_commands.command(name="morse", description="モールス信号に変換します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def morse_convert(self, interaction: discord.Interaction, テキスト: str):
        words = {
            "A": "・－",
            "B": "－・・・",
            "C": "－・－・",
            "D": "－・・",
            "E": "・",
            "F": "・・－・",
            "G": "－－・",
            "H": "・・・・",
            "I": "・・",
            "J": "・－－－",
            "K": "－・－",
            "L": "・－・・",
            "M": "－－",
            "N": "－・",
            "O": "－－－",
            "P": "・－－・",
            "Q": "－－・－",
            "R": "・－・",
            "S": "・・・",
            "T": "－",
            "U": "・・－",
            "V": "・・・－",
            "W": "・－－",
            "X": "－・・－",
            "Y": "－・－－",
            "Z": "－－・・",
        }

        def morse_code_encrypt(st: str):
            try:
                codes = [words[s] for s in st.upper() if s in words]
                return "  ".join(codes)
            except:
                return None

        text = morse_code_encrypt(テキスト)

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="モールス信号に変換しました。",
                description=text
                if text
                else "変換に失敗しました。\n英語にしか対応していません。",
            )
        )


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

class AnimalGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="animal", description="動物系の面白いコマンド")

    @app_commands.command(name="cat", description="ネコの画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def cat(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.thecatapi.com/v1/images/search?size=med&mime_types=jpg&format=json&has_breeds=true&order=RANDOM&page=0&limit=1"
            ) as cat:
                msg = await interaction.response.send_message(
                    embed=make_embed.success_embed(
                        title="猫の画像を生成しました。"
                    ).set_image(url=json.loads(await cat.text())[0]["url"])
                )

    @app_commands.command(name="dog", description="犬の画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dog(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as dog_:
                await interaction.response.send_message(
                    embed=make_embed.success_embed(
                        title="犬の画像を生成しました。"
                    ).set_image(url=f"{json.loads(await dog_.text())['message']}")
                )

    @app_commands.command(name="fox", description="キツネの画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def fox(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomfox.ca/floof/") as dog_:
                await interaction.response.send_message(
                    embed=make_embed.success_embed(
                        title="キツネの画像を生成しました。"
                    ).set_image(url=f"{json.loads(await dog_.text())['image']}")
                )

    @app_commands.command(name="duck", description="アヒルの画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def duck(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://random-d.uk/api/random") as dog_:
                await interaction.response.send_message(
                    embed=make_embed.success_embed(
                        title="アヒルの画像を生成しました。"
                    ).set_image(url=f"{json.loads(await dog_.text())['url']}")
                )

    @app_commands.command(name="lizard", description="トカゲの画像を生成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def lizard(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://nekos.life/api/v2/img/lizard") as lizard:
                await interaction.response.send_message(
                    embed=make_embed.success_embed(
                        title="トカゲの画像を生成しました。"
                    ).set_image(url=f"{json.loads(await lizard.text())['url']}")
                )


class ImageGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="image", description="画像系の面白いコマンド")

    @app_commands.command(name="5000", description="5000兆円ほしい！")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def _5000(
        self,
        interaction: discord.Interaction,
        上: str,
        下: str,
        noアルファ: bool = None,
        虹色にするか: bool = False,
    ):
        await interaction.response.defer()

        def make_5000(up: str, down: str, noa: bool = None, rainbow: bool = False):
            text = f"https://gsapi.cbrx.io/image?top={urllib.parse.quote(up)}&bottom={urllib.parse.quote(down)}"
            if noa:
                text += "&noalpha=true"
            if rainbow:
                text += "&rainbow=true"
            return text

        async with aiohttp.ClientSession() as session:
            async with session.get(
                make_5000(上, 下, noアルファ, 虹色にするか)
            ) as response:
                saved_image = io.BytesIO(await response.read())

                msg = await interaction.followup.send(
                    embed=make_embed.success_embed(title="5000兆円ほしい！").set_image(
                        url="attachment://5000choyen.png"
                    ),
                    file=discord.File(saved_image, "5000choyen.png"),
                )

                saved_image.close()

    @app_commands.command(name="emoji-kitchen", description="絵文字を合体させます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        調理方法=[
            app_commands.Choice(name="合成させる", value="mix"),
            app_commands.Choice(name="重ねる", value="layer"),
        ]
    )
    async def emoji_kitchen(
        self,
        interaction: discord.Interaction,
        unicode絵文字: str,
        unicode絵文字2: str,
        調理方法: app_commands.Choice[str],
    ):
        await interaction.response.defer()
        if 調理方法.value == "layer":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://emojik.vercel.app/s/{urllib.parse.quote(unicode絵文字)}_{urllib.parse.quote(unicode絵文字2)}"
                ) as response:
                    image = await response.read()
                    i = io.BytesIO(image)
                    await interaction.followup.send(
                        embed=make_embed.success_embed(
                            title="絵文字を合成させました。"
                        ).set_image(url="attachment://emoji.png"),
                        file=discord.File(i, filename="emoji.png"),
                    )
                    i.close()
        elif 調理方法.value == "mix":

            def make_emoji_mix():
                img = Image.new(mode="RGBA", size=(500, 500))
                emojI_1 = io.BytesIO(
                    requests.get(
                        f"https://emojicdn.elk.sh/{urllib.parse.quote(unicode絵文字)}"
                    ).content
                )
                emojI_2 = io.BytesIO(
                    requests.get(
                        f"https://emojicdn.elk.sh/{urllib.parse.quote(unicode絵文字2)}"
                    ).content
                )
                img_emoji_1 = Image.open(emojI_1).resize((500, 500))
                img_emoji_2 = Image.open(emojI_2).resize((500, 500))
                img.paste(img_emoji_1)
                img.paste(img_emoji_2, (0, 0, 500, 500), img_emoji_2)
                img_emoji_1.close()
                img_emoji_2.close()
                emojI_1.close()
                emojI_2.close()
                i_ = io.BytesIO()
                img.save(i_, format="png")
                i_.seek(0)
                return i_

            e = await asyncio.to_thread(make_emoji_mix)
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="絵文字を合成させました。"
                ).set_image(url="attachment://emoji.png"),
                file=discord.File(e, filename="emoji.png"),
            )
            e.close()

    @app_commands.command(name="textmoji", description="テキストを絵文字にします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        色=[
            app_commands.Choice(name="赤", value="FF0000"),
            app_commands.Choice(name="青", value="1111FF"),
            app_commands.Choice(name="黄", value="FFFF00"),
            app_commands.Choice(name="緑", value="32A852"),
            app_commands.Choice(name="黒", value="000000"),
        ]
    )
    @app_commands.choices(
        フォント=[
            app_commands.Choice(name="Discordフォント", value="discordfont"),
            app_commands.Choice(name="ガマフォント", value="gamafont"),
            app_commands.Choice(name="クラフト明朝", value="craft"),
            app_commands.Choice(name="Minecraftフォント", value="minecraft"),
        ]
    )
    async def textmoji(
        self,
        interaction: discord.Interaction,
        色: app_commands.Choice[str],
        フォント: app_commands.Choice[str],
        テキスト: str,
        正方形にするか: bool,
    ):
        await interaction.response.defer()

        def make_text(text: str, color: str, sq: bool, font: str):
            if font == "discordfont":
                font = ImageFont.truetype("data/DiscordFont.ttf", 50)
            elif font == "gamafont":
                font = ImageFont.truetype("data/GamaFont.ttf", 50)
            elif font == "craft":
                font = ImageFont.truetype("data/CraftFont.otf", 50)
            elif font == "minecraft":
                font = ImageFont.truetype("data/MinecraftFont.ttf", 50)
            else:
                font = ImageFont.truetype("data/DiscordFont.ttf", 50)

            dummy_img = Image.new("RGBA", (1, 1))
            draw_dummy = ImageDraw.Draw(dummy_img)
            bbox = draw_dummy.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            padding = 0
            img = Image.new(
                "RGBA", (text_w + padding * 2, text_h + padding * 2), (255, 255, 255, 0)
            )
            draw = ImageDraw.Draw(img)

            draw.text(
                (padding - bbox[0], padding - bbox[1]),
                text,
                fill=f"#{color}",
                font=font,
            )

            if sq:
                img = img.resize((200, 200))

            i = io.BytesIO()
            img.save(i, format="PNG")
            i.seek(0)
            return i

        image = await asyncio.to_thread(
            make_text, テキスト, 色.value, 正方形にするか, フォント.value
        )

        if interaction.is_user_integration() and not interaction.is_guild_integration():
            await interaction.followup.send(file=discord.File(image, "emoji.png"))
        else:
            await interaction.followup.send(
                file=discord.File(image, "emoji.png"),
                view=EditImageView(interaction.user),
            )
        image.close()

    @app_commands.command(name="httpcat", description="httpキャットを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def httpcat(self, interaction: discord.Interaction, ステータスコード: int):
        embed = (
            discord.Embed(title="HTTPCat", color=discord.Color.blue())
            .set_image(url=f"https://http.cat/{ステータスコード}")
            .set_footer(text="Httpcat", icon_url="https://i.imgur.com/6mKRXgR.png")
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="httpdog", description="httpドッグを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def httpdog(self, interaction: discord.Interaction, ステータスコード: int):
        embed = (
            discord.Embed(title="HTTPDog", color=discord.Color.blue())
            .set_image(url=f"https://http.dog/{ステータスコード}.jpg")
            .set_footer(text="Httpdog")
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
            app_commands.Choice(name="ピンク", value="pink"),
            app_commands.Choice(name="青", value="blue"),
        ]
    )
    @app_commands.choices(
        タイプ=[
            app_commands.Choice(name="通常", value="normal"),
            app_commands.Choice(name="外交風", value="gaikou"),
        ]
    )
    async def miq(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User,
        発言: str,
        色: app_commands.Choice[str],
        背景色: app_commands.Choice[str],
        タイプ: app_commands.Choice[str],
    ):
        is_blockd = await block.is_blocked_func(
            interaction.client, ユーザー.id, "Miq機能"
        )
        if is_blockd:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのメンバーはMiq機能を\nブロックしています。"
                ),
            )

        await interaction.response.defer()
        if タイプ.value == "gaikou":
            i = io.BytesIO()
            m = await asyncio.to_thread(miq_china.MinistryGenerator)
            image_binary = io.BytesIO()
            now = datetime.datetime.now()
            formatted_date = now.strftime("%Y年%m月%d日")
            await asyncio.to_thread(
                m.generate_image,
                発言.replace("\\n", "\n"),
                ユーザー.display_name,
                formatted_date,
                is_fake=True,
                output=image_binary,
            )
            file = discord.File(fp=image_binary, filename="fake_quote.png")
            await interaction.followup.send(file=file)
            image_binary.close()
            return

        av = ユーザー.avatar if ユーザー.avatar else ユーザー.default_avatar
        av = await av.read()
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
        elif 背景色.value == "pink":
            back = (247, 124, 192)
            text = (0, 0, 0)
        elif 背景色.value == "blue":
            back = (128, 124, 247)
            text = (0, 0, 0)

        pattern = r"<(?:(@!?|#|@&)(\d+))>"

        def replacer(match):
            type_, id_ = match.groups()
            obj_id = int(id_)

            if type_.startswith("@"):
                user = interaction.client.get_user(obj_id)
                return f"@{user.display_name}" if user else "@不明ユーザー"
            elif type_ == "@&":
                role = interaction.guild.get_role(obj_id)
                return f"@{role.name}" if role else "@不明ロール"
            elif type_ == "#":
                channel = interaction.client.get_channel(obj_id)
                return f"#{channel.name}" if channel else "#不明チャンネル"
            return match.group(0)

        content = re.sub(pattern, replacer, 発言)

        miq_ = await miq.make_quote_async(
            ユーザー.display_name, content, av, back, text, color, negapoji, True
        )
        image_binary = io.BytesIO()
        await asyncio.to_thread(miq_.save, image_binary, "PNG")
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename="fake_quote.png")
        await interaction.followup.send(
            file=file
        )
        image_binary.close()
        await quest.quest_clear(interaction, "miq")
        return

    @app_commands.command(name="ascii", description="アスキーアートを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ascii(self, interaction: discord.Interaction, 画像: discord.Attachment):
        await interaction.response.defer()
        rd = await 画像.read()
        io_ = io.BytesIO(rd)
        io_.seek(0)
        text = await asyncio.to_thread(image_to_ascii, io_)
        st = io.StringIO(text)
        await interaction.followup.send(file=discord.File(st, "ascii.txt"))
        st.close()
        io_.close()

    @app_commands.command(name="imgur", description="Imgurで画像を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def imgur(self, interaction: discord.Interaction, 検索ワード: str):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.imgur.com/3/gallery/search",
                    params={"q": 検索ワード},
                    headers={"Authorization": f"Client-ID {settings.IMGUR_CLIENTID}"},
                ) as resp:
                    data = await resp.json()

                    if data and "data" in data:
                        for item in data["data"]:
                            return await interaction.followup.send(f"{item['link']}")

                    return await interaction.followup.send(
                        f"結果が見つかりませんでした。"
                    )
        except:
            return await interaction.followup.send(f"検索に失敗しました。")

    @app_commands.command(name="game", description="ゲームのコラ画像を作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(タイプ=[app_commands.Choice(name="3ds", value="_3ds")])
    async def game_package_image_(
        self,
        interaction: discord.Interaction,
        タイプ: app_commands.Choice[str],
        添付ファイル: discord.Attachment,
    ):
        await interaction.response.defer(ephemeral=True)

        def make_image(type_: str, image: io.BytesIO) -> io.BytesIO:
            if type_ == "3ds":
                with Image.open("data/3ds.jpg") as base, Image.open(image) as im:
                    im = im.resize((772, 774))
                    base.paste(im, (5, 18))
                    output = io.BytesIO()
                    base.save(output, "PNG")
                    output.seek(0)
                    return output
            return image

        img = io.BytesIO(await 添付ファイル.read())
        try:
            image = await asyncio.to_thread(make_image, タイプ.name, img)
            await interaction.followup.send(
                file=discord.File(image, filename=f"{タイプ.name}.png"),
                ephemeral=True,
            )
        finally:
            img.close()
            image.close()
        return

class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> FunCog")

    fun = app_commands.Group(
        name="fun",
        description="面白いコマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    fun.add_command(TextGroup())
    fun.add_command(ImageGroup())
    fun.add_command(AnimalGroup())
    fun.add_command(NounaiGroup())
    fun.add_command(SayGroup())
    fun.add_command(BirthdayGroup())

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not message.guild:
            return

        db = self.bot.async_db["MainTwo"].Hiroyuki

        dbfind = await db.find_one(
            {"Guild": message.guild.id, "Channel": message.channel.id}
        )
        if dbfind is None:
            return

        current_time = time.time()
        last_message_time = cooldown_hiroyuki.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        cooldown_hiroyuki[message.guild.id] = current_time

        try:
            async with aiohttp.ClientSession() as session:
                wh = discord.Webhook.from_url(dbfind.get("WebHook"), session=session)

                if message.clean_content.startswith("miq"):
                    async with message.channel.typing():
                        content = message.clean_content.removeprefix("miq")
                        g_text = await markov.generate_text(HIROYUKI_TEXT, content, 30)
                        async with session.get(
                            "https://dol.ismcdn.jp/mwimgs/d/5/-/img_88f89f52d1e1833ee8de671a178c006544566.jpg"
                        ) as av:
                            miq_ = await miq.make_quote_async(
                                "ひろゆき",
                                g_text,
                                await av.read(),
                                (0, 0, 0),
                                textcolor=(255, 255, 255),
                                color=True,
                                negapoji=False,
                            )
                            i = io.BytesIO()
                            await asyncio.to_thread(miq_.save, i, format="png")
                            i.seek(0)

                            c = 0

                            while True:
                                if c > 8:
                                    return await wh.send(
                                        content="データなんかねーよ",
                                        username="ひろゆき",
                                        avatar_url="https://dol.ismcdn.jp/mwimgs/d/5/-/img_88f89f52d1e1833ee8de671a178c006544566.jpg",
                                    )

                                try:
                                    await wh.send(
                                        content="画像を生成したの見てもらってもいいですか？",
                                        username="ひろゆき",
                                        avatar_url="https://dol.ismcdn.jp/mwimgs/d/5/-/img_88f89f52d1e1833ee8de671a178c006544566.jpg",
                                        file=discord.File(i, filename="miq.png"),
                                    )
                                except aiohttp.ClientOSError:
                                    c += 1
                                    await asyncio.sleep(0.5)
                                    continue
                                break
                            miq_.close()
                            i.close()

                            await message.channel.send(
                                message.author.mention, delete_after=3
                            )

                    return

                ca = random.randint(0, 12)

                async def send_hiroyuki():
                    if ca == 11:
                        await wh.send(
                            content=await markov.generate_text(
                                HIROYUKI_TEXT, message.clean_content[:50], 100
                            ),
                            username="パワー系ひろゆき",
                            avatar_url="https://assets.st-note.com/production/uploads/images/152150583/rectangle_large_type_2_8a80ddb83cbc1b260fe6b958986ca4bd.jpeg?width=1280",
                        )
                        return

                    if ca == 10:
                        ishiba_text = random.choice(
                            [
                                f"{message.clean_content[:50]}とは...何か(ﾈｯﾄﾘ",
                                "恥を知れ",
                            ]
                        )
                        await wh.send(
                            content=ishiba_text,
                            username="石破茂",
                            avatar_url="https://ishiba2024.jp/contents/wp-content/uploads/2024/09/profile_77.jpg",
                        )
                        return

                    await wh.send(
                        content=await markov.generate_text(
                            HIROYUKI_TEXT, message.clean_content[:50], 100
                        ),
                        username="ひろゆき",
                        avatar_url="https://dol.ismcdn.jp/mwimgs/d/5/-/img_88f89f52d1e1833ee8de671a178c006544566.jpg",
                    )

                r = random.randint(0, 2)

                if r == 0:
                    await send_hiroyuki()
                else:
                    for _ in range(0, r):
                        await send_hiroyuki()
                        await asyncio.sleep(1)

        except Exception as e:
            await db.delete_one({"Guild": message.guild.id})
            return await message.channel.send(
                embed=make_embed.error_embed(
                    title="ひろゆきが消滅してしまいました。",
                    description="消滅したため登録を解除しました。",
                ).add_field(name="エラーコード", value=f"```{e}```", inline=False)
            )

    @fun.command(name="hiroyuki", description="ひろゆきを召喚します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def hiroyuki(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="テキストチャンネルでのみ召喚できます。"
                ),
            )

        await interaction.response.defer()

        db = interaction.client.async_db["MainTwo"].Hiroyuki

        dbfind = await db.find_one({"Guild": interaction.guild.id})
        if dbfind is None:
            wh = await interaction.channel.create_webhook(name="ひろゆき")
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Channel": interaction.channel.id, "WebHook": wh.url}},
                upsert=True,
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="ひろゆきを召喚しました。")
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.followup.send(
                embed=make_embed.success_embed(title="ひろゆきを退出させました。")
            )

    @fun.command(name="ranking", description="様々なランキングを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ランキングの種類=[
            app_commands.Choice(name="Top.ggのVoteランキング", value="vote")
        ]
    )
    async def ranking(
        self,
        interaction: discord.Interaction,
        ランキングの種類: app_commands.Choice[str],
    ):
        await interaction.response.defer()

        if ランキングの種類.value == "vote":
            db = interaction.client.async_db["Main"]["TOPGGVote"]
            top_users = await db.find().sort("count", -1).limit(15).to_list(length=15)
            if len(top_users) == 0:
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="TOPGGVote回数",
                        description="まだTopggでVoteされていません。",
                    )
                )
                return
            ranking_message = ""
            for index, user_data in enumerate(top_users, start=1):
                user_id = user_data["_id"]
                delete_count = user_data["count"]
                member = self.bot.get_user(user_id)
                username = (
                    f"{member.display_name} ({user_id})"
                    if member
                    else f"Unknown ({user_id})"
                )
                ranking_message += f"{index}. **{username}** - {delete_count} 回\n"

            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="TOPGGVote回数", description=ranking_message
                )
            )

    @fun.command(name="janken", description="じゃんけんをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def janken(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
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

            @discord.ui.button(
                label="ぐー", style=discord.ButtonStyle.blurple, emoji="🪨"
            )
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

            @discord.ui.button(
                label="ちょき", style=discord.ButtonStyle.blurple, emoji="✂️"
            )
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

            @discord.ui.button(
                label="ぱー", style=discord.ButtonStyle.blurple, emoji="📜"
            )
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
