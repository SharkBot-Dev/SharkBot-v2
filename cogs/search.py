import asyncio
from functools import partial
import json
import re
import ssl
from urllib.parse import urlparse
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
import datetime

import requests
from discord import app_commands
from models import command_disable, make_embed, web_translate, pages

import pytesseract
from PIL import Image
import io

DISCORD_EPOCH = 1420070400000


def decode_snowflake(snowflake: int):
    timestamp = ((snowflake >> 22) + DISCORD_EPOCH) / 1000
    dt = datetime.datetime.utcfromtimestamp(timestamp)

    worker_id = (snowflake & 0x3E0000) >> 17
    process_id = (snowflake & 0x1F000) >> 12
    increment = snowflake & 0xFFF

    return {
        "timestamp": dt,
        "worker_id": worker_id,
        "process_id": process_id,
        "increment": increment,
    }


async def ocr_async(image_: io.BytesIO):
    image = await asyncio.to_thread(Image.open, image_)

    text = await asyncio.to_thread(pytesseract.image_to_string, image)

    return text


STATUS_EMOJIS = {
    discord.Status.online: "<:online:1407922300535181423>",
    discord.Status.idle: "<:idle:1407922295711727729>",
    discord.Status.dnd: "<:dnd:1407922294130741348>",
    discord.Status.offline: "<:offline:1407922298563854496>",
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

EMOJI_RE = re.compile(r"(<a?:(\w+):(\d+?)>)")


def extract_discord_emoji_info(text):
    matches = EMOJI_RE.findall(text)

    results = []
    for full_emoji, name, emoji_id in matches:
        is_animated = full_emoji.startswith("<a:")

        results.append((name, emoji_id, is_animated))

    return results


class NomTranslater:
    def __init__(self):
        self.se = requests.Session()
        self.index = self.se.get("https://racing-lagoon.info/nomu/translate.php").text
        self.bs = BeautifulSoup(self.index, "html.parser")
        self.token = self.bs.find({"input": {"name": "token"}})["value"]

    def translare(self, text: str):
        data = {
            "token": self.token,
            "before": text,
            "level": "2",
            "options": "nochk",
            "transbtn": "翻訳",
            "after1": "",
            "options_permanent": "",
            "new_japanese": "",
            "new_nomulish": "",
            "new_setugo": "",
            "setugo": "settou",
        }

        nom_index = self.se.post(
            "https://racing-lagoon.info/nomu/translate.php", data=data
        )

        bs = BeautifulSoup(nom_index.text, "html.parser")

        return bs.find_all(
            {"textarea": {"class": "maxfield outputfield form-control selectAll"}}
        )[1].get_text()


class WebGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="web", description="Webから検索します。")

    @app_commands.command(name="translate", description="翻訳をします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        翻訳先=[
            app_commands.Choice(name="日本語へ", value="ja"),
            app_commands.Choice(name="英語へ", value="en"),
            app_commands.Choice(name="中国語へ", value="zh-CN"),
            app_commands.Choice(name="韓国語へ", value="ko"),
            app_commands.Choice(name="ロシア語へ", value="ru"),
            app_commands.Choice(name="ノムリッシュ語へ", value="nom"),
            app_commands.Choice(name="ルーン文字へ", value="rune"),
        ]
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        翻訳先: app_commands.Choice[str],
        テキスト: str = None,
        画像: discord.Attachment = None,
    ):
        await interaction.response.defer()

        if テキスト:
            if 翻訳先.value == "nom":
                loop = asyncio.get_running_loop()
                nom = await loop.run_in_executor(None, partial(NomTranslater))
                text = await loop.run_in_executor(
                    None, partial(nom.translare, テキスト)
                )

                embed = make_embed.success_embed(
                    title="翻訳 (ノムリッシュ語へ)", description=f"```{text}```"
                )
                await interaction.followup.send(embed=embed)
                return

            if 翻訳先.value == "rune":
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api-ryo001339.onrender.com/rune/{urllib.parse.quote(テキスト)}",
                        ssl=ssl_context,
                    ) as response:
                        js = await response.json()
                        embed = make_embed.success_embed(
                            title="ルーン文字へ",
                            description=f"```{js.get('transformatedText', '？？？')}```",
                        )
                        await interaction.followup.send(embed=embed)
                        return

            try:
                translated_text = await web_translate.translate(web_translate.targetToSource(翻訳先.value), 翻訳先.value, テキスト)

                embed = make_embed.success_embed(
                    title=f"翻訳 ({翻訳先.value} へ)",
                    description=f"```{translated_text.get('text')}```",
                )
                await interaction.followup.send(embed=embed)

            except Exception:
                embed = make_embed.error_embed(
                    title="翻訳に失敗しました",
                    description="指定された言語コードが正しいか確認してください。",
                )
                await interaction.followup.send(embed=embed)
        else:
            if not 画像:
                return await interaction.followup.send(
                    content="テキストか画像、どちらかを指定してください。"
                )
            if not 画像.filename.endswith((".png", ".jpg", ".jpeg")):
                return await interaction.followup.send(
                    content="`.png`と`.jpg`のみ対応しています。"
                )
            i = io.BytesIO(await 画像.read())
            text_ocrd = await ocr_async(i)
            i.close()

            if text_ocrd == "":
                return await interaction.followup.send(
                    content="画像にはテキストがありません。"
                )

            if 翻訳先.value == "nom":
                loop = asyncio.get_running_loop()
                nom = await loop.run_in_executor(None, partial(NomTranslater))
                text = await loop.run_in_executor(
                    None, partial(nom.translare, text_ocrd)
                )

                embed = make_embed.success_embed(
                    title="翻訳 (ノムリッシュ語へ)", description=f"```{text}```"
                )
                await interaction.followup.send(embed=embed)
                return

            if 翻訳先.value == "rune":
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"https://api-ryo001339.onrender.com/rune/{urllib.parse.quote(text_ocrd)}",
                        ssl=ssl_context,
                    ) as response:
                        js = await response.json()
                        embed = make_embed.success_embed(
                            title="ルーン文字へ",
                            description=f"```{js.get('transformatedText', '？？？')}```",
                        )
                        await interaction.followup.send(embed=embed)
                        return

            try:
                translated_text = await web_translate.translate(web_translate.targetToSource(翻訳先.value), 翻訳先.value, text_ocrd)

                embed = make_embed.success_embed(
                    title=f"翻訳 ({翻訳先.value} へ)",
                    description=f"```{translated_text.get('text')}```",
                )
                await interaction.followup.send(embed=embed)

            except Exception as e:
                embed = make_embed.error_embed(
                    title="翻訳に失敗しました"
                )
                await interaction.followup.send(embed=embed)

    @app_commands.command(name="news", description="ニュースを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def news(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://mainichi.jp/", ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                title = soup.find_all("div", class_="toppickup")[0]
                url = title.find_all("a")[0]
                await interaction.followup.send(f"https:{url['href']}")

    @app_commands.command(
        name="wikipedia", description="ウィキペディアから取得します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def wikipedia(self, interaction: discord.Interaction, 検索ワード: str):
        await interaction.response.defer()

        encoded = urllib.parse.quote(検索ワード)
        wikipedia_api_url = (
            f"https://ja.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        )

        headers = {"User-Agent": "DiscordBot/1.0 (https://example.com)"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(wikipedia_api_url, headers=headers) as resp:
                    if resp.status == 404:
                        await interaction.followup.send(
                            "Wikipedia記事が見つかりませんでした。"
                        )
                        return

                    resp.raise_for_status()
                    data = await resp.json()

            page_url = data.get("content_urls", {}).get("desktop", {}).get("page")
            extract = data.get("extract", None)
            title = data.get("title", 検索ワード)

            if not page_url:
                await interaction.followup.send("Wikipedia記事が見つかりませんでした。")
                return

            if data.get("type") == "disambiguation":
                embed = make_embed.success_embed(
                    title="曖昧な検索語です。",
                    description=extract
                    if extract
                    else "以下のボタンのページを確認してください。",
                )

                view = discord.ui.View()
                view.add_item(discord.ui.Button(label="アクセスする", url=page_url))

                await interaction.followup.send(embed=embed, view=view)
                return

            embed = make_embed.success_embed(
                title=title, description=extract if extract else "説明文がありません。"
            )

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="アクセスする", url=page_url))

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: `{e}`")

    @app_commands.command(name="safeweb", description="サイトの安全性を調べます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def safeweb(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://findredirect.com/api/redirects", json={"url": url}
            ) as response_expand:
                js_short = await response_expand.json()

        async with aiohttp.ClientSession() as session_safeweb:
            if not js_short[0].get("redirect", False):
                q = urlparse(url).netloc
                async with session_safeweb.get(
                    f"https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0",
                    ssl=ssl_context,
                ) as response:
                    js = json.loads(await response.text())
                    if js["rating"] == "b":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは危険です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.red(),
                            )
                        )
                    elif js["rating"] == "w":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは注意が必要です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.yellow(),
                            )
                        )
                    elif js["rating"] == "g":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは評価されていません。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.blue(),
                            )
                        )
                    else:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは多分安全です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.green(),
                            )
                        )
            else:
                q = urlparse(js_short[0].get("redirect", False)).netloc
                async with session_safeweb.get(
                    f"https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0",
                    ssl=ssl_context,
                ) as response:
                    js = json.loads(await response.text())
                    if js["rating"] == "b":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは危険です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.red(),
                            )
                        )
                    elif js["rating"] == "w":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは注意が必要です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.yellow(),
                            )
                        )
                    elif js["rating"] == "g":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは評価されていません。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.blue(),
                            )
                        )
                    else:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは多分安全です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.green(),
                            )
                        )

    @app_commands.command(name="anime", description="アニメを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def anime(self, interaction: discord.Interaction, タイトル: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://kitsu.io/api/edge/anime?filter[text]={タイトル}"
            ) as response:
                js = await response.json()
                datas = js["data"]
                if datas == []:
                    return await interaction.followup.send(
                        embed=make_embed.error_embed(
                            title="見つかりませんでした",
                            description="別のタイトルで試してください。",
                        )
                    )
                anime = datas[0]
                info = anime["attributes"]
                titlename = info["titles"]["ja_jp"]
                posterImage = info["posterImage"]["medium"]
                description = info["description"]
                loop = asyncio.get_running_loop()
                translator = await loop.run_in_executor(
                    None, partial(GoogleTranslator, source="auto", target="ja")
                )
                translated_text = await loop.run_in_executor(
                    None, partial(translator.translate, description)
                )
                await interaction.followup.send(
                    embed=make_embed.success_embed(title="アニメの検索結果")
                    .add_field(name="タイトル", value=titlename, inline=False)
                    .add_field(name="説明", value=translated_text, inline=False)
                    .set_image(url=posterImage)
                )

    @app_commands.command(name="discord", description="Discordのステータスやバグ情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def discord_status_search_web(self, interaction: discord.Interaction):

        await interaction.response.defer()

        status_url = "https://discordstatus.com/api/v2/status.json"
        incidents_url = "https://discordstatus.com/api/v2/incidents/unresolved.json"

        async with aiohttp.ClientSession() as session:

            async with session.get(status_url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(embed=make_embed.error_embed(title="ステータスAPIにアクセスできませんでした。"))
                status_data = await resp.json()

            async with session.get(incidents_url) as resp2:
                if resp2.status != 200:
                    return await interaction.followup.send(embed=make_embed.error_embed(title="障害情報APIにアクセスできませんでした。"))
                incidents_data = await resp2.json()

        embed_resp = make_embed.success_embed(title="Discordのステータスを取得しました。", description="以下がステータス情報です。")

        indicator = status_data["status"]["indicator"]
        description = status_data["status"]["description"]

        color = (
            discord.Color.green() if indicator == "none" else
            discord.Color.orange() if indicator in ["minor", "major"] else
            discord.Color.red()
        )

        embed = discord.Embed(
            title="📡 Discord Status",
            description=description,
            color=color
        )
        embed.add_field(name="レベル", value=indicator)

        incidents = incidents_data.get("incidents", [])

        if len(incidents) == 0:
            embed.add_field(
                name="🟢 現在の障害",
                value="現在発生中の障害はありません。",
                inline=False
            )
        else:
            text = ""
            for inc in incidents:
                name = inc["name"]
                impact = inc["impact"]
                updates = inc["incident_updates"]
                latest_update = updates[0]["body"] if updates else "更新情報なし"

                text += f"● **{name}**（影響度: `{impact}`）\n{latest_update}\n\n"

            embed.add_field(
                name="🔴 発生中の障害",
                value=text,
                inline=False
            )

        embed.set_footer(text="ソース: discordstatus.com")

        await interaction.followup.send(embeds=[embed_resp, embed])

    @app_commands.command(name="iss", description="国際宇宙ステーションの位置を検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def iss_search_web(self, interaction: discord.Interaction):
        await interaction.response.defer()

        url = "http://api.open-notify.org/iss-now.json"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(embed=make_embed.error_embed(title="取得に失敗しました。", description="しばらく待ってから再度お試しください。"))

                data = await resp.json()

        position = data["iss_position"]
        latitude = position["latitude"]
        longitude = position["longitude"]

        embed = make_embed.success_embed(
            title="国際宇宙ステーション 現在位置"
        )
        embed.add_field(name="緯度 (Latitude)", value=latitude, inline=True)
        embed.add_field(name="経度 (Longitude)", value=longitude, inline=True)

        embed.add_field(
            name="地図リンク",
            value=f"https://www.google.com/maps?q={latitude},{longitude}",
            inline=False
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="note", description="note.comの記事の検索をします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def note_search_web(self, interaction: discord.Interaction, 検索ワード: str):
        await interaction.response.defer()

        url = f"https://note.com/api/v3/searches?context=note&mode=typeahead&q={urllib.parse.quote(検索ワード)}"

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ja,en-US;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return await interaction.followup.send(embed=make_embed.error_embed(title="取得に失敗しました。", description="しばらく待ってから再度お試しください。"))

                data = await resp.json()

        data = data["data"]
        notes = data["notes"]
        contents = notes["contents"]

        if not contents:
            return await interaction.followup.send(embed=make_embed.error_embed(title="取得に失敗しました。", description="その検索ワードからは何も得られませんでした。"))
        
        note = contents[0]

        embed = make_embed.success_embed(title=note["name"])
        embed.title = note["name"]

        if note.get('publish_at'):
            embed.add_field(name="作成日", value=note.get('publish_at'), inline=False)
        if note.get('eyecatch'):
            embed.set_image(url=note.get('eyecatch'))
        if note.get('user'):
            user = note.get('user')
            name = user["name"]
            user_profile_image_path = user.get('user_profile_image_path')
            if user_profile_image_path:
                embed.set_author(name=name, icon_url=user_profile_image_path)
            else:
                embed.set_author(name=name)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="アクセスする", url=f"https://note.com/nobisiro_2023/n/{note['key']}"))

        await interaction.followup.send(embed=embed, view=view)

class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> SearchCog")

    async def get_user_savedata(self, user: discord.User):
        db = self.bot.async_db["Main"].LoginData
        try:
            dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind

    async def get_user_point(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        return dbfind["count"]

    async def get_user_tag_(self, user: discord.User):
        db = self.bot.async_db["Main"].UserTag
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return "称号なし"
        if dbfind is None:
            return "称号なし"
        return dbfind["Tag"]

    async def get_user_color(self, user: discord.User):
        db = self.bot.async_db["Main"].UserColor
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return discord.Color.green()
        if dbfind is None:
            return discord.Color.green()
        if dbfind["Color"] == "red":
            return discord.Color.red()
        elif dbfind["Color"] == "yellow":
            return discord.Color.yellow()
        elif dbfind["Color"] == "blue":
            return discord.Color.blue()
        elif dbfind["Color"] == "random":
            return discord.Color.random()
        return discord.Color.green()

    async def get_connect_data(self, user: discord.User):
        db = self.bot.async_db["Main"].LoginConnectData
        try:
            dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
        except:
            return {"Youtube": "取得できません。", "Twitter": "取得できません。"}
        if dbfind is None:
            return {"Youtube": "取得できません。", "Twitter": "取得できません。"}
        return {"Youtube": dbfind["youtube"], "Twitter": dbfind["X"]}

    async def gold_user_data(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotGoldPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        try:
            return dbfind.get("count", 0)
        except:
            return 0

    async def pfact_user_data(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotPointFactory
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        try:
            return dbfind.get("count", 0)
        except:
            return 0

    async def get_bot_adder_from_audit_log(
        self, guild: discord.Guild, bot_user: discord.User
    ):
        if not bot_user.bot:
            return "Botではありません。"
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.bot_add, limit=None
            ):
                if entry.target == bot_user:
                    return f"{entry.user.display_name} ({entry.user.id})"
            return "取得失敗しました"
        except discord.Forbidden:
            return "監査ログを閲覧する権限がありません。"
        except Exception as e:
            return f"監査ログの確認中にエラーが発生しました: {e}"

    async def roles_get(self, guild: discord.Guild, user: discord.User):
        try:
            mem = await guild.fetch_member(user.id)
            return "**ロール一覧**: " + " ".join([f"{r.mention}" for r in mem.roles])
        except:
            return "**ロール一覧**: このサーバーにいません。"

    search = app_commands.Group(
        name="search",
        description="検索系コマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    search.add_command(WebGroup())

    @search.command(name="multi", description="様々な情報を一括で検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def multi_search(self, interaction: discord.Interaction, 名前かid: str):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="検索中です..", description="しばらくお待ちください。"
            ),
            ephemeral=True,
        )

        await asyncio.sleep(1)

        guild = interaction.guild
        members = guild.members
        emojis = guild.emojis
        if interaction.user.guild_permissions.administrator:
            channels = guild.channels
            roles = guild.roles
        else:
            channels = []
            roles = []

        members_searched = []
        emojis_searched = []
        channels_searched = []
        roles_searched = []

        for m in members:
            if 名前かid in m.name:
                members_searched.append(f"{m.name} ({m.id})")
                continue
            if 名前かid in m.display_name:
                members_searched.append(f"{m.name} ({m.id})")
                continue
            if 名前かid == str(m.id):
                members_searched.append(f"{m.name} ({m.id})")
                continue

        for em in emojis:
            if 名前かid in em.name:
                emojis_searched.append(em.__str__())
                continue
            if 名前かid in str(em.id):
                emojis_searched.append(em.__str__())
                continue

        if interaction.user.guild_permissions.administrator:
            for ch in channels:
                if 名前かid in ch.name:
                    channels_searched.append(f"{ch.name} ({ch.id})")
                    continue
                if 名前かid in str(ch.id):
                    channels_searched.append(f"{ch.name} ({ch.id})")
                    continue

            for r in roles:
                if 名前かid in r.name:
                    roles_searched.append(f"{r.name} ({r.id})")
                    continue
                if 名前かid in str(r.id):
                    roles_searched.append(f"{r.name} ({r.id})")
                    continue

        text_member = "\n".join(members_searched)
        text_member = text_member if text_member else "なし"

        text_emoji = "\n".join(emojis_searched)
        text_emoji = text_emoji if text_emoji else "なし"
        if interaction.user.guild_permissions.administrator:
            text_channels = "\n".join(channels_searched)
            text_channels = text_channels if text_channels else "なし"

            text_roles = "\n".join(roles_searched)
            text_roles = text_roles if text_roles else "なし"

        embed = make_embed.success_embed(title="検索結果です。")
        embed.add_field(name="メンバー", value=text_member, inline=False)

        if interaction.user.guild_permissions.administrator:
            embed.add_field(name="チャンネル", value=text_channels, inline=False)
            embed.add_field(name="ロール", value=text_roles, inline=False)

        embed.add_field(name="絵文字", value=text_emoji, inline=False)
        await interaction.edit_original_response(embed=embed)

    @search.command(
        name="tag", description="サーバータグを何人がつけているかを検索します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def tag_search(self, interaction: discord.Interaction, サーバータグ名: str):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="検索中です..", description="しばらくお待ちください。"
            )
        )

        await asyncio.sleep(1)

        count = 0
        tag_member = []

        members = interaction.guild.members
        for m in members:
            if m.primary_guild.tag == サーバータグ名:
                count += 1
                tag_member.append(m.name + f" ({m.id})")

        embed = make_embed.success_embed(title="サーバータグを検索しました。")
        embed.add_field(
            name="何人がつけているか", value=str(count) + "人", inline=False
        )
        embed.add_field(
            name="誰がつけているか (20人まで)", value="\n".join(tag_member[:20])
        )

        await interaction.edit_original_response(embed=embed)

    @search.command(name="user", description="ユーザーを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def user_search(self, interaction: discord.Interaction, user: discord.User):
        await interaction.response.defer()
        JST = datetime.timezone(datetime.timedelta(hours=9))
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            embed = make_embed.success_embed(title=f"{user.display_name}の情報")

            if user.bot:
                isbot = "はい"
            else:
                isbot = "いいえ"

            embed.add_field(
                name="基本情報",
                value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nBot？: **{isbot}**\n認証Bot？: **{'はい' if user.public_flags.verified_bot else 'いいえ'}**",
            )

            embed.set_thumbnail(
                url=user.avatar.url if user.avatar else user.default_avatar.url
            )

            await interaction.followup.send(embed=embed)

            return

        try:
            isguild = None
            isbot = None
            if interaction.guild.get_member(user.id):
                isguild = "います。"
            else:
                isguild = "いません。"
            if user.bot:
                isbot = "はい"
            else:
                isbot = "いいえ"
            permissions = "ユーザー"
            try:
                if (
                    self.bot.get_guild(1343124570131009579).get_role(
                        1344470846995169310
                    )
                    in self.bot.get_guild(1343124570131009579).get_member(user.id).roles
                ):
                    permissions = "モデレーター"
                if user.id == 1335428061541437531:
                    permissions = "管理者"
                if user.id == 1346643900395159572:
                    permissions = "SharkBot"
            except:
                pass
            embed = make_embed.success_embed(
                title=f"{user.display_name}の情報 (ページ1)"
            )
            embed.add_field(
                name="基本情報",
                value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**\n認証Bot？: **{'はい' if user.public_flags.verified_bot else 'いいえ'}**",
            ).add_field(name="サービス情報", value=f"権限: **{permissions}**")
            if not user.bot:
                p_g = user.primary_guild
                if p_g != None:
                    t_name = p_g.tag
                else:
                    t_name = "なし"
            else:
                t_name = "なし"

            if interaction.guild.get_member(user.id):
                mem_status = interaction.guild.get_member(user.id)

                text = ""

                emoji = STATUS_EMOJIS.get(mem_status.status, "❔")

                text += f"ステータス: {emoji} ({mem_status.status})\n"

                text += (
                    f"スマホか？: {'はい' if mem_status.is_on_mobile() else 'いいえ'}\n"
                )

                if mem_status.activity and isinstance(
                    mem_status.activity, discord.CustomActivity
                ):
                    custom_status = mem_status.activity.name
                    if mem_status.activity.emoji:
                        text += f"カスタムステータス: {mem_status.activity.emoji} {custom_status}\n"
                    else:
                        text += f"カスタムステータス: {custom_status}\n"

                embed.add_field(name="ステータス情報", value=text, inline=False)
            embed.add_field(
                name="その他のAPIからの情報",
                value=f"""
スパムアカウントか？: {"✅" if user.public_flags.spammer else "❌"}
HypeSquadEventsメンバーか？: {"✅" if user.public_flags.hypesquad else "❌"}
早期チームユーザーか？: {"✅" if user.public_flags.team_user else "❌"}
サーバータグ: {t_name}
""",
                inline=False,
            )
            bag = ""
            if user.public_flags.active_developer:
                bag += "<:developer:1399747643260797091> "
            if user.public_flags.staff:
                bag += "<:staff:1399747719186088036> "
            if user.public_flags.partner:
                bag += "<:part:1399748417999077557> "
            if user.public_flags.bug_hunter:
                bag += "<:bag1:1399748326395478196> "
            if user.public_flags.bug_hunter_level_2:
                bag += "<:bag2:1399748401096294441> "
            if user.public_flags.verified_bot_developer:
                bag += "<:soukidev:1399748801220317225> "
            if user.public_flags.discord_certified_moderator:
                bag += "<:mod:1399749105248370728> "
            if user.public_flags.system:
                bag += "<:discord_icon:1399750113156403281> "
            if user.public_flags.early_supporter:
                bag += "<:fast_support:1399750316660101172> "
            if user.public_flags.hypesquad_bravery:
                bag += "<:HouseofBravery:1422122705964240936> "
            if user.public_flags.hypesquad_brilliance:
                bag += "<:HypeSquadBrilliance:1399751490049933322> "
            if user.public_flags.hypesquad_balance:
                bag += "<:HypeSquadBalance:1399751701669478511> "
            if bag != "":
                embed.add_field(name="バッジ", value=bag, inline=False)
            embed.set_image(url=user.banner.url if user.banner else None)
            roles = await self.roles_get(interaction.guild, user)
            embed2 = make_embed.success_embed(
                title=f"{user.display_name}の情報 (ページ2)",
                description=roles,
            )
            
            pages_view = [embed, embed2]
            view = pages.Pages(embeds=pages_view, now_page=0, page_owner=interaction.user)

            if user.avatar:
                await interaction.followup.send(
                    embed=embed.set_thumbnail(url=user.avatar.url), view=view
                )
            else:
                await interaction.followup.send(
                    embed=embed.set_thumbnail(url=user.default_avatar.url), view=view
                )
        except:
            return

    @search.command(name="server", description="サーバー情報を確認します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def server_info(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.defer()
        embed = make_embed.success_embed(title=f"{interaction.guild.name}の情報")
        embed.add_field(name="サーバー名", value=interaction.guild.name)
        embed.add_field(name="サーバーID", value=str(interaction.guild.id))
        embed.add_field(
            name="チャンネル数", value=f"{len(interaction.guild.channels)}個"
        )
        embed.add_field(name="絵文字数", value=f"{len(interaction.guild.emojis)}個")
        embed.add_field(name="ロール数", value=f"{len(interaction.guild.roles)}個")
        embed.add_field(name="ロールリスト", value="`/listing role`\nで見れます。")
        embed.add_field(name="メンバー数", value=f"{interaction.guild.member_count}人")
        embed.add_field(
            name="Nitroブースト",
            value=f"{interaction.guild.premium_subscription_count}人",
        )
        embed.add_field(
            name="オーナー名",
            value=self.bot.get_user(interaction.guild.owner_id).name
            if self.bot.get_user(interaction.guild.owner_id)
            else "取得失敗",
        )
        embed.add_field(name="オーナーID", value=str(interaction.guild.owner_id))
        JST = datetime.timezone(datetime.timedelta(hours=9))
        embed.add_field(
            name="作成日", value=interaction.guild.created_at.astimezone(JST)
        )

        onlines = [
            m for m in interaction.guild.members if m.status == discord.Status.online
        ]
        idles = [
            m for m in interaction.guild.members if m.status == discord.Status.idle
        ]
        dnds = [m for m in interaction.guild.members if m.status == discord.Status.dnd]
        offlines = [
            m for m in interaction.guild.members if m.status == discord.Status.offline
        ]

        pcs = [m for m in interaction.guild.members if m.client_status.desktop]
        sms = [m for m in interaction.guild.members if m.client_status.mobile]
        webs = [m for m in interaction.guild.members if m.client_status.web]

        embed.add_field(
            name="ステータス情報",
            value=f"""
<:online:1407922300535181423> {len(onlines)}人
<:idle:1407922295711727729> {len(idles)}人
<:dnd:1407922294130741348> {len(dnds)}人
<:offline:1407922298563854496> {len(offlines)}人
💻 {len(pcs)}人
📱 {len(sms)}人
🌐 {len(webs)}人
""",
            inline=False,
        )

        embed.add_field(
            name="Botからの情報", value=f"Shard番号: {interaction.guild.shard_id}番"
        )

        if interaction.guild.icon:
            await interaction.followup.send(
                embed=embed.set_thumbnail(url=interaction.guild.icon.url)
            )
        else:
            await interaction.followup.send(embed=embed)

    @search.command(name="channel", description="チャンネルを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def channel_search(
        self, interaction: discord.Interaction, チャンネルid: str = None
    ):
        JST = datetime.timezone(datetime.timedelta(hours=9))

        if チャンネルid:
            if (
                interaction.is_user_integration()
                and not interaction.is_guild_integration()
            ):
                return await interaction.response.send_message(
                    ephemeral=True,
                    embed=make_embed.error_embed(
                        title="このコマンドは使用できません。",
                        description="サーバーにBotをインストールして使用してください。",
                    ),
                )

            if not interaction.user.guild_permissions.manage_channels:
                return await interaction.response.send_message(
                    ephemeral=True,
                    embed=make_embed.error_embed(
                        title="コマンドを実行する権限がありません！",
                        description=f"不足している権限: チャンネルの管理",
                    ),
                )

            await interaction.response.defer()

            try:
                channel = await interaction.guild.fetch_channel(int(チャンネルid))
            except discord.InvalidData:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="チャンネルが存在しません。",
                        description="別サーバーにある場合も取得できません。",
                    )
                )
            except ValueError:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="無効なチャンネルidです。",
                        description="チャンネルidは数字である必要があります。",
                    )
                )

            embed = make_embed.success_embed(title="チャンネルの情報")
            embed.add_field(name="名前", value=channel.name, inline=False)
            embed.add_field(name="ID", value=str(channel.id), inline=False)

            embed.add_field(
                name="作成日",
                value=str(channel.created_at.astimezone(JST)),
                inline=False,
            )

            if channel.category:
                embed.add_field(
                    name="カテゴリ", value=channel.category.name, inline=False
                )
            else:
                embed.add_field(name="カテゴリ", value="なし", inline=False)
            embed.add_field(name="位置", value=str(channel.position), inline=False)
            embed.add_field(name="メンション", value=channel.mention, inline=False)
            embed.set_footer(text=f"{channel.guild.name} / {channel.guild.id}")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.defer()

            channel = interaction.channel

            embed = make_embed.success_embed(title="チャンネルの情報")
            embed.add_field(name="名前", value=channel.name, inline=False)
            embed.add_field(name="ID", value=str(channel.id), inline=False)

            embed.add_field(
                name="作成日",
                value=str(channel.created_at.astimezone(JST)),
                inline=False,
            )

            if channel.category:
                embed.add_field(
                    name="カテゴリ", value=channel.category.name, inline=False
                )
            else:
                embed.add_field(name="カテゴリ", value="なし", inline=False)
            embed.add_field(name="位置", value=str(channel.position), inline=False)
            embed.add_field(name="メンション", value=channel.mention, inline=False)
            embed.set_footer(text=f"{channel.guild.name} / {channel.guild.id}")
            await interaction.followup.send(embed=embed)

    async def get_ban_user_from_audit_log(
        self, guild: discord.Guild, user: discord.User
    ):
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.ban, limit=None
            ):
                if entry.target.id == user.id:
                    return f"{entry.user.display_name} ({entry.user.id})"
            return "取得失敗しました"
        except discord.Forbidden:
            return "監査ログを閲覧する権限がありません。"
        except Exception as e:
            return f"監査ログの確認中にエラーが発生しました"

    @search.command(name="ban", description="banされたメンバーを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_info(self, interaction: discord.Interaction, ユーザー: discord.User):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.defer()
        try:
            ban_user = await interaction.guild.fetch_ban(ユーザー)
            embed = make_embed.success_embed(title="BANされたユーザーの情報")
            embed.add_field(
                name="ユーザー名",
                value=f"{ban_user.user.display_name} ({ban_user.user.id})",
                inline=False,
            )
            embed.add_field(
                name="ユーザーid", value=f"{ban_user.user.id}", inline=False
            )
            embed.add_field(
                name="BANされた理由",
                value=ban_user.reason if ban_user.reason else "理由なし",
            )
            User = await self.get_ban_user_from_audit_log(interaction.guild, ユーザー)
            embed.add_field(name="BANした人", value=User, inline=False)
            embed.set_thumbnail(
                url=ban_user.user.avatar.url
                if ban_user.user.avatar
                else ban_user.user.default_avatar.url
            )
            embed.set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}")
            await interaction.followup.send(embed=embed)
        except discord.NotFound:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="その人はBANされていません。", color=discord.Color.red()
                )
            )

    async def get_bot_inviter(self, guild: discord.Guild, user: discord.User):
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.bot_add, limit=100
            ):
                if entry.target.id == user.id:
                    JST = datetime.timezone(datetime.timedelta(hours=9))
                    return (
                        f"{entry.user.display_name} ({entry.user.id})",
                        f"{entry.created_at.astimezone(JST)}",
                    )
            return "取得失敗しました", "取得失敗しました"
        except discord.Forbidden:
            return (
                "監査ログを閲覧する権限がありません。",
                "監査ログを閲覧する権限がありません。",
            )
        except Exception as e:
            return (
                f"監査ログの確認中にエラーが発生しました",
                "監査ログの確認中にエラーが発生しました",
            )

    @search.command(name="bot", description="導入されたbotを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def bot_info(self, interaction: discord.Interaction, bot: discord.User):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        if not bot.bot:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="その人はBotはありません。",
                    description="Botを指定してください。",
                ),
            )

        await interaction.response.defer()
        embed = make_embed.success_embed(title="Botの情報")
        embed.add_field(name="Bot名", value=bot.display_name, inline=False)
        embed.add_field(name="ユーザーid", value=f"{bot.id}", inline=False)
        bot_inv, time = await self.get_bot_inviter(interaction.guild, bot)
        embed.add_field(name="Botを入れた人", value=bot_inv, inline=False)
        embed.add_field(name="Botが入れられた時間", value=time, inline=False)
        embed.set_thumbnail(
            url=bot.avatar.url if bot.avatar else bot.default_avatar.url
        )
        embed.set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}")
        await interaction.followup.send(embed=embed)

    @search.command(name="invite", description="招待リンク情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def invite_info(self, interaction: discord.Interaction, 招待リンク: str):
        if interaction.is_guild_integration():
            if not interaction.user.guild_permissions.manage_guild:
                return await interaction.response.send_message(
                    ephemeral=True,
                    embed=make_embed.error_embed(
                        title="コマンドを実行する権限がありません！",
                        description="不足している権限: サーバーの管理",
                    ),
                )

        await interaction.response.defer()
        JST = datetime.timezone(datetime.timedelta(hours=9))
        try:
            invite = await self.bot.fetch_invite(招待リンク)
        except ValueError:
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="招待リンクが見つかりません。")
            )
        embed = (
            make_embed.success_embed(title="招待リンクの情報")
            .add_field(name="サーバー名", value=f"{invite.guild.name}", inline=False)
            .add_field(name="サーバーid", value=f"{invite.guild.id}", inline=False)
            .add_field(
                name="招待リンク作成者",
                value=f"{invite.inviter.display_name if invite.inviter else '不明'} ({invite.inviter.id if invite.inviter else '不明'})",
                inline=False,
            )
            .add_field(
                name="招待リンクの使用回数",
                value=f"{invite.uses if invite.uses else '0'} / {invite.max_uses if invite.max_uses else '無限'}",
                inline=False,
            )
        )
        embed.add_field(
            name="チャンネル",
            value=f"{invite.channel.name if invite.channel else '不明'} ({invite.channel.id if invite.channel else '不明'})",
            inline=False,
        )
        embed.add_field(
            name="メンバー数",
            value=f"{invite.approximate_member_count if invite.approximate_member_count else '不明'}",
            inline=False,
        )
        embed.add_field(
            name="オンライン数",
            value=f"{invite.approximate_presence_count if invite.approximate_presence_count else '不明'}",
            inline=False,
        )
        embed.add_field(
            name="作成時刻",
            value=f"{invite.created_at.astimezone(JST) if invite.created_at else '不明'}",
            inline=False,
        )
        if invite.guild.icon:
            embed.set_thumbnail(url=invite.guild.icon.url)
        await interaction.followup.send(embed=embed)

    @search.command(name="avatar", description="アバターを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def avatar(self, interaction: discord.Interaction, ユーザー: discord.User):
        await interaction.response.defer()
        if ユーザー.avatar == None:

            class AvatarLayout(discord.ui.LayoutView):
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"### {ユーザー.name}さんのアバター",
                    ),
                    discord.ui.TextDisplay(
                        f"ダウンロード\n[.png]({ユーザー.default_avatar.with_format('png').url})",
                    ),
                    discord.ui.Separator(),
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(ユーザー.default_avatar.url)
                    ),
                    accent_colour=discord.Colour.green(),
                )

            await interaction.followup.send(view=AvatarLayout())

        else:

            class AvatarLayout(discord.ui.LayoutView):
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"### {ユーザー.name}さんのアバター",
                    ),
                    discord.ui.TextDisplay(
                        f"ダウンロード\n[.png]({ユーザー.avatar.with_format('png').url}) [.jpg]({ユーザー.avatar.with_format('jpg').url}) [.webp]({ユーザー.avatar.with_format('webp').url})",
                    ),
                    discord.ui.Separator(),
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(ユーザー.avatar.url)
                    ),
                    discord.ui.Separator(),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            label="デフォルトアバターURL",
                            url=ユーザー.default_avatar.url,
                        )
                    ),
                    accent_colour=discord.Colour.green(),
                )

            await interaction.followup.send(view=AvatarLayout())

        return

    @search.command(name="banner", description="バナーを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def banner(self, interaction: discord.Interaction, ユーザー: discord.User):
        ユーザー = await self.bot.fetch_user(ユーザー.id)
        if not ユーザー.banner:
            return await interaction.response.send_message(
                ephemeral=True, content="その人はバナーをつけていません。"
            )
        embed = make_embed.success_embed(title=f"{ユーザー.name}さんのバナー")
        await interaction.response.send_message(
            embed=embed.set_image(url=ユーザー.banner.url if ユーザー.banner else None)
        )

    @search.command(name="emoji", description="絵文字を検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def emoji(self, interaction: discord.Interaction, 絵文字: str):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        JST = datetime.timezone(datetime.timedelta(hours=9))

        await interaction.response.defer()
        for e in interaction.guild.emojis:
            if 絵文字 == e.__str__():
                embed = make_embed.success_embed(title=f"{e.name} の情報")
                await interaction.followup.send(
                    embed=embed.set_image(url=e.url)
                    .add_field(name="名前", value=e.name, inline=False)
                    .add_field(name="id", value=str(e.id), inline=False)
                    .add_field(
                        name="作成日時",
                        value=str(e.created_at.astimezone(JST)),
                        inline=False,
                    )
                    .add_field(
                        name="絵文字が動くか",
                        value="はい" if e.animated else "いいえ",
                        inline=False,
                    )
                    .add_field(
                        name="Botから見た絵文字",
                        value=f"```{e.__str__()}```",
                        inline=False,
                    )
                )
                return

        extracted_info = extract_discord_emoji_info(絵文字)
        for name, emoji_id, is_animated in extracted_info:
            embed = make_embed.success_embed(title=f"{name} の情報")
            embed.add_field(name="名前", value=name, inline=False)
            embed.add_field(name="id", value=emoji_id, inline=False)
            sn = decode_snowflake(int(emoji_id))
            ts = sn.get("timestamp", None)
            if ts:
                embed.add_field(name="作成日時", value=str(ts.astimezone(JST)))
            embed.add_field(
                name="絵文字が動くか",
                value="はい" if is_animated else "いいえ",
                inline=False,
            )
            if is_animated:
                embed.set_image(url=f"https://cdn.discordapp.com/emojis/{emoji_id}.gif")
            else:
                embed.set_image(url=f"https://cdn.discordapp.com/emojis/{emoji_id}.png")
            embed.set_footer(text="この絵文字はこのサーバーには存在しません。")
            await interaction.followup.send(embed=embed)
            return

        await interaction.followup.send(
            embed=make_embed.error_embed(
                title="絵文字が存在しません。",
                description="絵文字が取得できませんでした。",
            )
        )

    @search.command(
        name="spotify", description="メンバーの聞いている曲の情報を表示します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def spotify_info(
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

        user = メンバー.id if メンバー else interaction.user.id

        if not interaction.guild.get_member(user):
            return await interaction.response.send_message(
                content="このサーバーにいるメンバーだけ指定できます。", ephemeral=True
            )

        for activity in interaction.guild.get_member(user).activities:
            if isinstance(activity, discord.Spotify):
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=f"{interaction.guild.get_member(user).name}の聞いている曲",
                        color=discord.Color.green(),
                    )
                    .add_field(name="曲名", value=activity.title, inline=False)
                    .add_field(name="アーティスト", value=activity.artist, inline=False)
                    .add_field(name="トラックid", value=activity.track_id, inline=False)
                    .set_thumbnail(url=activity.album_cover_url),
                    view=discord.ui.View().add_item(
                        discord.ui.Button(label="アクセスする", url=activity.track_url)
                    ),
                )
                return

        await interaction.response.send_message(
            ephemeral=True, content="曲を検出できませんでした。"
        )

    @search.command(name="snowflake", description="SnowFlakeを解析します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def snowflake_info(self, interaction: discord.Interaction, snowflake: str):
        try:
            sn = int(snowflake)
            info = decode_snowflake(sn)
            embed = make_embed.success_embed(title="Snowflake解析結果")
            embed.add_field(
                name="作成日時 (UTC)", value=str(info["timestamp"]), inline=False
            )
            embed.add_field(name="Worker ID", value=str(info["worker_id"]))
            embed.add_field(name="Process ID", value=str(info["process_id"]))
            embed.add_field(name="Increment", value=str(info["increment"]))
            await interaction.response.send_message(embed=embed)
        except:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="SnowFlakeが不正です。",
                    description="正常なSnowFlakeを入力してください。",
                ),
            )


async def setup(bot):
    await bot.add_cog(SearchCog(bot))
