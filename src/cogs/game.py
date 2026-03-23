import base64
import io
import time
from discord.ext import commands
import discord
import random
from discord import app_commands
import urllib
from urllib.parse import quote

import re

import jaconv
from consts import settings

import asyncio

import aiohttp
import json

from models import make_embed, quest, block

from PIL import Image, ImageDraw, ImageFont, ImageOps

from ossapi import OssapiAsync

from models.akinator import characters, questions

import math

from janome.tokenizer import Tokenizer

import redis.asyncio as redis

tokenizer = Tokenizer()


def entropy(feature, probabilities, characters):
    yes = 0
    no = 0
    unk = 0

    for char, prob in probabilities.items():
        val = characters[char].get(feature, None)
        if val is True:
            yes += prob
        elif val is False:
            no += prob
        else:
            unk += prob

    def h(p):
        return -p * math.log2(p) if p > 0 else 0

    return h(yes) + h(no) + h(unk)


def choose_best_question(prob, asked_questions):
    best_q = None
    best_entropy = -1

    for q in questions:
        if q["id"] in asked_questions:
            continue

        e = entropy(q["id"], prob, characters)
        if e > best_entropy:
            best_entropy = e
            best_q = q

    return best_q


def bayesian_update(prob, feature, answer):
    for char in prob:
        char_value = characters[char].get(feature, None)

        if answer == "yes":
            likelihood = (
                0.9 if char_value is True else (0.1 if char_value is False else 0.5)
            )
        elif answer == "no":
            likelihood = (
                0.9 if char_value is False else (0.1 if char_value is True else 0.5)
            )
        else:
            likelihood = 0.5

        prob[char] *= likelihood

    total = sum(prob.values())
    for c in prob:
        prob[c] /= total

    return prob


class AkiView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, probabilities, asked):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.prob = probabilities
        self.asked = asked

        self.current_q = choose_best_question(self.prob, self.asked)

    async def ask_new_question(self, interaction):
        self.current_q = choose_best_question(self.prob, self.asked)

        if not self.current_q:
            best = max(self.prob, key=self.prob.get)
            await interaction.response.edit_message(
                embed=make_embed.success_embed(
                    title="アキネーターの推理",
                    description=f"多分… **{best}** だと思います！",
                ),
                view=None,
            )
            return

        await interaction.response.edit_message(
            embed=discord.Embed(
                title="アキネーターからの質問",
                description=self.current_q["text"],
                color=discord.Color.blue(),
            ),
            view=self,
        )

    async def process_answer(self, interaction, answer):
        if self.interaction.user.id != interaction.user.id:
            return

        f = self.current_q["id"]
        self.asked.append(f)

        self.prob = bayesian_update(self.prob, f, answer)

        best = max(self.prob, key=self.prob.get)
        if self.prob[best] >= 0.80:
            await interaction.response.edit_message(
                embed=make_embed.success_embed(
                    title="アキネーターの推理",
                    description=f"あなたのキャラは **{best}** ですね？",
                ),
                view=None,
            )
            return

        await self.ask_new_question(interaction)

    @discord.ui.button(label="はい", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, "yes")

    @discord.ui.button(label="いいえ", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, "no")

    @discord.ui.button(label="わからない", style=discord.ButtonStyle.grey)
    async def unknown(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await self.process_answer(interaction, "unknown")


cooldown_shiritori = {}

villagers = {
    "無職": "https://minecraft.wiki/images/thumb/Nitwit_refusing.gif/120px-Nitwit_refusing.gif?81c0e",
    "防具鍛冶": "https://minecraft.wiki/images/thumb/Plains_Armorer.png/120px-Plains_Armorer.png?0dee1",
    "肉屋": "https://static.wikitide.net/minecraftjapanwiki/thumb/2/22/Plains_Butcher.png/68px-Plains_Butcher.png",
    "製図家": "https://static.wikitide.net/minecraftjapanwiki/thumb/6/66/Plains_Cartographer.png/68px-Plains_Cartographer.png",
    "聖職者": "https://static.wikitide.net/minecraftjapanwiki/thumb/7/78/Plains_Cleric.png/68px-Plains_Cleric.png",
    "農民": "https://static.wikitide.net/minecraftjapanwiki/thumb/4/41/Plains_Farmer.png/68px-Plains_Farmer.png",
    "釣り人": "https://static.wikitide.net/minecraftjapanwiki/thumb/b/b5/Plains_Fisherman.png/68px-Plains_Fisherman.png",
    "矢士": "https://static.wikitide.net/minecraftjapanwiki/thumb/9/96/Plains_Fletcher.png/68px-Plains_Fletcher.png",
    "革細工師": "https://static.wikitide.net/minecraftjapanwiki/thumb/4/45/Plains_Leatherworker.png/68px-Plains_Leatherworker.png",
    "司書": "https://static.wikitide.net/minecraftjapanwiki/thumb/1/1c/Plains_Librarian.png/68px-Plains_Librarian.png",
    "石工": "https://static.wikitide.net/minecraftjapanwiki/thumb/3/3e/Plains_Stone_Mason.png/68px-Plains_Stone_Mason.png",
    "羊飼い": "https://static.wikitide.net/minecraftjapanwiki/thumb/7/7f/Plains_Shepherd.png/68px-Plains_Shepherd.png",
    "道具鍛冶": "https://static.wikitide.net/minecraftjapanwiki/thumb/c/cb/Plains_Toolsmith.png/68px-Plains_Toolsmith.png",
    "武器鍛冶": "https://static.wikitide.net/minecraftjapanwiki/thumb/b/b7/Plains_Weaponsmith.png/68px-Plains_Weaponsmith.png",
}


class EmeraldGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="emerald", description="エメラルドを使ったゲームです。")

    @app_commands.command(name="info", description="エメラルドの個数を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def emerald_info(
        self, interaction: discord.Interaction, ユーザー: discord.User = None
    ):
        await interaction.response.defer()
        user = ユーザー if ユーザー else interaction.user

        db = interaction.client.async_db["MainTwo"].EmeraldGame

        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except Exception as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="取得に失敗しました。",
                    description=f"エラーです。\n\nエラーコード: ```{e}```",
                )
            )
        if dbfind is None:
            return await interaction.followup.send(
                embed=make_embed.success_embed(title=f"{user.name} の情報").add_field(
                    name="エメラルド",
                    value="0 <:Emerald:1439453979594723388>",
                    inline=False,
                )
            )

        tip = dbfind.get("Tip", 0)
        vs = dbfind.get("Villagers", None)

        return await interaction.followup.send(
            embed=make_embed.success_embed(title=f"{user.name} の情報")
            .add_field(
                name="エメラルド",
                value=f"{tip} <:Emerald:1439453979594723388>",
                inline=False,
            )
            .add_field(
                name="集めた村人の一覧",
                value="\n".join(vs) if vs else "なし",
                inline=False,
            )
        )

    @app_commands.command(
        name="slot", description="エメラルドを使ってスロットを回します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def emerald_slot(
        self, interaction: discord.Interaction, エメラルドの個数: int
    ):
        await interaction.response.defer()
        db = interaction.client.async_db["MainTwo"].EmeraldGame

        try:
            dbfind = await db.find_one({"User": interaction.user.id}, {"_id": False})
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エメラルドが足りません。",
                    description=f"現在はエメラルドを「0個」持っています。",
                )
            )
        if dbfind is None:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エメラルドが足りません。",
                    description=f"現在はエメラルドを「0個」持っています。",
                )
            )

        tip = dbfind.get("Tip", 0)

        if tip < エメラルドの個数:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エメラルドが足りません。",
                    description=f"現在はエメラルドを「{tip}個」持っています。",
                )
            )

        await db.update_one(
            {"User": interaction.user.id},
            {"$inc": {"Tip": -エメラルドの個数}},
            upsert=True,
        )

        symbols = ["🍒", "🍋", "🍇", "⭐", "💎", "<:Emerald:1439453979594723388>"]

        def spin_slot():
            return [random.choice(symbols) for _ in range(3)]

        def check_win(result):
            if result[0] == result[1] == result[2]:
                return True
            else:
                return False

        result = spin_slot()

        win = check_win(result)

        if win:
            await db.update_one(
                {"User": interaction.user.id},
                {"$inc": {"Tip": エメラルドの個数 * 2}},
                upsert=True,
            )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="スロットを回しました。", description=" | ".join(result)
            ).add_field(
                name="結果",
                value="🎉 そろいました！" if win else "ハズレ...",
                inline=False,
            )
        )

    @app_commands.command(name="mining", description="エメラルドを採掘します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def emerald_mining(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].EmeraldGame
        data = await db.find_one({"User": interaction.user.id})
        now = time.time()
        cooldown_time = 2 * 60 * 60

        if data and "LastMining" in data:
            last_up = float(data["LastMining"])
            remaining = cooldown_time - (now - last_up)
            if remaining > 0:
                m, s = divmod(int(remaining), 60)
                embed = make_embed.error_embed(
                    title="まだ採掘できません。",
                    description=f"あと **{m}分{s}秒** 待ってから再度お試しください。",
                )
                return await interaction.response.send_message(embed=embed)

        await interaction.response.defer()

        ems = random.randint(1, 3)
        await db.update_one(
            {"User": interaction.user.id},
            {"$inc": {"Tip": ems}},
            upsert=True,
        )

        await db.update_one(
            {"User": interaction.user.id},
            {
                "$set": {
                    "LastMining": str(time.time()),
                }
            },
            upsert=True,
        )

        embed = make_embed.success_embed(
            title="エメラルドを採掘しました。",
            description="2時間後に再度採掘できます。",
        )
        embed.add_field(
            name="採掘した個数",
            value=f"{ems} <:Emerald:1439453979594723388>",
            inline=False,
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="buy", description="エメラルドをアイテムと交換します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        アイテム名=[
            app_commands.Choice(name="ランダムな村人 (3エメラルド)", value="villager"),
        ]
    )
    async def emerald_buy(
        self, interaction: discord.Interaction, アイテム名: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        db = interaction.client.async_db["MainTwo"].EmeraldGame

        try:
            dbfind = await db.find_one({"User": interaction.user.id}, {"_id": False})
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エメラルドが足りません。",
                    description=f"現在はエメラルドを「0個」持っています。",
                )
            )
        if dbfind is None:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エメラルドが足りません。",
                    description=f"現在はエメラルドを「0個」持っています。",
                )
            )

        tip = dbfind.get("Tip", 0)

        if アイテム名.value == "villager":
            if tip < 3:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="エメラルドが足りません。",
                        description=f"現在はエメラルドを「{tip}個」持っています。",
                    )
                )

            await db.update_one(
                {"User": interaction.user.id},
                {"$inc": {"Tip": -3}},
                upsert=True,
            )
            keys = []
            for k in villagers.keys():
                keys.append(k)
            r_k = random.choice(keys)

            await db.update_one(
                {"User": interaction.user.id},
                {"$addToSet": {"Villagers": r_k}},
                upsert=True,
            )

            embed = make_embed.success_embed(title=f"{r_k} が出てきました。")
            embed.set_image(
                url=villagers.get(
                    r_k,
                    "https://static.wikitide.net/minecraftjapanwiki/b/b4/Nitwit_refusing.gif",
                )
            )
            await interaction.followup.send(embed=embed)
            return


class ScratchGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="scratch", description="スクラッチ関連のコマンドです。")

    @app_commands.command(name="user", description="スクラッチのユーザーを検索します。")
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
                profile = response["profile"]
                if profile.get("images", None):
                    img = profile.get("images", {}).get("90x90", None)
                    if img:
                        embed.set_thumbnail(url=img)
                embed.add_field(
                    name="自己紹介", value=profile.get("bio", "なし"), inline=False
                )
                embed.add_field(
                    name="ステータス", value=profile.get("status", "なし"), inline=False
                )
                embed.add_field(
                    name="国", value=profile.get("country", "なし"), inline=False
                )
                await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="project", description="スクラッチのプロジェクトを検索します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def scratch_project(
        self, interaction: discord.Interaction, プロジェクトid: str
    ):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.scratch.mit.edu/projects/" + quote(プロジェクトid)
            ) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        "スクラッチ作品が見つかりません。", ephemeral=True
                    )
                    return

                embed = make_embed.success_embed(title=f"{プロジェクトid} の情報")
                response = await resp.json()

                title = response.get("title", "なし")
                description = response.get("description", "なし")
                image = response.get("image", "なし")

                history = response.get("history", {})
                created = history.get("created", "なし")
                modified = history.get("modified", "なし")
                shared = history.get("shared", "なし")

                stats = response.get("stats", {})
                views = stats.get("views", "0")
                loves = stats.get("loves", "0")
                favorites = stats.get("favorites", "0")
                remixes = stats.get("remixes", "0")

                embed.add_field(name="タイトル", value=title, inline=False)
                embed.add_field(name="説明", value=description, inline=False)

                embed.add_field(name="作成日", value=created, inline=True)
                embed.add_field(name="変更日", value=modified, inline=True)
                embed.add_field(name="シェアされた日", value=shared, inline=True)

                embed.add_field(
                    name="表示された感じ", value=str(views) + "回", inline=True
                )
                embed.add_field(
                    name="いいねされた回数", value=str(loves) + "回", inline=True
                )
                embed.add_field(
                    name="お気に入りされた回数",
                    value=str(favorites) + "回",
                    inline=True,
                )
                embed.add_field(
                    name="リミックス回数", value=str(remixes) + "回", inline=True
                )

                embed.set_image(url=image)

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
                embed=make_embed.error_embed(title="ユーザーが見つかりません。")
            )
        await interaction.followup.send(
            embed=make_embed.success_embed(title="Osuのユーザー検索")
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

                embed = make_embed.success_embed(
                    title=f"{poke_name} (#{poke_id})",
                    description=f"**タイプ:** {types}",
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
                        embed=make_embed.error_embed(
                            title="プレイヤーが見つかりませんでした。"
                        )
                    )
                await interaction.response.send_message(
                    embed=make_embed.success_embed(title=user + " の実績")
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
                                embed=make_embed.success_embed(
                                    title="Minecraftのユーザー情報",
                                    description=f"ID: {j['id']}\nName: {j['name']}",
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
                embed=make_embed.error_embed(title="ユーザー情報の取得に失敗しました。")
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
                        embed = make_embed.success_embed(
                            title=f"「{j['motd']['clean'][0]}」\nの情報"
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
                                ii.close()
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
                await interaction.followup.send(
                    "サーバー情報を取得できませんでした。\nサーバーがオフラインである可能性があります。"
                )

class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.geo_s = "北海道,青森県,宮城県,秋田県,山形県,福島県,茨城県,栃木県,群馬県,埼玉県,千葉県,東京都,神奈川県,山梨県,長野県,新潟県,富山県,石川県,福井県,岐阜県,静岡県,愛知県,三重県,滋賀県,京都府,大阪府,兵庫県,奈良県,和歌山県,鳥取県,島根県,岡山県,広島県,山口県,徳島県,香川県,愛媛県,高知県,福岡県,佐賀県,長崎県,熊本県,大分県,宮崎県,鹿児島県,沖縄県"
        self.quests = [
            {"miq": "/fun image miqでMake it a quoteを作ってみよう！"},
            {"geo": "地理クイズで正解してみよう！"},
            {"8ball": "8ballで占ってもらおう！"},
        ]
        print("init -> GameCog")

    game = app_commands.Group(
        name="game",
        description="ゲーム系のコマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    game.add_command(MinecraftGroup())
    game.add_command(FortniteGroup())
    game.add_command(PokemonGroup())
    game.add_command(OsuGroup())
    game.add_command(ScratchGroup())
    game.add_command(EmeraldGroup())

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
        embed = make_embed.success_embed(
            title=f"8ballの回答", description=random.choice(responses)
        )
        await interaction.response.send_message(embed=embed)
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

    @game.command(name="coinflip", description="コインフリップをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def coinflip(self, interaction: discord.Interaction):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Webバージョン", url="https://sharkbot-dev.github.io/CoinFlip/"))
        await interaction.response.send_message(f"🪙{random.choice(['表', '裏'])} が出ました", view=view)

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

        embed = make_embed.success_embed(
            title="おみくじを引きました。",
            description=f"```{omikuzi[random.randrange(len(omikuzi))]}```",
        )

        await interaction.response.send_message(
            embed=embed.set_footer(text="結果は完全にランダムです。")
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
        is_blockd = await block.is_blocked_func(
            interaction.client, メンバー1.id, "恋愛度計算機"
        )
        if is_blockd:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのメンバーは恋愛度計算機を\nブロックしています。"
                ),
            )

        is_blockd = await block.is_blocked_func(
            interaction.client, メンバー2.id, "恋愛度計算機"
        )
        if is_blockd:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="そのメンバーは恋愛度計算機を\nブロックしています。"
                ),
            )

        await interaction.response.defer()
        love_percent = random.randint(0, 100)

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
            await asyncio.to_thread(img.save, image_binary, "PNG")
            image_binary.seek(0)
            await interaction.followup.send(
                file=discord.File(fp=image_binary, filename="love.png")
            )

    @game.command(name="geo-quiz", description="地理クイズをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def geo_quiz(self, interaction: discord.Interaction):
        await interaction.response.defer()

        ans = [random.choice(self.geo_s.split(",")) for _ in range(3)]
        r = random.randint(0, 2)

        async with aiohttp.ClientSession(
            headers={"User-Agent": "DiscordBot/1.0 (https://example.com)"}
        ) as session:
            try:
                title = urllib.parse.quote(ans[r])
                url = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{title}"

                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")

                    j = await resp.json()

                    image_url = None
                    if "originalimage" in j:
                        image_url = j["originalimage"]["source"]
                    elif "thumbnail" in j:
                        image_url = j["thumbnail"]["source"]
                    else:
                        raise Exception("画像がありません")

                class AnsView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=180)

                    async def check_answer(
                        self, interaction_: discord.Interaction, idx: int
                    ):
                        await interaction_.response.defer(ephemeral=True)

                        if interaction.user.id != interaction_.user.id:
                            return

                        await interaction_.edit_original_response(view=None)

                        if ans[idx] == ans[r]:
                            await interaction.followup.send(
                                embed=discord.Embed(
                                    title="正解です！",
                                    description=f"正解は **{ans[r]}** です！",
                                    color=discord.Color.green(),
                                )
                            )
                            await asyncio.sleep(1)
                            await quest.quest_clear(interaction, "geo")
                        else:
                            await interaction.followup.send(
                                embed=discord.Embed(
                                    title="不正解です",
                                    description=f"正解は **{ans[r]}** です",
                                    color=discord.Color.red(),
                                )
                            )

                    @discord.ui.button(label=ans[0], style=discord.ButtonStyle.gray)
                    async def ans_1(self, interaction_, button):
                        await self.check_answer(interaction_, 0)

                    @discord.ui.button(label=ans[1], style=discord.ButtonStyle.gray)
                    async def ans_2(self, interaction_, button):
                        await self.check_answer(interaction_, 1)

                    @discord.ui.button(label=ans[2], style=discord.ButtonStyle.gray)
                    async def ans_3(self, interaction_, button):
                        await self.check_answer(interaction_, 2)

                await interaction.followup.send(
                    embed=discord.Embed(
                        title="ここはどこ？",
                        color=discord.Color.blue(),
                    ).set_image(url=image_url),
                    view=AnsView(),
                )

            except Exception as e:
                print(f"GeoQuizエラー: {e}")
                await interaction.followup.send(
                    content="画像の取得に失敗しました。別の問題で再試行してください。"
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
                    await interaction_.response.send_message(
                        "あなたの問題ではありません。", ephemeral=True
                    )
                    return

                await interaction_.response.defer()
                await interaction_.edit_original_response(view=None)

                if choice == correct_answer:
                    return await interaction.followup.send(
                        embed=discord.Embed(
                            title="正解です！",
                            description=f"正解は {correct_answer} でした！",
                            color=discord.Color.green(),
                        )
                    )
                else:
                    return await interaction.followup.send(
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
                description=f"```{question}```",
            ),
            view=view,
        )

    @game.command(name="guess", description="数字あてゲームをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def guess(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.defer()
        number = random.randint(1, 100)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="数字あてゲーム",
                description="1から100までの数字を当ててください。10回以内に当ててね！",
            )
        )

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
                    await interaction.channel.send(
                        embed=discord.Embed(
                            title="ヒント",
                            description="もっと大きい数字です。",
                            color=discord.Color.orange(),
                        )
                    )
                elif guess > number:
                    await interaction.channel.send(
                        embed=discord.Embed(
                            title="ヒント",
                            description="もっと小さい数字です。",
                            color=discord.Color.orange(),
                        )
                    )
                else:
                    await interaction.channel.send(
                        embed=make_embed.success_embed(
                            description=f"正解です！ {attempts} 回で当てました。",
                            title="おめでとう！",
                        )
                    )
                    return
            except ValueError:
                await interaction.channel.send(
                    embed=make_embed.error_embed(
                        title="エラー",
                        description="数字以外が入力されました。ゲームを終了します。",
                    )
                )
                return
            except asyncio.TimeoutError:
                await interaction.channel.send(
                    make_embed.error_embed(
                        description="時間切れです。ゲームを終了します。", title="エラー"
                    )
                )
                return

        await asyncio.sleep(0.8)

        await interaction.channel.send(
            embed=make_embed.error_embed(
                description=f"残念！正解は {number} でした。", title="ゲームオーバー"
            )
        )

    @game.command(name="shiritori", description="しりとりをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def shiritori(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        db = self.bot.async_db["MainTwo"].ShiritoriChannel

        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
            {"_id": False},
        )
        if dbfind is None:
            await db.update_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
                {
                    "$set": {
                        "Guild": interaction.guild.id,
                        "Channel": interaction.channel.id,
                    }
                },
                upsert=True,
            )

            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="しりとりを開始しました。",
                    description="ひらがなのみ使用可能です。\nんで終わるか、同じワードを送信すると負けです。",
                )
            )
        else:
            await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="しりとりを終了しました。",
                    description="再度始める際は、このコマンドを実行して下さい。",
                )
            )

    @commands.Cog.listener("on_message")
    async def shiritori_on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        db = self.bot.async_db["MainTwo"].ShiritoriChannel
        dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id})
        if dbfind is None:
            return

        word = message.content.strip()
        if not word:
            return

        current_time = time.time()
        last_message_time = cooldown_shiritori.get(message.author.id, 0)
        if current_time - last_message_time < 2:
            return
        cooldown_shiritori[message.author.id] = current_time

        if word == "reset":
            await db.update_one(
                {"Guild": message.guild.id, "Channel": message.channel.id},
                {"$set": {"LastWord": None, "Word": []}},
                upsert=True,
            )
            return await message.reply(embed=make_embed.success_embed(title="しりとりをリセットしました。"))

        is_all_hira = re.fullmatch(r"[ぁ-んー]+", word)

        if is_all_hira:
            yomi = word
        else:
            tokens = list(await asyncio.to_thread(tokenizer.tokenize, word))
            
            if len(tokens) != 1 or tokens[0].part_of_speech.split(',')[0] != '名詞':
                return await message.reply(
                    embed=make_embed.error_embed(title="無効な入力", description="名詞を一つだけ入力してください。")
                )
            
            yomi_katakana = tokens[0].reading if tokens[0].reading != '*' else word
            yomi = await asyncio.to_thread(jaconv.kata2hira, yomi_katakana)

        if yomi.endswith("ん"):
            await db.update_one(
                {"Guild": message.guild.id, "Channel": message.channel.id},
                {"$set": {"LastWord": None, "Word": []}},
                upsert=True,
            )
            return await message.reply(
                embed=make_embed.error_embed(title="あなたの負け", description=f"「{word}({yomi})」は「ん」で終わっています！")
            )

        last_word_yomi = dbfind.get("LastWordYomi")
        if last_word_yomi:
            target_char = last_word_yomi[-1]
            if target_char == "ー" and len(last_word_yomi) > 1:
                target_char = last_word_yomi[-2]

            if yomi[0] != target_char:
                return await message.reply(
                    embed=make_embed.error_embed(
                        title="始まりの文字が違います。",
                        description=f"「{target_char}」から始まる単語を入力してください。(前の単語: {dbfind.get('LastWord')})",
                    )
                )

        used_words = dbfind.get("Word", [])
        if word in used_words:
            await db.update_one(
                {"Guild": message.guild.id, "Channel": message.channel.id},
                {"$set": {"LastWord": None, "Word": []}},
                upsert=True,
            )
            return await message.reply(
                embed=make_embed.error_embed(title="あなたの負け", description="その言葉はすでに使われています！")
            )

        await db.update_one(
            {"Guild": message.guild.id, "Channel": message.channel.id},
            {
                "$set": {"LastWord": word, "LastWordYomi": yomi}, 
                "$addToSet": {"Word": word}
            },
            upsert=True,
        )
        await message.add_reaction("✅")

    @game.command(
        name="bot-quest", description="Botの出してくるクエストに挑戦するゲームです。"
    )
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

        class QuestView(discord.ui.LayoutView):
            container = discord.ui.Container(
                discord.ui.TextDisplay(content="### Botのクエスト"),
                discord.ui.Separator(),
                discord.ui.TextDisplay(content=description),
                discord.ui.TextDisplay(
                    content="-# クリアすると次のクエストが表示されます。"
                ),
                accent_color=discord.Color.green(),
            )

        await interaction.followup.send(view=QuestView())

    @game.command(name="werewolf", description="人狼ゲームをプレイします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def werewolf_game(self, interaction: discord.Interaction):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(title="エラー", description="サーバーにBotをインストールしてください。", color=discord.Color.red())
            )
        
        await interaction.response.defer()

        channel_id = interaction.channel.id
        await self.cleanup_game(channel_id)

        members_key = f"werewolf:members:{channel_id}"
        membercount_key = f"werewolf:membercount:{channel_id}"
        owner_key = f"werewolf:owner:{channel_id}"
        await self.bot.redis.rpush(members_key, str(interaction.user.id))
        await self.bot.redis.set(membercount_key, "1")
        await self.bot.redis.set(owner_key, str(interaction.user.id))

        await self.bot.redis.expire(members_key, 86400)
        await self.bot.redis.expire(membercount_key, 86400)
        await self.bot.redis.expire(owner_key, 86400)

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="参加する", custom_id="werewolf_join", style=discord.ButtonStyle.blurple))
        
        embed = discord.Embed(title="人狼ゲーム 募集", color=discord.Color.blue())
        embed.add_field(name="参加メンバー", value=f"{interaction.user.mention}", inline=False)

        await interaction.followup.send(view=view, embed=embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("werewolf_"):
            return

        channel_id = interaction.channel_id or (custom_id.split(":")[-1] if ":" in custom_id else None)
        if not channel_id: return

        if custom_id == "werewolf_join":
            await self._handle_join(interaction, channel_id)

        if custom_id == "werewolf_force_start":
            owner_key = f"werewolf:owner:{channel_id}"
            owner_id = await self.bot.redis.get(owner_key)
            if owner_id != str(interaction.user.id):
                await interaction.response.send_message(ephemeral=True, content="あなたは主催者ではありません。")
                return

            status_key = f"werewolf:status:{channel_id}"
            await self.bot.redis.set(status_key, "running", ex=3600)

            embed = interaction.message.embeds[0].copy()
            await interaction.message.edit(view=None)
            await self.assign_roles(interaction, channel_id, embed)

        elif custom_id.startswith(("werewolf_kill:", "werewolf_divine:")):
            await self._handle_night_action(interaction, custom_id)

        elif custom_id.startswith("werewolf_vote_select:"):
            await self._handle_vote(interaction, custom_id)

        elif custom_id.startswith("werewolf_skip_discuss:"):
            channel_id = custom_id.split(":")[1]
            ready_key = f"werewolf:ready:{channel_id}"
            user_id = str(interaction.user.id)

            if not user_id in interaction.message.embeds[0].fields[0].value:
                await interaction.response.send_message(ephemeral=True, content="あなたは生存していません。")
                return

            await self.bot.redis.sadd(ready_key, user_id)
            ready_count = await self.bot.redis.scard(ready_key)
            members_key = f"werewolf:members:{channel_id}"
            survivor_count = await self.bot.redis.llen(members_key)
            if ready_count >= survivor_count:
                await interaction.message.edit(view=None)
                await self.bot.redis.set(f"werewolf:status:{channel_id}", "voting")
                await interaction.response.send_message("全員の準備が整いました。投票に移ります。")
                await self.start_voting_phase(channel_id)
            else:
                await interaction.response.send_message(f"準備完了通知を出しました ({ready_count}/{survivor_count})", ephemeral=True)

    async def _handle_join(self, interaction: discord.Interaction, channel_id):
        status_key = f"werewolf:status:{channel_id}"
        members_key = f"werewolf:members:{channel_id}"
        membercount_key = f"werewolf:membercount:{channel_id}"

        if await self.bot.redis.get(status_key):
            return await interaction.response.send_message("このゲームは既に進行中、または開始されています。", ephemeral=True)

        user_id_str = str(interaction.user.id)
        existing_bin = await self.bot.redis.lrange(members_key, 0, -1)
        if any(m == user_id_str for m in existing_bin):
            return await interaction.response.send_message("既に参加しています。", ephemeral=True)

        await interaction.response.defer()

        await self.bot.redis.rpush(members_key, user_id_str)
        await self.bot.redis.expire(members_key, 3600)
        
        count = await self.bot.redis.incr(membercount_key)
        await self.bot.redis.expire(membercount_key, 3600)

        embed = interaction.message.embeds[0].copy()
        current_mentions = embed.fields[0].value
        embed.set_field_at(0, name=f"参加メンバー ({count}/8)", value=f"{current_mentions}\n{interaction.user.mention}", inline=False)

        view = discord.ui.View(timeout=None)

        view.add_item(discord.ui.Button(label="参加する", custom_id="werewolf_join", style=discord.ButtonStyle.blurple, disabled=(count >= 8)))
        
        if count >= 3:
            view.add_item(discord.ui.Button(label="ゲームを開始する", custom_id="werewolf_force_start", style=discord.ButtonStyle.green))

        if count >= 8:
            await self.bot.redis.set(status_key, "running", ex=3600)
            await interaction.message.edit(embed=embed, view=None)
            await self.assign_roles(interaction, channel_id, embed)
        else:
            await interaction.message.edit(embed=embed, view=view)

    async def assign_roles(self, interaction, channel_id, embed):
        members_key = f"werewolf:members:{channel_id}"
        roles_key = f"werewolf:roles:{channel_id}"
        
        member_ids = [m for m in await self.bot.redis.lrange(members_key, 0, -1)]
        count = len(member_ids)
        
        if count <= 3:
            roles = ["人狼", "占い師", "村人"]
        elif count == 4:
            roles = ["人狼", "占い師", "村人", "村人"]
        elif count == 5:
            roles = ["人狼", "占い師", "騎士", "村人", "村人"]
        elif count <= 8:
            roles = ["人狼", "人狼", "占い師", "騎士"] + ["村人"] * (count - 4)
        else:
            roles = ["人狼", "人狼", "狂人", "占い師", "騎士"] + ["村人"] * (count - 5)

        random.shuffle(roles)
        
        role_map = dict(zip(member_ids, roles))
        await self.bot.redis.hset(roles_key, mapping=role_map)
        await self.bot.redis.expire(roles_key, 86400)

        for u_id, role in role_map.items():
            try:
                user = await self.bot.fetch_user(int(u_id))
                description = self._get_role_description(role)
                await user.send(embed=discord.Embed(title="人狼ゲーム", description=f"あなたの役職は **{role}** です。\n{description}", color=discord.Color.blue()))
            except:
                await interaction.channel.send(f"<@{u_id}> DMを解放してください。")

            await asyncio.sleep(1)

        embed.title = f"人狼ゲーム - 開始（参加者: {count}名）"
        embed.description = "全員に役職を送信しました。夜の行動を開始します。"
        await interaction.message.edit(embed=embed)
        
        await self.start_night_phase(interaction.channel, role_map)

    def _get_role_description(self, role):
        descriptions = {
            "人狼": "夜に一人を指名して襲撃します。自分以外の狼は誰か分かります。",
            "占い師": "夜に一人を占って、その人が「人狼」か「人間」かを知ることができます。",
            "騎士": "夜に一人を守ります。その人が襲撃された場合、死亡を防げます。",
            "狂人": "人間ですが、人狼陣営です。占われても「人間」と出ます。",
            "村人": "特別な能力はありません。議論で人狼を見つけ出してください。"
        }
        return descriptions.get(role, "")

    async def start_night_phase(self, channel, role_map):
        for u_id, role in role_map.items():
            if role == "村人": continue
            
            user = await self.bot.fetch_user(int(u_id))
            view = discord.ui.View(timeout=None)
            targets = [m for m in role_map.keys() if m != u_id]

            for t_id in targets:
                t_user = await self.bot.fetch_user(int(t_id))
                action_type = "kill" if role == "人狼" else "divine"
                view.add_item(discord.ui.Button(
                    label=f"{t_user.name}を{'襲撃' if action_type == 'kill' else '占う'}",
                    style=discord.ButtonStyle.danger if action_type == "kill" else discord.ButtonStyle.primary,
                    custom_id=f"werewolf_{action_type}:{t_id}:{channel.id}"
                ))
            await user.send(f"夜の行動を選択してください。", view=view)

    async def _handle_night_action(self, interaction, custom_id):
        action_parts = custom_id.split(":")
        action = action_parts[0]
        target_id = action_parts[1]
        channel_id = action_parts[2]
        
        action_key = f"werewolf:actions:{channel_id}"
        roles_key = f"werewolf:roles:{channel_id}"
        
        await interaction.response.defer(ephemeral=True)

        await interaction.message.edit(view=None)

        if "kill" in action:
            await self.bot.redis.hset(action_key, f"kill:{interaction.user.id}", target_id)
            await interaction.followup.send("襲撃先を選択しました。", ephemeral=True)
        elif "divine" in action:
            target_role = (await self.bot.redis.hget(roles_key, target_id))
            res = "人狼" if target_role == "人狼" else "人間"
            await self.bot.redis.hset(action_key, f"divine:{interaction.user.id}", target_id)
            await interaction.followup.send(f"占い結果: <@{target_id}> は **{res}** です。", ephemeral=True)
        elif "guard" in action:
            await self.bot.redis.hset(action_key, f"guard:{interaction.user.id}", target_id)
            await interaction.followup.send("守衛先を選択しました。", ephemeral=True)

        all_roles = await self.bot.redis.hgetall(roles_key)

        active_roles_count = sum(1 for r in all_roles.values() if r in ["人狼", "占い師", "騎士"])
        
        completed_actions = await self.bot.redis.hlen(action_key)

        if completed_actions >= active_roles_count:
            await self.process_morning(channel_id)

    async def start_discussion_phase(self, channel_id):
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return

        members_key = f"werewolf:members:{channel_id}"
        survivors = [s for s in await self.bot.redis.lrange(members_key, 0, -1)]
        
        status_key = f"werewolf:status:{channel_id}"
        await self.bot.redis.set(status_key, "discussing", ex=600)

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="議論を終了して投票へ", 
            custom_id=f"werewolf_skip_discuss:{channel_id}", 
            style=discord.ButtonStyle.secondary
        ))

        embed = discord.Embed(
            title="昼の議論フェーズ", 
            description="生存者で話し合い、人狼を見つけ出してください。\n制限時間は **3分** です。", 
            color=discord.Color.orange()
        )
        embed.add_field(
            name="現在の生存者", 
            value="\n".join([f"<@{s}>" for s in survivors]), 
            inline=False
        )
        
        discussion_msg = await channel.send(embed=embed, view=view)

        for i in range(18):
            await asyncio.sleep(10)
            current_status = await self.bot.redis.get(status_key)
            if not current_status or current_status != "discussing":
                await discussion_msg.edit(view=None)
                return

        await self.start_voting_phase(channel_id)

    async def process_morning(self, channel_id):
        action_key = f"werewolf:actions:{channel_id}"
        members_key = f"werewolf:members:{channel_id}"
        
        actions = await self.bot.redis.hgetall(action_key)
        actions = {k: v for k, v in actions.items()}
        
        victim_id = None
        guarded_id = None
        for key, value in actions.items():
            if key.startswith("kill:"): victim_id = value
            if key.startswith("guard:"): guarded_id = value

        channel = self.bot.get_channel(int(channel_id))
        embed = discord.Embed(title="朝が来ました", color=discord.Color.gold())

        if victim_id and victim_id != guarded_id:
            embed.description = f"昨晩、<@{victim_id}> が無残な姿で発見されました。"
            await self.bot.redis.lrem(members_key, 0, victim_id)
        else:
            embed.description = "昨晩は誰も死にませんでした。平和な朝です。"

        await channel.send(embed=embed)
        
        await self.bot.redis.delete(action_key)
        
        if not await self.check_win_condition(channel_id):
            await self.start_discussion_phase(channel_id)

    async def start_voting_phase(self, channel_id):
        members_key = f"werewolf:members:{channel_id}"
        survivors = [m for m in await self.bot.redis.lrange(members_key, 0, -1)]
        
        view = discord.ui.View(timeout=None)
        select = discord.ui.Select(custom_id=f"werewolf_vote_select:{channel_id}", placeholder="追放する人を選択")
        for s_id in survivors:
            user = await self.bot.fetch_user(int(s_id))
            select.add_option(label=user.name, value=s_id)
        
        view.add_item(select)
        await self.bot.get_channel(int(channel_id)).send("議論を終了し、投票を行ってください。", view=view)

    async def process_tally(self, channel_id):
        vote_key = f"werewolf:votes:{channel_id}"
        members_key = f"werewolf:members:{channel_id}"
        
        votes = await self.bot.redis.hgetall(vote_key)
        vote_counts = {}

        for voter_id, voted_id in votes.items():
            v_id = voted_id
            vote_counts[v_id] = vote_counts.get(v_id, 0) + 1

        max_votes = max(vote_counts.values())
        candidates = [k for k, v in vote_counts.items() if v == max_votes]

        channel = self.bot.get_channel(int(channel_id))
        
        if len(candidates) > 1:
            expelled_id = random.choice(candidates)
            await channel.send(f"投票が割れましたが、厳正なる抽選の結果、<@{expelled_id}> が追放されました。")
        else:
            expelled_id = candidates[0]
            await channel.send(f"投票の結果、もっとも疑わしかった <@{expelled_id}> が追放されました。")

        await self.bot.redis.lrem(members_key, 0, expelled_id)

        await self.bot.redis.delete(vote_key)

        await self.check_win_condition(channel_id)

    async def _handle_vote(self, interaction: discord.Interaction, custom_id: str):
        channel_id = custom_id.split(":")[1]
        voted_id = interaction.data["values"][0]
        user_id = str(interaction.user.id)
        
        members_key = f"werewolf:members:{channel_id}"
        vote_key = f"werewolf:votes:{channel_id}"

        survivors_bin = await self.bot.redis.lrange(members_key, 0, -1)
        survivors = [s for s in survivors_bin]

        if user_id not in survivors:
            return await interaction.response.send_message(
                "あなたは生存者ではないため、投票権がありません。", 
                ephemeral=True
            )

        is_new = await self.bot.redis.hset(vote_key, user_id, voted_id)
        if is_new == 0:
            return await interaction.response.send_message(
                "既に投票済みです。変更はできません。", 
                ephemeral=True
            )

        await interaction.response.send_message(f"<@{voted_id}> に投票しました。", ephemeral=True)

        total_votes = await self.bot.redis.hlen(vote_key)
        if total_votes >= len(survivors):
            try:
                await interaction.message.edit(view=None)
            except:
                pass
            
            await self.process_tally(channel_id)

    async def check_win_condition(self, channel_id) -> bool:
        members_key = f"werewolf:members:{channel_id}"
        roles_key = f"werewolf:roles:{channel_id}"
        
        survivors = [s for s in await self.bot.redis.lrange(members_key, 0, -1)]
        
        all_roles = await self.bot.redis.hgetall(roles_key)
        all_roles = {k: v for k, v in all_roles.items()}
        
        wolf_count = 0
        human_count = 0
        
        for s_id in survivors:
            role = all_roles.get(s_id)
            if role == "人狼":
                wolf_count += 1
            else:
                human_count += 1
        
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return True

        if wolf_count == 0:
            embed = discord.Embed(title="ゲーム終了", description="人狼が全滅しました！\n\n**村人陣営の勝利です！**", color=discord.Color.green())
            await channel.send(embed=embed)
            await self.cleanup_game(channel_id)
            return True

        elif wolf_count >= human_count:
            embed = discord.Embed(title="ゲーム終了", description="人狼の数が人間以上になりました！\n\n**人狼陣営の勝利です！**", color=discord.Color.red())
            await channel.send(embed=embed)
            await self.cleanup_game(channel_id)
            return True

        return False

    async def cleanup_game(self, channel_id):
        keys = [
            f"werewolf:roles:{channel_id}",
            f"werewolf:members:{channel_id}",
            f"werewolf:actions:{channel_id}",
            f"werewolf:votes:{channel_id}",
            f"werewolf:membercount:{channel_id}",
            f"werewolf:owner:{channel_id}",
            f"werewolf:status:{channel_id}",
            f"werewolf:ready:{channel_id}"
        ]

        await self.bot.redis.delete(*keys)

async def setup(bot):
    await bot.add_cog(GameCog(bot))
