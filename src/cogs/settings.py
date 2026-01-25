from collections import defaultdict
import datetime
import re
from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
import sys
import random
import time
import asyncio
import aiohttp
from discord import app_commands

from consts import mongodb
from models import block, command_disable, make_embed, translate

COOLDOWN_TIME_KEIGO = 5
cooldown_keigo_time = {}
COOLDOWN_TIME_TRANS = 3
cooldown_trans_time = {}
COOLDOWN_TIME_EXPAND = 5
cooldown_expand_time = {}
cooldown_auto_protect_time = {}
cooldown_auto_translate = {}
cooldown_auto_thread = {}
cooldown_dice = {}

ratelimit_search = {}

cooldown_sharkass = {}

cooldown_pets = {}

cooldown_check_url = {}

cooldown_engonly = {}

cooldown_disable_command = {}

cooldown_sharkbot_mention = {}

message_counts = defaultdict(int)
spam_threshold = 3
time_window = 5

message_counts_userapp = defaultdict(int)


class CommandDisableChannel(commands.CommandError):
    pass


class BanBotError(commands.CommandError):
    pass


DISCORD_EMOJI_RE = re.compile(r"<(a?):([a-zA-Z0-9_]{1,32}):([0-9]{17,22})>")
UNICODE_EMOJI_RE = re.compile(
    r"["
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    r"\U0001F700-\U0001F77F"  # Alchemical Symbols (less common for emojis)
    r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    r"\U0001F800-\U0001F82F"  # Supplemental Arrows-C
    r"\U0001F830-\U0001F8FF"  # Supplemental Symbols and Pictographs (continued)
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs (more modern emojis)
    r"\U00002600-\U000027BF"  # Miscellaneous Symbols
    r"\U00002B50"  # Star symbol
    r"]+",
    flags=re.UNICODE,
)
COMBINED_EMOJI_RE = re.compile(
    r"<a?:[a-zA-Z0-9_]{1,32}:[0-9]{17,22}>|" + UNICODE_EMOJI_RE.pattern,
    flags=re.UNICODE | re.DOTALL,
)


class StatSettingsGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="stat", description="統計情報の取得・設定をします。")

    @app_commands.command(name="show", description="統計情報を表示します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def stat_show(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].ServerStat
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="統計情報の収集が無効化されています。"
                )
            )
        if not dbfind.get("Enabled"):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="統計情報の収集が無効化されています。"
                )
            )

        message = dbfind.get("Message")
        now_message = dbfind.get("NowMessage")

        embed = make_embed.success_embed(title="統計情報を表示しました。")
        embed.add_field(name="合計メッセージ数", value=f"{message}個")
        embed.add_field(name="今日のメッセージ数", value=f"{now_message}個")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="setting", description="統計情報を収集していいか設定します。"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def stat_settings(self, interaction: discord.Interaction):
        db = interaction.client.async_db["MainTwo"].ServerStat
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except Exception:
            return
        if not dbfind:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Enabled": True}},
                upsert=True,
            )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(title="統計情報の収集を有効化しました。")
            )
        else:
            if not dbfind.get("Enabled"):
                await db.update_one(
                    {"Guild": interaction.guild.id},
                    {"$set": {"Enabled": True}},
                    upsert=True,
                )
                return await interaction.response.send_message(
                    embed=make_embed.success_embed(
                        title="統計情報の収集を有効化しました。"
                    )
                )
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Enabled": False}},
                upsert=True,
            )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(title="統計情報の収集を無効化しました。")
            )


class DiceSettingGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="dice", description="ダイスを設定します。")

    @app_commands.command(name="dice", description="ダイスの設定を変更します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dice_setting(self, interaction: discord.Interaction, 有効化するか: bool):
        db = interaction.client.async_db["MainTwo"].Dice
        if 有効化するか:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id}},
                upsert=True,
            )
            return await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="ダイスを有効化しました。",
                    description="反応する言葉の例: `3d8`, `9d3`, `ダイス`, `dd`, `🎲`, `チンチロ`",
                )
            )
        else:
            result = await db.delete_one({"Guild": interaction.guild.id})
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=make_embed.error_embed(title="ダイスは有効化されていません。")
                )
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="ダイスを無効化しました。")
            )


class CommandsManageGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="commands", description="コマンド管理系コマンド")

    @app_commands.command(name="disable", description="コマンドを無効化します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def commands_disable(self, interaction: discord.Interaction, コマンド名: str):
        await interaction.response.defer()

        cmds = await mongodb.mongo["DashboardBot"].Commands.find().to_list(None)
        all_cmds = [c.get("name") for c in cmds]

        if コマンド名 not in all_cmds:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="そのコマンドは存在しません。",
                    color=discord.Color.red(),
                )
            )

        await command_disable.add_disabled_command(interaction.guild.id, コマンド名)
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{コマンド名} を無効化しました。", color=discord.Color.orange()
            )
        )

    @app_commands.command(name="enable", description="コマンドを有効化します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def commands_enable(self, interaction: discord.Interaction, コマンド名: str):
        await interaction.response.defer()

        cmds = await mongodb.mongo["DashboardBot"].Commands.find().to_list(None)
        all_cmds = [c.get("name") for c in cmds]

        if コマンド名 not in all_cmds:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="エラー",
                    description="そのコマンドは存在しません。",
                    color=discord.Color.red(),
                )
            )

        await command_disable.remove_disabled_command(interaction.guild.id, コマンド名)
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"{コマンド名} を有効化しました。", color=discord.Color.green()
            )
        )


class RoleCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="role", description="ロール系の設定です。")

    @app_commands.command(
        name="sticky-roles", description="ロール復元機能を設定します。"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def sticky_role(self, interaction: discord.Interaction, 有効化するか: bool):
        db = interaction.client.async_db["Main"].RoleRestore
        if 有効化するか:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id}},
                upsert=True,
            )
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="ロール復元を有効化しました。", color=discord.Color.green()
                )
            )
        else:
            result = await db.delete_one({"Guild": interaction.guild.id})
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="ロール復元は有効化されていません。",
                        color=discord.Color.red(),
                    )
                )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ロール復元を無効化しました。", color=discord.Color.red()
                )
            )

    @app_commands.command(
        name="auto-role", description="参加時にロールを追加する機能を設定・確認します。"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def autorole_setting(
        self, interaction: discord.Interaction, ロール: discord.Role = None
    ):
        await interaction.response.defer()
        db = interaction.client.async_db["MainTwo"].AutoRole
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except:
            return
        if ロール is None:
            if not dbfind is None:
                _ = "\n".join([f"<@&{r}>" for r in dbfind.get("Roles", [])])
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        "現在のメンバー参加時のロール追加機能の設定",
                        description=_ if _ else "まだ設定がありません。",
                    ).set_footer(
                        text="設定を変更するにはこのコマンドにロールを指定してください。"
                    )
                )
                return
            else:
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        "現在のメンバー参加時のロール追加機能の設定",
                        description="まだ設定がありません。",
                    ).set_footer(
                        text="設定を変更するにはこのコマンドにロールを指定してください。"
                    )
                )
                return
        message = ""
        if dbfind is None:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$addToSet": {"Roles": ロール.id}},
                upsert=True,
            )
            message = f"{ロール.mention} をメンバー参加時に追加するようにします。"
        else:
            if not ロール.id in dbfind.get("Roles", []):
                await db.update_one(
                    {"Guild": interaction.guild.id},
                    {"$addToSet": {"Roles": ロール.id}},
                    upsert=True,
                )
                message = f"{ロール.mention} をメンバー参加時に追加するようにします。"
            else:
                await db.update_one(
                    {"Guild": interaction.guild.id},
                    {"$pull": {"Roles": ロール.id}},
                    upsert=True,
                )
                message = f"{ロール.mention} をメンバー参加時に追加しないようにします。"
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="メンバー参加時のロール追加機能の設定を変更しました。",
                description=message,
            )
        )


class WelcomeCommands(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="welcome", description="よろしくメッセージ系のコマンドです。"
        )

    @app_commands.command(
        name="welcome", description="ようこそメッセージを設定します。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def welcome(self, interaction: discord.Interaction, 有効化するか: bool):
        if 有効化するか:

            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="ようこそメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(
                        label="タイトル",
                        placeholder="タイトルを入力",
                        style=discord.TextStyle.long,
                        required=True,
                        default="<name> さん、よろしく！",
                    )
                    self.desc = discord.ui.TextInput(
                        label="説明",
                        placeholder="説明を入力",
                        style=discord.TextStyle.long,
                        required=True,
                        default="あなたは <count> 人目のメンバーです！\n\nアカウント作成日: <createdat>",
                    )
                    self.add_item(self.etitle)
                    self.add_item(self.desc)

                async def on_submit(self, interaction_: discord.Interaction) -> None:
                    db = self.db["Main"].WelcomeMessage
                    await db.update_one(
                        {
                            "Guild": interaction_.guild.id,
                        },
                        {
                            "$set": {
                                "Channel": interaction_.channel.id,
                                "Guild": interaction_.guild.id,
                                "Title": self.etitle.value,
                                "Description": self.desc.value,
                            }
                        },
                        upsert=True,
                    )
                    await interaction_.response.send_message(
                        embed=make_embed.success_embed(
                            title="よろしくメッセージを有効化しました。"
                        )
                    )

            await interaction.response.send_modal(send(interaction.client.async_db))
        else:
            db = interaction.client.async_db["Main"].WelcomeMessage
            result = await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="よろしくメッセージを無効化しました。"
                )
            )

    @app_commands.command(
        name="goodbye", description="さようならメッセージを設定します。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def goodbye(self, interaction: discord.Interaction, 有効化するか: bool):
        if 有効化するか:

            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="さようならメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(
                        label="タイトル",
                        placeholder="タイトルを入力",
                        style=discord.TextStyle.long,
                        required=True,
                        default="<name> さん、さようなら・・",
                    )
                    self.desc = discord.ui.TextInput(
                        label="説明",
                        placeholder="説明を入力",
                        style=discord.TextStyle.long,
                        required=True,
                        default="またいつか会おうね！",
                    )
                    self.add_item(self.etitle)
                    self.add_item(self.desc)

                async def on_submit(self, interaction_: discord.Interaction) -> None:
                    db = self.db["Main"].GoodByeMessage
                    await db.update_one(
                        {
                            "Guild": interaction_.guild.id,
                        },
                        {
                            "$set": {
                                "Channel": interaction_.channel.id,
                                "Guild": interaction_.guild.id,
                                "Title": self.etitle.value,
                                "Description": self.desc.value,
                            }
                        },
                        upsert=True,
                    )
                    await interaction_.response.send_message(
                        embed=make_embed.success_embed(
                            title="さようならメッセージを有効化しました。"
                        )
                    )

            await interaction.response.send_modal(send(interaction.client.async_db))
        else:
            db = interaction.client.async_db["Main"].GoodByeMessage
            result = await db.delete_one(
                {
                    "Guild": interaction.guild.id,
                }
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="さようならメッセージを無効化しました。"
                )
            )

    @app_commands.command(name="ban", description="BANメッセージを有効化します。")
    @app_commands.checks.has_permissions(manage_channels=True, ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ban(self, interaction: discord.Interaction, 有効化するか: bool):
        if 有効化するか:

            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="BANメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(
                        label="タイトル",
                        placeholder="タイトルを入力",
                        style=discord.TextStyle.long,
                        required=True,
                        default="<name> がBANされました。",
                    )
                    self.desc = discord.ui.TextInput(
                        label="説明",
                        placeholder="説明を入力",
                        style=discord.TextStyle.long,
                        required=True,
                        default="いままでありがとう！",
                    )
                    self.add_item(self.etitle)
                    self.add_item(self.desc)

                async def on_submit(self, interaction_: discord.Interaction) -> None:
                    db = self.db["Main"].BanMessage
                    await db.update_one(
                        {
                            "Guild": interaction.guild.id,
                        },
                        {
                            "$set": {
                                "Channel": interaction.channel.id,
                                "Guild": interaction.guild.id,
                                "Title": self.etitle.value,
                                "Description": self.desc.value,
                            }
                        },
                        upsert=True,
                    )
                    await interaction_.response.send_message(
                        embed=make_embed.success_embed(
                            title="BANメッセージを有効化しました。"
                        )
                    )

            await interaction.response.send_modal(send(interaction.client.async_db))
        else:
            db = interaction.client.async_db["Main"].BanMessage
            result = await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="BANメッセージを無効化しました。")
            )

    @app_commands.command(
        name="rta", description="即抜けをするとメッセージを送信するようにします。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def welcome_rta(self, interaction: discord.Interaction, 有効か: bool):
        db = interaction.client.async_db["Main"].FastGoodByeRTAMessage
        await db.update_one(
            {
                "Guild": interaction.guild.id,
            },
            {
                "$set": {
                    "Channel": interaction.channel.id,
                    "Guild": interaction.guild.id,
                }
            },
            upsert=True,
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"即抜けメッセージを {'有効化' if 有効か else '無効化'} しました。",
                description="参加してから1分以内に退出するとメッセージを送信します。",
            )
        )

    @app_commands.command(
        name="help", description="各メッセージのセットアップ方法のヘルプです。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def welcome_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="各メッセージのセットアップ方法", color=discord.Color.green()
            )
            .add_field(
                name="よろしくメッセージ",
                value="""
タイトルと説明を設定して、
メンバー参加時にメッセージを送信します。
以下が該当コマンドです。
```
/settings welcome welcome
```
また、参加したメンバーの名前などを送信させることもできます。
""",
                inline=False,
            )
            .add_field(
                name="さようならメッセージ",
                value="""
タイトルと説明を設定して、
メンバー退出時にメッセージを送信します。
以下が該当コマンドです。
```
/settings welcome goodbye
```
また、退出したメンバーの名前などを送信させることもできます。
""",
                inline=False,
            )
            .add_field(
                name="BANメッセージ",
                value="""
タイトルと説明を設定して、
ユーザーBAN時にメッセージを送信します。
以下が該当コマンドです。
```
/settings welcome ban
```
また、BANしたユーザーの名前などを送信させることもできます。
""",
                inline=False,
            )
            .add_field(
                name="置き換えられる文字列たち",
                value=f"""
これらの文字列は、メッセージ送信時に自動的に置き換えられます。
```
<name> .. 名前に置きかえられる
<count> .. 現在のメンバー数に置き換えられる
<guild> .. サーバー名に置き換えられる
<createdat> .. メンバーのアカウント作成日に置き換えられる
```""",
                inline=False,
            )
        )


class SettingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> SettingCog")

        bot.add_check(self.ban_user_block)
        bot.add_check(self.ban_guild_block)
        bot.add_check(self.disable_channel)

    def cog_unload(self):
        self.bot.remove_check(self.ban_user_block)
        self.bot.remove_check(self.ban_guild_block)
        self.bot.remove_check(self.disable_channel)

    @commands.Cog.listener("on_message")
    async def on_message_stat(self, message: discord.Message):
        if not message.guild:
            return
        db = self.bot.async_db["MainTwo"].ServerStat

        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return

        if dbfind is None:
            return

        if not dbfind.get("Enabled"):
            return

        now = datetime.datetime.now().strftime("%Y-%m-%d")
        stored_day = dbfind.get("Now")

        if stored_day != now:
            await db.update_one(
                {"Guild": message.guild.id},
                {"$set": {"Now": now, "NowMessage": 1}, "$inc": {"Message": 1}},
            )
        else:
            await db.update_one(
                {"Guild": message.guild.id}, {"$inc": {"NowMessage": 1, "Message": 1}}
            )

    @commands.Cog.listener("on_member_join")
    async def on_member_join_auto_role(self, member: discord.Member):
        if member.bot:
            return

        db = self.bot.async_db["MainTwo"].AutoRole
        try:
            dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        roles = dbfind.get("Roles")
        if not roles:
            return

        role_objs = [
            member.guild.get_role(role_id)
            for role_id in roles
            if member.guild.get_role(role_id) is not None
        ]

        if not role_objs:
            return

        try:
            await member.add_roles(*role_objs, reason="AutoRole機能により追加。")
        except:
            pass

    @commands.Cog.listener("on_member_remove")
    async def on_member_remove_role_backup(self, member: discord.Member):
        if member.bot:
            return

        db = self.bot.async_db["Main"].RoleRestore
        try:
            dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        role_ids = [r.id for r in member.roles if r.name != "@everyone"]
        if role_ids:
            db_rs = self.bot.async_db["Main"].RoleRestoreBackup
            await db_rs.update_one(
                {"Guild": member.guild.id, "UserID": member.id},
                {"$set": {"Roles": role_ids}},
                upsert=True,
            )

    @commands.Cog.listener("on_member_join")
    async def on_member_join_role_restore(self, member: discord.Member):
        if member.bot:
            return

        db = self.bot.async_db["Main"].RoleRestore
        try:
            dbfind = await db.find_one({"Guild": member.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        db_rs = self.bot.async_db["Main"].RoleRestoreBackup
        data = await db_rs.find_one_and_delete(
            {"Guild": member.guild.id, "UserID": member.id}
        )

        if data and "Roles" in data:
            roles = [member.guild.get_role(rid) for rid in data["Roles"]]
            roles = [r for r in roles if r]

            added_roles = []
            error_roles = []

            for role in roles:
                try:
                    await member.add_roles(role, reason="ロール復元機能による再付与")
                    added_roles.append(role.name)
                    await asyncio.sleep(0.8)
                except:
                    error_roles.append(role.name)
                    continue

            await asyncio.sleep(3)

            try:
                embed = discord.Embed(
                    title="ロールが復元されました。", color=discord.Color.green()
                )
                if added_roles:
                    embed.add_field(name="復元したロール", value="\n".join(added_roles))
                await member.send(embed=embed)
            except:
                return

    async def disable_channel(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].CommandDisable
        try:
            dbfind = await db.find_one({"Channel": ctx.channel.id}, {"_id": False})
        except:
            return True
        if dbfind is not None:
            try:
                if ctx.author.guild_permissions.manage_guild:
                    return True
            except:
                return True
            raise CommandDisableChannel
        return True

    async def ban_user_block(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": ctx.author.id}, {"_id": False})
        except:
            return True
        if dbfind is not None:
            raise BanBotError
        return True

    async def ban_guild_block(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].BlockGuild
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return True
        if dbfind is not None:
            raise BanBotError
        return True

    @commands.Cog.listener("on_message")
    async def on_message_translate_auto(self, message: discord.Message):
        if message.author.bot:
            return

        db = self.bot.async_db["Main"].AutoTranslate

        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_auto_translate.get(message.channel.id, 0)
        if current_time - last_message_time < 5:
            return
        cooldown_auto_translate[message.channel.id] = current_time

        translator = await asyncio.to_thread(
            GoogleTranslator, source="auto", target=dbfind.get("Lang", "en")
        )
        translated_text = await asyncio.to_thread(translator.translate, message.content)

        embed = make_embed.success_embed(
            title=f"翻訳 ({dbfind.get('Lang', 'en')} へ)",
            description=f"{translated_text}",
        ).set_footer(text="Google Translate")

        await message.reply(embed=embed)

    @commands.Cog.listener("on_app_command_error")
    async def on_app_command_error_functiondisabled(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, CommandDisableChannel):
            current_time = time.time()
            last_message_time = cooldown_engonly.get(interaction.guild.id, 0)
            if current_time - last_message_time < 5:
                return
            cooldown_engonly[interaction.guild.id] = current_time

            try:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="このチャンネルではコマンドを使用できません。",
                        description="`サーバーの管理`の権限がある場合は実行できます。",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="このチャンネルではコマンドを使用できません。",
                        description="`サーバーの管理`の権限がある場合は実行できます。",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

        elif isinstance(error, BanBotError):
            current_time = time.time()
            last_message_time = cooldown_engonly.get(interaction.guild.id, 0)
            if current_time - last_message_time < 5:
                return
            cooldown_engonly[interaction.guild.id] = current_time

            try:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="あなた、もしくはサーバーがBotからBanされています。",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            except discord.InteractionResponded:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="あなた、もしくはサーバーがBotからBanされています。",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )

    async def return_setting(self, ctx: commands.Context, name: str):
        db = self.bot.async_db["Main"][name]
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        return True

    async def return_text(self, ctx: commands.Context, name: str):
        db = self.bot.async_db["Main"][name]
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return "標準"
        if dbfind is None:
            return "標準"
        return dbfind

    async def return_bool(self, tf: bool):
        if tf:
            return "<:ON:1333716076244238379>"
        return "<:OFF:1333716084364279838>"

    async def keigo_trans(self, kougo_text):
        request_data = {
            "kougo_writing": kougo_text,
            "mode": "direct",
            "platform": 0,
            "translation_id": "",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://y026dvhch0.execute-api.ap-northeast-1.amazonaws.com/translate",
                    json=request_data,
                ) as response:
                    if response.status != 200:
                        return "Error"
                    response_data = await response.json()
                    return response_data.get("content", "敬語に変換できませんでした。")

        except aiohttp.ClientError as e:
            return f"Network error occurred: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    @commands.Cog.listener("on_message")
    async def on_message_command(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author == self.bot.user:
            return

        await self.bot.process_commands(message)
        return

    @commands.Cog.listener("on_member_join")
    async def on_member_join_stickrole(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].StickRole
        try:
            dbfind = await db.find_one(
                {"Guild": g.id, "User": member.id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            return
        try:
            r = member.guild.get_role(dbfind["Role"])
            await member.add_roles(r)
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_filedeletor(self, message: discord.Message):
        if message.author.bot:
            return
        if message.attachments == []:
            return
        if not message.guild:
            return
        if message.author.guild_permissions.administrator:
            return
        db = self.bot.async_db["Main"].FileAutoDeletor
        try:
            dbfind = await db.find_one({"guild_id": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        check = dbfind.get("end", None)
        if not check:
            return
        for at in message.attachments:
            for c in check:
                if at.filename.endswith(f"{c}"):
                    try:
                        await message.author.timeout(datetime.timedelta(minutes=3))
                        await message.delete()
                    except:
                        return
                    return

    @commands.Cog.listener("on_message")
    async def on_message_englishonly(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].EnglishOnlyChannel
        try:
            dbfind = await db.find_one(
                {"Guild": message.guild.id, "Channel": message.channel.id},
                {"_id": False},
            )
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_engonly.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        cooldown_engonly[message.guild.id] = current_time
        try:
            if re.match(r"^[A-Za-z\s.,!?\"'()\-:;]+$", message.content):
                return
            else:
                await message.delete()
        except:
            return

    @commands.Cog.listener("on_voice_state_update")
    async def on_voice_state_update_datetime(self, member, before, after):
        return
        if after.channel is not None:
            voice_channel = after.channel
            db = self.bot.async_db["Main"].VoiceTime
            try:
                dbfind = await db.find_one(
                    {"Channel": voice_channel.id}, {"_id": False}
                )
            except:
                return
            if dbfind is None:
                return
            now = datetime.datetime.now()
            try:
                n = voice_channel.name.split("-")[0]
                await voice_channel.edit(name=f"{n}-{now.strftime('%m_%d_%H_%M_%S')}")
            except:
                n = voice_channel.name
                await voice_channel.edit(name=f"{n}-{now.strftime('%m_%d_%H_%M_%S')}")

    async def send_modlog(self, guild: discord.Guild, text: str):
        db = self.bot.async_db["MainTwo"].AutoModLog

        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})

            if dbfind is None:
                return
        except:
            return

        channel = dbfind.get("Channel", None)
        if not channel:
            return
        channel = guild.get_channel(channel)
        if not channel:
            return
        try:
            await channel.send(content=text)
        except:
            return

    async def get_score_warn(self, guild: discord.Guild, score: int):
        db = self.bot.async_db["Main"].WarnScoreSetting
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Score": score}, {"_id": False}
            )
            return dbfind["Setting"]
        except:
            return 0

    def return_warn_text(self, sc: int):
        if sc == 0:
            return "🤐タイムアウト3分"
        elif sc == 1:
            return "🤐タイムアウト5分"
        elif sc == 2:
            return "🤐タイムアウト10分"
        elif sc == 3:
            return "👢Kick"
        elif sc == 4:
            return "🔨BAN"
        elif sc == 5:
            return "❔なし"
        else:
            return "🤐タイムアウト3分"

    async def run_warn(self, score: int, message: discord.Message):
        sc = await self.get_score_warn(message.guild, score)
        if sc == 0:
            await message.author.timeout(datetime.timedelta(minutes=3))
        elif sc == 1:
            await message.author.timeout(datetime.timedelta(minutes=5))
        elif sc == 2:
            await message.author.timeout(datetime.timedelta(minutes=10))
        elif sc == 3:
            await message.author.kick()
        elif sc == 4:
            await message.author.ban()
        elif sc == 5:
            return
        else:
            await message.author.timeout(datetime.timedelta(minutes=3))

    async def run_warn_automod(
        self, score: int, guild: discord.Guild, member: discord.Member
    ):
        sc = await self.get_score_warn(guild, score)
        if sc == 0:
            await member.timeout(datetime.timedelta(minutes=3))
        elif sc == 1:
            await member.timeout(datetime.timedelta(minutes=5))
        elif sc == 2:
            await member.timeout(datetime.timedelta(minutes=10))
        elif sc == 3:
            await member.kick()
        elif sc == 4:
            await member.ban()
        elif sc == 5:
            return
        else:
            await member.timeout(datetime.timedelta(minutes=3))

    async def run_warn_int_author(
        self,
        score: int,
        message: discord.Message,
        int_: discord.MessageInteractionMetadata,
    ):
        sc = await self.get_score_warn(message.guild, score)
        if sc == 0:
            await message.guild.get_member(int_.user.id).timeout(
                datetime.timedelta(minutes=3)
            )
        elif sc == 1:
            await message.guild.get_member(int_.user.id).timeout(
                datetime.timedelta(minutes=5)
            )
        elif sc == 2:
            await message.guild.get_member(int_.user.id).timeout(
                datetime.timedelta(minutes=10)
            )
        elif sc == 3:
            await message.guild.get_member(int_.user.id).kick()
        elif sc == 4:
            await message.guild.get_member(int_.user.id).ban()
        elif sc == 5:
            return
        else:
            await message.guild.get_member(int_.user.id).timeout(
                datetime.timedelta(minutes=3)
            )

    async def warn_user(self, message: discord.Message):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one(
                {"Guild": message.guild.id, "User": message.author.id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            await db.update_one(
                {"Guild": message.guild.id, "User": message.author.id},
                {
                    "$set": {
                        "Guild": message.guild.id,
                        "User": message.author.id,
                        "Score": 1,
                    }
                },
                upsert=True,
            )
            try:
                await self.run_warn(1, message)
                return
            except:
                return
        else:
            await db.update_one(
                {"Guild": message.guild.id, "User": message.author.id},
                {
                    "$set": {
                        "Guild": message.guild.id,
                        "User": message.author.id,
                        "Score": dbfind["Score"] + 1,
                    }
                },
                upsert=True,
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.update_one(
                    {"Guild": message.guild.id, "User": message.author.id},
                    {
                        "$set": {
                            "Guild": message.guild.id,
                            "User": message.author.id,
                            "Score": 0,
                        }
                    },
                    upsert=True,
                )
                return await self.run_warn(10, message)
            else:
                try:
                    await self.run_warn(nowscore, message)
                    return
                except:
                    return

    async def warn_user_automod(
        self,
        guild: discord.Guild,
        user: discord.Member,
    ):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "User": user.id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            await db.update_one(
                {"Guild": guild.id, "User": user.id},
                {"$set": {"Guild": guild.id, "User": user.id, "Score": 1}},
                upsert=True,
            )
            try:
                await self.run_warn_automod(1, guild, user)
                return
            except:
                return
        else:
            await db.update_one(
                {"Guild": guild.id, "User": user.id},
                {
                    "$set": {
                        "Guild": guild.id,
                        "User": user.id,
                        "Score": dbfind["Score"] + 1,
                    }
                },
                upsert=True,
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.update_one(
                    {"Guild": guild.id, "User": user.id},
                    {"$set": {"Guild": guild.id, "User": user.id, "Score": 0}},
                    upsert=True,
                )
                return await self.run_warn_automod(10, guild, user)
            else:
                try:
                    await self.run_warn_automod(nowscore, guild, user)
                    return
                except:
                    return

    async def warn_user_int(
        self, message: discord.Message, int_: discord.MessageInteractionMetadata
    ):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one(
                {"Guild": message.guild.id, "User": int_.user.id}, {"_id": False}
            )
        except:
            return print(f"{sys.exc_info()}")
        if dbfind is None:
            await db.update_one(
                {"Guild": message.guild.id, "User": int_.user.id},
                {"$set": {"Guild": message.guild.id, "User": int_.user.id, "Score": 1}},
                upsert=True,
            )
            try:
                await self.run_warn_int_author(1, message, int_)
                return
            except Exception:
                return
        else:
            await db.update_one(
                {"Guild": message.guild.id, "User": int_.user.id},
                {
                    "$set": {
                        "Guild": message.guild.id,
                        "User": int_.user.id,
                        "Score": dbfind["Score"] + 1,
                    }
                },
                upsert=True,
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.update_one(
                    {"Guild": message.guild.id, "User": int_.user.id},
                    {
                        "$set": {
                            "Guild": message.guild.id,
                            "User": int_.user.id,
                            "Score": 0,
                        }
                    },
                    upsert=True,
                )
                return await self.run_warn_int_author(10, message, int_)
            else:
                try:
                    await self.run_warn_int_author(nowscore, message, int_)
                    return
                except Exception:
                    return

    async def score_get(self, guild: discord.Guild, user: discord.User):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "User": user.id}, {"_id": False}
            )
        except:
            return 0
        if dbfind is None:
            return 0
        else:
            return dbfind["Score"]

    @commands.Cog.listener("on_message")
    async def on_message_emojis(self, message: discord.Message):
        if message.author.bot:
            return
        if isinstance(message.channel, discord.DMChannel):
            return
        if not message.guild:
            return
        if message.author.guild_permissions.administrator:
            return

        emojis = COMBINED_EMOJI_RE.findall(message.content)
        emoji_count = len(emojis)

        if emoji_count < 10:
            return

        db = self.bot.async_db["MainTwo"].AutoMods
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return

        if dbfind is None or "emojis" not in dbfind.get("AutoMods", []):
            return

        channel_db = self.bot.async_db["Main"].UnBlockChannel
        try:
            channel_db_find = await channel_db.find_one(
                {"Channel": message.channel.id}, {"_id": False}
            )
        except:
            channel_db_find = None

        if channel_db_find is not None:
            return

        try:
            await self.warn_user(message)
            try:
                await message.delete()
            except:
                pass

            sc = await self.score_get(message.guild, message.author)
            await message.channel.send(
                embed=discord.Embed(
                    description=f"10個以上の絵文字を送信したため処罰されました。\n現在のスコア: {sc}",
                    color=discord.Color.yellow(),
                ),
                content=f"{message.author.mention}",
            )
            await self.send_modlog(
                message.guild,
                f"{message.author.name} は10個以上の絵文字を送信したため、処罰されました。",
            )
        except Exception as e:
            return

    @commands.Cog.listener("on_message")
    async def on_message_everyone_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        if "@everyone" in message.content or "@here" in message.content:
            db = self.bot.async_db["Main"].EveryoneBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one(
                    {"Channel": message.channel.id}, {"_id": False}
                )
            except:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)

                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"全体メンションを送信したため処罰されました。\n現在のスコア: {sc}",
                            color=discord.Color.yellow(),
                        ),
                        content=f"{message.author.mention}",
                    )

                    await self.send_modlog(
                        message.guild,
                        f"{message.author.name} は全体メンションを送信しようとしたため、処罰されました。",
                    )
                except:
                    return
            if channel_db_find is None:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)

                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"全体メンションを送信したため処罰されました。\n現在のスコア: {sc}",
                            color=discord.Color.yellow(),
                        ),
                        content=f"{message.author.mention}",
                    )

                    await self.send_modlog(
                        message.guild,
                        f"{message.author.name} は全体メンションを送信しようとしたため、処罰されました。",
                    )
                except:
                    return

    @commands.Cog.listener("on_message")
    async def on_message_invite_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        INVITE_LINK_REGEX = r"(discord\.(gg|com/invite|app\.com/invite)[/\\][\w-]+)"
        if re.search(INVITE_LINK_REGEX, message.content):
            db = self.bot.async_db["Main"].InviteBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one(
                    {"Channel": message.channel.id}, {"_id": False}
                )
            except:
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"招待リンクを送信したため処罰されました。\n現在のスコア: {sc}",
                            color=discord.Color.yellow(),
                        ),
                        content=f"{message.author.mention}",
                    )

                    await self.send_modlog(
                        message.guild,
                        f"{message.author.name} は招待リンクを送信したため、処罰されました。",
                    )
                except:
                    return
            if channel_db_find is None:
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)

                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"招待リンクを送信したため処罰されました。\n現在のスコア: {sc}",
                            color=discord.Color.yellow(),
                        ),
                        content=f"{message.author.mention}",
                    )

                    await self.send_modlog(
                        message.guild,
                        f"{message.author.name} は招待リンクを送信したため、処罰されました。",
                    )
                except:
                    return

    @commands.Cog.listener("on_message")
    async def on_message_token_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        TOKEN_REGEX = r"[A-Za-z\d]{24}\.[\w-]{6}\.[\w-]{27}"
        if re.search(TOKEN_REGEX, message.content):
            db = self.bot.async_db["Main"].TokenBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one(
                    {"Channel": message.channel.id}, {"_id": False}
                )
            except:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"Tokenを送信したため処罰されました。\n現在のスコア: {sc}",
                            color=discord.Color.yellow(),
                        ),
                        content=f"{message.author.mention}",
                    )

                    await self.send_modlog(
                        message.guild,
                        f"{message.author.name} はTokenを送信したため、処罰されました。",
                    )
                except:
                    return
            if channel_db_find is None:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(
                        embed=discord.Embed(
                            description=f"Tokenを送信したため処罰されました。\n現在のスコア: {sc}",
                            color=discord.Color.yellow(),
                        ),
                        content=f"{message.author.mention}",
                    )

                    await self.send_modlog(
                        message.guild,
                        f"{message.author.name} はTokenを送信したため、処罰されました。",
                    )
                except:
                    return

    async def unblock_ch_check(self, message: discord.Message):
        channel_db = self.bot.async_db["Main"].UnBlockChannel
        try:
            channel_db_find = await channel_db.find_one(
                {"Channel": message.channel.id}, {"_id": False}
            )
        except:
            return False
        if channel_db_find is None:
            return False
        return True

    async def unblock_ch_check_channel(self, channel: discord.abc.GuildChannel):
        channel_db = self.bot.async_db["Main"].UnBlockChannel
        try:
            channel_db_find = await channel_db.find_one(
                {"Channel": channel.id}, {"_id": False}
            )
        except:
            return False
        if channel_db_find is None:
            return False
        return True

    @commands.Cog.listener("on_message")
    async def on_message_spam_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        try:
            db = self.bot.async_db["Main"].SpamBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            check_ = await self.unblock_ch_check(message)
            if check_:
                return
            message_counts[message.author.id] += 1

            # 指定した回数を超えたら警告
            if message_counts[message.author.id] >= spam_threshold:
                try:
                    await self.warn_user(message)
                except:
                    return
                print(
                    f"SpamDetected: {message.author.id}/{message.author.display_name}"
                )
                message_counts[message.author.id] = 0  # リセット
                await self.send_modlog(
                    message.guild,
                    f"{message.author.name} はスパムをしたため、処罰されました。",
                )

            # 指定時間後にカウントを減らす
            await asyncio.sleep(time_window)
            message_counts[message.author.id] -= 1
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_userapplication_spam_block(self, message: discord.Message):
        if type(message.channel) == discord.DMChannel:
            return
        if message.interaction_metadata is None:
            return
        try:
            if message.guild.get_member(
                message.interaction_metadata.user.id
            ).guild_permissions.administrator:
                return
            db = self.bot.async_db["Main"].UserApplicationSpamBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return

            check_ = await self.unblock_ch_check(message)
            if check_:
                return

            message_counts_userapp[message.interaction_metadata.user.id] += 1

            if message_counts_userapp[message.interaction_metadata.user.id] >= 3:
                try:
                    await self.warn_user_int(message, message.interaction_metadata)
                except:
                    return
                print(
                    f"AppSpamDetected: {message.interaction_metadata.user.id}/{message.interaction_metadata.user.display_name}"
                )
                message_counts_userapp[message.interaction_metadata.user.id] = 0
                await self.send_modlog(
                    message.guild,
                    f"{message.author.name} はスラッシュコマンドを連打したため、処罰されました。",
                )

            await asyncio.sleep(time_window)
            message_counts_userapp[message.interaction_metadata.user.id] -= 1
        except:
            return

    @commands.Cog.listener("on_automod_action")
    async def on_automod_action(self, execution: discord.AutoModAction):
        guild = self.bot.get_guild(execution.guild_id)
        if type(execution.channel) == discord.DMChannel:
            return
        if not guild.get_member(execution.user_id):
            return
        if guild.get_member(execution.user_id).guild_permissions.administrator:
            return
        db_automod = self.bot.async_db["Main"].AutoModDetecter
        try:
            dbfind = await db_automod.find_one(
                {"Guild": execution.guild_id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            return
        try:
            member = guild.get_member(execution.user_id)
            automod_rule = await guild.fetch_automod_rule(execution.rule_id)
            if automod_rule.creator_id != self.bot.user.id:
                return
            check_ = await self.unblock_ch_check_channel(execution.channel)
            if check_:
                return
            try:
                await self.warn_user_automod(guild, member)
                sc = await self.score_get(guild, member)
                await execution.channel.send(
                    embed=discord.Embed(
                        description=f"{automod_rule.name.replace('対策', '')} を送信しようとしたため処罰されました。\n現在のスコア: {sc}",
                        color=discord.Color.yellow(),
                    ),
                    content=f"{member.mention}",
                )

                await self.send_modlog(
                    execution.guild,
                    f"{member.name} {automod_rule.name.replace('対策', '')}を送信しようとしたため処罰されました。",
                )
            except:
                return
        except:
            return

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if isinstance(channel, discord.TextChannel):
            db = self.bot.async_db["Main"].AutoProtectSetting
            try:
                gu = self.bot.get_guild(channel.guild.id).id
                try:
                    dbfind = await db.find_one({"Guild": gu}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                current_time = time.time()
                last_message_time = cooldown_auto_protect_time.get(channel.guild.id, 0)
                if current_time - last_message_time < 5:
                    return
                cooldown_auto_protect_time[channel.guild.id] = current_time
                overwrite = channel.overwrites_for(channel.guild.default_role)
                overwrite.use_external_apps = False
                await channel.set_permissions(
                    channel.guild.default_role, overwrite=overwrite
                )
            except:
                return
        elif isinstance(channel, discord.VoiceChannel):
            db = self.bot.async_db["Main"].AutoProtectSetting
            try:
                gu = self.bot.get_guild(channel.guild.id).id
                try:
                    dbfind = await db.find_one({"Guild": gu}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                current_time = time.time()
                last_message_time = cooldown_auto_protect_time.get(channel.guild.id, 0)
                if current_time - last_message_time < 5:
                    return
                cooldown_auto_protect_time[channel.guild.id] = current_time
                overwrite = channel.overwrites_for(channel.guild.default_role)
                overwrite.use_external_apps = False
                await channel.set_permissions(
                    channel.guild.default_role, overwrite=overwrite
                )
            except:
                return

    async def check_run_ok_ass(self, message: discord.Message):
        db = self.bot.async_db["Main"].AIChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return True
        if dbfind is None:
            return True
        return False

    async def get_call_pets_random(self, message: discord.Message):
        db = self.bot.async_db["Main"].CallBeasts
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return self.bot.user
        if dbfind is None:
            return self.bot.user
        p = dbfind.get("pet", None)
        if not p:
            return self.bot.user
        return (
            self.bot.get_user(random.choice(p))
            if self.bot.get_user(random.choice(p))
            else self.bot.user
        )

    @commands.Cog.listener("on_message")
    async def on_message_auto_delete_nsfw(self, message: discord.Message):
        if message.author.bot:
            return  # ボットのメッセージは無視
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].NSFWDeleter
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        if message.author.guild_permissions.administrator:
            return
        if message.channel.nsfw:
            return

        async def check_nsfw(image_bytes):
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field(
                    "image",
                    image_bytes,
                    filename="image.jpg",
                    content_type="image/jpeg",
                )

                async with session.post(
                    "http://localhost:3000/analyze", data=data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result
                    else:
                        return {"safe": True}

        if message.attachments:
            for attachment in message.attachments:
                for k in [".png", ".jpg", ".jpeg", ".webp"]:
                    if attachment.filename.endswith(k):
                        async with aiohttp.ClientSession() as session:
                            async with session.get(attachment.url) as resp:
                                image_bytes = await resp.read()
                                result = await check_nsfw(image_bytes)

                                if not result["safe"]:
                                    try:
                                        await message.delete()
                                    except:
                                        return
                                    try:
                                        await self.warn_user(message)
                                        sc = await self.score_get(
                                            message.guild, message.author
                                        )
                                        await message.channel.send(
                                            f"スコアが追加されました。\n現在のスコア: {sc}"
                                        )
                                    except:
                                        return
                                else:
                                    return
                        return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_timeout_removerole(
        self, before: discord.Member, after: discord.Member
    ):
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until is not None:  # タイムアウトされた
                db = self.bot.async_db["Main"].AutoRoleRemover
                try:
                    g = self.bot.get_guild(after.guild.id)
                    dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                role = after.guild.get_role(dbfind["Role"])
                if role in after.roles:
                    try:
                        await after.remove_roles(role)
                    except discord.Forbidden:
                        return
                    except discord.HTTPException:
                        return

    @commands.Cog.listener("on_message")
    async def on_message_dice(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return

        db = self.bot.async_db["MainTwo"].Dice
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return

        try:
            match = re.fullmatch(r"(\d+)d(\d+)", message.content)
            if not match:
                current_time = time.time()
                last_message_time = cooldown_dice.get(message.channel.id, 0)
                if current_time - last_message_time < 2:
                    return
                cooldown_dice[message.channel.id] = current_time

                if "ダイス" == message.content:
                    await message.reply(
                        f"🎲 {message.author.mention}: {random.randint(1, 6)}"
                    )
                    return
                if "🎲" == message.content:
                    await message.reply(
                        f"🎲 {message.author.mention}: {random.randint(1, 6)}"
                    )
                    return
                if "dd" == message.content:
                    await message.reply(
                        f"🎲 {message.author.mention}: {random.randint(1, 100)}"
                    )
                    return
                if "チンチロ" == message.content:
                    a = random.randint(1, 6)
                    b = random.randint(1, 6)
                    c = random.randint(1, 6)

                    def check():
                        if a == b == c == 1:
                            return "ピンゾロ！"
                        elif a == b == c != 1:
                            return "ゾロ目！"
                        elif a != b != c and a + b + c == 15:
                            return "シゴロ！"
                        elif a == b != c:
                            return f"結果は{c}！"
                        elif b == c != a:
                            return f"結果は{a}！"
                        elif c == a != b:
                            return f"結果は{b}！"
                        elif a != b != c and a + b + c == 6:
                            return "残念！ヒフミ！"
                        else:
                            return "残念！目無し！"

                    await message.reply(
                        f"🎲 {message.author.mention}: {a}, {b}, {c} ... {check()}"
                    )
                    return

            current_time = time.time()
            last_message_time = cooldown_dice.get(message.channel.id, 0)
            if current_time - last_message_time < 2:
                return
            cooldown_dice[message.channel.id] = current_time

            num_dice, sides = map(int, match.groups())
            if num_dice > 100:
                return
            if sides > 100:
                return
            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            str_rolls = [str(r) for r in rolls]
            await message.reply(
                f"🎲 {message.author.mention}: {', '.join(str_rolls)} → {sum(rolls)}"
            )
        except:
            return

    settings = app_commands.Group(name="settings", description="設定系のコマンドです。")

    settings.add_command(RoleCommands())
    settings.add_command(DiceSettingGroup())
    settings.add_command(WelcomeCommands())
    settings.add_command(CommandsManageGroup())
    settings.add_command(StatSettingsGroup())

    @settings.command(name="lock-message", description="メッセージを固定します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def lock_message(self, interaction: discord.Interaction, 有効にするか: bool):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if 有効にするか:

            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="メッセージ固定の設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(
                        label="タイトル",
                        placeholder="タイトルを入力",
                        style=discord.TextStyle.long,
                        required=True,
                    )
                    self.desc = discord.ui.TextInput(
                        label="説明",
                        placeholder="説明を入力",
                        style=discord.TextStyle.long,
                        required=True,
                    )
                    self.add_item(self.etitle)
                    self.add_item(self.desc)

                async def on_submit(self, interaction: discord.Interaction) -> None:
                    view = discord.ui.View()
                    view.add_item(
                        discord.ui.Button(
                            style=discord.ButtonStyle.red,
                            label="削除",
                            custom_id="lockmessage_delete+",
                        )
                    )
                    view.add_item(
                        discord.ui.Button(
                            style=discord.ButtonStyle.blurple,
                            label="編集",
                            custom_id="lockmessage_edit+",
                        )
                    )
                    msg = await interaction.channel.send(
                        embed=discord.Embed(
                            title=self.etitle.value,
                            description=self.desc.value,
                            color=discord.Color.random(),
                        ),
                        view=view,
                    )
                    db = self.db["Main"].LockMessage
                    await db.update_one(
                        {
                            "Channel": interaction.channel.id,
                            "Guild": interaction.guild.id,
                        },
                        {
                            "$set": {
                                "Channel": interaction.channel.id,
                                "Guild": interaction.guild.id,
                                "Title": self.etitle.value,
                                "Desc": self.desc.value,
                                "MessageID": msg.id,
                            }
                        },
                        upsert=True,
                    )
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title="メッセージ固定を有効化しました。",
                            color=discord.Color.green(),
                        ),
                        ephemeral=True,
                    )

            await interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].LockMessage
            result = await db.delete_one(
                {
                    "Channel": interaction.channel.id,
                }
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="メッセージ固定は有効化されていません。",
                        color=discord.Color.red(),
                    )
                )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="メッセージ固定を無効化しました。", color=discord.Color.red()
                )
            )

    @settings.command(name="prefix", description="頭文字を変更します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def prefix(self, interaction: discord.Interaction, prefix: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        db = self.bot.async_db["DashboardBot"].CustomPrefixBot
        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$set": {"Guild": interaction.guild.id, "Prefix": prefix}},
            upsert=True,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="Prefixを設定しました。",
                description=f"「{prefix}」",
                color=discord.Color.green(),
            )
        )

    @settings.command(name="score", description="スコアをチェックします。")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def setting_score(
        self, interaction_: discord.Interaction, ユーザー: discord.User
    ):
        if not await command_disable.command_enabled_check(interaction_):
            return await interaction_.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        class ScoreSettingView(discord.ui.View):
            def __init__(self, db, ユーザーs):
                super().__init__(timeout=None)
                self.db = db
                self.ユーザー = ユーザーs

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="スコアに関しての設定",
                options=[
                    discord.SelectOption(label="スコアを9に設定"),
                    discord.SelectOption(label="スコアを8に設定"),
                    discord.SelectOption(label="スコアを5に設定"),
                    discord.SelectOption(label="スコアを3に設定"),
                    discord.SelectOption(label="スコアをクリア"),
                ],
            )
            async def select(
                self, interaction: discord.Interaction, select: discord.ui.Select
            ):
                if interaction.user.id == interaction_.user.id:
                    if "スコアを8に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {"_id": False},
                            )
                        except:
                            return
                        if dbfind is None:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 8,
                                    }
                                },
                                upsert=True,
                            )
                        else:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 8,
                                    }
                                },
                                upsert=True,
                            )
                        await interaction.response.send_message(
                            "スコアを8に設定しました。", ephemeral=True
                        )
                    elif "スコアを5に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {"_id": False},
                            )
                        except:
                            return
                        if dbfind is None:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 5,
                                    }
                                },
                                upsert=True,
                            )
                        else:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 5,
                                    }
                                },
                                upsert=True,
                            )
                        await interaction.response.send_message(
                            "スコアを5に設定しました。", ephemeral=True
                        )
                    elif "スコアを3に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {"_id": False},
                            )
                        except:
                            return
                        if dbfind is None:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 3,
                                    }
                                },
                                upsert=True,
                            )
                        else:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 3,
                                    }
                                },
                                upsert=True,
                            )
                        await interaction.response.send_message(
                            "スコアを3に設定しました。", ephemeral=True
                        )
                    elif "スコアを9に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {"_id": False},
                            )
                        except:
                            return
                        if dbfind is None:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 9,
                                    }
                                },
                                upsert=True,
                            )
                        else:
                            await db.update_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "$set": {
                                        "Guild": interaction.guild.id,
                                        "User": self.ユーザー.id,
                                        "Score": 9,
                                    }
                                },
                                upsert=True,
                            )
                        await interaction.response.send_message(
                            "スコアを9に設定しました。", ephemeral=True
                        )
                    elif "スコアをクリア" == select.values[0]:
                        db = self.db.WarnUserScore
                        result = await db.delete_one(
                            {"Guild": interaction.guild.id, "User": self.ユーザー.id}
                        )
                        await interaction.response.send_message(
                            "スコアをクリアしました。", ephemeral=True
                        )

        sc = await self.score_get(interaction_.guild, ユーザー)
        await interaction_.response.send_message(
            embed=discord.Embed(
                title=f"{ユーザー.display_name}さんのスコア",
                description=f"スコア: {sc}",
                color=discord.Color.green(),
            ),
            view=ScoreSettingView(self.bot.async_db["Main"], ユーザー),
        )

    @settings.command(
        name="warn-setting", description="警告時に実行するものを選択します。"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def setting_warn_setting(
        self, interaction_: discord.Interaction, スコア: int = None
    ):
        if not await command_disable.command_enabled_check(interaction_):
            return await interaction_.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        class ScoreView(discord.ui.View):
            def __init__(self, スコア: int, db):
                super().__init__(timeout=None)
                self.db = db
                self.sc = スコア

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="警告時の設定",
                options=[
                    discord.SelectOption(label="タイムアウト3分"),
                    discord.SelectOption(label="タイムアウト5分"),
                    discord.SelectOption(label="タイムアウト10分"),
                    discord.SelectOption(label="Kick"),
                    discord.SelectOption(label="BAN"),
                    discord.SelectOption(label="なし"),
                ],
            )
            async def select(
                self, interaction: discord.Interaction, select: discord.ui.Select
            ):
                if interaction.user.id == interaction_.user.id:
                    if "タイムアウト3分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.update_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "$set": {
                                    "Guild": interaction_.guild.id,
                                    "Score": self.sc,
                                    "Setting": 0,
                                }
                            },
                            upsert=True,
                        )
                    elif "タイムアウト5分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.update_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "$set": {
                                    "Guild": interaction_.guild.id,
                                    "Score": self.sc,
                                    "Setting": 1,
                                }
                            },
                            upsert=True,
                        )
                    elif "タイムアウト10分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.update_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "$set": {
                                    "Guild": interaction_.guild.id,
                                    "Score": self.sc,
                                    "Setting": 2,
                                }
                            },
                            upsert=True,
                        )
                    elif "Kick" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.update_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "$set": {
                                    "Guild": interaction_.guild.id,
                                    "Score": self.sc,
                                    "Setting": 3,
                                }
                            },
                            upsert=True,
                        )
                    elif "BAN" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.update_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "$set": {
                                    "Guild": interaction_.guild.id,
                                    "Score": self.sc,
                                    "Setting": 4,
                                }
                            },
                            upsert=True,
                        )
                    elif "なし" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.update_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "$set": {
                                    "Guild": interaction_.guild.id,
                                    "Score": self.sc,
                                    "Setting": 5,
                                }
                            },
                            upsert=True,
                        )
                    await interaction.response.send_message(
                        f"設定しました。\n{self.sc}: {select.values[0]}", ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        "あなたはコマンドの実行者ではありません。", ephemeral=True
                    )

        s1 = await self.get_score_warn(interaction_.guild, 1)
        s2 = await self.get_score_warn(interaction_.guild, 2)
        s3 = await self.get_score_warn(interaction_.guild, 3)
        s4 = await self.get_score_warn(interaction_.guild, 4)
        s5 = await self.get_score_warn(interaction_.guild, 5)
        s6 = await self.get_score_warn(interaction_.guild, 6)
        s7 = await self.get_score_warn(interaction_.guild, 7)
        s8 = await self.get_score_warn(interaction_.guild, 8)
        s9 = await self.get_score_warn(interaction_.guild, 9)
        s10 = await self.get_score_warn(interaction_.guild, 10)

        if スコア:
            await interaction_.response.send_message(
                view=ScoreView(スコア, self.bot.async_db["Main"]),
                embed=discord.Embed(
                    title="警告時の設定",
                    description=f"""
1. {self.return_warn_text(s1)}
2. {self.return_warn_text(s2)}
3. {self.return_warn_text(s3)}
4. {self.return_warn_text(s4)}
5. {self.return_warn_text(s5)}
6. {self.return_warn_text(s6)}
7. {self.return_warn_text(s7)}
8. {self.return_warn_text(s8)}
9. {self.return_warn_text(s9)}
10. {self.return_warn_text(s10)}
            """,
                    color=discord.Color.blue(),
                ),
            )
        else:
            await interaction_.response.send_message(
                embed=discord.Embed(
                    title="警告時の設定リスト",
                    description=f"""
1. {self.return_warn_text(s1)}
2. {self.return_warn_text(s2)}
3. {self.return_warn_text(s3)}
4. {self.return_warn_text(s4)}
5. {self.return_warn_text(s5)}
6. {self.return_warn_text(s6)}
7. {self.return_warn_text(s7)}
8. {self.return_warn_text(s8)}
9. {self.return_warn_text(s9)}
10. {self.return_warn_text(s10)}
            """,
                    color=discord.Color.blue(),
                )
            )

    @settings.command(name="expand", description="メッセージ展開を有効化します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def setting_message_expand(
        self,
        interaction: discord.Interaction,
        有効化するか: bool,
        外部からの展開を許可するか: bool,
    ):
        db = self.bot.async_db["Main"].ExpandSettings

        if 有効化するか:
            # 有効化する場合
            await db.update_one(
                {"Guild": interaction.guild.id},
                {
                    "$set": {
                        "Guild": interaction.guild.id,
                        "Enabled": True,
                        "Outside": 外部からの展開を許可するか,
                    }
                },
                upsert=True,
            )

            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="メッセージ展開を有効化しました。",
                    description=(
                        "メッセージURLを送信すると自動的に展開されます。\n"
                        f"外部からの展開: {'許可' if 外部からの展開を許可するか else '不許可'}"
                    ),
                )
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Enabled": False, "Outside": 外部からの展開を許可するか}},
                upsert=True,
            )

            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="メッセージ展開を無効化しました。",
                    description=f"外部からの展開: {'許可' if 外部からの展開を許可するか else '不許可'}",
                )
            )

    async def announce_pun_set_setting(
        self, guild: discord.Guild, channel: discord.TextChannel, tf=False
    ):
        db = self.bot.async_db["Main"].AnnouncePun
        if not tf:
            return await db.delete_one({"Guild": guild.id, "Channel": channel.id})
        else:
            await db.update_one(
                {"Guild": guild.id, "Channel": channel.id},
                {"$set": {"Guild": guild.id, "Channel": channel.id}},
                upsert=True,
            )

    @settings.command(name="auto-publish", description="自動アナウンス公開をします。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def auto_publication(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.TextChannel,
        有効にするか: bool,
    ):
        try:
            await interaction.response.defer()
            await self.announce_pun_set_setting(
                interaction.guild, チャンネル, 有効にするか
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="自動アナウンス公開を設定しました。",
                    description=f"{チャンネル.mention} で {'有効' if 有効にするか else '無効'} にしました。",
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="自動アナウンス公開を設定できませんでした。",
                    description="権限エラーです。",
                )
            )

    @settings.command(
        name="auto-replace-reply",
        description="アナウンスチャンネルで返信をすると自動的にBotのメッセージになる設定をします。",
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def auto_replace_reply(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.TextChannel,
        有効にするか: bool,
    ):
        if not チャンネル.is_news():
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="設定できませんでした。",
                    description="アナウンスチャンネルを指定して下さい。",
                ),
                ephemeral=True,
            )

        await interaction.response.defer()
        db = self.bot.async_db["MainTwo"].AnnounceAutoReplace
        if not 有効にするか:
            await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": チャンネル.id}
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id, "Channel": チャンネル.id},
                {"$set": {"Guild": interaction.guild.id, "Channel": チャンネル.id}},
                upsert=True,
            )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="自動アナウンスチャンネルでの\n返信メッセージ置き換えを設定しました。",
                description=f"{チャンネル.mention} で {'有効' if 有効にするか else '無効'} にしました。",
            )
        )

    @settings.command(
        name="file-deletor", description="自動的に削除するファイル形式を設定します。"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def file_deletor(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        拡張子: str,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        db = self.bot.async_db["Main"].FileAutoDeletor
        if 操作.value == "add":
            await db.update_one(
                {"guild_id": interaction.guild.id},
                {"$addToSet": {"end": 拡張子.replace(".", "")}},
                upsert=True,
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title=f"`.{拡張子.replace('.', '')}`をブロックするようにしました。"
                )
            )
        else:
            await db.update_one(
                {"guild_id": interaction.guild.id},
                {"$pull": {"end": 拡張子.replace(".", "")}},
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title=f"`.{拡張子.replace('.', '')}`をブロックしないようにしました。"
                )
            )

    @settings.command(name="auto-translate", description="自動翻訳をします。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.choices(
        翻訳先=[
            app_commands.Choice(name="日本語へ", value="ja"),
            app_commands.Choice(name="英語へ", value="en"),
        ]
    )
    async def auto_translate(
        self,
        interaction: discord.Interaction,
        翻訳先: app_commands.Choice[str],
        有効にするか: bool,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        db = self.bot.async_db["Main"].AutoTranslate
        if 有効にするか:
            await db.update_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
                {
                    "$set": {
                        "Guild": interaction.guild.id,
                        "Channel": interaction.channel.id,
                        "Lang": 翻訳先.value,
                    }
                },
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="自動翻訳を有効化しました。")
            )
        else:
            result = await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="自動翻訳は有効化されていません。"
                    )
                )
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="自動翻訳を無効化しました。")
            )

    @settings.command(
        name="good-morning", description="おはよう挨拶チャンネルをセットアップします。"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def good_morning(
        self,
        interaction: discord.Interaction,
        有効にするか: bool,
    ):
        db = self.bot.async_db["Main"].GoodMorningChannel
        if 有効にするか:
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
                    title="おはよう挨拶を有効化しました。",
                    description="毎日8時に通知します。",
                )
            )
        else:
            result = await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(title="おはよう挨拶は有効化されていません。")
                )
            await interaction.response.send_message(
                embed=make_embed.success_embed(title="おはよう挨拶を無効化しました。")
            )

    @commands.Cog.listener("on_message")
    async def on_message_auto_thread(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild:
            return

        db = self.bot.async_db["MainTwo"].AutoThread

        dbfind = await db.find_one({"Guild": message.guild.id})
        if not dbfind or "Channels" not in dbfind:
            return

        channels = dbfind["Channels"]

        channel_data = channels.get(str(message.channel.id))
        if not channel_data:
            return

        current_time = time.time()
        last_message_time = cooldown_auto_thread.get(message.channel.id, 0)
        if current_time - last_message_time < 3:
            return
        cooldown_auto_thread[message.channel.id] = current_time

        thread_name = channel_data.get("ThreadName", "{Name}のスレッド").format(
            Name=message.author.display_name, Channel=message.channel.name
        )

        try:
            await message.create_thread(name=thread_name)
        except discord.HTTPException as e:
            return

    @settings.command(name="auto-thread", description="自動スレッド作成を設定します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def auto_thread(
        self,
        interaction: discord.Interaction,
        チャンネル: discord.TextChannel,
        有効にするか: bool,
        スレッド名: str = "{Name}のスレッド",
    ):
        db = interaction.client.async_db["MainTwo"].AutoThread
        guild_id = interaction.guild.id

        dbfind = await db.find_one({"Guild": guild_id}) or {
            "Guild": guild_id,
            "Channels": {},
        }
        channels = dbfind.get("Channels", {})

        if 有効にするか:
            channels[str(チャンネル.id)] = {"ThreadName": スレッド名}
            await db.update_one(
                {"Guild": guild_id}, {"$set": {"Channels": channels}}, upsert=True
            )
            status_text = "有効化"
        else:
            channels.pop(str(チャンネル.id), None)
            await db.update_one(
                {"Guild": guild_id}, {"$set": {"Channels": channels}}, upsert=True
            )
            status_text = "無効化"

        embed = make_embed.success_embed(
            title=f"自動スレッド作成を{status_text}しました",
            description=f"チャンネル: {チャンネル.mention}\nスレッド名テンプレート: `{スレッド名}`",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @settings.command(name="lang", description="Change the bot's language. (Beta)")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.choices(
        言語=[
            app_commands.Choice(name="日本語", value="ja"),
            app_commands.Choice(name="English", value="en"),
        ]
    )
    async def bot_langs(
        self, interaction: discord.Interaction, 言語: app_commands.Choice[str]
    ):
        await translate.set_guild_lang(interaction.guild.id, 言語.value)
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="Change the bot's language.", description=言語.name
            )
        )

    async def user_setting_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=setting_name, value=setting_name)
            for setting_name in block.SETTINDS_LIST
            if current.lower() in setting_name.lower()
        ]

    @settings.command(name="block", description="機能のブロックを設定します。")
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.autocomplete(設定=user_setting_autocomplete)
    async def block_setting(
        self, interaction: discord.Interaction, 設定: str, 有効か: bool
    ):
        if not 設定 in block.SETTINDS_LIST:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="ブロックに失敗しました。",
                    description="その機能は存在しません。",
                ),
            )
        db = interaction.client.async_db["MainTwo"].UserBlockSetting
        if 有効か:
            await db.update_one(
                {"user_id": interaction.user.id},
                {"$addToSet": {"blockd_func": 設定}},
                upsert=True,
            )
            await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="機能をブロックしました。",
                    description=f"{設定}をブロックしました。",
                ),
            )
        else:
            await db.update_one(
                {"user_id": interaction.user.id},
                {"$pull": {"blockd_func": 設定}},
                upsert=True,
            )
            await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="機能をブロックしました。",
                    description=f"{設定}のブロックを解除しました。",
                ),
            )


async def setup(bot):
    await bot.add_cog(SettingCog(bot))
