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
from models import command_disable

COOLDOWN_TIME_KEIGO = 5
cooldown_keigo_time = {}
COOLDOWN_TIME_TRANS = 3
cooldown_trans_time = {}
COOLDOWN_TIME_EXPAND = 5
cooldown_expand_time = {}
cooldown_auto_protect_time = {}
cooldown_auto_translate = {}

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
            await db.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id},
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
                    await db.replace_one(
                        {
                            "Channel": interaction_.channel.id,
                            "Guild": interaction_.guild.id,
                        },
                        {
                            "Channel": interaction_.channel.id,
                            "Guild": interaction_.guild.id,
                            "Title": self.etitle.value,
                            "Description": self.desc.value,
                        },
                        upsert=True,
                    )
                    await interaction_.response.send_message(
                        embed=discord.Embed(
                            title="ウェルカムメッセージを有効化しました。",
                            color=discord.Color.green(),
                        )
                    )

            await interaction.response.send_modal(send(interaction.client.async_db))
        else:
            db = interaction.client.async_db["Main"].WelcomeMessage
            result = await db.delete_one(
                {
                    "Channel": interaction.channel.id,
                }
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="ウェルカムメッセージを無効化しました。",
                    color=discord.Color.green(),
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
                    await db.replace_one(
                        {
                            "Channel": interaction_.channel.id,
                            "Guild": interaction_.guild.id,
                        },
                        {
                            "Channel": interaction_.channel.id,
                            "Guild": interaction_.guild.id,
                            "Title": self.etitle.value,
                            "Description": self.desc.value,
                        },
                        upsert=True,
                    )
                    await interaction_.response.send_message(
                        embed=discord.Embed(
                            title="さようならメッセージを有効化しました。",
                            color=discord.Color.green(),
                        )
                    )

            await interaction.response.send_modal(send(interaction.client.async_db))
        else:
            db = interaction.client.async_db["Main"].GoodByeMessage
            result = await db.delete_one(
                {
                    "Channel": interaction.channel.id,
                }
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="さようならメッセージを無効化しました。",
                    color=discord.Color.green(),
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
                    await db.replace_one(
                        {
                            "Channel": interaction.channel.id,
                            "Guild": interaction.guild.id,
                        },
                        {
                            "Channel": interaction.channel.id,
                            "Guild": interaction.guild.id,
                            "Title": self.etitle.value,
                            "Description": self.desc.value,
                        },
                        upsert=True,
                    )
                    await interaction_.response.send_message(
                        embed=discord.Embed(
                            title="BANメッセージを有効化しました。",
                            color=discord.Color.green(),
                        )
                    )

            await interaction.response.send_modal(send(interaction.client.async_db))
        else:
            db = interaction.client.async_db["Main"].BanMessage
            result = await db.delete_one(
                {
                    "Channel": interaction.channel.id,
                }
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="BANメッセージを無効化しました。", color=discord.Color.green()
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

        translator = GoogleTranslator(source="auto", target=dbfind.get("Lang", "en"))
        translated_text = translator.translate(message.content)

        embed = discord.Embed(
            title=f"<:Success:1362271281302601749> 翻訳 ({dbfind.get('Lang', 'en')} へ)",
            description=f"{translated_text}",
            color=discord.Color.green(),
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
            await db.replace_one(
                {"Guild": message.guild.id, "User": message.author.id},
                {"Guild": message.guild.id, "User": message.author.id, "Score": 1},
                upsert=True,
            )
            try:
                await self.run_warn(1, message)
                return
            except:
                return
        else:
            await db.replace_one(
                {"Guild": message.guild.id, "User": message.author.id},
                {
                    "Guild": message.guild.id,
                    "User": message.author.id,
                    "Score": dbfind["Score"] + 1,
                },
                upsert=True,
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.replace_one(
                    {"Guild": message.guild.id, "User": message.author.id},
                    {"Guild": message.guild.id, "User": message.author.id, "Score": 0},
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
            await db.replace_one(
                {"Guild": guild.id, "User": user.id},
                {"Guild": guild.id, "User": user.id, "Score": 1},
                upsert=True,
            )
            try:
                await self.run_warn_automod(1, guild, user)
                return
            except:
                return
        else:
            await db.replace_one(
                {"Guild": guild.id, "User": user.id},
                {"Guild": guild.id, "User": user.id, "Score": dbfind["Score"] + 1},
                upsert=True,
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.replace_one(
                    {"Guild": guild.id, "User": user.id},
                    {"Guild": guild.id, "User": user.id, "Score": 0},
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
            await db.replace_one(
                {"Guild": message.guild.id, "User": int_.user.id},
                {"Guild": message.guild.id, "User": int_.user.id, "Score": 1},
                upsert=True,
            )
            try:
                await self.run_warn_int_author(1, message, int_)
                return
            except Exception:
                return
        else:
            await db.replace_one(
                {"Guild": message.guild.id, "User": int_.user.id},
                {
                    "Guild": message.guild.id,
                    "User": int_.user.id,
                    "Score": dbfind["Score"] + 1,
                },
                upsert=True,
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.replace_one(
                    {"Guild": message.guild.id, "User": int_.user.id},
                    {"Guild": message.guild.id, "User": int_.user.id, "Score": 0},
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
                        f"スコアが追加されました。\n現在のスコア: {sc}"
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
                        f"スコアが追加されました。\n現在のスコア: {sc}"
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
                        f"スコアが追加されました。\n現在のスコア: {sc}"
                    )
                except:
                    return
            if channel_db_find is None:
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(
                        f"スコアが追加されました。\n現在のスコア: {sc}"
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
                        f"スコアが追加されました。\n現在のスコア: {sc}"
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
                        f"スコアが追加されました。\n現在のスコア: {sc}"
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
                    f"スコアが追加されました。\n現在のスコア: {sc}"
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

    settings = app_commands.Group(name="settings", description="設定系のコマンドです。")

    settings.add_command(RoleCommands())
    settings.add_command(WelcomeCommands())
    settings.add_command(CommandsManageGroup())

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
                    msg = await interaction.channel.send(
                        embed=discord.Embed(
                            title=self.etitle.value,
                            description=self.desc.value,
                            color=discord.Color.random(),
                        ),
                        view=view,
                    )
                    db = self.db["Main"].LockMessage
                    await db.replace_one(
                        {
                            "Channel": interaction.channel.id,
                            "Guild": interaction.guild.id,
                        },
                        {
                            "Channel": interaction.channel.id,
                            "Guild": interaction.guild.id,
                            "Title": self.etitle.value,
                            "Desc": self.desc.value,
                            "MessageID": msg.id,
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
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {"Guild": interaction.guild.id, "Prefix": prefix},
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
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 8,
                                },
                                upsert=True,
                            )
                        else:
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 8,
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
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 5,
                                },
                                upsert=True,
                            )
                        else:
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 5,
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
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 3,
                                },
                                upsert=True,
                            )
                        else:
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 3,
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
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 9,
                                },
                                upsert=True,
                            )
                        else:
                            await db.replace_one(
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                },
                                {
                                    "Guild": interaction.guild.id,
                                    "User": self.ユーザー.id,
                                    "Score": 9,
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
                        await dbs.replace_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "Guild": interaction_.guild.id,
                                "Score": self.sc,
                                "Setting": 0,
                            },
                            upsert=True,
                        )
                    elif "タイムアウト5分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "Guild": interaction_.guild.id,
                                "Score": self.sc,
                                "Setting": 1,
                            },
                            upsert=True,
                        )
                    elif "タイムアウト10分" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "Guild": interaction_.guild.id,
                                "Score": self.sc,
                                "Setting": 2,
                            },
                            upsert=True,
                        )
                    elif "Kick" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "Guild": interaction_.guild.id,
                                "Score": self.sc,
                                "Setting": 3,
                            },
                            upsert=True,
                        )
                    elif "BAN" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "Guild": interaction_.guild.id,
                                "Score": self.sc,
                                "Setting": 4,
                            },
                            upsert=True,
                        )
                    elif "なし" == select.values[0]:
                        dbs = self.db.WarnScoreSetting
                        await dbs.replace_one(
                            {"Guild": interaction_.guild.id, "Score": self.sc},
                            {
                                "Guild": interaction_.guild.id,
                                "Score": self.sc,
                                "Setting": 5,
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
        self, interaction: discord.Interaction, 有効化するか: bool
    ):
        db = self.bot.async_db["Main"].ExpandSettings
        if 有効化するか:
            await db.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="メッセージ展開を有効化しました。",
                    color=discord.Color.green(),
                )
            )
        else:
            result = await db.delete_one({"Guild": interaction.guild.id})
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="メッセージ展開は無効です。", color=discord.Color.red()
                    )
                )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="メッセージ展開を無効化しました。", color=discord.Color.red()
                )
            )

    async def announce_pun_set_setting(
        self, guild: discord.Guild, channel: discord.TextChannel, tf=False
    ):
        db = self.bot.async_db["Main"].AnnouncePun
        if not tf:
            return await db.delete_one({"Guild": guild.id, "Channel": channel.id})
        else:
            await db.replace_one(
                {"Guild": guild.id, "Channel": channel.id},
                {"Guild": guild.id, "Channel": channel.id},
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
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        try:
            await interaction.response.defer()
            await self.announce_pun_set_setting(
                interaction.guild, チャンネル, 有効にするか
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="自動アナウンス公開を設定しました。",
                    color=discord.Color.green(),
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="自動アナウンス公開を設定できませんでした。",
                    color=discord.Color.red(),
                    description="権限エラーです。",
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
                embed=discord.Embed(
                    title=f"`.{拡張子.replace('.', '')}`をブロックするようにしました。",
                    color=discord.Color.green(),
                )
            )
        else:
            await db.update_one(
                {"guild_id": interaction.guild.id},
                {"$pull": {"end": 拡張子.replace(".", "")}},
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"`.{拡張子.replace('.', '')}`をブロックしないようにしました。",
                    color=discord.Color.green(),
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
            await db.replace_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id},
                {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "Lang": 翻訳先.value,
                },
                upsert=True,
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="自動翻訳を有効化しました。", color=discord.Color.green()
                )
            )
        else:
            result = await db.delete_one(
                {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=discord.Embed(
                        title="自動翻訳は有効化されていません。",
                        color=discord.Color.red(),
                    )
                )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="自動翻訳を無効化しました。", color=discord.Color.red()
                )
            )


async def setup(bot):
    await bot.add_cog(SettingCog(bot))
