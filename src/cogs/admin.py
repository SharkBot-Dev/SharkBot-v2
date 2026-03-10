import ast
import datetime
from pathlib import Path
import re
import sys
import traceback
from discord.ext import commands
import discord
import urllib.parse

from models import make_embed, save_commands, translate
from consts import settings

from discord import app_commands

import asyncio

import importlib.util

import aiohttp

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.DEBUG_LIST = [1343124570131009579, 1424924684566396950, 706905953320304772, 1361909980873359390]
        print("init -> AdminCog")

    async def get_admins(self, user: discord.User):
        db = self.bot.async_db["Main"].BotAdmins
        user_data = await db.find_one({"User": user.id})

        if not user_data:
            return False
        else:
            return True

    # サポートサーバー: 1343124570131009579
    # テストサーバー: 1424924684566396950
    # SGCサーバー: 706905953320304772
    # 絵文字サーバーたち: 1361909980873359390

    admin = app_commands.Group(
        name="admin",
        description="SharkBot管理者向けのコマンドです。",
        guild_ids=[1343124570131009579, 1424924684566396950, 706905953320304772, 1361909980873359390]
    )

    @admin.command(name="cogs", description="cogの操作をします。")
    @app_commands.choices(
        操作の種類=[
            app_commands.Choice(name="リロード", value="reload"),
            app_commands.Choice(name="モジュールリロード", value="modulereload"),
            app_commands.Choice(name="ロード", value="load"),
        ]
    )
    async def cogs_setting(
        self,
        interaction: discord.Interaction,
        操作の種類: app_commands.Choice[str],
        cog名: str,
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作の種類.value == "reload":
            await self.bot.reload_extension(f"cogs.{cog名}")
            return await interaction.followup.send(
                embed=make_embed.success_embed(title="Cogをリロードしました。")
            )
        elif 操作の種類.value == "load":
            await self.bot.load_extension(f"cogs.{cog名}")
            return await interaction.followup.send(
                embed=make_embed.success_embed(title="Cogをロードしました。")
            )
        elif 操作の種類.value == "modulereload":
            if cog名 == "bot":
                return await interaction.followup.send(
                    embed=make_embed.error_embed(title="Bot本体をリロードできません。")
                )
            if cog名 == "api":
                return await interaction.followup.send(
                    embed=make_embed.error_embed(title="API本体をリロードできません。")
                )

            try:
                if cog名 in sys.modules:
                    importlib.reload(sys.modules[cog名])
                else:
                    importlib.import_module(cog名)

                return await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="モジュールをリロードしました。",
                        description=f"`{cog名}` を再読み込みしました。",
                    )
                )

            except Exception as e:
                tb = traceback.format_exc()
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="モジュールリロードに失敗しました。",
                        description=f"```{tb}```",
                    )
                )

    @admin.command(name="sync", description="スラッシュコマンドを同期します。")
    async def sync_setting(self, interaction: discord.Interaction, サーバーid: str = None):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if サーバーid:

            guild = discord.Object(id=int(サーバーid))
            await self.bot.tree.sync(guild=guild)
        else:
            await self.bot.tree.sync()

        await interaction.followup.send(
            embed=make_embed.success_embed(title="スラッシュコマンドを同期しました。")
        )

    @admin.command(name="debug-sync", description="スラッシュコマンドをデバッグサーバーに同期します。")
    async def debug_sync_setting(self, interaction: discord.Interaction):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        for d in self.DEBUG_LIST:
            guild = discord.Object(id=d)
            await self.bot.tree.sync(guild=guild)

        text = '\n'.join([str(_) for _ in self.DEBUG_LIST])

        await interaction.followup.send(
            embed=make_embed.success_embed(title="以下のサーバーに同期しました。", description=text)
        )

    @admin.command(
        name="ipban", description="IPを一部サイトで制限します。"
    )
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def ip_ban(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        内容: str,
        理由: str,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        db = self.bot.async_db["MainTwo"].BlockIP

        if 操作.value == "add":
            await db.insert_one({
                "ip": 内容,
                "reason": 理由
            })
        else:
            await db.delete_one({
                "ip": 内容
            })

        await interaction.followup.send(embed=make_embed.success_embed(title=f"{内容} を{操作.name}しました。"))

    @admin.command(
        name="ban", description="Botからbanをします。サーバーからはbanされません。"
    )
    @app_commands.choices(
        操作の種類=[
            app_commands.Choice(name="サーバー", value="server"),
            app_commands.Choice(name="ユーザー", value="user"),
        ]
    )
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def ban_bot(
        self,
        interaction: discord.Interaction,
        操作の種類: app_commands.Choice[str],
        操作: app_commands.Choice[str],
        内容: str,
        理由: str,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作の種類.value == "user":
            if 操作.value == "add":
                if int(内容) == 1335428061541437531:
                    return
                user = await self.bot.fetch_user(int(内容))
                db = self.bot.async_db["Main"].BlockUser
                await db.update_one(
                    {"User": user.id},
                    {
                        "$set": {
                            "User": user.id,
                            "Reason": 理由,
                            "Runner": interaction.user.id,
                        }
                    },
                    upsert=True,
                )
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"{user.name}をBotからBANしました。"
                    )
                )

                await self.bot.get_channel(1359793645842206912).send(
                    embed=make_embed.success_embed(
                        title="ブロックしているユーザーを追加しました。"
                    )
                    .add_field(name="ユーザー名", value=user.name, inline=False)
                    .add_field(name="ユーザーID", value=str(user.id), inline=False)
                    .add_field(name="理由", value=理由, inline=False)
                    .set_footer(
                        text=f"実行者: {interaction.user.name}",
                        icon_url=interaction.user.avatar.url
                        if interaction.user.avatar
                        else interaction.user.default_avatar.url,
                    )
                )
            elif 操作.value == "remove":
                user = await self.bot.fetch_user(int(内容))
                db = self.bot.async_db["Main"].BlockUser
                await db.delete_one({"User": user.id})
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"{user.name}のBotからのBanを解除しました。"
                    )
                )
        elif 操作の種類.value == "server":
            if 操作.value == "add":
                db = self.bot.async_db["Main"].BlockGuild
                await db.update_one(
                    {"Guild": int(内容)},
                    {
                        "$set": {
                            "Guild": int(内容),
                            "Reason": 理由,
                            "Runner": interaction.user.id,
                        }
                    },
                    upsert=True,
                )
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"サーバーをBotからBANしました。"
                    )
                )
            elif 操作.value == "remove":
                db = self.bot.async_db["Main"].BlockGuild
                await db.delete_one({"Guild": int(内容)})
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"サーバーのBotからのBanを解除しました。"
                    )
                )

    @admin.command(
        name="server", description="Botの入っているサーバーを管理します。(退出など)"
    )
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="退出", value="leave"),
            app_commands.Choice(name="警告", value="warn"),
            app_commands.Choice(name="情報取得", value="getinfo"),
        ]
    )
    async def manage_server(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        内容: str,
        理由: str = None,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作.value == "leave":
            await self.bot.get_guild(int(内容)).leave()
            await interaction.followup.send(
                embed=make_embed.success_embed(title="サーバーから退出しました。")
            )
        elif 操作.value == "warn":
            if 理由 is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(title="警告理由を入力してください。")
                )

            await self.bot.get_guild(int(内容)).owner.send(
                embed=discord.Embed(
                    title=f"{self.bot.get_guild(int(内容))} はSharkBotから警告されました。",
                    description=f"```{理由}```",
                    color=discord.Color.yellow(),
                ).set_footer(text="詳しくはSharkBot公式サポートサーバーまで。")
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="サーバーを警告しました。")
            )
        elif 操作.value == "getinfo":
            guild = self.bot.get_guild(int(内容))

            embed = make_embed.success_embed(title=f"{guild.name}の情報")
            embed.add_field(name="サーバー名", value=guild.name)
            embed.add_field(name="サーバーID", value=str(guild.id))
            embed.add_field(name="チャンネル数", value=f"{len(guild.channels)}個")
            embed.add_field(name="絵文字数", value=f"{len(guild.emojis)}個")
            embed.add_field(name="ロール数", value=f"{len(guild.roles)}個")
            embed.add_field(name="ロールリスト", value="`/listing role`\nで見れます。")
            embed.add_field(name="メンバー数", value=f"{guild.member_count}人")
            embed.add_field(
                name="Nitroブースト",
                value=f"{guild.premium_subscription_count}人",
            )
            embed.add_field(
                name="オーナー名",
                value=self.bot.get_user(guild.owner_id).name
                if self.bot.get_user(guild.owner_id)
                else "取得失敗",
            )
            embed.add_field(name="オーナーID", value=str(guild.owner_id))
            JST = datetime.timezone(datetime.timedelta(hours=9))
            embed.add_field(name="作成日", value=guild.created_at.astimezone(JST))

            onlines = [m for m in guild.members if m.status == discord.Status.online]
            idles = [m for m in guild.members if m.status == discord.Status.idle]
            dnds = [m for m in guild.members if m.status == discord.Status.dnd]
            offlines = [m for m in guild.members if m.status == discord.Status.offline]

            pcs = [m for m in guild.members if m.client_status.desktop]
            sms = [m for m in guild.members if m.client_status.mobile]
            webs = [m for m in guild.members if m.client_status.web]

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

            if guild.icon:
                await interaction.followup.send(
                    embed=embed.set_thumbnail(url=guild.icon.url)
                )
            else:
                await interaction.followup.send(embed=embed)

    @admin.command(name="debug", description="デバッグコマンドを実行します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="埋め込み解析", value="embedget"),
            app_commands.Choice(name="頭文字リセット", value="prefixreset"),
            app_commands.Choice(name="デバッグメッセージ", value="debugmsg"),
        ]
    )
    async def debug_admin(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        内容: str,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        await interaction.response.defer()

        if 操作.value == "embedget":
            msg = await interaction.channel.fetch_message(int(内容))
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="埋め込みを解析しました。",
                    description=f"```{msg.embeds[0].to_dict()}```",
                ),
            )
        elif 操作.value == "prefixreset":
            db = self.bot.async_db["DashboardBot"].CustomPrefixBot
            result = await db.delete_one(
                {
                    "Guild": int(内容),
                }
            )
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.success_embed(title="頭文字をリセットしました。"),
            )
        else:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.success_embed(title="デバッグしました。"),
            )

    @admin.command(name="member", description="管理者を追加します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def admins_member(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        ユーザー: discord.User,
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )
        db = self.bot.async_db["Main"].BotAdmins
        if 操作.value == "add":
            await db.update_one(
                {"User": ユーザー.id}, {"$set": {"User": ユーザー.id}}, upsert=True
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="管理者を追加しました。")
            )
        else:
            await db.delete_one({"User": ユーザー.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="管理者を削除しました。")
            )

    @admin.command(name="premium", description="プレミアムユーザーを手動で追加します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def admin_premium(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        ユーザー: discord.User,
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        db = self.bot.async_db["Main"].PremiumUser
        if 操作.value == "add":
            await db.update_one(
                {"User": ユーザー.id}, {"$set": {"User": ユーザー.id}}, upsert=True
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="プレミアムユーザーを追加しました。"
                )
            )
        else:
            await db.delete_one({"User": ユーザー.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="プレミアムユーザーを削除しました。"
                )
            )

    @admin.command(name="money", description="コインを追加・削除します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
            app_commands.Choice(name="設定", value="set"),
        ]
    )
    async def money_admin(self, interaction: discord.Interaction, ユーザー: discord.User, 操作: app_commands.Choice[str], 数値: int):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        db = interaction.client.async_db["DashboardBot"].Account

        check = await db.find_one({
            "user_id": ユーザー.id
        })
        if not check:
            await interaction.followup.send(embed=make_embed.error_embed(title="アカウントが存在しません。"))
            return
        
        if 操作.value == "add":
            await db.update_one({"user_id": ユーザー.id}, {"$inc": {"money": 数値}})
        elif 操作.value == "remove":
            await db.update_one({"user_id": ユーザー.id}, {"$inc": {"money": 数値}})
        else:
            await db.update_one({"user_id": ユーザー.id}, {"$set": {"money": 数値}})

        await interaction.followup.send(embed=make_embed.success_embed(title=f"{ユーザー.name}のコインを{操作.name}しました。"))

    @admin.command(name="redis", description="Redisにアクセスします。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="取得 (Get/GetAll)", value="get"),
            app_commands.Choice(name="設定・追加 (Set/Push/Add)", value="set"),
            app_commands.Choice(name="削除 (Del)", value="remove")
        ],
        タイプ=[
            app_commands.Choice(name="文字列 (String)", value="string"),
            app_commands.Choice(name="リスト (List)", value="list"),
            app_commands.Choice(name="セット (Set)", value="set"),
            app_commands.Choice(name="ハッシュ (Hash)", value="hash")
        ]
    )
    async def admin_redis(
        self, 
        interaction: discord.Interaction, 
        操作: app_commands.Choice[str], 
        タイプ: app_commands.Choice[str], 
        キー: str, 
        値: str = None
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(title="あなたはSharkBotのオーナーではないため実行できません。")
            )

        await interaction.response.send_message(embed=make_embed.loading_embed(title="操作中です..."))

        if not self.bot.redis:
            return await interaction.edit_original_response(embed=make_embed.error_embed(title="Redisに接続されていません。"))

        op = 操作.value
        data_type = タイプ.value
        res_title = ""
        res_desc = ""

        try:
            if op == "get":
                if data_type == "string":
                    res_desc = await self.bot.redis.get(キー)
                elif data_type == "list":
                    res_desc = await self.bot.redis.lrange(キー, 0, -1)
                elif data_type == "set":
                    res_desc = list(await self.bot.redis.smembers(キー))
                elif data_type == "hash":
                    res_desc = await self.bot.redis.hgetall(キー)
                
                res_title = "取得しました。"

            elif op == "set":
                if not 値:
                    return await interaction.edit_original_response(embed=make_embed.error_embed(title="設定には値が必要です。"))
                
                if data_type == "string":
                    await self.bot.redis.set(キー, 値)
                elif data_type == "list":
                    await self.bot.redis.rpush(キー, 値)
                elif data_type == "set":
                    await self.bot.redis.sadd(キー, 値)
                elif data_type == "hash":
                    if ":" not in 値:
                        return await interaction.edit_original_response(embed=make_embed.error_embed(title="Hash形式は 'フィールド:値' で入力してください。"))
                    f, v = 値.split(":", 1)
                    await self.bot.redis.hset(キー, f, v)
                
                res_title = "設定・追加しました。"
                res_desc = 値

            elif op == "remove":
                await self.bot.redis.delete(キー)
                res_title = "削除しました。"
                res_desc = f"Key `{キー}` を削除しました。"

            embed = make_embed.success_embed(title=res_title, description=f"```py\n{res_desc}\n```")
            embed.set_footer(text=f"Key: {キー} | Type: {data_type}")
            await interaction.edit_original_response(embed=embed)

        except Exception as e:
            await interaction.edit_original_response(embed=make_embed.error_embed(title="操作に失敗しました。", description=str(e)))

    @admin.command(name="short", description="SharkBotの運営する短縮URLサービスを操作します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="コード情報取得", value="codelookup"),
            app_commands.Choice(name="コード使用者取得", value="userlookup")
        ]
    )
    async def admin_short(
        self, 
        interaction: discord.Interaction, 
        操作: app_commands.Choice[str], 
        内容: str
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(title="あなたはSharkBotのオーナーではないため実行できません。")
            )
        
        await interaction.response.defer(ephemeral=True)

        target_code = None
        if 内容.startswith("https://"):
            match = re.search(r"shb\.red/s/([a-zA-Z0-9_-]+)", 内容)
            if match:
                target_code = match.group(1)
            else:
                return await interaction.followup.send(embed=make_embed.error_embed(title="URLからコードを抽出できませんでした。"))
        else:
            target_code = 内容.strip()

        async with aiohttp.ClientSession() as session:
            if 操作.value == "codelookup":
                url = f"https://shb.red/admin/lookup/{urllib.parse.quote(target_code)}"
                headers = {"X-Admin-Token": settings.SHORT_TOKEN}
                
                async with session.get(url, headers=headers) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        msg = error_data.get("message", "不明なエラーが発生しました。")
                        return await interaction.followup.send(embed=make_embed.error_embed(title=f"取得失敗 ({response.status})", description=msg))

                    data = await response.json()

                    code = data.get("code", "不明")
                    created_at = data.get("created_at", "不明")
                    ip = data.get("ip", "不明")
                    original_url = data.get("original_url", "不明")

                    embed = make_embed.success_embed(
                        title="作成者情報を取得しました",
                        description=f"**コード:** `{code}`\n**作成日:** `{created_at}`\n**作成者IP:** `{ip}`\n**元URL:** {original_url}"
                    )
                    await interaction.followup.send(embed=embed)

            elif 操作.value == "userlookup":
                url = f"https://shb.red/admin/history/{urllib.parse.quote(target_code)}"
                async with session.get(url, headers={"X-Admin-Token": settings.SHORT_TOKEN}) as response:
                    if response.status != 200:
                        return await interaction.followup.send(embed=make_embed.error_embed(title="履歴の取得に失敗しました。"))
                    
                    data = await response.json()
                    history = data.get("history", [])
                    
                    if not history:
                        return await interaction.followup.send(content="アクセス履歴はありませんでした。")

                    history_str = "\n".join([f"・{h['accessed_at']} ({h['ip']})" for h in history[:10]])
                    await interaction.followup.send(embed=make_embed.success_embed(title=f"アクセス履歴 (最新10件)", description=history_str))

            else:
                await interaction.followup.send(content="未実装の操作です。")

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        # await guild.leave()
        db = self.bot.async_db["Main"].BlockUser
        try:
            profile = await db.find_one({"User": guild.owner_id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                await asyncio.sleep(1)
                await self.bot.get_channel(1359793645842206912).send(
                    embed=make_embed.success_embed(
                        title=f"ブロックされているサーバーから退出しました。"
                    )
                    .set_thumbnail(url=guild.icon.url if guild.icon else None)
                    .add_field(name=f"サーバー名", value=guild.name, inline=False)
                    .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
                    .add_field(
                        name=f"理由", value=profile.get("Reason", "なし"), inline=False
                    )
                )
                return
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(
            embed=discord.Embed(
                title=f"サーバーに参加しました。",
                color=discord.Color.green(),
            )
            .set_thumbnail(url=guild.icon.url if guild.icon else None)
            .add_field(name=f"サーバー名", value=guild.name, inline=False)
            .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
        )

        db = self.bot.async_db["Main"].BlockGuild

        try:
            profile = await db.find_one({"Guild": guild.id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                await asyncio.sleep(1)
                await self.bot.get_channel(1359793645842206912).send(
                    embed=make_embed.success_embed(
                        title=f"ブロックされているサーバーから退出しました。"
                    )
                    .set_thumbnail(url=guild.icon.url if guild.icon else None)
                    .add_field(name=f"サーバー名", value=guild.name, inline=False)
                    .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
                    .add_field(
                        name=f"理由", value=profile.get("Reason", "なし"), inline=False
                    )
                )
                return
        except:
            return

    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(
            embed=discord.Embed(
                title=f"サーバーから退出しました。", color=discord.Color.red()
            )
            .set_thumbnail(url=guild.icon.url if guild.icon else None)
            .add_field(name=f"サーバー名", value=guild.name, inline=False)
            .add_field(name=f"サーバーID", value=str(guild.id), inline=False)
        )


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
