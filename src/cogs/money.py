import asyncio
import datetime
from discord.ext import commands
import discord
import random
import time
from discord import app_commands
import io
import json

from models import make_embed

user_last_message_time_work = {}

# トランプカード
suits = ["♠", "♥", "♦", "♣"]
ranks = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}


def draw_card(deck):
    return deck.pop()


def calculate_score(hand):
    score = sum(ranks[card[:-1]] for card in hand)

    aces = sum(1 for card in hand if card.startswith("A"))
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score


class ScratchCardview(discord.ui.View):
    def __init__(self, player: discord.User, coin: int):
        super().__init__(timeout=60)
        self.player = player
        self.game_over = False
        self.coin = coin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "このゲームはあなたのものではありません！", ephemeral=True
            )
            return False
        return True

    async def end_game(self, interaction: discord.Interaction, hit_id: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.message.edit(
            embed=discord.Embed(
                title="スクラッチカードを削っています・・", color=discord.Color.green()
            ),
            view=None,
        )
        await asyncio.sleep(3)

        rand = random.randint(1, 3)
        if rand == hit_id:
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, -self.coin
            )
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, self.coin * 2
            )
            await interaction.message.edit(
                embed=make_embed.success_embed(title="当たりました。")
            )
        else:
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, -self.coin
            )
            await interaction.message.edit(
                embed=make_embed.error_embed(title="外れました・・")
            )

    @discord.ui.button(label="1つめ", style=discord.ButtonStyle.blurple)
    async def _1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction, 1)

    @discord.ui.button(label="2つめ", style=discord.ButtonStyle.blurple)
    async def _2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction, 2)

    @discord.ui.button(label="3つめ", style=discord.ButtonStyle.blurple)
    async def _3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.end_game(interaction, 3)


class BlackjackView(discord.ui.View):
    def __init__(self, player: discord.User, player_hand, dealer_hand, deck, coin: int):
        super().__init__(timeout=60)
        self.player = player
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.game_over = False
        self.coin = coin

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "このゲームはあなたのものではありません！", ephemeral=True
            )
            return False
        return True

    async def update_message(self, interaction, msg=""):
        player_score = calculate_score(self.player_hand)
        dealer_score = calculate_score(self.dealer_hand[:1])
        embed = discord.Embed(
            title="🃏 ブラックジャック", description=msg, color=discord.Color.green()
        )
        embed.add_field(
            name="あなたの手札",
            value=f"{' '.join(self.player_hand)} (得点: {player_score})",
            inline=False,
        )
        embed.add_field(
            name="ディーラーの手札",
            value=f"{self.dealer_hand[0]} ?? (得点: {dealer_score}+)",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def end_game(self, interaction: discord.Interaction):
        self.game_over = True
        self.clear_items()

        while calculate_score(self.dealer_hand) < 17:
            self.dealer_hand.append(draw_card(self.deck))

        player_score = calculate_score(self.player_hand)
        dealer_score = calculate_score(self.dealer_hand)

        if player_score > 21:
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, -self.coin
            )
            result = "バースト！あなたの負けです…"
        elif dealer_score > 21 or player_score > dealer_score:
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, -self.coin
            )
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, self.coin * 2
            )
            result = "あなたの勝ち！"
        elif player_score < dealer_score:
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, -self.coin
            )
            result = "あなたの負け…"
        else:
            result = "引き分け！"

        embed = discord.Embed(
            title="🃏 ブラックジャック", description=result, color=discord.Color.green()
        )
        embed.add_field(
            name="あなたの手札",
            value=f"{' '.join(self.player_hand)} (得点: {player_score})",
            inline=False,
        )
        embed.add_field(
            name="ディーラーの手札",
            value=f"{' '.join(self.dealer_hand)} (得点: {dealer_score})",
            inline=False,
        )
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="ヒット", style=discord.ButtonStyle.green)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game_over:
            return
        self.player_hand.append(draw_card(self.deck))
        if calculate_score(self.player_hand) > 21:
            await self.end_game(interaction)
        else:
            await self.update_message(interaction, "カードを引きました！")

    @discord.ui.button(label="スタンド", style=discord.ButtonStyle.red)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game_over:
            return
        await self.end_game(interaction)


class Money:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        pass

    async def clear_cooldown(
        self,
        guild: discord.Guild,
        author: discord.User,
        cooldown_type: str = "work",
    ):
        db = self.bot.async_db["Main"].ServerMoneyCooldwon
        key = f"{guild.id}-{author.id}-{cooldown_type}"

        await db.delete_one(
            {
                "_id": key,
            }
        )

        return True, 0

    async def add_cooldown(
        self,
        guild: discord.Guild,
        author: discord.User,
        cooldown: int = 3600,
        cooldown_type: str = "work",
    ):
        db = self.bot.async_db["Main"].ServerMoneyCooldwon
        key = f"{guild.id}-{author.id}-{cooldown_type}"
        current_time = time.time()

        user_data = await db.find_one({"_id": key})

        if user_data:
            last_time = user_data.get("last_time", 0)
            elapsed = current_time - last_time

            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                return False, remaining

            await db.update_one(
                {"_id": key},
                {"$set": {"last_time": current_time}},
            )

        else:
            await db.insert_one(
                {
                    "_id": key,
                    "Guild": guild.id,
                    "User": author.id,
                    "last_time": current_time,
                    "type": cooldown_type,
                }
            )

        return True, 0

    async def add_server_money(
        self, guild: discord.Guild, author: discord.User, coin: int
    ):
        db = self.bot.async_db["Main"].ServerMoney
        user_data = await db.find_one({"_id": f"{guild.id}-{author.id}"})
        if user_data:
            await db.update_one(
                {"_id": f"{guild.id}-{author.id}"}, {"$inc": {"count": coin}}
            )
        else:
            await db.insert_one(
                {
                    "_id": f"{guild.id}-{author.id}",
                    "count": coin,
                    "Guild": guild.id,
                    "User": author.id,
                }
            )
        return True

    async def add_server_money_bank(
        self, guild: discord.Guild, author: discord.User, coin: int
    ):
        db = self.bot.async_db["Main"].ServerMoney
        user_data = await db.find_one({"_id": f"{guild.id}-{author.id}"})
        if user_data:
            await db.update_one(
                {"_id": f"{guild.id}-{author.id}"}, {"$inc": {"bank": coin}}
            )
        else:
            await db.insert_one(
                {
                    "_id": f"{guild.id}-{author.id}",
                    "count": 0,
                    "bank": coin,
                    "Guild": guild.id,
                    "User": author.id,
                }
            )
        return True

    async def get_server_money(self, guild: discord.Guild, author: discord.User):
        db = self.bot.async_db["Main"].ServerMoney
        dbfind = await db.find_one({"_id": f"{guild.id}-{author.id}"}, {"_id": False})
        if not dbfind:
            return 0
        return dbfind.get("count", 0)

    async def get_server_money_bank(self, guild: discord.Guild, author: discord.User):
        db = self.bot.async_db["Main"].ServerMoney
        dbfind = await db.find_one({"_id": f"{guild.id}-{author.id}"}, {"_id": False})
        if not dbfind:
            return 0
        return dbfind.get("bank", 0)

    async def get_server_ranking(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].ServerMoney

        cursor = db.find({"Guild": guild.id})
        all_users = await cursor.to_list(length=100)

        if not all_users:
            return "このサーバーのランキングはありません。"

        ranked_users = sorted(
            all_users, key=lambda u: u.get("count", 0) + u.get("bank", 0), reverse=True
        )[:10]

        leaderboard_text = f"**{guild.name} のお金持ちランキング**\n\n"

        c_n = await self.get_currency_name(guild)

        for i, user_data in enumerate(ranked_users, start=1):
            user_id = user_data["User"]
            member = guild.get_member(user_id)

            name = member.display_name if member else f"不明: {user_id}"
            total_money = user_data.get("count", 0) + user_data.get("bank", 0)

            leaderboard_text += f"{i}. {name} — {total_money:,}{c_n}\n"

        return leaderboard_text

    # 通貨名管理
    async def set_currency_name(self, guild: discord.Guild, name: str):
        db = self.bot.async_db["Main"].ServerMoneyCurrency
        _id = f"{guild.id}"
        user_data = await db.find_one({"_id": _id})
        if user_data:
            await db.update_one({"_id": _id}, {"$set": {"Name": name}})
        else:
            await db.insert_one({"_id": _id, "Guild": guild.id, "Name": name})
        return True

    async def get_currency_name(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].ServerMoneyCurrency
        _id = f"{guild.id}"
        dbfind = await db.find_one({"_id": _id}, {"_id": False})
        if not dbfind:
            return "コイン"
        return dbfind.get("Name", "コイン")

    # --- アイテム管理 ---
    async def add_server_item(
        self, guild: discord.Guild, author: discord.User, itemname: str, count: int
    ):
        db = self.bot.async_db["Main"].ServerMoneyItem
        _id = f"{guild.id}-{author.id}-{itemname}"
        user_data = await db.find_one({"_id": _id})
        if user_data:
            await db.update_one({"_id": _id}, {"$inc": {"count": count}})
        else:
            await db.insert_one(
                {
                    "_id": _id,
                    "Guild": guild.id,
                    "User": author.id,
                    "ItemName": itemname,
                    "count": count,
                }
            )
        return True

    async def get_server_item(
        self, guild: discord.Guild, author: discord.User, itemname: str
    ):
        db = self.bot.async_db["Main"].ServerMoneyItem
        _id = f"{guild.id}-{author.id}-{itemname}"
        dbfind = await db.find_one({"_id": _id}, {"_id": False})
        if not dbfind:
            return 0, 0
        rr = await self.get_server_items(guild, itemname)
        if not rr:
            return dbfind.get("count", 0), 0
        return dbfind.get("count", 0), rr.get("Role", 0), rr.get("DM", "なし")

    async def create_server_items(
        self,
        guild: discord.Guild,
        money: int,
        itemname: str,
        role: discord.Role = None,
        dm: str = None,
    ):
        db = self.bot.async_db["Main"].ServerMoneyItems
        await db.update_one(
            {"Guild": guild.id, "ItemName": itemname},
            {
                "$set": {
                    "Guild": guild.id,
                    "ItemName": itemname,
                    "Role": role.id if role else 0,
                    "DM": dm if dm else "なし",
                    "Money": money,
                }
            },
            upsert=True,
        )

    async def remove_server_items(self, guild: discord.Guild, itemname: str):
        db = self.bot.async_db["Main"].ServerMoneyItems
        result = await db.delete_one({"Guild": guild.id, "ItemName": itemname})
        return result.deleted_count > 0

    async def get_server_items(self, guild: discord.Guild, itemname: str):
        db = self.bot.async_db["Main"].ServerMoneyItems
        dbfind = await db.find_one(
            {"Guild": guild.id, "ItemName": itemname}, {"_id": False}
        )
        return dbfind

    async def get_server_items_list(self, guild: discord.Guild, author: discord.User):
        text = ""
        db = self.bot.async_db["Main"].ServerMoneyItems
        c_n = await self.get_currency_name(guild)
        async for b in db.find({"Guild": guild.id}):
            i_n = b.get("ItemName")
            dbfind = await self.bot.async_db["Main"].ServerMoneyItem.find_one(
                {"_id": f"{guild.id}-{author.id}-{i_n}"}, {"_id": False}
            )
            count = dbfind.get("count") if dbfind else 0
            text += f"{i_n}({b.get('Money', 0)}{c_n}) .. {count}個\n"
        return text


class GachaGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="gacha", description="ガチャ系のコマンドです。")

    @app_commands.command(name="create", description="ガチャを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_create(
        self,
        interaction: discord.Interaction,
        名前: str,
        金額: int,
        説明: str = "ガチャが引けます。",
        ロール: discord.Role = None,
    ):
        db = interaction.client.async_db["Main"].ServerMoneyGacha

        await db.replace_one(
            {"Guild": interaction.guild.id, "Name": 名前},
            {
                "Guild": interaction.guild.id,
                "Name": 名前,
                "Money": 金額,
                "Text": 説明,
                "Item": [],
                "Role": ロール.id if ロール else 0,
            },
            upsert=True,
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="ガチャを作成しました。", color=discord.Color.green()
            )
        )

    @app_commands.command(
        name="import", description="ガチャをjsonからインポートします。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_json_import(
        self, interaction: discord.Interaction, ファイル: discord.Attachment
    ):
        await interaction.response.defer()
        try:
            res = json.loads(await ファイル.read())
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Json読み込みに失敗しました。", color=discord.Color.red()
                )
            )

        for i_n in res.get("Item", []):
            sm = await Money(interaction.client).get_server_items(
                interaction.guild, i_n.get("Name")
            )
            if not sm:
                await Money(interaction.client).create_server_items(
                    interaction.guild, i_n.get("Money"), i_n.get("Name")
                )

        db = interaction.client.async_db["Main"].ServerMoneyGacha

        await db.replace_one(
            {"Guild": interaction.guild.id, "Name": res.get("Name", "ガチャ名")},
            {
                "Guild": interaction.guild.id,
                "Name": res.get("Name", "ガチャ名"),
                "Money": res.get("Money", "ガチャ金額"),
                "Text": res.get("Text", "ガチャ説明"),
                "Item": [i.get("Name") for i in res.get("Item", [])],
                "Role": res.get("Role", 0),
            },
            upsert=True,
        )

        await interaction.followup.send(
            embed=discord.Embed(
                title="ガチャをインポートしました。", color=discord.Color.green()
            )
        )

    @app_commands.command(
        name="export", description="ガチャをjsonにエクスポートします。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_json_export(
        self, interaction: discord.Interaction, ガチャ名: str
    ):
        await interaction.response.defer()
        db = interaction.client.async_db["Main"].ServerMoneyGacha
        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.followup.send(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        if dbfind.get("Item", []) == []:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="アイテムの無いガチャはエクスポートできません。",
                    color=discord.Color.red(),
                )
            )

        js = {}
        js["Name"] = ガチャ名
        js["Text"] = dbfind.get("Text", "ガチャ説明")
        js["Money"] = dbfind.get("Money", 0)

        i_ = []
        for i_n in dbfind.get("Item", []):
            sm = await Money(interaction.client).get_server_items(
                interaction.guild, i_n
            )
            if sm:
                i_.append({"Name": i_n, "Money": sm.get("Money")})

        js["Item"] = i_

        s = io.StringIO(json.dumps(js))

        await interaction.followup.send(file=discord.File(s, "gacha.json"))
        s.close()

    @app_commands.command(
        name="multi-add",
        description="確率操作をするために、一つのアイテムを複数追加します。",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_multi_add(
        self,
        interaction: discord.Interaction,
        ガチャ名: str,
        アイテム名: str,
        個数: int,
    ):
        if 個数 > 10:
            return await interaction.response.send_message(
                ephemeral=True, content="11個以上一回で追加できません。"
            )
        await interaction.response.defer()
        db = interaction.client.async_db["Main"].ServerMoneyGacha

        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.followup.send(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        sm = await Money(interaction.client).get_server_items(
            interaction.guild, アイテム名
        )
        if not sm:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="アイテムが見つかりません。",
                    color=discord.Color.red(),
                    description="先に、`/economy item create`で作成してください。",
                )
            )

        for c in range(個数):
            await db.update_one(
                {"Guild": interaction.guild.id, "Name": ガチャ名},
                {"$push": {"Item": アイテム名}},
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title="ガチャに複数同じアイテムを追加しました。",
                color=discord.Color.green(),
            )
        )

    @app_commands.command(name="add", description="ガチャにアイテムを追加します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_add(
        self, interaction: discord.Interaction, ガチャ名: str, アイテム名: str
    ):
        db = interaction.client.async_db["Main"].ServerMoneyGacha

        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        sm = await Money(interaction.client).get_server_items(
            interaction.guild, アイテム名
        )
        if not sm:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="アイテムが見つかりません。",
                    color=discord.Color.red(),
                    description="先に、`/economy item create`で作成してください。",
                )
            )

        await db.update_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名},
            {"$push": {"Item": アイテム名}},
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="ガチャにアイテムを追加しました。", color=discord.Color.green()
            )
        )

    @app_commands.command(name="remove", description="ガチャのアイテムを削除します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_remove(
        self, interaction: discord.Interaction, ガチャ名: str, アイテム名: str
    ):
        db = interaction.client.async_db["Main"].ServerMoneyGacha

        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        await db.update_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名},
            {"$pull": {"Item": アイテム名}},
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="ガチャからアイテムを削除しました。", color=discord.Color.green()
            )
        )

    @app_commands.command(
        name="clear", description="ガチャのアイテムをリセットします。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_clear(
        self, interaction: discord.Interaction, ガチャ名: str
    ):
        db = interaction.client.async_db["Main"].ServerMoneyGacha

        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        if dbfind.get("Item", []) == []:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャにアイテムがありません。"
            )

        await db.update_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"$set": {"Item": []}}
        )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="ガチャのアイテムをリセットしました。",
                color=discord.Color.green(),
            )
        )

    @app_commands.command(
        name="items", description="ガチャから出るアイテムを設定します。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_items(
        self, interaction: discord.Interaction, ガチャ名: str
    ):
        db = interaction.client.async_db["Main"].ServerMoneyGacha
        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        if dbfind.get("Item", []) == []:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャにアイテムがありません。"
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="ガチャから出るアイテムをリストです。",
                description=f"\n".join(dbfind.get("Item", [])),
                color=discord.Color.green(),
            )
        )

    @app_commands.command(name="list", description="ガチャリストを確認します。")
    async def economy_gacha_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = interaction.client.async_db["Main"].ServerMoneyGacha

        text = ""

        async for b in db.find({"Guild": interaction.guild.id}):
            text += f"{b.get('Name')}({b.get('Money', 0)}コイン) .. {b.get('Text', 'ガチャが引けます。')}\n"

        await interaction.followup.send(
            embed=discord.Embed(
                title="サーバー内のガチャリスト",
                description=text,
                color=discord.Color.blue(),
            )
        )

    @app_commands.command(name="buy", description="ガチャを引きます。")
    async def economy_gacha_buy(self, interaction: discord.Interaction, ガチャ名: str):
        db = interaction.client.async_db["Main"].ServerMoneyGacha
        dbfind = await db.find_one(
            {"Guild": interaction.guild.id, "Name": ガチャ名}, {"_id": False}
        )
        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャが見つかりません。"
            )

        if dbfind.get("Item", []) == []:
            return await interaction.response.send_message(
                ephemeral=True, content="ガチャにアイテムがありません。"
            )

        if dbfind.get("Role", 0) != 0:
            if (
                interaction.guild.get_role(dbfind.get("Role", 0))
                not in interaction.user.roles
            ):
                return await interaction.response.send_message(
                    ephemeral=True,
                    content="指定したロールを持っていないためガチャを引けません。",
                )

        await interaction.response.defer()

        if dbfind["Money"] != 0:
            m = await Money(interaction.client).get_server_money(
                interaction.guild, interaction.user
            )
            if m < dbfind["Money"]:
                return await interaction.followup.send(
                    ephemeral=True,
                    embed=discord.Embed(
                        title="ガチャを引くためのお金がありません。",
                        color=discord.Color.red(),
                    ),
                )

        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, -dbfind.get("Money", 1)
        )

        ch = random.choice(dbfind.get("Item", []))

        sm = await Money(interaction.client).get_server_items(interaction.guild, ch)
        if not sm:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="ガチャを引いたが、アイテムが出てきませんでした。",
                    color=discord.Color.red(),
                )
            )

        await Money(interaction.client).add_server_item(
            interaction.guild, interaction.user, ch, 1
        )

        await interaction.followup.send(
            embed=discord.Embed(
                title=f"ガチャを引きました。",
                description=f"「{ch}」が出てきました。",
                color=discord.Color.green(),
            )
        )


class GamesGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="games", description="ゲームで遊びます。")

    @app_commands.command(name="coinflip", description="コインの裏表を予想します。")
    async def economy_games_coinflip_server(
        self, interaction: discord.Interaction, 裏表: str, 金額: int
    ):
        if 金額 < 100:
            return await interaction.response.send_message(
                "金額は100以上で入力してください。", ephemeral=True
            )

        m = await Money(interaction.client).get_server_money(
            interaction.guild, interaction.user
        )
        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        if m < 金額:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="残高が足りません。",
                    description=f"コインの裏表を予想をするには100{c_n}以上が必要です。",
                    color=discord.Color.red(),
                )
            )

        if 裏表.lower() not in ["表", "裏"]:
            return await interaction.response.send_message(
                "コインの裏表を入力してください。\n例: /economy games coinflip 裏",
                ephemeral=True,
            )

        await interaction.response.defer()
        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, -金額
        )
        result = random.choice(["表", "裏"])
        if 裏表.lower() == result:
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, 金額 * 2
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="コインの裏表を予想しました。",
                    description=f"結果は {result} で、あなたの勝ちです！",
                    color=discord.Color.green(),
                )
            )
        else:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="コインの裏表を予想しました。",
                    description=f"結果は {result} で、あなたの負けです…",
                    color=discord.Color.red(),
                )
            )

    @app_commands.command(name="blackjack", description="ブラックジャックをします。")
    async def economy_games_blackjack_server(
        self, interaction: discord.Interaction, 金額: int
    ):
        if 金額 < 100:
            return await interaction.response.send_message(
                "金額は100以上で入力してください。", ephemeral=True
            )

        m = await Money(interaction.client).get_server_money(
            interaction.guild, interaction.user
        )
        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        if m < 金額:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="残高が足りません。",
                    description=f"ブラックジャックをするには100{c_n}以上が必要です。",
                    color=discord.Color.red(),
                )
            )

        deck = [rank + suit for rank in ranks for suit in suits]
        random.shuffle(deck)

        player_hand = [draw_card(deck), draw_card(deck)]
        dealer_hand = [draw_card(deck), draw_card(deck)]

        view = BlackjackView(interaction.user, player_hand, dealer_hand, deck, 金額)
        embed = discord.Embed(
            title="🃏 ブラックジャック",
            description="ゲーム開始！",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="あなたの手札",
            value=f"{' '.join(player_hand)} (得点: {calculate_score(player_hand)})",
            inline=False,
        )
        embed.add_field(
            name="ディーラーの手札", value=f"{dealer_hand[0]} ??", inline=False
        )

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name="scratch-card", description="スクラッチカードを削ります。"
    )
    async def economy_games_scratch_card(
        self, interaction: discord.Interaction, 金額: int
    ):
        if 金額 < 100:
            return await interaction.response.send_message(
                "金額は100以上で入力してください。", ephemeral=True
            )

        m = await Money(interaction.client).get_server_money(
            interaction.guild, interaction.user
        )
        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        if m < 金額:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="残高が足りません。",
                    description=f"スクラッチカードをするには100{c_n}以上が必要です。",
                    color=discord.Color.red(),
                )
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="スクラッチカード",
                description="以下の三つのどれかのボタンを押してください。",
                color=discord.Color.green(),
            ),
            view=ScratchCardview(interaction.user, 金額),
        )

    @app_commands.command(name="info", description="ゲームの情報を取得します。")
    async def economy_games_info_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(
            embed=make_embed.success_embed(title="ゲームの情報")
            .add_field(
                name="/economy games coinflip",
                value="コインの裏表を予想します。\n勝ったら賭け金×2が返ってきます。\n負けたら賭け金を失います。",
                inline=False,
            )
            .add_field(
                name="/economy games blackjack",
                value="ブラックジャックをします。\n21を超えたらゲームオーバーです。\n勝ったら賭け金が二倍に、\n負けたら賭け金を失います。",
                inline=False,
            )
            .add_field(
                name="/economy games scratch-card",
                value="スクラッチカードを削ります。\n三つのどれかを削るゲームです。",
                inline=False,
            )
        )


class ManageGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="manage", description="お金を管理します。")

    @app_commands.command(name="add", description="お金を追加します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_manage_money_add(
        self, interaction: discord.Interaction, メンバー: discord.Member, 金額: int
    ):
        await interaction.response.defer()
        await Money(interaction.client).add_server_money(
            interaction.guild, メンバー, 金額
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(title="金額を追加しました。")
        )

    @app_commands.command(name="remove", description="お金を減らします。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_manage_money_remove(
        self, interaction: discord.Interaction, メンバー: discord.Member, 金額: int
    ):
        await interaction.response.defer()
        await Money(interaction.client).add_server_money(
            interaction.guild, メンバー, -金額
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(title="金額を減らしました。")
        )

    @app_commands.command(name="currency", description="新しい通貨名を設定します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_manage_currency(
        self, interaction: discord.Interaction, 通貨名: str
    ):
        await interaction.response.defer()
        await Money(interaction.client).set_currency_name(interaction.guild, 通貨名)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="新しい通貨名を設定しました。", description=f"通貨名: {通貨名}"
            )
        )

    @app_commands.command(
        name="chatmoney", description="会話するたびにお金がもらえるようにします。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_manage_chatmoney(
        self, interaction: discord.Interaction, 金額: int = None
    ):
        db = interaction.client.async_db["Main"].ServerChatMoney
        if not 金額:
            await db.delete_many({"Guild": interaction.guild.id})
            return await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="会話をしてもお金をもらえなくしました。"
                )
            )

        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$set": {"Guild": interaction.guild.id, "Money": 金額}},
            upsert=True,
        )

        c_n = await Money(interaction.client).get_currency_name(interaction.guild)

        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="会話するたびに、お金がもらえるようにしました。",
                description=f"{金額}{c_n}です。",
            )
        )

    @app_commands.command(
        name="clear-cooldown",
        description="指定ユーザーのクールダウンをリセットします。",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        種類=[
            app_commands.Choice(name="仕事", value="work"),
            app_commands.Choice(name="犯罪", value="crime"),
            app_commands.Choice(name="物乞い", value="beg"),
        ]
    )
    async def economy_manage_clear_cooldown(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User,
        種類: app_commands.Choice[str],
    ):
        await Money(interaction.client).clear_cooldown(
            interaction.guild, ユーザー, 種類.value
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="クールダウンをリセットしました。",
                description=f"{ユーザー.mention} の {種類.name} のクールダウンをリセットしました。",
            )
        )


class ItemGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="item", description="アイテム管理系のコマンドです。")

    @app_commands.command(name="create", description="アイテムを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_item_create_server(
        self,
        interaction: discord.Interaction,
        アイテム名: str,
        値段: int,
        ロール: discord.Role = None,
        使用時にdmに送信するメッセージ: str = None,
    ):
        await interaction.response.defer()
        if ロール and not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="管理者権限が必要です。")
            )

        await Money(interaction.client).create_server_items(
            interaction.guild, 値段, アイテム名, ロール, 使用時にdmに送信するメッセージ
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(title="アイテムを作成しました。").set_footer(
                text="/economy items で確認できます。"
            )
        )

    @app_commands.command(name="remove", description="アイテムを削除します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_item_remove_server(
        self, interaction: discord.Interaction, アイテム名: str
    ):
        await interaction.response.defer()
        b = await Money(interaction.client).remove_server_items(
            interaction.guild, アイテム名
        )
        if b:
            await interaction.followup.send(
                embed=make_embed.success_embed(title="アイテムを削除しました。")
            )
        else:
            await interaction.followup.send(
                embed=make_embed.error_embed(title="アイテムが見つかりませんでした。")
            )


class ShopPanelGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="shop", description="ショップパネルを作成するためのコマンドたちです。"
        )

    @app_commands.command(
        name="item", description="アイテムショップパネルを作成します。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def economy_shop_item_create(
        self,
        interaction: discord.Interaction,
        タイトル: str,
        アイテム名1: str,
        アイテム名2: str = None,
        アイテム名3: str = None,
        アイテム名4: str = None,
        アイテム名5: str = None,
    ):
        await interaction.response.defer()
        items = [
            i
            for i in [アイテム名1, アイテム名2, アイテム名3, アイテム名4, アイテム名5]
            if i is not None
        ]
        embed = discord.Embed(title=タイトル, color=discord.Color.green())
        view = discord.ui.View()
        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        for _, i in enumerate(items):
            db = await Money(interaction.client).get_server_items(interaction.guild, i)
            if not db:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title=f"{i} というアイテムが見つかりません。"
                    )
                )
            embed.add_field(name=i, value=f"{db.get('Money', 0)} {c_n}", inline=False)
            view.add_item(discord.ui.Button(label=i, custom_id=f"item_shop+{_}"))
        await interaction.channel.send(embed=embed, view=view)
        await interaction.delete_original_response()


class ServerMoneyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> ServerMoneyCog")

    @commands.Cog.listener("on_message")
    async def on_message_chatmoney(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        db = self.bot.async_db["Main"].ServerChatMoney
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except Exception:
            return

        if dbfind is None:
            return

        await Money(self.bot).add_server_money(
            message.guild, message.author, dbfind.get("Money", 0)
        )

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_shop_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id.startswith("item_shop+"):
                    await interaction.response.defer(ephemeral=True)
                    f = interaction.message.embeds[0].fields[
                        int(custom_id.split("item_shop+")[1])
                    ]

                    m = await Money(interaction.client).get_server_money(
                        interaction.guild, interaction.user
                    )
                    if m < int(f.value.split(" ")[0]):
                        c_n = await Money(interaction.client).get_currency_name(
                            interaction.guild
                        )
                        return await interaction.followup.send(
                            embed=make_embed.error_embed(
                                title="残高が足りません。",
                                description=f"「{f.name}」を買うには {f.value.split(' ')[0]}{c_n}が必要です。",
                            ),
                            ephemeral=True,
                        )

                    await Money(interaction.client).add_server_money(
                        interaction.guild, interaction.user, -int(f.value.split(" ")[0])
                    )

                    await Money(self.bot).add_server_item(
                        interaction.guild, interaction.user, f.name, 1
                    )
                    await interaction.followup.send(
                        embed=make_embed.success_embed(
                            title="アイテムを買いました。", description=f"「{f.name}」"
                        ),
                        ephemeral=True,
                    )
        except:
            return

    server_economy = app_commands.Group(
        name="economy", description="サーバー内の経済機能"
    )

    server_economy.add_command(ItemGroup())
    server_economy.add_command(ManageGroup())
    server_economy.add_command(GamesGroup())
    server_economy.add_command(GachaGroup())
    server_economy.add_command(ShopPanelGroup())

    # ====== work ======
    @server_economy.command(name="work", description="60分に1回働けます。")
    async def economy_work_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        m = random.randint(300, 1500)
        ok, remaining = await Money(interaction.client).add_cooldown(
            guild=interaction.guild,
            author=interaction.user,
            cooldown=3600,
            cooldown_type="work",
        )

        if not ok:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="まだ働けません。",
                    description=f"あと {str(datetime.timedelta(seconds=remaining))} 待ってください。",
                )
            )

        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, m
        )
        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="働きました。", description=f"{m}{c_n}入手しました。"
            )
        )

    @server_economy.command(name="beg", description="物乞いをしてお金を得ます。")
    async def economy_beg_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        m = random.randint(10, 300)
        ok, remaining = await Money(interaction.client).add_cooldown(
            guild=interaction.guild,
            author=interaction.user,
            cooldown=600,
            cooldown_type="beg",
        )

        if not ok:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="まだ物乞いできません。",
                    description=f"あと {str(datetime.timedelta(seconds=remaining))} 待ってください。",
                )
            )

        if random.randint(1, 2) == 2:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="物乞いに失敗しました。",
                    description="誰もお金をくれませんでした。",
                )
            )

        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, m
        )
        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="物乞いをしました。", description=f"{m}{c_n}入手しました。"
            )
        )

    @server_economy.command(
        name="crime", description="犯罪をしてお金を得ます。(リスクあり)"
    )
    @app_commands.choices(
        内容=[
            app_commands.Choice(name="強盗", value="gotou"),
            app_commands.Choice(name="詐欺", value="sagi"),
            app_commands.Choice(name="横領", value="ouyou"),
            app_commands.Choice(name="闇バイト", value="yamibaito"),
        ]
    )
    async def economy_crime_server(
        self, interaction: discord.Interaction, 内容: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        m = random.randint(100, 1000)
        ok, remaining = await Money(interaction.client).add_cooldown(
            guild=interaction.guild,
            author=interaction.user,
            cooldown=3600,
            cooldown_type="crime",
        )

        if not ok:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="まだ犯罪できません。",
                    description=f"あと {str(datetime.timedelta(seconds=remaining))} 待ってください。",
                )
            )

        c_n = await Money(interaction.client).get_currency_name(interaction.guild)
        if random.randint(1, 4) == 4:
            lost = random.randint(100, 500)
            await Money(interaction.client).add_server_money(
                interaction.guild, interaction.user, -lost
            )
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title=f"{内容.name}に失敗しました。",
                    description=f"{lost}{c_n}を失いました。",
                )
            )

        if 内容.value == "gotou":
            m = random.randint(500, 3000)
        elif 内容.value == "sagi":
            m = random.randint(300, 2000)
        elif 内容.value == "ouyou":
            m = random.randint(200, 1500)
        else:
            m = random.randint(100, 1000)

        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, m
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{内容.name}をしました。", description=f"{m}{c_n}入手しました。"
            )
        )

    # ====== balance ======
    @server_economy.command(
        name="balance", description="サーバー内で残高を取得します。"
    )
    async def economy_balance_server(
        self, interaction: discord.Interaction, メンバー: discord.User = None
    ):
        await interaction.response.defer()
        target = メンバー or interaction.user
        m = Money(interaction.client)
        sm = await m.get_server_money(interaction.guild, target)
        sb_m = await m.get_server_money_bank(interaction.guild, target)
        c_n = await m.get_currency_name(interaction.guild)
        await interaction.followup.send(
            embed=make_embed.success_embed(title=f"{target.name}の残高です。")
            .add_field(name="手持ち", value=f"{sm}{c_n}")
            .add_field(name="預金", value=f"{sb_m}{c_n}")
        )

    @server_economy.command(
        name="pay", description="指定したメンバーにサーバー内通貨を送金します。"
    )
    async def economy_pay_server(
        self, interaction: discord.Interaction, メンバー: discord.User, 金額: int
    ):
        await interaction.response.defer()
        m = Money(interaction.client)
        guild = interaction.guild
        user = interaction.user

        c_n = await m.get_currency_name(guild)
        sender_balance = await m.get_server_money(guild, user)

        if メンバー.id == user.id:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="送金エラー", description="自分自身には送金できません。"
                )
            )

        if メンバー.bot:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="送金エラー", description="Botには送金できません。"
                )
            )

        if 金額 <= 0:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="送金エラー", description="0以下の金額は送金できません。"
                )
            )

        if sender_balance < 金額:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="残高不足",
                    description=f"あなたの残高（{sender_balance} {c_n}）より多い金額は送金できません。",
                )
            )

        await m.add_server_money(guild, user, -金額)
        await m.add_server_money(guild, メンバー, 金額)

        new_sender_balance = await m.get_server_money(guild, user)
        receiver_balance = await m.get_server_money(guild, メンバー)

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="送金完了",
                description=(
                    f"{メンバー.mention} に {金額} {c_n} を送金しました。\n\n"
                    f"あなたの残高: {new_sender_balance} {c_n}\n"
                    f"相手の残高: {receiver_balance} {c_n}"
                ),
            )
        )

    @server_economy.command(name="deposit", description="銀行にお金を預けます。")
    async def economy_deposit_server(self, interaction: discord.Interaction, 金額: int):
        await interaction.response.defer()
        m = Money(interaction.client)
        sm = await m.get_server_money(interaction.guild, interaction.user)
        c_n = await m.get_currency_name(interaction.guild)
        if sm < 金額:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title=f"{sm} {c_n}より大きい金額は預けられません。"
                )
            )
        await m.add_server_money(interaction.guild, interaction.user, -金額)
        await m.add_server_money_bank(interaction.guild, interaction.user, 金額)
        b_m = await m.get_server_money_bank(interaction.guild, interaction.user)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"銀行にお金を預けました。",
                description=f"預けた{c_n}: {金額}\n現在の{c_n}: {b_m}",
            )
        )

    @server_economy.command(name="withdraw", description="銀行からお金を引き出します。")
    async def economy_withdraw_server(
        self, interaction: discord.Interaction, 金額: int
    ):
        await interaction.response.defer()
        m = Money(interaction.client)
        bm = await m.get_server_money_bank(interaction.guild, interaction.user)
        c_n = await m.get_currency_name(interaction.guild)
        if bm < 金額:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title=f"{bm} {c_n}より大きい金額は引き出せません。"
                )
            )
        await m.add_server_money_bank(interaction.guild, interaction.user, -金額)
        await m.add_server_money(interaction.guild, interaction.user, 金額)
        _m = await m.get_server_money(interaction.guild, interaction.user)
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"銀行からお金を引き出しました。",
                description=f"引き出した{c_n}: {金額}\n現在の手持ち: {_m}",
            )
        )

    # ====== ranking ======
    @server_economy.command(name="ranking", description="お金持ちランキングを見ます。")
    async def economy_ranking_server(self, interaction: discord.Interaction):
        text = await Money(interaction.client).get_server_ranking(interaction.guild)
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="お金持ちランキングです。", description=text
            )
        )

    # ====== buy ======
    @server_economy.command(name="buy", description="サーバー内のアイテムを買います。")
    async def economy_buy_server(
        self, interaction: discord.Interaction, アイテム名: str
    ):
        await interaction.response.defer()
        sm = await Money(interaction.client).get_server_items(
            interaction.guild, アイテム名
        )
        if not sm:
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="アイテムが見つかりません。")
            )

        c_n = await Money(interaction.client).get_currency_name(interaction.guild)

        m = await Money(interaction.client).get_server_money(
            interaction.guild, interaction.user
        )
        if m < sm["Money"]:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="残高が足りません。",
                    description=f"「{アイテム名}」を買うには {sm.get('Money', 0)}{c_n}が必要です。",
                )
            )

        await Money(interaction.client).add_server_item(
            interaction.guild, interaction.user, アイテム名, 1
        )
        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, -sm["Money"]
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="アイテムを買いました。"
            )
            .add_field(name="買ったアイテム", value=アイテム名, inline=False)
            .add_field(name="アイテムを使用する方法", value="/economy useにアイテム名を指定すれば\n使用することができます。", inline=False)
        )

    # ====== use ======
    @server_economy.command(name="use", description="サーバー内のアイテムを使います。")
    async def economy_use_server(
        self, interaction: discord.Interaction, アイテム名: str
    ):
        await interaction.response.defer()
        sm = await Money(interaction.client).get_server_items(
            interaction.guild, アイテム名
        )
        if not sm:
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="アイテムが見つかりません。")
            )

        count, role, dm = await Money(interaction.client).get_server_item(
            interaction.guild, interaction.user, アイテム名
        )
        if count < 1:
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="アイテムを持っていません。")
            )

        flag = "アイテムが一つ使用されました。\n"

        if role != 0:
            role_obj = interaction.guild.get_role(role)
            if role_obj:
                await interaction.user.add_roles(role_obj)
                flag += "ロールが追加されました。"
            else:
                flag += "ロールが追加できませんでした。"

        await Money(interaction.client).add_server_item(
            interaction.guild, interaction.user, アイテム名, -1
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="アイテムを使用しました。", description=flag
            )
        )

        if dm != "なし":
            await interaction.user.send(
                embed=discord.Embed(
                    title=f"{アイテム名}にメッセージが添付されていました！",
                    description=f"内容\n```{dm}```",
                    color=discord.Color.blue(),
                ).set_footer(
                    text=interaction.guild.name,
                    icon_url=interaction.guild.icon.url
                    if interaction.guild.icon
                    else None,
                )
            )

    # ====== items ======
    @server_economy.command(
        name="items", description="サーバー内のアイテム一覧を見ます。"
    )
    async def economy_items_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        text = await Money(interaction.client).get_server_items_list(
            interaction.guild, interaction.user
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="アイテムリストです。", description=text
            )
        )


async def setup(bot):
    await bot.add_cog(ServerMoneyCog(bot))
