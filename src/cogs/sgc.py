import asyncio
import json
import time

import aiohttp
from discord.ext import commands
from discord import app_commands
import discord
import urllib.parse
from models import is_ban, make_embed
import io

user_last_message_timegc = {}

class SuperGlobalChatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.DEBUG = 707158343952629780
        self.DEBUG_DB = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        self.MAIN = 707158257818664991
        self.MAIN_DB = self.bot.async_db["Main"].AlpheSuperGlobalChat
        print("init -> SuperGlobalChatCog")

    # 招待リンクなどがあるかをチェック
    def filter_global(self, content: str) -> bool:
        blocked_words = [
            "discord.com",
            "discord.gg",
            "x.gd",
            "shorturl.asia",
            "tiny.cc",
            "everyone",
            "here",
        ]
        return not any(word in content for word in blocked_words)

    # Json作成
    async def sgc_make_json(self, message: discord.Message):
        dic = {
            "type": "message",
            "userId": str(message.author.id),
            "userName": message.author.name,
            "x-userGlobal_name": message.author.global_name,
            "userDiscriminator": message.author.discriminator,
            "userAvatar": getattr(message.author.avatar, "key", None),
            "isBot": message.author.bot,
            "guildId": str(message.guild.id) if message.guild else None,
            "guildName": message.guild.name if message.guild else "DM",
            "guildIcon": getattr(message.guild.icon, "key", None) if message.guild else None,
            "channelId": str(message.channel.id),
            "channelName": getattr(message.channel, "name", "DM"),
            "messageId": str(message.id),
            "content": message.content.replace("@", "＠")
        }

        if message.attachments:
            dic["attachmentsUrl"] = [a.url for a in message.attachments]

        pg = getattr(message.author, "primary_guild", None)
        if pg and getattr(pg, "tag", None):
            dic["x-userTag"] = pg.tag
            dic["x-userPrimaryGuild"] = {"tag": pg.tag}

        if message.reference:
            reference_msg = await message.channel.fetch_message(
                message.reference.message_id
            )  # メッセージIDから、元のメッセージを取得
            reference_mid = 0
            if (
                reference_msg.embeds
                and self.bot.user.id == reference_msg.application_id
            ):  # 返信の元のメッセージが、埋め込みメッセージかつ、このBOTが送信したメッセージのとき→グローバルチャットの他のサーバーからのメッセージと判断
                arr = reference_msg.embeds[0].footer.text.split(
                    " / "
                )  # 埋め込みのフッターを「 / 」区切りで取得

                for ref_msg in arr:  # 区切ったフッターをループ
                    if "mID:" in ref_msg:  # 「mID:」が含まれるとき
                        reference_mid = ref_msg.replace(
                            "mID:", "", 1
                        )  # 「mID:」を取り除いたものをメッセージIDとして取得
                        break

            elif (
                reference_msg.author != reference_msg.application_id
            ):  # 返信の元のメッセージが、このBOTが送信したメッセージでは無い時→同じチャンネルのメッセージと判断
                reference_mid = str(reference_msg.id)  # 返信元メッセージIDを取得

            dic.update({"reference": reference_mid})

        return json.dumps(dic, ensure_ascii=False)
    
    # ここからデバッグ
    async def send_super_global_chat_debug(self, message: discord.Message):
        if not self.filter_global(message.content):
            return

        db = self.DEBUG_DB
        channels = db.find()

        rmsg = None
        if message.reference:
            try:
                rmsg = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)
            except: pass

        async with aiohttp.ClientSession() as session:
            async for channel_config in channels:
                if channel_config["Channel"] == message.channel.id:
                    continue

                target_channel = self.bot.get_channel(channel_config["Channel"])
                if not target_channel:
                    continue

                embed = discord.Embed(color=discord.Color.blue())
                embed.set_footer(text=f"mID:{message.id} / SharkBot")
                
                author_icon = message.author.display_avatar.url

                if message.attachments:
                    first_at = message.attachments[0]
                    if any(first_at.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webm"]):
                        embed.set_image(url=first_at.url)
                    embed.add_field(name="添付ファイル", value=first_at.url, inline=False)

                if rmsg:
                    if rmsg.author.id != self.bot.user.id:
                        ref_val = rmsg.content or "（内容なし）"
                        embed.add_field(name=f"返信 ({rmsg.author})", value=ref_val[:1000], inline=False)
                    elif rmsg.embeds:
                        ref_name = rmsg.embeds[0].author.name.split(']')[1].split('/')[0].strip() if ']' in rmsg.embeds[0].author.name else "Unknown"
                        embed.add_field(name=f"返信 ({ref_name})", value=(rmsg.embeds[0].description or "（内容なし）")[:1000], inline=False)

                try:
                    webhook = discord.Webhook.from_url(channel_config.get("Webhook"), session=session)
                    await webhook.send(
                        content=message.clean_content,
                        embeds=[embed],
                        username=f"{message.author.name} ({message.author.id})",
                        avatar_url=author_icon,
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except: pass

    @commands.Cog.listener("on_message")
    async def on_message_superglobal_getjson_debug(self, message: discord.Message):
        if message.author.id == self.bot.user.id or message.guild is None:
            return
        if message.channel.id != self.DEBUG:
            return

        try:
            dic = json.loads(message.content)
        except: return

        if dic.get("type") != "message":
            return

        past_logs = []
        reference_mid = dic.get("reference")
        if reference_mid and reference_mid != "0":
            async for past_message in message.channel.history(limit=1000):
                try:
                    p_dic = json.loads(past_message.content)
                    if p_dic["type"] != "message":
                        continue
                    past_logs.append(p_dic)
                except: continue

        ref_author = "Unknown"
        ref_content = "メッセージが見つかりませんでした"
        if past_logs:
            for p_dic in past_logs:
                if str(p_dic.get("messageId")) == str(reference_mid):
                    ref_author = f"{p_dic.get('userName')}#{p_dic.get('userDiscriminator')}"
                    ref_content = p_dic.get("content", "内容なし")
                    break

        content = dic.get('content', "???")
        if not self.filter_global(content):
            await message.add_reaction("❌")
            return

        db = self.DEBUG_DB
        async with aiohttp.ClientSession() as session:
            async for ch in db.find():
                target_channel = self.bot.get_channel(ch["Channel"])
                if not target_channel:
                    continue

                embed = discord.Embed(color=discord.Color.blue())
                embed.set_footer(text=f"mID:{dic['messageId']} / {message.author.display_name}")
                
                avatar_url = f"https://cdn.discordapp.com/avatars/{dic['userId']}/{dic['userAvatar']}.png?size=1024" if dic["userAvatar"] else message.author.default_avatar.url

                if dic.get("attachmentsUrl"):
                    at_url = dic["attachmentsUrl"][0]
                    embed.add_field(name="添付ファイル", value=at_url)
                    if any(ext in at_url.lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".webm"]):
                        embed.set_image(url=urllib.parse.unquote(at_url))

                if reference_mid and reference_mid != "0":
                    embed.add_field(name=f"返信 ({ref_author})", value=ref_content[:1000], inline=False)

                try:
                    webhook = discord.Webhook.from_url(ch.get("Webhook"), session=session)
                    await webhook.send(
                        content=dic["content"],
                        embeds=[embed],
                        username=f"{dic['userName']} ({dic['userId']})",
                        avatar_url=avatar_url,
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except: pass

        await message.add_reaction("✅")

    async def demo_super_globalchat_check_message(self, message: discord.Message):
        db = self.DEBUG_DB
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    @commands.Cog.listener("on_message")
    async def on_message_super_global_debug(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if "!." in message.content:
            return

        check = await self.demo_super_globalchat_check_message(message)

        if not check:
            return

        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.author.id, 0)
        if current_time - last_message_time < 3:
            return
        user_last_message_timegc[message.author.id] = current_time

        await message.add_reaction("🔄")

        js = await self.sgc_make_json(message)
        await self.bot.get_channel(self.DEBUG).send(
            content=js, allowed_mentions=discord.AllowedMentions.none()
        )

        await self.send_super_global_chat_debug(message)
        await message.remove_reaction("🔄", self.bot.user)

        await message.add_reaction("✅")
        await asyncio.sleep(3)
        await message.remove_reaction("✅", message.guild.me)

    # ここから本番
    async def send_super_global_chat(self, message: discord.Message):
        if not self.filter_global(message.content):
            return

        db = self.MAIN_DB
        channels = db.find()

        rmsg = None
        if message.reference:
            try:
                rmsg = message.reference.resolved or await message.channel.fetch_message(message.reference.message_id)
            except: pass

        async with aiohttp.ClientSession() as session:
            async for channel_config in channels:
                if channel_config["Channel"] == message.channel.id:
                    continue

                target_channel = self.bot.get_channel(channel_config["Channel"])
                if not target_channel:
                    continue

                embed = discord.Embed(color=discord.Color.blue())
                embed.set_footer(text=f"mID:{message.id} / SharkBot")
                
                author_icon = message.author.display_avatar.url

                if message.attachments:
                    first_at = message.attachments[0]
                    if any(first_at.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webm"]):
                        embed.set_image(url=first_at.url)
                    embed.add_field(name="添付ファイル", value=first_at.url, inline=False)

                if rmsg:
                    if rmsg.author.id != self.bot.user.id:
                        ref_val = rmsg.content or "（内容なし）"
                        embed.add_field(name=f"返信 ({rmsg.author})", value=ref_val[:1000], inline=False)
                    elif rmsg.embeds:
                        ref_name = rmsg.embeds[0].author.name.split(']')[1].split('/')[0].strip() if ']' in rmsg.embeds[0].author.name else "Unknown"
                        embed.add_field(name=f"返信 ({ref_name})", value=(rmsg.embeds[0].description or "（内容なし）")[:1000], inline=False)

                try:
                    webhook = discord.Webhook.from_url(channel_config.get("Webhook"), session=session)
                    await webhook.send(
                        content=message.clean_content,
                        embeds=[embed],
                        username=f"{message.author.name} ({message.author.id})",
                        avatar_url=author_icon,
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except: pass

    @commands.Cog.listener("on_message")
    async def on_message_superglobal_getjson(self, message: discord.Message):
        if message.author.id == self.bot.user.id or message.guild is None:
            return
        if message.channel.id != self.MAIN:
            return

        try:
            dic = json.loads(message.content)
        except: return

        if dic.get("type") != "message":
            return
        
        past_logs = []
        reference_mid = dic.get("reference")
        if reference_mid and reference_mid != "0":
            async for past_message in message.channel.history(limit=1000):
                try:
                    p_dic = json.loads(past_message.content)
                    if p_dic["type"] != "message":
                        continue
                    past_logs.append(p_dic)
                except: continue

        ref_author = "Unknown"
        ref_content = "メッセージが見つかりませんでした"
        if past_logs:
            for p_dic in past_logs:
                if str(p_dic.get("messageId")) == str(reference_mid):
                    ref_author = f"{p_dic.get('userName')}#{p_dic.get('userDiscriminator')}"
                    ref_content = p_dic.get("content", "内容なし")
                    break

        content = dic.get('content', "???")
        if not self.filter_global(content):
            await message.add_reaction("❌")
            return

        db = self.MAIN_DB
        async with aiohttp.ClientSession() as session:
            async for ch in db.find():
                target_channel = self.bot.get_channel(ch["Channel"])
                if not target_channel:
                    continue

                embed = discord.Embed(color=discord.Color.blue())
                embed.set_footer(text=f"mID:{dic['messageId']} / {message.author.display_name}")
                
                avatar_url = f"https://cdn.discordapp.com/avatars/{dic['userId']}/{dic['userAvatar']}.png?size=1024" if dic["userAvatar"] else message.author.default_avatar.url

                if dic.get("attachmentsUrl"):
                    at_url = dic["attachmentsUrl"][0]
                    embed.add_field(name="添付ファイル", value=at_url)
                    if any(ext in at_url.lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".webm"]):
                        embed.set_image(url=urllib.parse.unquote(at_url))

                if reference_mid and reference_mid != "0":
                    embed.add_field(name=f"返信 ({ref_author})", value=ref_content[:1000], inline=False)

                try:
                    webhook = discord.Webhook.from_url(ch.get("Webhook"), session=session)
                    await webhook.send(
                        content=dic["content"],
                        embeds=[embed],
                        username=f"{dic['userName']} ({dic['userId']})",
                        avatar_url=avatar_url,
                        allowed_mentions=discord.AllowedMentions.none()
                    )
                except: pass

        await message.add_reaction("✅")

    async def super_globalchat_check_message(self, message: discord.Message):
        db = self.MAIN_DB
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    @commands.Cog.listener("on_message")
    async def on_message_super_global(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if "!." in message.content:
            return

        check = await self.super_globalchat_check_message(message)

        if not check:
            return

        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.author.id, 0)
        if current_time - last_message_time < 3:
            return
        user_last_message_timegc[message.author.id] = current_time

        await message.add_reaction("🔄")

        js = await self.sgc_make_json(message)
        await self.bot.get_channel(self.MAIN).send(
            content=js, allowed_mentions=discord.AllowedMentions.none()
        )

        await self.send_super_global_chat(message)
        await message.remove_reaction("🔄", self.bot.user)

        await message.add_reaction("✅")
        await asyncio.sleep(3)
        await message.remove_reaction("✅", message.guild.me)

async def setup(bot):
    await bot.add_cog(SuperGlobalChatCog(bot))
