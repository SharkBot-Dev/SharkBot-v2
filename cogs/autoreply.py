from discord.ext import commands
import discord
from discord import app_commands
import re
import datetime
import time

import json
import io
from models import command_disable, make_embed
import random

COOLDOWN_TIME = 10
user_last_message_time = {}

COOLDOWN_TIME = 5
user_last_message_time2 = {}

cooldown_autoreply_word = {}

blacklist_word = [
    "ちん",
    "うんち",
    "ヘイト",
    "児童",
    "ポルノ",
    "死ね",
    "氏ね",
    "ファック",
    "セックス",
    "ペニス",
    "ちんこ",
    "ちんぽ",
    "喘",
    "孕",
    "まんこ",
    "ちんちん",
    "おっぱい",
    "くそ",
    "タヒね",
    "ﾀﾋね",
    "オナホ",
]


class AutoReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> AutoReplyCog")

    @commands.Cog.listener("on_message")
    async def on_message_ul(self, message):
        if message.author.bot:
            return
        if not message.content:
            return
        if "@" in message.content:
            return
        db = self.bot.async_db["Main"].ExpandSettingsUser
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        pattern = r"\d{17,19}"
        current_time = time.time()
        last_message_time = user_last_message_time2.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME:
            return
        user_last_message_time2[message.guild.id] = current_time
        msg = [int(match) for match in re.findall(pattern, message.content)]
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
            us = self.bot.get_user(msg[0])
            if us:
                if us.avatar:
                    await message.reply(
                        embed=discord.Embed(
                            title=f"{us.display_name}の情報",
                            color=discord.Color.green(),
                        )
                        .set_thumbnail(url=us.avatar.url)
                        .add_field(
                            name="基本情報",
                            value=f"ID: **{us.id}**\nユーザーネーム: **{us.name}#{us.discriminator}**\n作成日: **{us.created_at.astimezone(JST)}**",
                        )
                    )
                else:
                    await message.reply(
                        embed=discord.Embed(
                            title=f"{us.display_name}の情報",
                            color=discord.Color.green(),
                        ).add_field(
                            name="基本情報",
                            value=f"ID: **{us.id}**\nユーザーネーム: **{us.name}#{us.discriminator}**\n作成日: **{us.created_at.astimezone(JST)}**",
                        )
                    )
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_auto_reply_word(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].AutoReply
        try:
            dbfind = await db.find_one(
                {"Guild": message.guild.id, "Word": message.content}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_autoreply_word.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        cooldown_autoreply_word[message.guild.id] = current_time
        word = dbfind.get("ReplyWord", None)
        if not word:
            return
        if dbfind.get('TextChannel', 0) != 0:
            if dbfind.get('TextChannel', 0) != message.channel.id:
                return
        if dbfind.get('Roles', []) != []:
            for r in dbfind.get('Roles', []):
                if message.guild.get_role(r) in message.author.roles:
                    for b in blacklist_word:
                        if b in word:
                            return await message.reply("不適切な言葉が含まれています。")

                    word = word.split("|")

                    if len(word) != 1:
                        word = random.choice(word)
                    else:
                        word = dbfind.get("ReplyWord", None)
                    try:
                        await message.reply(
                            word.replace("\\n", "\n")
                            + "\n-# このメッセージは自動返信機能によるものです。"
                        )
                    except:
                        return
                    return
            return
        for b in blacklist_word:
            if b in word:
                return await message.reply("不適切な言葉が含まれています。")

        word = word.split("|")

        if len(word) != 1:
            word = random.choice(word)
        else:
            word = dbfind.get("ReplyWord", None)
        try:
            await message.reply(
                word.replace("\\n", "\n")
                + "\n-# このメッセージは自動返信機能によるものです。"
            )
        except:
            return

    autoreply = app_commands.Group(
        name="autoreply", description="自動返信関連の設定です。"
    )

    @autoreply.command(name="create", description="自動返信を作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreply_create_(
        self, interaction: discord.Interaction, 条件: str, 結果: str, 特定のチャンネルだけ: discord.TextChannel = None, 反応するロール1: discord.Role = None, 反応するロール2: discord.Role = None, 反応するロール3: discord.Role = None
    ):
        roles = [r.id for r in (反応するロール1, 反応するロール2, 反応するロール3) if r]

        channel_id = 特定のチャンネルだけ.id if 特定のチャンネルだけ else 0
        db = self.bot.async_db["Main"].AutoReply
        await db.update_one(
            {"Guild": interaction.guild.id, "Word": 条件},
            {"$set": {
                "Guild": interaction.guild.id,
                "Word": 条件,
                "ReplyWord": 結果,
                "TextChannel": channel_id,
                "Roles": roles
            }},
            upsert=True
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="自動返信を追加しました。"
            ).add_field(name="条件", value=条件, inline=False)
            .add_field(name="結果", value=結果, inline=False)
        )

    @autoreply.command(name="delete", description="自動返信を削除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreply_delete(self, interaction: discord.Interaction, 条件: str):
        db = self.bot.async_db["Main"].AutoReply
        result = await db.delete_one({"Guild": interaction.guild.id, "Word": 条件})
        if result.deleted_count == 0:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="何も削除されませんでした。"
                )
            )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="自動返信を削除しました。"
            )
        )

    @autoreply.command(name="list", description="自動返信をリストします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreply_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].AutoReply
        word_list = [
            f"{b.get('Word')} - {b.get('ReplyWord')}"
            async for b in db.find({"Guild": interaction.guild.id})
        ]
        for b in blacklist_word:
            if b in "\n".join(word_list):
                return await interaction.followup.send(
                    "不適切なワードが検出されました。"
                )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="自動返信のリストです"
            ).add_field(name="特定のワードに対して", value="\n".join(word_list))
        )

    @autoreply.command(
        name="templates", description="自動返信をテンプレートから作成します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.choices(
        テンプレート=[
            app_commands.Choice(name="挨拶", value="hello"),
            app_commands.Choice(name="ネタ", value="fun"),
            app_commands.Choice(name="絵文字", value="emoji"),
        ]
    )
    async def autoreply_templates(
        self, interaction: discord.Interaction, テンプレート: app_commands.Choice[str]
    ):
        db = self.bot.async_db["Main"].AutoReply
        if テンプレート.value == "hello":
            for t in [
                ("こんにちは", "こんにちは"),
                ("こんばんは", "こんばんは"),
                ("おはよう", "おはようございます"),
            ]:
                await db.update_one(
                    {"Guild": interaction.guild.id, "Word": t[0]},
                    {"$set": {
                        "Guild": interaction.guild.id,
                        "Word": t[0],
                        "ReplyWord": t[1]
                    }},
                    upsert=True
                )
        elif テンプレート.value == "fun":
            for t in [
                ("草", '草刈り～(o⌒▽⌒)o>━━"((卍))"ﾌﾞﾝﾌﾞﾝ♪'),
                ("334", "なんでや！阪神関係ないやろ！"),
                ("過疎", "バッチェ冷えてますよ〜"),
                ("そうだよ", "そうだよ(便乗)"),
                ("いいね", "あぁ〜^いいっすねぇ〜^"),
                ("ぬるぽ", "ガッ！"),
            ]:
                await db.update_one(
                    {"Guild": interaction.guild.id, "Word": t[0]},
                    {"$set": {
                        "Guild": interaction.guild.id,
                        "Word": t[0],
                        "ReplyWord": t[1]
                    }},
                    upsert=True
                )
        elif テンプレート.value == "emoji":
            for t in [("🌾", '草刈り～(o⌒▽⌒)o>━━"((卍))"ﾌﾞﾝﾌﾞﾝ♪'), ("👈", "👈")]:
                await db.update_one(
                    {"Guild": interaction.guild.id, "Word": t[0]},
                    {"$set": {
                        "Guild": interaction.guild.id,
                        "Word": t[0],
                        "ReplyWord": t[1]
                    }},
                    upsert=True
                )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title=f"自動返信を「{テンプレート.name}」から追加しました。"
            )
        )

    @autoreply.command(
        name="export", description="自動返信をjsonにエクスポートします。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreply_export(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].AutoReply
        word_list = [b async for b in db.find({"Guild": interaction.guild.id})]

        j = {}
        j["AutoReplys"] = [{w.get("Word"): w.get("ReplyWord")} for w in word_list]
        i_ = io.StringIO(json.dumps(j))
        await interaction.followup.send(file=discord.File(i_, "autoreply.json"))
        i_.close()

    @autoreply.command(
        name="import", description="自動返信をjsonからインポートします。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreply_import(
        self, interaction: discord.Interaction, ファイル: discord.Attachment
    ):
        await interaction.response.defer()
        try:
            res = json.loads(await ファイル.read())
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="Json読み込みに失敗しました。"
                )
            )

        c = 0
        db = self.bot.async_db["Main"].AutoReply
        for re in res.get("AutoReplys", []):
            if type(re) == dict:
                for k, v in re.items():
                    await db.replace_one(
                        {"Guild": interaction.guild.id, "Word": k},
                        {"Guild": interaction.guild.id, "Word": k, "ReplyWord": v},
                        upsert=True,
                    )
                    c += 1

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="自動返信をインポートしました。",
                description=f"{c}件インポートしました。"
            )
        )


async def setup(bot):
    await bot.add_cog(AutoReplyCog(bot))
