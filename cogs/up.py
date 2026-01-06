import math
from discord.ext import commands
import discord
import time
from unbelievaboat import Client
import asyncio
from discord import app_commands
from models import command_disable, make_embed

from datetime import datetime, timedelta, timezone

class UpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> UpCog")

    async def get_bump_status_embed(self, interaction):
        now = datetime.now()
        db_main = self.bot.async_db["Main"]
        db_maintwo = self.bot.async_db["MainTwo"]

        services = {
            "Dicoall": "dicoall",
            "Distopia": "distopia",
            "SabaChannel": "sabachan",
            "DissokuChannel": "dissoku",
            "DisboardChannel": "disboard",
            "DiscafeChannel": "discafe",
            "DisCadiaChannel": "discadia",
            "SharkBotChannel": "sharkbot"
        }

        services_to_slash = {
            "dicoall": "</up:935190259111706754>",
            "distopia": "</bump:1309070135360749620>",
            "sabachan": "</vote:1233256792507682860>",
            "dissoku": "</up:1363739182672904354>",
            "disboard": "</bump:947088344167366698>",
            "discafe": "</up:980136954169536525>",
            "discadia": "</bump:1225075208394768496>",
            "sharkbot": "</global up:1408658655532023855>"
        }

        services_name = {
            "dicoall": "Dicoall",
            "distopia": "Distopia",
            "sabachan": "鯖チャンネル",
            "dissoku": "ディス速",
            "disboard": "ディスボード",
            "discafe": "DCafe",
            "discadia": "Discadia",
            "sharkbot": "SharkBot"
        }

        alert_db = db_main["AlertQueue"]

        async def find_channel(collection):
            try:
                data = await collection.find_one(
                    {"Channel": interaction.channel.id},
                    {"_id": False}
                )
                return data or False
            except Exception:
                return False

        possible = []      # Bump可能
        cooldown = []      # クールタイム中
        disabled = []      # 未設定

        for db_name, service_id in services.items():
            collection = db_main[db_name]
            config = await find_channel(collection)

            if not config:
                disabled.append(service_id)
                continue

            exists = await alert_db.find_one({
                "Channel": interaction.channel.id,
                "ID": service_id,
                "NotifyAt": {"$gt": now}
            })

            if exists:
                remaining = exists["NotifyAt"] - now
                minutes = remaining.seconds // 60
                seconds = remaining.seconds % 60
                cooldown.append(f"{services_name.get(service_id)}（あと {discord.utils.format_dt(discord.utils.utcnow() + timedelta(seconds=seconds, minutes=minutes), 'R')}）")
            else:
                possible.append(f"{services_name.get(service_id)} {services_to_slash.get(service_id, 'スラッシュコマンド取得失敗')}")

        collection = db_maintwo["SharkBotChannel"]
        config = await find_channel(collection)

        if config:
                

            exists = await alert_db.find_one({
                "Channel": interaction.channel.id,
                "ID": "sharkbot",
                "NotifyAt": {"$gt": now}
            })

            if exists:
                remaining = exists["NotifyAt"] - now
                minutes = remaining.seconds // 60
                seconds = remaining.seconds % 60
                cooldown.append(f"SharkBot（あと {discord.utils.format_dt(discord.utils.utcnow() + timedelta(seconds=seconds, minutes=minutes), 'R')}）")
            else:
                possible.append(f"Sharkbot {services_to_slash.get('sharkbot', 'スラッシュコマンド取得失敗')}")

        embed = discord.Embed(
            title="Bump 状況一覧",
            description="🟢 Bump可能:\n{}\n\n🟡 クールダウン中:\n{}".format("\n".join(possible) if possible else "なし", "\n".join(cooldown) if cooldown else "なし"),
            color=discord.Color.green()
        )

        return embed


    async def add_money(self, message: discord.Message):
        return
        db = self.bot.async_db["Main"].BumpUpEconomy
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        if dbfind.get("Money", 0) == 0:
            return
        try:
            client = Client(self.mt)
            guild = await client.get_guild(message.guild.id)
            user = await guild.get_user_balance(message.interaction_metadata.user.id)
            await user.set(cash=dbfind.get("Money", 0) + user.cash)

            await message.channel.send(
                embed=discord.Embed(
                    title="Up・Bumpなどをしたため、給料がもらえました。",
                    description=f"{dbfind.get('Money', 0)}コインです。",
                    color=discord.Color.pink(),
                )
            )
        except Exception:
            return await message.channel.send(
                embed=discord.Embed(
                    title="追加に失敗しました。",
                    description="以下を管理者権限を持っている人に\n認証してもらってください。\nhttps://unbelievaboat.com/applications/authorize?app_id=1326818885663592015",
                    color=discord.Color.yellow(),
                )
            )

    async def mention_get(self, message: discord.Message):
        db = self.bot.async_db["Main"].BumpUpMention
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return "メンションするロールがありません。"
        if dbfind is None:
            return "メンションするロールがありません。"

        try:
            role = message.guild.get_role(dbfind.get("Role", None))
            return role.mention
        except:
            return "メンションするロールがありません。"

    @commands.Cog.listener("on_message")
    async def on_message_up_dicoall(self, message: discord.Message):
        if message.author.id == 903541413298450462:
            try:
                if "サーバーは上部に表示" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(3600)
                    await self.bot.alert_add(
                        "dicoall",
                        message.channel.id,
                        ment,
                        "DicoallをUpしてね！",
                        "</up:935190259111706754> でアップ。",
                        3600,
                    )
                    # await message.channel.send(embed=discord.Embed(title="DicoallをUpしてね！", description="</up:935190259111706754> でアップ。", color=discord.Color.green()), content=ment)
                elif "is displayed at the top." in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(3600)
                    await self.bot.alert_add(
                        "dicoall",
                        message.channel.id,
                        ment,
                        "DicoallをUpしてね！",
                        "</up:935190259111706754> でアップ。",
                        3600,
                    )
                    # await message.channel.send(embed=discord.Embed(title="DicoallをUpしてね！", description="</up:935190259111706754> でアップ。", color=discord.Color.green()), content=ment)
                elif "サーバーが上部に表示されました" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(3600)
                    await self.bot.alert_add(
                        "dicoall",
                        message.channel.id,
                        ment,
                        "DicoallをUpしてね！",
                        "</up:935190259111706754> でアップ。",
                        3600,
                    )
                elif "サーバーが上位に表示されました" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(3600)
                    await self.bot.alert_add(
                        "dicoall",
                        message.channel.id,
                        ment,
                        "DicoallをUpしてね！",
                        "</up:935190259111706754> でアップ。",
                        3600,
                    )
                elif "サーバーがリストの最上段に更新されました" in message.embeds[0].title:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(3600)
                    await self.bot.alert_add(
                        "dicoall",
                        message.channel.id,
                        ment,
                        "DicoallをUpしてね！",
                        "</up:935190259111706754> でアップ。",
                        3600,
                    )
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_bump_distopia(self, message: discord.Message):
        if message.author.id == 1300797373374529557:
            try:
                if "表示順を上げました" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Distopia
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Bumpを検知しました。",
                            description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(7200)
                    await self.bot.alert_add(
                        "distopia",
                        message.channel.id,
                        ment,
                        "DisTopiaをBumpしてね！",
                        "</bump:1309070135360749620> でBump。",
                        7200,
                    )
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_vote_sabachannel(self, message: discord.Message):
        if message.author.id == 1233072112139501608:
            try:
                if "このサーバーに1票を投じました！" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].SabaChannel
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    next = (
                        message.embeds[0]
                        .fields[0]
                        .value.replace("<t:", "")
                        .replace(":R>", "")
                    )
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Voteを検知しました。",
                            description=f"<t:{next}:R>に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)

                    await self.bot.alert_add(
                        "sabachan",
                        message.channel.id,
                        ment,
                        "鯖チャンネルをVoteしてね！",
                        "</vote:1233256792507682860> でVote。",
                        math.ceil(int(next) - time.time()),
                    )

                    # await asyncio.sleep()
                    # await message.channel.send(
                    #     embed=discord.Embed(
                    #         title="鯖チャンネルをVoteしてね！",
                    #         description="</vote:1233256792507682860> でVote。",
                    #         color=discord.Color.green(),
                    #     ),
                    #     content=ment,
                    # )
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_bump_disboard(self, message: discord.Message):
        if message.author.id == 302050872383242240:
            try:
                if "表示順をアップ" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].DisboardChannel
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Bumpを検知しました。",
                            description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    # await asyncio.sleep(7200)
                    await self.bot.alert_add(
                        "disboard",
                        message.channel.id,
                        ment,
                        "DisboardをBumpしてね！",
                        "</bump:947088344167366698> でBump。",
                        7200,
                    )
                    # await message.channel.send(embed=discord.Embed(title="DisboardをBumpしてね！", description="</bump:947088344167366698> でBump。", color=discord.Color.green()), content=ment)
                elif "Bump done" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].DisboardChannel
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Bumpを検知しました。",
                            description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    # await asyncio.sleep(7200)
                    await self.bot.alert_add(
                        "disboard",
                        message.channel.id,
                        ment,
                        "DisboardをBumpしてね！",
                        "</bump:947088344167366698> でBump。",
                        7200,
                    )
                    # await message.channel.send(embed=discord.Embed(title="DisboardをBumpしてね！", description="</bump:947088344167366698> でBump。", color=discord.Color.green()), content=ment)
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_up_discafe(self, message: discord.Message):
        if message.author.id == 850493201064132659:
            try:
                if "サーバーの表示順位を" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].DiscafeChannel
                    try:
                        dbfind = await db.find_one(
                            {"Channel": message.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    ment = await self.mention_get(message)
                    await message.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"一時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )
                    await self.add_money(message)
                    # await asyncio.sleep(3600)
                    await self.bot.alert_add(
                        "discafe",
                        message.channel.id,
                        ment,
                        "DisCafeをUpしてね！",
                        "</up:980136954169536525> でUp。",
                        3600,
                    )
            except:
                return

    async def get_active_level(self, message: discord.Message):
        try:
            if not message.embeds:
                return "取得失敗"
            embed = (
                message.embeds[0]
                .fields[0]
                .value.split("_**ActiveLevel ... ")[1]
                .replace("**_", "")
            )
            return f"{embed}"
        except:
            return "取得失敗"

    async def get_nokori_time(self, message: discord.Message):
        try:
            if not message.embeds:
                return "取得失敗"
            embed = (
                message.embeds[0]
                .fields[0]
                .value.replace("間隔をあけてください(", "")
                .replace(")", "")
            )
            return embed
        except:
            return "取得失敗"

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_dissoku(
        self, before: discord.Message, after: discord.Message
    ):
        if after.author.id == 761562078095867916:
            try:
                if "をアップしたよ!" in after.embeds[0].fields[0].name:
                    db = self.bot.async_db["Main"].DissokuChannel
                    try:
                        dbfind = await db.find_one(
                            {"Channel": after.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return
                    acl = await self.get_active_level(after)
                    ment = await self.mention_get(after)
                    await after.reply(
                        embed=discord.Embed(
                            title="Upを検知しました。",
                            description=f"二時間後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        ).add_field(name="現在のアクティブレベル", value=f"{acl}レベル")
                    )
                    await self.add_money(after)
                    # await asyncio.sleep(7200)
                    await self.bot.alert_add(
                        "dissoku",
                        after.channel.id,
                        ment,
                        "ディス速をUpしてね！",
                        "</up:1363739182672904354> でアップ。",
                        7200,
                    )
                    # await after.channel.send(embed=discord.Embed(title="ディス速をUpしてね！", description="</up:1363739182672904354> でアップ。", color=discord.Color.green()), content=ment)
            except:
                return

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_discadia(
        self, before: discord.Message, after: discord.Message
    ):
        if after.author.id == 1222548162741538938:
            try:
                if "has been successfully bumped!" in after.content:
                    db = self.bot.async_db["Main"].DisCadiaChannel
                    try:
                        dbfind = await db.find_one(
                            {"Channel": after.channel.id}, {"_id": False}
                        )
                    except:
                        return
                    if dbfind is None:
                        return

                    ment = await self.mention_get(after)
                    await after.reply(
                        embed=discord.Embed(
                            title="Bumpを検知しました。",
                            description=f"一日後に通知します。\n以下のロールに通知します。\n{ment}",
                            color=discord.Color.green(),
                        )
                    )

                    await self.bot.alert_add(
                        "discadia",
                        after.channel.id,
                        ment,
                        "DiscadiaをUpしてね！",
                        "</bump:1225075208394768496> でBump。\n注意！オーナーか管理者しかBumpできません！",
                        86400,
                    )
            except:
                return

    bump = app_commands.Group(name="bump", description="Bump通知のコマンドです。")

    @bump.command(name="dicoall", description="DicoallのUp通知を有効化します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def up_dicoall(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].Dicoall
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="Dicoallの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="Dicoallの通知をOFFにしました。")
            )

    @bump.command(name="distopia", description="DisTopiaの通知します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def up_distopia(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].Distopia
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="Distopiaの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="Distopiaの通知をOFFにしました。")
            )

    @bump.command(name="sabachannel", description="鯖チャンネルの通知をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def sabachannel_vote(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].SabaChannel
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="鯖チャンネルの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="鯖チャンネルの通知をOFFにしました。"
                )
            )

    @bump.command(name="dissoku", description="ディス速の通知をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dissoku_up(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].DissokuChannel
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="ディス速の通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="ディス速の通知をOFFにしました。")
            )

    @bump.command(name="disboard", description="Disboardの通知をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def disboard_bump(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].DisboardChannel
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="Disboardの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="Disboardの通知をOFFにしました。")
            )

    @bump.command(name="dcafe", description="Dcafeの通知をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dcafe_up(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].DiscafeChannel
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="DCafeの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="DCafeの通知をOFFにしました。")
            )

    @bump.command(name="discadia", description="discadiaの通知をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def discadia_bump(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["Main"].DisCadiaChannel
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="Discadiaの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="Discadiaの通知をOFFにしました。")
            )

    @bump.command(name="sharkbot", description="SharkBotのUp通知をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def sharkbot_up(self, interaction: discord.Interaction, onか: bool):
        db = self.bot.async_db["MainTwo"].SharkBotChannel
        if onか:
            await db.update_one(
                {"Channel": interaction.channel.id},
                {"$set": {"Channel": interaction.channel.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="SharkBotの通知をONにしました。",
                    description="チャンネルごとにOnにする必要があります。",
                )
            )
        else:
            await db.delete_one({"Channel": interaction.channel.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="SharkBotの通知をOFFにしました。")
            )

    @bump.command(name="mention", description="Bump・Up通知時にメンションをします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def mention_up(
        self, interaction: discord.Interaction, ロール: discord.Role = None
    ):
        db = self.bot.async_db["Main"].BumpUpMention
        if not ロール:
            await db.delete_one({"Channel": interaction.channel.id})
            return await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="Up・Bump通知時にロールを\n通知しないようにしました。"
                )
            )
        await db.update_one(
            {"Channel": interaction.channel.id},
            {"$set": {"Channel": interaction.channel.id, "Role": ロール.id}},
            upsert=True,
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="Up・Bump通知時にロールを\n通知するようにしました。"
            )
        )

    @bump.command(name="pin", description="Bumpなどがあと何分後にできるかをチャンネルの下にピン止めします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def bump_pin(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].LockMessage

        dbfind = await db.find_one(
            {"Channel": interaction.channel.id}, {"_id": False}
        )

        if dbfind:
            await db.delete_one(
                {
                    "Channel": interaction.channel.id,
                }
            )
            await interaction.response.send_message(ephemeral=True, embed=make_embed.error_embed(title="ピン止めメッセージを削除しました。"))
            return

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.red,
            label="削除",
            custom_id="lockmessage_delete+"
        ))

        await interaction.response.defer(ephemeral=True)

        embed = await self.get_bump_status_embed(interaction)

        msg = await interaction.channel.send(embed=embed, view=view)

        await db.update_one(
            {
                "Channel": interaction.channel.id,
                "Guild": interaction.guild.id,
            },
            {
                "$set": {
                    "Channel": interaction.channel.id,
                    "Guild": interaction.guild.id,
                    "Title": embed.title,
                    "Desc": embed.description,
                    "MessageID": msg.id,
                    "Service": "bump_pin"
                }
            },
            upsert=True,
        )

        await interaction.followup.send(embed=make_embed.success_embed(title="ピン止めメッセージを作成しました。"), ephemeral=True)


async def setup(bot):
    await bot.add_cog(UpCog(bot))
