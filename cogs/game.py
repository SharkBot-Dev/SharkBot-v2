import base64
import io
from discord.ext import commands
import discord
import random
from discord import app_commands
import urllib

import re
from consts import settings

import aiohttp
import json

from consts import settings

from ossapi import OssapiAsync


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
                            f"サーバー情報を取得できませんでした。ステータスコード: {response.status}"
                        )
            except Exception:
                await interaction.followup.send("予期せぬエラーが発生しました。")


class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.geo_s = "北海道,青森県,宮城県,秋田県,山形県,福島県,茨城県,栃木県,群馬県,埼玉県,千葉県,東京都,神奈川県,山梨県,長野県,新潟県,富山県,石川県,福井県,岐阜県,静岡県,愛知県,三重県,滋賀県,京都府,大阪府,兵庫県,奈良県,和歌山県,鳥取県,島根県,岡山県,広島県,山口県,徳島県,香川県,愛媛県,高知県,福岡県,佐賀県,長崎県,熊本県,大分県,宮崎県,鹿児島県,沖縄県"
        print("init -> GameCog")

    game = app_commands.Group(name="game", description="ゲーム系のコマンドです。")

    game.add_command(MinecraftGroup())
    game.add_command(FortniteGroup())
    game.add_command(PokemonGroup())
    game.add_command(OsuGroup())

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
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="8ball",
                description=random.choice(responses),
                color=discord.Color.green(),
            )
        )

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
                                    return await interaction.channel.send(
                                        embed=discord.Embed(
                                            title="正解です！",
                                            description=f"正解は{ans[r]}です！",
                                            color=discord.Color.green(),
                                        )
                                    )
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


async def setup(bot):
    await bot.add_cog(GameCog(bot))
