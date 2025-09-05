from discord.ext import commands
import discord
import random
import time
from discord import app_commands

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
        """このViewが誰に操作を許可するかを制御"""
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "❌ このゲームはあなたのものではありません！", ephemeral=True
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

    async def get_server_money(self, guild: discord.Guild, author: discord.User):
        db = self.bot.async_db["Main"].ServerMoney
        dbfind = await db.find_one({"_id": f"{guild.id}-{author.id}"}, {"_id": False})
        if not dbfind:
            return 0
        return dbfind.get("count", 0)

    async def get_server_ranking(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].ServerMoney

        cursor = db.find({"Guild": guild.id}).sort("count", -1).limit(10)
        top_users = await cursor.to_list(length=10)

        if not top_users:
            return "このサーバーのランキングはありません。"

        leaderboard_text = f"**{guild.name} のお金持ちランキング**\n\n"

        for i, user_data in enumerate(top_users, start=1):
            member = guild.get_member(user_data["User"])
            name = member.display_name if member else f"ユーザーID: {user_data['User']}"
            leaderboard_text += f"{i}. {name} — {user_data['count']}コイン\n"

        return leaderboard_text

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
        return dbfind.get("count", 0), rr.get("Role", 0)

    async def create_server_items(
        self, guild: discord.Guild, money: int, itemname: str, role: discord.Role = None
    ):
        db = self.bot.async_db["Main"].ServerMoneyItems
        await db.replace_one(
            {"Guild": guild.id, "ItemName": itemname},
            {
                "Guild": guild.id,
                "ItemName": itemname,
                "Role": role.id if role else 0,
                "Money": money,
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
        async for b in db.find({"Guild": guild.id}):
            i_n = b.get("ItemName")
            dbfind = await self.bot.async_db["Main"].ServerMoneyItem.find_one(
                {"_id": f"{guild.id}-{author.id}-{i_n}"}, {"_id": False}
            )
            count = dbfind.get("count") if dbfind else 0
            text += f"{i_n}({b.get('Money', 0)}コイン) .. {count}個\n"
        return text


class GachaGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="gacha", description="ガチャ系のコマンドです。")

    @app_commands.command(name="create", description="ガチャを作成します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
        name="multi-add",
        description="確率操作をするために、一つのアイテムを複数追加します。",
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    @app_commands.checks.has_permissions(manage_guild=True)
    async def economy_gacha_add(
        self, interaction: discord.Interaction, ガチャ名: str, アイテム名: str
    ):
        db = interaction.client.async_db["Main"].ServerMoneyGacha

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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
        if m < 金額:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="残高が足りません。",
                    description=f"コインの裏表を予想をするには100コイン以上が必要です。",
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
                interaction.guild, interaction.user, 金額 + 5
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
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
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
        if m < 金額:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="残高が足りません。",
                    description=f"ブラックジャックをするには100コイン以上が必要です。",
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

    @app_commands.command(name="info", description="ゲームの情報を取得します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_games_info_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.followup.send(
            embed=discord.Embed(title="ゲームの情報", color=discord.Color.blue())
            .add_field(
                name="/economy games coinflip",
                value="コインの裏表を予想します。\n勝ったら賭け金 + 5 コインが返ってきます。\n負けたら賭け金を失います。",
                inline=False,
            )
            .add_field(
                name="/economy games blackjack",
                value="ブラックジャックをします。\n21を超えたらゲームオーバーです。\n勝ったら賭け金が二倍に、\n負けたら賭け金を失います。",
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
            embed=discord.Embed(
                title="金額を追加しました。", color=discord.Color.green()
            )
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
            embed=discord.Embed(
                title="金額を減らしました。", color=discord.Color.green()
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
    ):
        await interaction.response.defer()
        if ロール and not interaction.user.guild_permissions.administrator:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="管理者権限が必要です。", color=discord.Color.red()
                )
            )

        await Money(interaction.client).create_server_items(
            interaction.guild, 値段, アイテム名, ロール
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="アイテムを作成しました。", color=discord.Color.green()
            ).set_footer(text="/economy items で確認できます。")
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
                embed=discord.Embed(
                    title="アイテムを削除しました。", color=discord.Color.green()
                )
            )
        else:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="アイテムが見つかりませんでした。", color=discord.Color.red()
                )
            )


class ServerMoneyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> ServerMoneyCog")

    server_economy = app_commands.Group(
        name="economy", description="サーバー内の経済機能"
    )

    server_economy.add_command(ItemGroup())
    server_economy.add_command(ManageGroup())
    server_economy.add_command(GamesGroup())
    server_economy.add_command(GachaGroup())

    # ====== work ======
    @server_economy.command(name="work", description="30分に1回働けます。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_work_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        m = random.randint(300, 1500)
        current_time = time.time()
        last_message_time = user_last_message_time_work.get(
            f"{interaction.user.id}-{interaction.guild.id}", 0
        )
        if current_time - last_message_time < 1800:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="30分に一回働けます。", color=discord.Color.red()
                ),
                ephemeral=True,
            )

        user_last_message_time_work[f"{interaction.user.id}-{interaction.guild.id}"] = (
            current_time
        )
        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, m
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="働きました。",
                description=f"{m}コイン入手しました。",
                color=discord.Color.green(),
            )
        )

    # ====== balance ======
    @server_economy.command(
        name="balance", description="サーバー内で残高を取得します。"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_balance_server(
        self, interaction: discord.Interaction, メンバー: discord.User = None
    ):
        await interaction.response.defer()
        target = メンバー or interaction.user
        sm = await Money(interaction.client).get_server_money(interaction.guild, target)
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{target.name}の残高です。",
                description=f"{sm}コイン",
                color=discord.Color.green(),
            )
        )

    # ====== ranking ======
    @server_economy.command(name="ranking", description="お金持ちランキングを見ます。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_ranking_server(self, interaction: discord.Interaction):
        text = await Money(interaction.client).get_server_ranking(interaction.guild)
        await interaction.response.send_message(
            embed=discord.Embed(description=text, color=discord.Color.yellow())
        )

    # ====== buy ======
    @server_economy.command(name="buy", description="サーバー内のアイテムを買います。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_buy_server(
        self, interaction: discord.Interaction, アイテム名: str
    ):
        await interaction.response.defer()
        sm = await Money(interaction.client).get_server_items(
            interaction.guild, アイテム名
        )
        if not sm:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="アイテムが見つかりません。", color=discord.Color.red()
                )
            )

        m = await Money(interaction.client).get_server_money(
            interaction.guild, interaction.user
        )
        if m < sm["Money"]:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="残高が足りません。",
                    description=f"「{アイテム名}」を買うには {sm.get('Money', 0)}コインが必要です。",
                    color=discord.Color.red(),
                )
            )

        await Money(interaction.client).add_server_item(
            interaction.guild, interaction.user, アイテム名, 1
        )
        await Money(interaction.client).add_server_money(
            interaction.guild, interaction.user, -sm["Money"]
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="アイテムを買いました。",
                description=f"「{アイテム名}」",
                color=discord.Color.green(),
            )
        )

    # ====== use ======
    @server_economy.command(name="use", description="サーバー内のアイテムを使います。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_use_server(
        self, interaction: discord.Interaction, アイテム名: str
    ):
        await interaction.response.defer()
        sm = await Money(interaction.client).get_server_items(
            interaction.guild, アイテム名
        )
        if not sm:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="アイテムが見つかりません。", color=discord.Color.red()
                )
            )

        count, role = await Money(interaction.client).get_server_item(
            interaction.guild, interaction.user, アイテム名
        )
        if count < 1:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="アイテムを持っていません。", color=discord.Color.red()
                )
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
            embed=discord.Embed(
                title="アイテムを使用しました。",
                description=flag,
                color=discord.Color.green(),
            )
        )

    # ====== items ======
    @server_economy.command(
        name="items", description="サーバー内のアイテム一覧を見ます。"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: (i.guild_id))
    async def economy_items_server(self, interaction: discord.Interaction):
        await interaction.response.defer()
        text = await Money(interaction.client).get_server_items_list(
            interaction.guild, interaction.user
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="アイテムリスト", description=text, color=discord.Color.green()
            )
        )


async def setup(bot):
    await bot.add_cog(ServerMoneyCog(bot))
