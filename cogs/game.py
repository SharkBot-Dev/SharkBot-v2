import base64
import io
from discord.ext import commands
import discord
import random
from discord import app_commands
import urllib
from urllib.parse import quote

import re
from consts import settings

import asyncio

import aiohttp
import json

from models import make_embed, quest

from PIL import Image, ImageDraw, ImageFont, ImageOps

from ossapi import OssapiAsync

class ScratchGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="scratch", description="スクラッチ関連のコマンドです。")

    @app_commands.command(name="user", description="ユーザーを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def scratch_user(self, interaction: discord.Interaction, ユーザーid: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.scratch.mit.edu/users/" + quote(ユーザーid)
            ) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        "スクラッチユーザーが見つかりません。", ephemeral=True
                    )
                    return
                
                embed = make_embed.success_embed(title=f"{ユーザーid} の情報")
                response = await resp.json()
                profile = response['profile']
                if profile.get('images', None):
                    img = profile.get('images', {}).get("90x90", None)
                    if img:
                        embed.set_thumbnail(url=img)
                embed.add_field(name="自己紹介", value=profile.get('bio', 'なし'), inline=False)
                embed.add_field(name="ステータス", value=profile.get('status', 'なし'), inline=False)
                embed.add_field(name="国", value=profile.get('country', 'なし'), inline=False)
                await interaction.followup.send(embed=embed)

class OsuGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="osu", description="Osu関連のコマンドです。")

    @app_commands.command(name="user", description="ユーザーを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def osu_user(self, interaction: discord.Interaction, ユーザーid: str):
        await interaction.response.defer()
        api = OssapiAsync(settings.OSU_CLIENT_ID, settings.OSU_CLIENT_SECRET)
        try:
            user = await api.user(ユーザーid)
            name = user.username
            avatar = user.avatar_url
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="ユーザーが見つかりません。", color=discord.Color.red()
                )
            )
        await interaction.followup.send(
            embed=discord.Embed(title="Osuのユーザー検索", color=discord.Color.blue())
            .add_field(name="ユーザー名", value=name, inline=False)
            .add_field(name="遊ぶモード", value=user.playmode, inline=False)
            .set_thumbnail(url=avatar)
            .set_image(url=user.cover_url)
        )


class PokemonGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="pokemon", description="ポケモン関連のコマンドです。")

    @app_commands.command(name="search", description="ポケモンを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def pokemon_search(self, interaction: discord.Interaction, ポケモン名: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pokeapi.co/api/v2/pokemon/" + ポケモン名.lower()
            ) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        "ポケモンが見つかりませんでした。", ephemeral=True
                    )
                    return

                data = await resp.json()

                poke_id = data["id"]
                poke_name = data["name"].capitalize()
                height = data["height"] / 10
                weight = data["weight"] / 10
                types = ", ".join(
                    [t["type"]["name"].capitalize() for t in data["types"]]
                )
                sprite = data["sprites"]["front_default"]

                embed = discord.Embed(
                    title=f"{poke_name} (#{poke_id})",
                    description=f"**タイプ:** {types}",
                    color=discord.Color.blue(),
                )
                embed.add_field(name="高さ", value=f"{height} m")
                embed.add_field(name="重さ", value=f"{weight} kg")
                if sprite:
                    embed.set_thumbnail(url=sprite)

                await interaction.followup.send(embed=embed)


class FortniteGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="fortnite", description="フォートナイト関連のコマンドです。"
        )

    @app_commands.command(name="map", description="フォートナイトのマップを取得するよ")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def fortnite_map(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="フォートナイトのマップ", color=discord.Color.purple()
            ).set_image(url="https://fortnite-api.com/images/map_ja.png")
        )

    @app_commands.command(
        name="player", description="フォートナイトのプレイヤーを検索します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def fortnite_player(
        self, interaction: discord.Interaction, プレイヤー名: str
    ):
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": settings.FORTNITE_APIKEY}
            async with session.get(
                f"https://fortnite-api.com/v2/stats/br/v2?name={プレイヤー名}&image=all",
                headers=headers,
            ) as response:
                data = json.loads(await response.text())
                try:
                    user = data["data"]["account"]["name"]
                    level = data["data"]["battlePass"]["level"]
                    wins = data["data"]["stats"]["all"]["overall"]["wins"]
                    kd = data["data"]["stats"]["all"]["overall"]["kd"]
                    image = data["data"]["image"]
                except:
                    return await interaction.response.send_message(
                        embed=discord.Embed(
                            title="プレイヤーが見つかりませんでした。",
                            color=discord.Color.red(),
                        )
                    )
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title=user + " の実績", color=discord.Color.green()
                    )
                    .add_field(name="バトルパスレベル", value=f"{level}")
                    .add_field(name="勝利数", value=f"{wins}")
                    .add_field(name="K/D", value=f"{kd}")
                    .set_image(url=image)
                )


class MinecraftGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="minecraft", description="Minecraft関連のコマンドです。")

    @app_commands.command(
        name="player", description="Minecraftのプレイヤーの情報を取得するよ"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def minecraft_player(
        self, interaction: discord.Interaction, ユーザーネーム: str
    ):
        await interaction.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.mojang.com/users/profiles/minecraft/{ユーザーネーム}"
                ) as response:
                    j = json.loads(await response.text())
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"https://api.minetools.eu/profile/{j['id']}"
                        ) as rs:
                            jj = json.loads(await rs.text())
                            await interaction.followup.send(
                                embed=discord.Embed(
                                    title="Minecraftのユーザー情報",
                                    description=f"ID: {j['id']}\nName: {j['name']}",
                                    color=discord.Color.green(),
                                )
                                .set_thumbnail(
                                    url=f"{jj['decoded']['textures']['SKIN']['url']}"
                                )
                                .set_image(
                                    url=f"https://mc-heads.net/body/{ユーザーネーム}/200"
                                )
                            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="ユーザー情報の取得に失敗しました。",
                    color=discord.Color.red(),
                )
            )

    @app_commands.command(
        name="java-server", description="Minecraftサーバー(Java)の情報を見ます。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def minecraft_server(self, interaction: discord.Interaction, アドレス: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"https://api.mcsrvstat.us/3/{アドレス}"
                ) as response:
                    if response.status == 200:
                        j = json.loads(await response.text())
                        embed = discord.Embed(
                            title=f"「{j['motd']['clean'][0]}」\nの情報",
                            color=discord.Color.green(),
                        )
                        pl = j.get("players", {}).get("list", [])
                        embed.add_field(
                            name="参加人数", value=f"{j['players']['online']}人"
                        )
                        embed.add_field(
                            name="最大参加人数", value=f"{j['players']['max']}人"
                        )
                        if pl:
                            embed.add_field(
                                name="参加者",
                                value="\n".join([f"{p['name']}" for p in pl]),
                                inline=False,
                            )
                        else:
                            embed.add_field(
                                name="参加者",
                                value="現在オンラインのプレイヤーはいません",
                                inline=False,
                            )

                        if "icon" in j:
                            try:
                                i = base64.b64decode(j["icon"].split(";base64,")[1])
                                ii = io.BytesIO(i)
                                embed.set_thumbnail(url="attachment://f.png")
                                await interaction.followup.send(
                                    embed=embed, file=discord.File(ii, "f.png")
                                )
                            except Exception:
                                await interaction.followup.send(
                                    embed=embed,
                                    content="サーバーアイコンの読み込みに失敗しました。",
                                )
                        else:
                            await interaction.followup.send(embed=embed)

                    else:
                        await interaction.followup.send(
                            f"サーバー情報を取得できませんでした。\nサーバーがオフラインである可能性があります。"
                        )
            except Exception:
                await interaction.followup.send("サーバー情報を取得できませんでした。\nサーバーがオフラインである可能性があります。")

    @app_commands.command(
        name="seedmap", description="シード値からマップを取得します"
    )
    @app_commands.choices(
        バージョン=[
            app_commands.Choice(name="1.21.5-Java", value="java_one"),
            app_commands.Choice(name="1.21.4-Java", value="java_two"),
        ]
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def minecraft_seedmao(
        self, interaction: discord.Interaction, バージョン: app_commands.Choice[str], シード値: str, 
    ):
        await interaction.response.send_message(embed=discord.Embed(title="シードマップ", color=discord.Color.green()).add_field(name="シード値", value=シード値, inline=False)
                                                .add_field(name="バージョン", value=バージョン.name, inline=False)
                                                , view=discord.ui.View().add_item(discord.ui.Button(label="アクセスする", url=f"https://mcseedmap.net/{バージョン.name}/{シード値}")), ephemeral=True)

class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.geo_s = "北海道,青森県,宮城県,秋田県,山形県,福島県,茨城県,栃木県,群馬県,埼玉県,千葉県,東京都,神奈川県,山梨県,長野県,新潟県,富山県,石川県,福井県,岐阜県,静岡県,愛知県,三重県,滋賀県,京都府,大阪府,兵庫県,奈良県,和歌山県,鳥取県,島根県,岡山県,広島県,山口県,徳島県,香川県,愛媛県,高知県,福岡県,佐賀県,長崎県,熊本県,大分県,宮崎県,鹿児島県,沖縄県"
        self.quests = [
            {'miq': '/fun image miqでMake it a quoteを作ってみよう！'},
            {'geo': '地理クイズで正解してみよう！'},
            {'8ball': '8ballで占ってもらおう！'},
        ]
        print("init -> GameCog")

    game = app_commands.Group(name="game", description="ゲーム系のコマンドです。")

    game.add_command(MinecraftGroup())
    game.add_command(FortniteGroup())
    game.add_command(PokemonGroup())
    game.add_command(OsuGroup())
    game.add_command(ScratchGroup())

    @game.command(name="8ball", description="占ってもらいます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def _8ball(self, interaction: discord.Interaction, 質問: str):
        responses = [
            "はい、間違いありません。",
            "多分そうでしょう。",
            "いい感じです。",
            "今は答えられません。",
            "もう一度聞いてください。",
            "やめたほうがいいです。",
            "ありえません。",
            "運命に聞いてください。",
            "可能性はあります。",
            "絶対にそうです！",
        ]
        embed = make_embed.success_embed(title=f"8ballの回答", description=random.choice(responses))
        await interaction.response.send_message(
            embed=embed
        )
        await asyncio.sleep(1)
        await quest.quest_clear(interaction, "8ball")
        return

    @game.command(name="roll", description="さいころをふります。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def roll(self, interaction: discord.Interaction, 何面か: str):
        match = re.fullmatch(r"(\d+)d(\d+)", 何面か)
        if not match:
            return await interaction.response.send_message(
                content="形式が正しくありません。\n例: `5d3`"
            )
        num_dice, sides = map(int, match.groups())
        if num_dice > 100:
            return await interaction.response.send_message(
                content="サイコロの個数は 100 以下にしてください"
            )
        if sides > 100:
            return await interaction.response.send_message(
                "100 面以上のサイコロは使えません。"
            )
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        str_rolls = [str(r) for r in rolls]
        await interaction.response.send_message(
            f"🎲 {interaction.user.mention}: {', '.join(str_rolls)} → {sum(rolls)}"
        )

    @game.command(name="omikuji", description="おみくじを引きます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def omikuji(self, interaction: discord.Interaction):
        omikuzi = [
            "大吉"
            if i < 2
            else "中吉"
            if 2 <= i < 10
            else "小吉"
            if 10 <= i < 20
            else "吉"
            if 20 <= i < 40
            else "末吉"
            if 40 <= i < 50
            else "凶"
            if 50 <= i < 55
            else "中凶"
            if 55 <= i < 59
            else "大凶"
            for i in range(61)
        ]

        embed = make_embed.success_embed(title="おみくじを引きました。", description=f"```{omikuzi[random.randrange(len(omikuzi))]}```")

        await interaction.response.send_message(
            embed=embed.set_footer(text="結果は完全にランダムです。"),
            view=discord.ui.View().add_item(
                discord.ui.Button(
                    label="おみくじWebで引く",
                    url="https://dashboard.sharkbot.xyz/omikuji",
                )
            ),
        )

    @game.command(name="lovecalc", description="恋愛度計算機で遊びます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def lovecalc(
        self,
        interaction: discord.Interaction,
        メンバー1: discord.User,
        メンバー2: discord.User,
    ):
        await interaction.response.defer()
        love_percent = random.randint(0, 100)

        c = 0

        while True:
            if c > 8:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="予期しないエラーが発生しました。",
                        color=discord.Color.red(),
                    )
                )

            img = await asyncio.to_thread(
                Image.new, "RGB", (600, 300), color=(255, 182, 193)
            )
            draw = await asyncio.to_thread(ImageDraw.Draw, img)

            try:
                font_title = await asyncio.to_thread(
                    ImageFont.truetype, "data/DiscordFont.ttf", 40
                )
                font_text = await asyncio.to_thread(
                    ImageFont.truetype, "data/DiscordFont.ttf", 25
                )
            except:
                font_title = await asyncio.to_thread(ImageFont.load_default)
                font_text = await asyncio.to_thread(ImageFont.load_default)

            async def get_avatar(member: discord.Member):
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(member.avatar.url)) as resp:
                        avatar_bytes = await resp.read()
                avatar = await asyncio.to_thread(Image.open, io.BytesIO(avatar_bytes))
                avatar = await asyncio.to_thread(avatar.convert, "RGB")
                avatar = await asyncio.to_thread(avatar.resize, (128, 128))

                mask = await asyncio.to_thread(Image.new, "L", avatar.size, 0)
                mask_draw = await asyncio.to_thread(ImageDraw.Draw, mask)
                await asyncio.to_thread(mask_draw.ellipse, (0, 0, 128, 128), fill=255)
                return avatar, mask

            avatar1, mask1 = await get_avatar(メンバー1)
            avatar2, mask2 = await get_avatar(メンバー2)

            await asyncio.to_thread(img.paste, avatar1, (100, 80), mask1)
            await asyncio.to_thread(img.paste, avatar2, (370, 80), mask2)

            await asyncio.to_thread(
                draw.text, (0, 0), "SharkBot", font=font_text, fill=(0, 0, 0)
            )
            await asyncio.to_thread(
                draw.text, (200, 30), "恋愛度診断", font=font_title, fill=(255, 0, 0)
            )
            await asyncio.to_thread(
                draw.text,
                (260, 230),
                f"{love_percent}%",
                font=font_text,
                fill=(0, 0, 0),
            )

            bar_x, bar_y = 150, 270
            bar_width, bar_height = 300, 20
            await asyncio.to_thread(
                draw.rectangle,
                [bar_x, bar_y, bar_x + bar_width, bar_y + bar_height],
                fill=(200, 200, 200),
            )
            filled_width = int(bar_width * (love_percent / 100))
            await asyncio.to_thread(
                draw.rectangle,
                [bar_x, bar_y, bar_x + filled_width, bar_y + bar_height],
                fill=(255, 0, 0),
            )

            with io.BytesIO() as image_binary:
                try:
                    await asyncio.to_thread(img.save, image_binary, "PNG")
                    image_binary.seek(0)
                    await interaction.followup.send(
                        file=discord.File(fp=image_binary, filename="love.png"),
                        content=f"-# {c}回再試行しました。",
                    )
                except:
                    c += 1
                    await asyncio.sleep(0.5)
                    continue
                return

    @game.command(name="geo-quiz", description="地理クイズをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def geo_quiz(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ans = [random.choice(self.geo_s.split(",")) for _ in range(3)]
        r = random.randint(0, 2)

        async with aiohttp.ClientSession(
            headers={"User-Agent": "DiscordBot/1.0"}
        ) as session:
            while True:
                try:
                    title = urllib.parse.quote(ans[r])
                    url = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{title}"
                    async with session.get(url) as cat:
                        if cat.status != 200:
                            raise Exception(f"HTTP {cat.status}")
                        j = await cat.json()

                        if "originalimage" not in j:
                            raise Exception("画像が見つかりません")

                        class AnsView(discord.ui.View):
                            def __init__(self):
                                super().__init__(timeout=180)

                            async def check_answer(self, interaction_, idx: int):
                                await interaction_.response.defer(ephemeral=True)
                                if interaction.user.id != interaction_.user.id:
                                    return
                                await interaction_.message.edit(view=None)
                                if ans[idx] == ans[r]:
                                    await interaction.channel.send(
                                        embed=discord.Embed(
                                            title="正解です！",
                                            description=f"正解は{ans[r]}です！",
                                            color=discord.Color.green(),
                                        )
                                    )

                                    await asyncio.sleep(1)
                                    await quest.quest_clear(interaction, "geo")

                                    return
                                return await interaction.channel.send(
                                    embed=discord.Embed(
                                        title="不正解です",
                                        description=f"正解は{ans[r]}です",
                                        color=discord.Color.red(),
                                    )
                                )

                            @discord.ui.button(
                                label=ans[0], style=discord.ButtonStyle.gray
                            )
                            async def ans_1(
                                self,
                                interaction_: discord.Interaction,
                                button: discord.ui.Button,
                            ):
                                await self.check_answer(interaction_, 0)

                            @discord.ui.button(
                                label=ans[1], style=discord.ButtonStyle.gray
                            )
                            async def ans_2(
                                self,
                                interaction_: discord.Interaction,
                                button: discord.ui.Button,
                            ):
                                await self.check_answer(interaction_, 1)

                            @discord.ui.button(
                                label=ans[2], style=discord.ButtonStyle.gray
                            )
                            async def ans_3(
                                self,
                                interaction_: discord.Interaction,
                                button: discord.ui.Button,
                            ):
                                await self.check_answer(interaction_, 2)

                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="ここはどこ？", color=discord.Color.blue()
                            ).set_image(url=j["originalimage"]["source"]),
                            view=AnsView(),
                        )
                        return

                except Exception as e:
                    print(f"GeoQuizエラー: {e}")
                    return await interaction.followup.send(
                        content="画像の取得に失敗しました。"
                    )

    @game.command(name="math-quiz", description="算数クイズをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def math_quiz(self, interaction: discord.Interaction):
        await interaction.response.defer()

        r_ = random.randint(0, 2)
        if r_ == 0:
            r = random.randint(100, 1000)
            r2 = random.randint(100, 1000)
            question = f"{r} * {r2}"
            correct_answer = r * r2
        elif r_ == 1:
            r = random.randint(100, 1000)
            r2 = random.randint(1, 1000)
            question = f"{r} / {r2}"
            correct_answer = round(r / r2, 2)
        else:
            r = random.randint(100, 1000)
            r2 = random.randint(100, 1000)
            question = f"{r} + {r2}"
            correct_answer = r + r2

        choices = [correct_answer]
        while len(choices) < 3:
            if isinstance(correct_answer, float):
                dummy = round(correct_answer + random.uniform(-50, 50), 2)
            else:
                dummy = correct_answer + random.randint(-50, 50)

            if dummy != correct_answer and dummy not in choices:
                choices.append(dummy)

        random.shuffle(choices)

        class AnsView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

            async def check_answer(self, interaction_: discord.Interaction, choice):
                if interaction.user.id != interaction_.user.id:
                    await interaction_.response.send_message("あなたの問題ではありません。", ephemeral=True)
                    return

                await interaction_.response.defer()
                await interaction_.message.edit(view=None)

                if choice == correct_answer:
                    return await interaction.channel.send(
                        embed=discord.Embed(
                            title="正解です！",
                            description=f"正解は {correct_answer} でした！",
                            color=discord.Color.green(),
                        )
                    )
                else:
                    return await interaction.channel.send(
                        embed=discord.Embed(
                            title="不正解です",
                            description=f"正解は {correct_answer} でした！",
                            color=discord.Color.red(),
                        )
                    )

        view = AnsView()
        for c in choices:
            button = discord.ui.Button(label=str(c), style=discord.ButtonStyle.gray)

            async def callback(interaction_: discord.Interaction, choice=c):
                await view.check_answer(interaction_, choice)

            button.callback = callback
            view.add_item(button)

        await interaction.followup.send(
            embed=discord.Embed(
                title="これの答えは？",
                color=discord.Color.blue(),
                description=f"```{question}```"
            ),
            view=view,
        )

    @game.command(name="guess", description="数字あてゲームをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def guess(self, interaction: discord.Interaction):
        await interaction.response.defer()
        number = random.randint(1, 100)
        await interaction.followup.send(embed=make_embed.success_embed(title="数字あてゲーム", description="1から100までの数字を当ててください。10回以内に当ててね！"))

        def check(m: discord.Message):
            return m.author == interaction.user and m.channel == interaction.channel
        
        attempts = 0
        while attempts < 10:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=30)

                await asyncio.sleep(0.8)

                guess = int(msg.content)
                attempts += 1

                if guess < number:
                    await interaction.channel.send(embed=discord.Embed(title="ヒント", description="もっと大きい数字です。", color=discord.Color.orange()))
                elif guess > number:
                    await interaction.channel.send(embed=discord.Embed(title="ヒント", description="もっと小さい数字です。", color=discord.Color.orange()))
                else:
                    await interaction.channel.send(embed=make_embed.success_embed(description=f"正解です！ {attempts} 回で当てました。", title="おめでとう！"))
                    return
            except ValueError:
                await interaction.channel.send(embed=make_embed.error_embed(title="エラー", description="数字以外が入力されました。ゲームを終了します。"))
                return
            except asyncio.TimeoutError:
                await interaction.channel.send(make_embed.error_embed(description="時間切れです。ゲームを終了します。", title="エラー"))
                return
            
        await asyncio.sleep(0.8)
            
        await interaction.channel.send(embed=make_embed.error_embed(description=f"残念！正解は {number} でした。", title="ゲームオーバー"))

    @game.command(name="bot-quest", description="Botの出してくるクエストに挑戦するゲームです。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bot_quest(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].BotQuest

        dbfind = await db.find_one({"User": interaction.user.id}, {"_id": False})

        if dbfind is None:
            quest = random.choice(self.quests)
            await db.update_one(
                {"User": interaction.user.id},
                {"$set": {"User": interaction.user.id, "Quest": quest}},
                upsert=True,
            )
        else:
            quest = dbfind.get("Quest")

        if not quest:
            await interaction.followup.send("現在進行中のクエストはありません。")
            return

        description = "\n".join(quest.values())
        embed = (
            discord.Embed(
                title="Botのクエスト",
                description=description,
                color=discord.Color.green(),
            )
            .set_footer(text="クリアすると次のクエストが表示されます。")
        )

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GameCog(bot))
