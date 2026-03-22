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

class GlobalMoney:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.JST = datetime.timezone(datetime.timedelta(hours=9))

    async def work_execute(self, interaction: discord.Interaction, is_silent: bool = False):
        db = interaction.client.async_db["DashboardBot"].Account
        user_data = await db.find_one({"user_id": interaction.user.id})

        if not user_data:
            await interaction.response.send_message(
                embed=make_embed.error_embed(title="アカウントが存在しません。"), 
                ephemeral=True
            )
            return
        
        now = datetime.datetime.now(self.JST)
        
        last_work = user_data.get("last_work_time")
        
        if last_work:
            if last_work.tzinfo is None:
                last_work = last_work.replace(tzinfo=datetime.timezone.utc)
            
            last_work_jst = last_work.astimezone(self.JST)

            delta = now - last_work_jst
            total_seconds = delta.total_seconds()
            
            if total_seconds < 1200:
                remaining = 1200 - int(total_seconds)
                minutes = remaining // 60
                seconds = remaining % 60
                return await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="まだ働けません！",
                        description=f"あと {minutes}分{seconds}秒 待ってください。"
                    ),
                    ephemeral=True
                )

        reward = random.randint(800, 1200)
        new_money = user_data.get("money", 0) + reward

        await db.update_one(
            {"user_id": interaction.user.id},
            {
                "$set": {
                    "last_work_time": now,
                    "money": new_money
                }
            }
        )

        embed = make_embed.success_embed(
            title="働きました。",
            description=f"{reward}コインを稼ぎました！\n現在の所持金: {new_money}コイン"
        )

        if is_silent:
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.send_message(embed=embed)

    async def slot_execute(self, interaction: discord.Interaction, coin: int, is_slient: bool = False):
        if coin <= 0:
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

        if user_data.get("money", 0) < coin:
            await interaction.response.send_message(embed=make_embed.success_embed(title="コインが足りません。"), ephemeral=True)
            return

        if is_slient:
            await interaction.response.defer(ephemeral=True, thinking=True)
        else:
            await interaction.response.defer()

        await db.update_one({"user_id": interaction.user.id}, {"$inc": {"money": -coin}})

        loading_emoji = "<a:loading:1480529495114121279>"
        embed = make_embed.loading_embed(
            "スロットを引いています・・", 
            description=f"{loading_emoji} | {loading_emoji} | {loading_emoji}"
        )
        if is_slient:
            msg = await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            msg = await interaction.followup.send(embed=embed)

        await asyncio.sleep(2)
        result = [random.choice(SLOT_EMOJIS) for _ in range(3)]
        result_str = f"**{result[0]} | {result[1]} | {result[2]}**"

        is_win = result[0] == result[1] == result[2]
        win_amount = 0

        if is_win:
            multiplier = PAYOUTS.get(result[0], 2)
            win_amount = coin * multiplier
            await db.update_one({"user_id": interaction.user.id}, {"$inc": {"money": win_amount}})
            
            status_title = "おめでとうございます！"
            status_desc = f"{result_str}\n\n揃いました！ **+{win_amount}** コイン獲得！"

            res_embed = make_embed.success_embed(title=status_title, description=status_desc)
        else:
            status_title = "残念..."
            status_desc = f"{result_str}\n\n外れです。 **-{coin}** コイン失いました。"

            res_embed = make_embed.error_embed(title=status_title, description=status_desc)
        
        await interaction.edit_original_response(embed=res_embed)

class SlotModal(discord.ui.Modal, title="スロットに賭ける"):
    coins = discord.ui.TextInput(
        label="賭けるコインの数を入力",
        placeholder="例: 100"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            coin = int(self.coins.value)
        except:
            await interaction.response.send_message(ephemeral=True, embed=make_embed.error_embed(title="スロットに賭けられませんでした。", description="不正な文字列です。"))
            return

        await GlobalMoney(interaction.client).slot_execute(interaction, coin, True)

class AccountsPanel(discord.ui.View):
    def __init__(self, *, timeout = 180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="働く", style=discord.ButtonStyle.blurple)
    async def accounts_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        await GlobalMoney(interaction.client).work_execute(interaction, True)

    @discord.ui.button(label="スロットに賭ける", style=discord.ButtonStyle.red)
    async def accounts_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SlotModal())

class AccountCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.global_money = GlobalMoney(self.bot)
        self.JST = datetime.timezone(datetime.timedelta(hours=9))

    @app_commands.command(name="accounts", description="アカウントのパネルを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def top_accounts(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        db = interaction.client.async_db["DashboardBot"].Account

        if not isinstance(db, AsyncIOMotorCollection):
            return
        
        check = await db.find_one({
            "user_id": interaction.user.id
        })
        if not check:
            await interaction.followup.send(embed=make_embed.error_embed(title="アカウントが存在しません。"))
            return
        
        embed = make_embed.success_embed(title="アカウントの操作パネル")
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        created_date = check.get('created_date')
        time_string = created_date.astimezone(self.JST)

        embed.add_field(name="アカウント作成日", value=time_string.strftime('%Y年%m月%d日 %H時%M分%S秒'), inline=False)

        money = check.get('money')
        embed.add_field(name="所持金", value=f"{money}コイン")
        
        pipeline = [
            {"$sort": {"money": -1}},
            {"$group": {"_id": None, "users": {"$push": "$$ROOT"}}},
            {"$unwind": {"path": "$users", "includeArrayIndex": "rank"}},
            {"$match": {"users.user_id": interaction.user.id}},
            {"$project": {"rank": {"$add": ["$rank", 1]}, "money": "$users.money"}}
        ]

        cursor = db.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if result:
            rank = result[0]["rank"]
            embed.add_field(name="順位", value=f"{rank}位")

        await interaction.followup.send(embed=embed, view=AccountsPanel())

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
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        time_string = created_date.astimezone(self.JST)

        embed.add_field(name="アカウント作成日", value=time_string.strftime('%Y年%m月%d日 %H時%M分%S秒'), inline=False)
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

    @account.command(name="work", description="20分に一回働きます。")
    async def account_work(
        self,
        interaction: discord.Interaction
    ):
        await self.global_money.work_execute(interaction)

    @account.command(name="slot", description="スロットを使用します。")
    async def account_slot(
        self,
        interaction: discord.Interaction,
        コイン: int
    ):
        await GlobalMoney(interaction.client).slot_execute(interaction, コイン, False)

async def setup(bot):
    await bot.add_cog(AccountCog(bot))