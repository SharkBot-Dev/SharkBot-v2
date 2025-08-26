from discord.ext import commands
import discord
from discord import app_commands
import traceback
import sys
import logging
import asyncio
import re
import datetime
import time
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
	"オナホ"
]

class AutoReplyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> AutoReplyCog")

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
                    await message.reply(embed=discord.Embed(title=f"{us.display_name}の情報", color=discord.Color.green()).set_thumbnail(url=us.avatar.url).add_field(name="基本情報", value=f"ID: **{us.id}**\nユーザーネーム: **{us.name}#{us.discriminator}**\n作成日: **{us.created_at.astimezone(JST)}**"))
                else:
                    await message.reply(embed=discord.Embed(title=f"{us.display_name}の情報", color=discord.Color.green()).add_field(name="基本情報", value=f"ID: **{us.id}**\nユーザーネーム: **{us.name}#{us.discriminator}**\n作成日: **{us.created_at.astimezone(JST)}**"))
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
            dbfind = await db.find_one({"Guild": message.guild.id, "Word": message.content}, {"_id": False})
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
        for b in blacklist_word:
            if b in word:
                return await message.reply("不適切な言葉が含まれています。")
        try:
            await message.reply(word.replace("\\n", "\n") + "\n-# このメッセージは自動返信機能によるものです。")
        except:
            return

    autoreply = app_commands.Group(name="autoreply", description="自動返信関連の設定です。")

    @autoreply.command(name="create", description="自動返信を作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @commands.has_permissions(manage_channels=True)
    async def autoreply_create_(self, interaction: discord.Interaction, 条件: str, 結果: str):
        db = self.bot.async_db["Main"].AutoReply
        await db.replace_one(
            {"Guild": interaction.guild.id, "Word": 条件}, 
            {"Guild": interaction.guild.id, "Word": 条件, "ReplyWord": 結果}, 
            upsert=True
        )
        await interaction.response.send_message(embed=discord.Embed(title="自動返信を追加しました。", color=discord.Color.green()))

    @autoreply.command(name="delete", description="自動返信を削除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @commands.has_permissions(manage_channels=True)
    async def autoreply_delete(self, interaction: discord.Interaction, 条件: str):
        db = self.bot.async_db["Main"].AutoReply
        result = await db.delete_one(
            {"Guild": interaction.guild.id, "Word": 条件}
        )
        if result.deleted_count == 0:
            return await interaction.response.send_message(embed=discord.Embed(title="何も削除されませんでした。", color=discord.Color.red()))
        await interaction.response.send_message(embed=discord.Embed(title="自動返信を削除しました。", color=discord.Color.green()))

    @autoreply.command(name="list", description="自動返信をリストします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    @commands.has_permissions(manage_channels=True)
    async def autoreply_list(self, interaction: discord.Interaction, 条件: str):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].AutoReply
        word_list = [f"{b.get("Word")} - {b.get("ReplyWord")}" async for b in db.find({"Guild": interaction.guild.id})]
        for b in blacklist_word:
            if b in "\n".join(word_list):
                return await interaction.followup.send("不適切なワードが検出されました。")
        await interaction.followup.send(embed=discord.Embed(title="自動返信のリスト", color=discord.Color.green()).add_field(name="特定のワードに対して", value="\n".join(word_list)))

async def setup(bot):
    await bot.add_cog(AutoReplyCog(bot))