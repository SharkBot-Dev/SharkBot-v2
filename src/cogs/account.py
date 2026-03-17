import asyncio
import datetime
import random
import secrets

from discord.ext import commands
import discord
from discord import app_commands
import urllib.parse

from models import make_embed
from motor.motor_asyncio import AsyncIOMotorCollection

SLOT_EMOJIS = ["🍎", "🍊", "🍇", "💎", "7️⃣"]
PAYOUTS = {
    "7️⃣": 5,
    "💎": 3,
    "🍎": 2,
    "🍊": 2,
    "🍇": 2,
}

class AccountCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.JST = datetime.timezone(datetime.timedelta(hours=9))

    account = app_commands.Group(
        name="account",
        description="SharkBot関連のアカウントのコマンドです。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=True),
    )

    @account.command(name="create", description="アカウントを作成します。")
    async def account_create(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.defer()

        db = interaction.client.async_db["DashboardBot"].Account

        if not isinstance(db, AsyncIOMotorCollection):
            return
        
        check = await db.find_one({
            "user_id": interaction.user.id
        })
        if check:
            await interaction.followup.send(embed=make_embed.error_embed(title="すでにアカウントが存在します。"))
            return

        await db.insert_one({
            "user_id": interaction.user.id,
            "user_name": interaction.user.name,
            "avatar_url": interaction.user.display_avatar.url,
            "created_date": datetime.datetime.now(),
            "last_date": datetime.datetime.now(),
            "money": 100,
            "is_ban": False
        })

        await interaction.followup.send(embed=make_embed.success_embed(title="アカウントを作成しました。", description="/account status で\nアカウントのステータスを\n確認できます。"))

    @account.command(name="join", description="シームレスにサーバー参加するための認証をします。")
    async def account_join(
        self,
        interaction: discord.Interaction
    ):
        db = interaction.client.async_db["DashboardBot"].JoinGuildAccount
        code = secrets.token_urlsafe(30)
        await db.update_one({
            "UserID": str(interaction.user.id)
        }, {"$set": {
            "Code": code,
            "Token": None,
            "RefToken": None
        }}, upsert=True)
        await interaction.response.send_message(embed=make_embed.success_embed(title="認証をしてください。", description="以下のボタンから認証をしてください。\n\nこの認証をすることで、招待リンクを使用せずに\nサーバー参加することができるようになります。"), view=discord.ui.View().add_item(discord.ui.Button(label="認証をする", url=f"https://discord.com/oauth2/authorize?client_id=1322100616369147924&response_type=code&redirect_uri=https%3A%2F%2Fwww.sharkbot.xyz%2Fregister&scope=guilds+identify+guilds.join&state={urllib.parse.quote(code)}")), ephemeral=True)

    @account.command(name="status", description="アカウントのステータスを表示します。")
    async def account_status(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User = None
    ):
        user = ユーザー if ユーザー else interaction.user

        await interaction.response.defer()

        db = interaction.client.async_db["DashboardBot"].Account

        if not isinstance(db, AsyncIOMotorCollection):
            return
        
        check = await db.find_one({
            "user_id": user.id
        })
        if not check:
            await interaction.followup.send(embed=make_embed.error_embed(title="アカウントが存在しません。"))
            return
        
        created_date = check.get('created_date')
        money = check.get('money')
        
        # 埋め込み
        embed = make_embed.success_embed(title=f"{user.name}さんのアカウント")
        embed.add_field(name="アカウント作成日", value=created_date.astimezone(self.JST), inline=False)
        embed.add_field(name="所持金", value=f"{money}コイン")

        # ランキングを取得
        pipeline = [
            {"$sort": {"money": -1}},
            {"$group": {"_id": None, "users": {"$push": "$$ROOT"}}},
            {"$unwind": {"path": "$users", "includeArrayIndex": "rank"}},
            {"$match": {"users.user_id": user.id}},
            {"$project": {"rank": {"$add": ["$rank", 1]}, "money": "$users.money"}}
        ]

        cursor = db.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if result:
            rank = result[0]["rank"]
            embed.add_field(name="順位", value=f"{rank}位")

        await interaction.followup.send(embed=embed)

    @account.command(name="leaderboard", description="アカウントのリーダーボードを表示します。")
    async def account_leaderboard(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.defer()

        db = interaction.client.async_db["DashboardBot"].Account

        cursor = db.find().sort("money", -1).limit(10)
        top_users = await cursor.to_list(length=10)

        if not top_users:
            await interaction.followup.send("まだデータがありません。")
            return

        description = ""
        for i, user in enumerate(top_users, start=1):
            name = user.get("user_name", "不明なユーザー")
            money = user.get("money", 0)
            
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"**{i}.**")
            description += f"{medal} {name} — `{money:,}コイン` \n"

        embed = make_embed.success_embed(
            title="所持金リーダーボード",
            description=description
        )

        await interaction.followup.send(embed=embed)

    @account.command(name="daily", description="一日一回のコインを受け取ります。")
    async def account_daily(
        self,
        interaction: discord.Interaction
    ):
        db = interaction.client.async_db["DashboardBot"].Account

        check = await db.find_one({
            "user_id": interaction.user.id
        })
        if not check:
            await interaction.response.send_message(embed=make_embed.error_embed(title="アカウントが存在しません。"), ephemeral=True)
            return

        await interaction.response.send_message(ephemeral=True, view=discord.ui.View().add_item(discord.ui.Button(label="投票する", url="https://top.gg/ja/bot/1322100616369147924/vote")), embed=make_embed.success_embed(title="コインを受け取る", description="以下のボタンから投票するとコインがもらえます。"))

    @account.command(name="slot", description="スロットを使用します。")
    async def account_slot(
        self,
        interaction: discord.Interaction,
        コイン: int
    ):
        if コイン <= 0:
            await interaction.response.send_message(embed=make_embed.error_embed(title="1コイン以上賭けてください。"), ephemeral=True)
            return

        db = interaction.client.async_db["DashboardBot"].Account
        user_data = await db.find_one({"user_id": interaction.user.id})

        if not user_data:
            await interaction.response.send_message(
                embed=make_embed.error_embed(title="アカウントが存在しません。"), 
                ephemeral=True
            )
            return

        if user_data.get("money", 0) < コイン:
            await interaction.response.send_message(embed=make_embed.success_embed(title="コインが足りません。"), ephemeral=True)
            return

        await interaction.response.defer()

        await db.update_one({"user_id": interaction.user.id}, {"$inc": {"money": -コイン}})

        loading_emoji = "<a:loading:1480529495114121279>"
        embed = make_embed.loading_embed(
            "スロットを引いています・・", 
            description=f"{loading_emoji} | {loading_emoji} | {loading_emoji}"
        )
        msg = await interaction.followup.send(embed=embed)

        await asyncio.sleep(2)
        result = [random.choice(SLOT_EMOJIS) for _ in range(3)]
        result_str = f"**{result[0]} | {result[1]} | {result[2]}**"

        is_win = result[0] == result[1] == result[2]
        win_amount = 0

        if is_win:
            multiplier = PAYOUTS.get(result[0], 2)
            win_amount = コイン * multiplier
            await db.update_one({"user_id": interaction.user.id}, {"$inc": {"money": win_amount}})
            
            status_title = "おめでとうございます！"
            status_desc = f"{result_str}\n\n揃いました！ **+{win_amount}** コイン獲得！"

            res_embed = make_embed.success_embed(title=status_title, description=status_desc)
        else:
            status_title = "残念..."
            status_desc = f"{result_str}\n\n外れです。 **-{コイン}** コイン失いました。"

            res_embed = make_embed.error_embed(title=status_title, description=status_desc)
        
        await interaction.edit_original_response(embed=res_embed)

async def setup(bot):
    await bot.add_cog(AccountCog(bot))