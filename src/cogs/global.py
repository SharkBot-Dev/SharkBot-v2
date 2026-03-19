import random

from discord.ext import commands
import discord
import time
import asyncio
import json
from discord import Webhook
from discord import app_commands
import aiohttp
import urllib.parse

from models import command_disable, make_embed, is_ban, globalchat
import re

from cryptography.fernet import Fernet

from consts import settings

COOLDOWN_TIMEGC = 3
user_last_message_timegc = {}
user_last_message_time_ad = {}

user_last_message_time_thread = {}

user_last_message_time_mute = {}

cooldown_transfer = {}
cooldown_up = {}

invite_only_check = re.compile(
    r"^(https?://)?(www\.)?(discord\.gg/|discord\.com/invite/)[a-zA-Z0-9]+$"
)

class RandomJoinView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
        
    @discord.ui.button(label="参加する！", style=discord.ButtonStyle.primary, emoji="🎲")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        button.disabled = True
        await interaction.edit_original_response(view=self)

        db_reg = self.bot.async_db["Main"].Register
        guilds_list = await db_reg.find({}).to_list(length=100)
        random.shuffle(guilds_list)

        success = False
        for g_data in guilds_list:
            target_id = g_data["Guild"]
            guild = self.bot.get_guild(target_id)

            if not guild or interaction.user in guild.members:
                continue

            invite = g_data.get('Invite')

            await interaction.followup.send(f"{guild.name} を当てました！\n\n{invite}", ephemeral=True)
            success = True
            break

        if not success:
            await interaction.followup.send("新しく参加できるサーバーが現在ありません。", ephemeral=True)

class RuleModal(discord.ui.Modal):
    def __init__(self, room_name: str):
        super().__init__(title="ルールを制定する", timeout=360)
        self.room_name = room_name

    text = discord.ui.TextInput(
        label="ルールを入力",
        placeholder="ここにルールを入力",
        style=discord.TextStyle.long,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        db = interaction.client.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": self.room_name, "Owner": interaction.user.id}, {"_id": False}
        )
        if not dbfind:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはルームのオーナーではありません！",
                    description="オーナーしか設定は変更できません。",
                ),
            )

        await db.update_one(
            {"Name": self.room_name, "Owner": interaction.user.id},
            {"$set": {"Rule": self.text.value}},
        )

        await interaction.followup.send(
            ephemeral=True,
            embed=make_embed.success_embed(
                title="ルールを制定しました。",
                description=self.text.value,
            ),
        )

class SitesModal(discord.ui.Modal, title="サイトの作成"):
    text = discord.ui.TextInput(
        label="説明",
        placeholder="とても人気なサーバーです！",
        style=discord.TextStyle.long,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        inv = await interaction.channel.create_invite()
        await interaction.client.async_db["MainTwo"].ServerPage.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Text": self.text.value,
                    "Name": interaction.guild.name,
                    "Invite": inv.url,
                    "Icon": interaction.guild.icon.url,
                }
            },
            upsert=True,
        )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="サイトを作成しました。",
                description=f"https://sharkbot.xyz/server/{interaction.guild.id}",
            )
        )


class GlobalThreadGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="thread", description="グローバルスレッド関連のコマンドです。"
        )

    @app_commands.command(name="join", description="グローバルスレッドに参加します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_thread_join(
        self, interaction: discord.Interaction, 板名: str = "総合"
    ):
        await interaction.response.defer()
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="テキストチャンネルでのみ参加できます。"
                )
            )
        wh = await interaction.channel.create_webhook(name=f"グローバルスレッド-{板名}")
        db = interaction.client.async_db["MainTwo"].GlobalThread
        await db.update_one(
            {"name": 板名},
            {
                "$push": {
                    "channels": {
                        "guild_id": interaction.guild.id,
                        "channel_id": interaction.channel.id,
                        "webhook_url": wh.url,
                    }
                }
            },
            upsert=True,
        )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title="グローバルスレッドに参加しました。",
                description="常識を持った発言してください。",
            )
        )

    @app_commands.command(
        name="leave", description="グローバルスレッドから退出します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_thread_leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = interaction.client.async_db["MainTwo"].GlobalThread

        data = await db.find_one({"channels.channel_id": interaction.channel.id})
        if not data:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="このチャンネルはグローバルスレッドではありません。"
                )
            )

        target_channel = next(
            (
                ch
                for ch in data["channels"]
                if ch["channel_id"] == interaction.channel.id
            ),
            None,
        )
        if not target_channel:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="このチャンネルは登録されていません。"
                )
            )

        existing_groups = data.get("thread_groups", [])

        for group in existing_groups:
            group["threads"] = [
                t
                for t in group.get("threads", [])
                if t["channel_id"] != interaction.channel.id
            ]

        await db.update_one(
            {"_id": data["_id"]},
            {
                "$pull": {"channels": {"channel_id": interaction.channel.id}},
                "$set": {"thread_groups": existing_groups},
            },
        )

        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title="グローバルスレッドから退出しました。",
                description="グローバルスレッドで使用されていたWebHookは各自削除してください。",
            )
        )


class GlobalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> GlobalCog")

    @commands.Cog.listener("on_thread_create")
    async def on_thread_create_global(self, thread: discord.Thread):
        if thread.owner_id == self.bot.user.id:
            return
        
        if thread.owner.bot:
            return

        db = self.bot.async_db["MainTwo"].GlobalThread
        parent_channel_id = thread.parent_id
        guild_id = thread.guild.id

        data = await db.find_one({"channels.channel_id": parent_channel_id})
        if not data:
            return

        current_time = time.time()
        last_message_time = user_last_message_time_thread.get(thread.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        user_last_message_time_thread[thread.guild.id] = current_time

        await thread.send('グローバルスレッドは削除されました。\n詳しくは公式サーバーを確認してください。')
        return

        thread_name = thread.name
        all_channels = data["channels"]

        thread_group = next(
            (g for g in data.get("thread_groups", []) if g["thread_id"] == thread.id),
            None,
        )

        if not thread_group:
            thread_group = {
                "parent_channel_id": parent_channel_id,
                "thread_id": thread.id,
                "threads": [],
            }

        thread_group["threads"].append(
            {
                "guild_id": guild_id,
                "channel_id": parent_channel_id,
                "thread_id": thread.id,
            }
        )

        async with aiohttp.ClientSession() as session:
            for ch in all_channels:
                if ch["channel_id"] == parent_channel_id:
                    continue

                target_guild = self.bot.get_guild(ch["guild_id"])
                if not target_guild:
                    continue

                target_channel = target_guild.get_channel(ch["channel_id"])
                if not target_channel:
                    continue

                try:
                    new_thread = await target_channel.create_thread(
                        name=thread_name, type=discord.ChannelType.public_thread
                    )
                except:
                    continue

                webhook = Webhook.from_url(ch["webhook_url"], session=session)

                try:
                    await webhook.send(
                        content=thread.starter_message.content,
                        username=thread.starter_message.author.display_name,
                        avatar_url=(
                            thread.starter_message.author.avatar.url
                            if thread.starter_message.author.avatar
                            else None
                        ),
                        allowed_mentions=discord.AllowedMentions.none(),
                        thread=new_thread,
                    )
                except:
                    continue

                thread_group["threads"].append(
                    {
                        "guild_id": ch["guild_id"],
                        "channel_id": ch["channel_id"],
                        "thread_id": new_thread.id,
                    }
                )

                await asyncio.sleep(1)

        existing_groups = data.get("thread_groups", [])

        existing_groups = [
            g for g in existing_groups if g.get("thread_id") != thread.id
        ]
        existing_groups.append(thread_group)

        await db.update_one(
            {"_id": data["_id"]}, {"$set": {"thread_groups": existing_groups}}
        )

        await thread.starter_message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_globalthread(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.type != discord.ChannelType.public_thread:
            return

        db = self.bot.async_db["MainTwo"].GlobalThread

        data = await db.find_one(
            {"thread_groups.threads.thread_id": message.channel.id}
        )

        if not data:
            return

        target_group = next(
            (
                group
                for group in data["thread_groups"]
                if any(t["thread_id"] == message.channel.id for t in group["threads"])
            ),
            None,
        )

        if not target_group:
            return

        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = user_last_message_time_thread.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        user_last_message_time_thread[message.guild.id] = current_time

        await message.reply('グローバルスレッドは削除されました。\n詳しくは公式サーバーを確認してください。')
        return

        async with aiohttp.ClientSession() as session:
            for t in target_group["threads"]:
                if t["thread_id"] == message.channel.id:
                    continue

                webhook_data = next(
                    (c for c in data["channels"] if c["channel_id"] == t["channel_id"]),
                    None,
                )
                if not webhook_data:
                    continue

                webhook = Webhook.from_url(webhook_data["webhook_url"], session=session)

                guild = self.bot.get_guild(t["guild_id"])
                if not guild:
                    continue
                target_channel = guild.get_channel(t["channel_id"])
                if not target_channel:
                    continue

                target_thread = target_channel.get_thread(t["thread_id"])
                if not target_thread:
                    try:
                        target_thread = await target_channel.fetch_message(
                            t["thread_id"]
                        )

                        await asyncio.sleep(1)
                    except:
                        await asyncio.sleep(1)
                        continue

                try:
                    if not message.attachments == []:
                        embed = discord.Embed(
                            title="添付ファイル", color=discord.Color.blue()
                        )

                        for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                            if kaku in message.attachments[0].filename:
                                embed.set_image(url=message.attachments[0].url)
                                break
                        embed.add_field(
                            name="添付ファイル",
                            value=message.attachments[0].url,
                            inline=False,
                        )

                        await webhook.send(
                            content=message.content,
                            username=message.author.display_name,
                            avatar_url=(
                                message.author.avatar.url
                                if message.author.avatar
                                else None
                            ),
                            thread=target_thread,
                            allowed_mentions=discord.AllowedMentions.none(),
                            embed=embed,
                        )
                    else:
                        await webhook.send(
                            content=message.content,
                            username=message.author.display_name,
                            avatar_url=(
                                message.author.avatar.url
                                if message.author.avatar
                                else None
                            ),
                            thread=target_thread,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                except:
                    continue

                await asyncio.sleep(0.3)

    async def getColor(self, user: discord.User):
        db = self.bot.async_db["MainTwo"].GlobalColor
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return discord.Color.blue()
        if dbfind is None:
            return discord.Color.blue()
        color = dbfind.get("Color", "blue")
        if color == "blue":
            return discord.Color.blue()
        elif color == "red":
            return discord.Color.red()
        elif color == "green":
            return discord.Color.green()
        elif color == "random":
            return discord.Color.random()

    async def check_edit_ticket(self, message: discord.Message):
        try:
            db = self.bot.async_db["Main"].SharkPoint
            user_data = await db.find_one({"_id": message.author.id})
            if user_data and user_data.get("editnick", 0) != 0:
                return True
            else:
                return False
        except:
            return False

    async def user_block(self, message: discord.Message):
        db = self.bot.async_db["Main"].BlockUser
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return False
        if dbfind is not None:
            return True
        return False

    async def get_guild_emoji(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].NewGlobalChatEmoji
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            if dbfind is None:
                return "😎"
            return dbfind.get("Emoji", "😎")
        except Exception:
            return "😎"

    async def send_one_join_globalchat(self, webhook: str, ctx: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                title=f"{ctx.guild.name}が参加したよ！よろしく！",
                description=f"オーナーID: {ctx.guild.owner_id}\nコマンド実行者: {ctx.user.display_name}/({ctx.user.id})",
                color=discord.Color.green(),
            )
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            await webhook_.send(
                embed=embed,
                avatar_url=self.bot.user.avatar.url,
                username="SharkBot-Global",
            )

    async def send_global_chat_join(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        tasks = []
        async for channel in channels:
            if channel["Channel"] == ctx.channel.id:
                continue

            try:
                target_channel = self.bot.get_channel(channel["Channel"])
                if target_channel:
                    await self.send_one_join_globalchat(channel["Webhook"], ctx)
                else:
                    continue
            except:
                continue

            await asyncio.sleep(1)

    async def send_one_leave_globalchat(self, webhook: str, ctx: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                title=f"{ctx.guild.name}が抜けちゃったよ・・",
                description=f"オーナーID: {ctx.guild.owner_id}\nコマンド実行者: {ctx.user.display_name}/({ctx.user.id})",
                color=discord.Color.red(),
            )
            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon.url)
            await webhook_.send(
                embed=embed,
                avatar_url=self.bot.user.avatar.url,
                username="SharkBot-Global",
            )

    async def send_global_chat_leave(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        tasks = []
        async for channel in channels:
            if channel["Channel"] == ctx.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                await self.send_one_leave_globalchat(channel["Webhook"], ctx)
            else:
                continue

            await asyncio.sleep(1)

    async def globalchat_join(self, ctx: discord.Interaction):
        web = await ctx.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.update_one(
            {"Guild": ctx.guild.id},
            {
                "$set": {
                    "Guild": ctx.guild.id,
                    "Channel": ctx.channel.id,
                    "GuildName": ctx.guild.name,
                    "Webhook": web.url,
                }
            },
            upsert=True,
        )
        return True

    async def globalchat_join_newch(self, channel: discord.TextChannel):
        web = await channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.update_one(
            {"Guild": channel.guild.id},
            {
                "$set": {
                    "Guild": channel.guild.id,
                    "Channel": channel.id,
                    "GuildName": channel.guild.name,
                    "Webhook": web.url,
                }
            },
            upsert=True,
        )
        return True

    async def globalchat_leave(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.delete_one({"Guild": ctx.guild.id})
        return True

    async def globalchat_leave_channel(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.delete_one({"Channel": ctx.channel.id})
        return True

    async def globalchat_check(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChat
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def globalchat_check_channel_for_interaction(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChat
        try:
            dbfind = await db.find_one({"Channel": interaction.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def globalchat_check_channel(self, message: discord.Message):
        db = self.bot.async_db["Main"].NewGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    def filter_global(self, message: discord.Message) -> bool:
        blocked_words = [
            "discord.com",
            "discord.gg",
            "x.gd",
            "shorturl.asia",
            "tiny.cc",
            "<sound:",
            "niga",
            "everyone",
            "here",
        ]
        return not any(word in message.content for word in blocked_words)

    async def badge_build(self, message: discord.Message):
        if message.author.id == 1335428061541437531:
            return "👑"

        try:
            if (
                self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
                in self.bot.get_guild(1343124570131009579)
                .get_member(message.author.id)
                .roles
            ):
                return "🛠️"
        except:
            return "😀"

        return "😀"

    async def send_one_globalchat(
        self, webhook: str, message: discord.Message, ref_msg: discord.Message = None
    ):
        if not self.filter_global(message):
            return

        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                description=message.content, color=await self.getColor(message.author)
            )
            em = await self.get_guild_emoji(message.guild)
            embed.set_footer(text=f"[{em}] {message.guild.name}/{message.guild.id}")

            bag = await self.badge_build(message)

            if message.author.avatar:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.avatar.url,
                )
            else:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.default_avatar.url,
                )
            if not message.stickers == []:
                try:
                    embed.set_image(url=message.stickers[0].url)
                except:
                    pass
            if not message.attachments == []:
                if message.stickers == []:
                    embed.add_field(
                        name="添付ファイル", value=message.attachments[0].url
                    )
                    for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                        if message.attachments[0].filename.endswith(kaku):
                            embed.set_image(url=message.attachments[0].url)
                            break

            if ref_msg:
                wh = ref_msg.webhook_id
                embed_ = ref_msg.embeds
                if wh:
                    try:
                        name = (
                            embed_[0]
                            .author.name.replace("[👑]", "")
                            .replace("[😀]", "")
                            .replace("[🛠️]", "")
                            .split("/")[0]
                        )
                        value = embed_[0].description
                    except:
                        name = ref_msg.author.name
                        value = ref_msg.content
                else:
                    name = ref_msg.author.name
                    value = ref_msg.content
                embed.add_field(name=name, value=value)
            try:
                await webhook_.send(
                    embed=embed,
                    avatar_url=self.bot.user.avatar.url,
                    username="SharkBot-GlobalChat",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except:
                return

    async def send_global_chat(
        self, message: discord.Message, ref_msg: discord.Message = None
    ):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                if not ref_msg:
                    await globalchat.send_one_global(
                        self.bot, channel["Webhook"], message
                    )
                    # await self.send_one_globalchat(channel["Webhook"], message)
                else:
                    await globalchat.send_one_global(
                        self.bot, channel["Webhook"], message, ref_msg
                    )
            else:
                continue

    async def send_one_globalchat_selectbot(self, webhook: str, bot: discord.User):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                description=f"{bot.display_name}",
                title="ランダムなBotが選択されました！",
                color=discord.Color.blue(),
            )
            embed.set_footer(text="ランダムなBot")
            embed.set_thumbnail(
                url=bot.avatar.url if bot.avatar else bot.default_avatar.url
            )

            embed.set_author(
                name=f"ランダムなBot/{bot.id}", icon_url=self.bot.user.avatar.url
            )
            await webhook_.send(
                embed=embed,
                avatar_url=self.bot.user.avatar.url,
                username="SharkBot-Global",
            )

    async def send_global_chat_room(
        self, room: str, message: discord.Message, ref_msg: discord.Message = None
    ):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        channels = db.find({"Name": room})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                if not ref_msg:
                    await globalchat.send_one_global(
                        self.bot, channel["Webhook"], message
                    )
                else:
                    await globalchat.send_one_global(
                        self.bot, channel["Webhook"], message, ref_msg
                    )
            else:
                continue

    async def send_global_chat_room_join(
        self, room: str, joind_channel: discord.TextChannel
    ):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        channels = db.find({"Name": room})

        async with aiohttp.ClientSession() as session:
            async for channel in channels:
                if channel["Channel"] == joind_channel.id:
                    continue

                target_channel = self.bot.get_channel(channel["Channel"])
                if target_channel:
                    webhook_object = discord.Webhook.from_url(
                        channel["Webhook"], session=session
                    )
                    embed = discord.Embed(
                        title=f"{joind_channel.guild.name}が参加したよ！よろしく！",
                        description=f"オーナーID: {joind_channel.guild.owner_id}",
                        color=discord.Color.green(),
                    )
                    if joind_channel.guild.icon:
                        embed.set_thumbnail(url=joind_channel.guild.icon.url)
                    await webhook_object.send(
                        embed=embed,
                        avatar_url=self.bot.user.avatar.url,
                        username="SharkBot-Global-Join",
                    )
                else:
                    continue

    async def globalchat_room_check(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        try:
            dbfind = await db.find_one({"Channel": ctx.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return dbfind.get("Name", None)
        except Exception:
            return False

    async def globalchat_room_join(self, ctx: discord.Interaction, roomname: str):
        web = await ctx.channel.create_webhook(name="SharkBot-GlobalRoom")
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        dbfind = await db.find_one({"Name": roomname}, {"_id": False})
        if not dbfind:
            db_setting = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
            await db_setting.update_one(
                {"Name": roomname},
                {"$set": {"Name": roomname, "Owner": ctx.user.id}},
                upsert=True,
            )
        await db.update_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id},
            {
                "$set": {
                    "Guild": ctx.guild.id,
                    "Channel": ctx.channel.id,
                    "GuildName": ctx.guild.name,
                    "Webhook": web.url,
                    "Name": roomname,
                }
            },
            upsert=True,
        )
        return True

    async def globalchat_room_leave(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalChatRoom
        await db.delete_one({"Guild": ctx.guild.id, "Channel": ctx.channel.id})
        return True

    globalchat = app_commands.Group(
        name="global", description="グローバルチャット系のコマンドです。"
    )

    # globalchat.add_command(GlobalThreadGroup())

    @globalchat.command(name="join", description="グローバルチャットに参加します。")
    @app_commands.checks.has_permissions(manage_channels=True, manage_webhooks=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_join(self, interaction: discord.Interaction, 部屋名: str = None):
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このチャンネルでは実行できません。",
                    description="テキストチャンネルでのみグローバルチャットに参加できます。",
                ),
            )

        await interaction.response.defer()
        if not 部屋名:
            check_room = await self.globalchat_room_check(interaction)
            if check_room:
                await self.globalchat_room_leave(interaction)
                return await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="グローバルチャットから脱退しました。"
                    )
                )
            check = await self.globalchat_check(interaction)
            if check:
                await self.globalchat_leave(interaction)
                return await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="グローバルチャットから脱退しました。"
                    )
                )

                await self.send_global_chat_leave(interaction)
            else:
                if interaction.guild.member_count < 20:
                    return await interaction.followup.send(
                        embed=make_embed.error_embed(
                            title="20人未満のサーバーは参加できません。"
                        )
                    )

                await self.globalchat_join(interaction)
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="グローバルチャットに参加しました。",
                        description="グローバルチャットのルール\n・荒らしをしない\n・宣伝をしない\n・r18やグロ関連のものを貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。",
                    )
                )

                await self.send_global_chat_join(interaction)

        else:
            check = await self.globalchat_room_check(interaction)
            if check:
                await self.globalchat_room_leave(interaction)
                return await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="グローバルチャットから脱退しました。"
                    )
                )
            else:
                db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
                dbfind = await db.find_one(
                    {"Name": 部屋名, "Owner": interaction.user.id}, {"_id": False}
                )
                if not dbfind:
                    await self.globalchat_room_join(interaction, 部屋名)
                    await interaction.followup.send(
                        embed=make_embed.success_embed(
                            title="グローバルチャットに参加しました。",
                            description=f"部屋名: {部屋名}",
                        )
                    )
                    return

                if dbfind.get("Password"):
                    await interaction.followup.send(
                        embed=make_embed.success_embed(
                            title="DMを確認してください。",
                            description="DMが送られてこない場合は、\n設定を確認してください。",
                        )
                    )
                    ch = await interaction.user.send(
                        embed=discord.Embed(
                            title="パスワードを入力",
                            description="グローバルルームのパスワードを入力してください。",
                            color=discord.Color.blue(),
                        )
                    )
                    try:
                        msg = await self.bot.wait_for(
                            "message",
                            check=lambda m: m.channel == ch.channel
                            and not m.author.bot,
                            timeout=30,
                        )
                    except asyncio.TimeoutError:
                        return await ch.edit(
                            embed=make_embed.error_embed(
                                title="操作がタイムアウトしました。"
                            )
                        )

                    if msg.content == dbfind.get("Password"):
                        await self.globalchat_room_join(interaction, 部屋名)
                        await interaction.edit_original_response(
                            embed=make_embed.success_embed(
                                title="グローバルチャットに参加しました。",
                                description=f"部屋名: {部屋名}",
                            )
                        )
                        await ch.edit(
                            embed=make_embed.success_embed(
                                title="サーバーを確認して下さい。"
                            )
                        )

                        await self.send_global_chat_room_join(
                            部屋名, interaction.channel
                        )
                        return
                    else:
                        await interaction.edit_original_response(
                            embed=make_embed.error_embed(
                                title="パスワードが違うみたいです。"
                            )
                        )
                        return await ch.edit(
                            embed=make_embed.error_embed(title="パスワードが違います。")
                        )
                else:
                    await self.globalchat_room_join(interaction, 部屋名)
                    await interaction.followup.send(
                        embed=make_embed.success_embed(
                            title="グローバルチャットに参加しました。",
                            description=f"部屋名: {部屋名}",
                        )
                    )
                    await self.send_global_chat_room_join(部屋名, interaction.channel)
                    return

    @globalchat.command(
        name="setting", description="グローバルルームの設定を確認します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_setting(self, interaction: discord.Interaction, 部屋名: str):
        db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": 部屋名, "Owner": interaction.user.id}, {"_id": False}
        )
        if not dbfind:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはルームのオーナーではありません！",
                    description="オーナーしか設定は変更できません。",
                ),
            )

        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(
                title="グローバルルームの設定一覧", color=discord.Color.green()
            )
            .add_field(name="オーナー", value=f"<@{dbfind.get('Owner')}>", inline=False)
            .add_field(
                name="パスワード",
                value=f"`{dbfind.get('Password') if dbfind.get('Password') else 'パスワードなし'}`",
                inline=False
            )
            .add_field(name="ルール", value=dbfind.get('Rule', 'ルール未制定'), inline=False),
        )

    @globalchat.command(name="moderate", description="グローバルルームでメンバーを管理します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="ミュート", value="mute"),
            app_commands.Choice(name="ミュート解除", value="unmute")
        ]
    )
    async def global_setting_moderate(
        self, interaction: discord.Interaction, 部屋名: str, 操作: app_commands.Choice[str], ユーザー: discord.User
    ):
        db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": 部屋名, "Owner": interaction.user.id}, {"_id": False}
        )
        if not dbfind:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはルームのオーナーではありません！",
                    description="オーナーしか設定は変更できません。",
                ),
            )

        if 操作.value == "mute":
            await db.update_one(
                {"Name": 部屋名, "Owner": interaction.user.id},
                {"$addToSet": {
                    "Mute": ユーザー.id
                }}
            )

            await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="ミュートしました。",
                    description=f"ユーザー: {ユーザー.mention}",
                ),
            )
        elif 操作.value == "unmute":
            await db.update_one(
                {"Name": 部屋名, "Owner": interaction.user.id},
                {"$pull": {
                    "Mute": ユーザー.id
                }}
            )

            await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="ミュートを解除しました。",
                    description=f"ユーザー: {ユーザー.mention}",
                ),
            )

    @globalchat.command(name="set-password", description="パスワードを設定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_setting_password(
        self, interaction: discord.Interaction, 部屋名: str, パスワード: str = None
    ):
        db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": 部屋名, "Owner": interaction.user.id}, {"_id": False}
        )
        if not dbfind:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはルームのオーナーではありません！",
                    description="オーナーしか設定は変更できません。",
                ),
            )

        await db.update_one(
            {"Name": 部屋名, "Owner": interaction.user.id},
            {"$set": {"Password": パスワード}},
        )

        await interaction.response.send_message(
            ephemeral=True,
            embed=make_embed.success_embed(
                title="パスワードを設定しました。",
                description=f"```{パスワード if パスワード else 'なし'}```",
            ),
        )

    @globalchat.command(name="rule", description="グローバルチャットのルールを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_setting_rule(
        self, interaction: discord.Interaction, 部屋名: str = None
    ):
        await interaction.response.defer()
        if not 部屋名:
            is_in_globalchat = await self.globalchat_check_channel_for_interaction(interaction)
            if is_in_globalchat:
                await interaction.followup.send(embed=make_embed.success_embed(title="グローバルチャットのルール", description="グローバルチャットのルール\n・荒らしをしない\n・宣伝をしない\n・r18やグロ関連のものを貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。"))
                return
            
            is_in_globalroom = await self.globalchat_room_check(interaction)
            if not is_in_globalroom:
                return await interaction.followup.send(embed=make_embed.error_embed(title="表示するルールがありません。", description="グローバルチャットの設定されている\nチャンネルで実行してください。"))

            db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
            dbfind = await db.find_one(
                {"Name": is_in_globalroom}, {"_id": False}
            )
            if not dbfind:
                return await interaction.followup.send(embed=make_embed.error_embed(title="表示するルールがありません。", description="グローバルチャットの設定が見つかりません、"))

            await interaction.followup.send(embed=make_embed.success_embed(title="グローバルチャットのルール", description=dbfind.get('Rule', 'まだルールが制定されていません。')))
            return

        db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": 部屋名}, {"_id": False}
        )
        if not dbfind:
            return await interaction.followup.send(embed=make_embed.error_embed(title="表示するルールがありません。", description="その部屋は存在しません。"))

        await interaction.followup.send(embed=make_embed.success_embed(title="グローバルチャットのルール", description=dbfind.get('Rule', 'まだルールが制定されていません。')))

    @globalchat.command(name="set-rule", description="グローバルチャットのルールを制定します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_setting_setrule(
        self, interaction: discord.Interaction, 部屋名: str
    ):
        db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": 部屋名, "Owner": interaction.user.id}, {"_id": False}
        )
        if not dbfind:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはルームのオーナーではありません！",
                    description="オーナーしか設定は変更できません。",
                ),
            )

        await interaction.response.send_modal(RuleModal(部屋名))

    async def globalshiritori_leave(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].GlobalShiritori
        await db.delete_one({"Channel": ctx.channel.id})
        return True

    @globalchat.command(name="leave", description="グローバルチャットから脱退します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_leave(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.globalchat_leave_channel(interaction)
        await self.globalchat_room_leave(interaction)
        await self.globalshiritori_leave(interaction)
        await interaction.followup.send(
            embed=make_embed.success_embed(title="グローバルチャットから脱退しました。")
        )

    async def set_emoji_guild(self, emoji: str, guild: discord.Guild):
        db = self.bot.async_db["Main"].NewGlobalChatEmoji
        await db.update_one(
            {"Guild": guild.id},
            {"$set": {"Guild": guild.id, "Emoji": emoji}},
            upsert=True,
        )

    @globalchat.command(
        name="emoji",
        description="グローバルチャットで使われるサーバー特有の絵文字を設定します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_emoji(self, interaction: discord.Interaction, 絵文字: str):
        await interaction.response.defer()
        if len(絵文字) > 3:
            return await interaction.followup.send("絵文字は3文字まででお願いします。")
        await self.set_emoji_guild(絵文字, interaction.guild)
        await interaction.followup.send(
            embed=discord.Embed(
                title="絵文字を変更しました。", color=discord.Color.green()
            ).add_field(name="絵文字", value=絵文字)
        )

    @globalchat.command(name="server", description="サーバー掲示板を確認します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_server(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="サーバー掲示板",
                description="以下のurlからアクセスできます。\nhttps://dashboard.sharkbot.xyz/servers",
            )
        )

    @globalchat.command(name="random", description="ボタンを押してランダムなサーバーに参加します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(1, 60, key=lambda i: i.user.id)
    async def global_random(self, interaction: discord.Interaction):
        view = RandomJoinView(self.bot)
        await interaction.response.send_message(
            embed=make_embed.success_embed(title="ランダムなサーバーに参加する", description="以下のボタンを押すと\nランダムな掲示板に登録されている\nサーバーの招待リンクを取得します。"),
            view=view,
            ephemeral=True
        )

    @global_random.error
    async def global_random_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = round(error.retry_after, 1)
            await interaction.response.send_message(
                embed=make_embed.error_embed(title="クールダウン中です。", description="不正使用防止のためです。\nよろしくお願いします。"),
                ephemeral=True
            )

    @globalchat.command(
        name="register", description="サーバー掲示板に登録・登録解除します。"
    )
    @app_commands.checks.has_permissions(manage_guild=True, create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_register(
        self, interaction: discord.Interaction, 説明: str = "説明なし"
    ):
        db = self.bot.async_db["Main"].Register

        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except:
            return
        if not dbfind is None:
            await db.delete_one(
                {
                    "Guild": interaction.guild.id,
                }
            )
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="サーバー掲示板から削除しました。", color=discord.Color.red()
                )
            )

        await interaction.response.defer()

        if interaction.guild.icon == None:
            return await interaction.reply(
                "サーバー掲示板に乗せるにはアイコンを設定する必要があります。"
            )

        inv = await interaction.channel.create_invite()
        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Name": interaction.guild.name,
                    "Description": 説明,
                    "Invite": inv.url,
                    "Icon": interaction.guild.icon.url,
                }
            },
            upsert=True,
        )
        embed = make_embed.success_embed(title="サーバーを掲載しました。")
        await interaction.followup.send(embed=embed)

    async def get_reg(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].Register
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
        except:
            return "https://discord.com", None
        if dbfind is None:
            return "https://discord.com", None
        return dbfind.get("Invite", "https://discord.com"), dbfind.get(
            "Description", "説明なし"
        )

    async def mention_get(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].BumpUpMention
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except:
            return "メンションするロールがありません。"
        if dbfind is None:
            return "メンションするロールがありません。"

        try:
            role = interaction.guild.get_role(dbfind.get("Role", None))
            return role.mention
        except:
            return "メンションするロールがありません。"

    @globalchat.command(name="up", description="サーバー掲示板でUpします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_up(self, interaction: discord.Interaction):
        if interaction.guild.icon == None:
            return await interaction.response.send_message(
                "Upをするにはアイコンを設定する必要があります。"
            )

        db = self.bot.async_db["Main"].Register
        inv, desc = await self.get_reg(interaction)
        if inv == "https://discord.com":
            embed = make_embed.error_embed(
                title="まだ登録されていません。",
                description=f"/global registerで登録してください。",
            )
            return await interaction.response.send_message(embed=embed)

        data = await db.find_one({"Guild": interaction.guild.id})
        now = time.time()
        cooldown_time = 2 * 60 * 60

        if data and "Up" in data:
            last_up = float(data["Up"])
            remaining = cooldown_time - (now - last_up)
            if remaining > 0:
                m, s = divmod(int(remaining), 60)
                embed = make_embed.error_embed(
                    title="まだUpできません。",
                    description=f"あと **{m}分{s}秒** 待ってから再度お試しください。",
                )
                return await interaction.response.send_message(embed=embed)

        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Name": interaction.guild.name,
                    "Description": desc,
                    "Invite": inv,
                    "Icon": interaction.guild.icon.url,
                    "Up": str(time.time()),
                }
            },
            upsert=True,
        )

        embed = make_embed.success_embed(
            title="サーバーをUpしました！", description="2時間後に再度Upできます。"
        )

        await interaction.response.send_message(embed=embed)

        db = self.bot.async_db["MainTwo"].SharkBotChannel
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            return

        await asyncio.sleep(1)
        try:
            await self.bot.alert_add(
                "sharkbot",
                interaction.channel_id,
                await self.mention_get(interaction),
                "SharkBotの掲示板をUpしてね！",
                "</global up:1408658655532023855> でUp。",
                7200,
            )

            await interaction.channel.send(
                embed=make_embed.success_embed(
                    title="Upを検知しました。", description="2時間後に通知します。"
                )
            )
        except:
            return

    @globalchat.command(
        name="sites", description="このサーバーを紹介するサイトを作成します。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_sites(self, interaction: discord.Interaction):
        if not interaction.guild.icon:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="アイコンが設定されていません。",
                    description="サイトを作成するには、\nサーバーアイコンを設定してください。",
                ),
            )
        await interaction.response.send_modal(SitesModal())

    @globalchat.command(
        name="private-join",
        description="パスワード付きグローバルチャットに参加します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_private_join(self, interaction: discord.Interaction):
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このチャンネルでは実行できません。",
                    description="テキストチャンネルでのみグローバルチャットに参加できます。",
                ),
            )

        class PrivateGlobalJoin(
            discord.ui.Modal, title="プライベートグローバルチャットに参加する"
        ):
            name = discord.ui.TextInput(
                label="名前を入力",
                required=True,
                style=discord.TextStyle.short,
                placeholder=f"{interaction.user.name}-global",
            )

            password = discord.ui.TextInput(
                label="グローバルチャットのパスワードを入力",
                required=True,
                style=discord.TextStyle.short,
                placeholder="password",
            )

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.defer(thinking=True)
                db = interaction.client.async_db["Main"].PrivateGlobal
                dbfind = await db.find_one(
                    {"Name": self.name.value, "Password": self.password.value},
                    {"_id": False},
                )
                if dbfind is not None:
                    web = await interaction.channel.create_webhook(
                        name="SharkBot-PrivateGlobal"
                    )
                    await db.update_one(
                        {"Guild": interaction.guild.id, "Name": self.name.value},
                        {
                            "$set": {
                                "Guild": interaction.guild.id,
                                "Name": self.name.value,
                                "Password": self.password.value,
                                "Owner": dbfind.get("Owner"),
                                "Channel": interaction.channel.id,
                                "Webhook": web.url,
                            }
                        },
                        upsert=True,
                    )
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="プライベートグローバルチャットに参加しました。",
                            color=discord.Color.green(),
                        )
                    )
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title=f"その名前 `{self.name.value}` のグローバルチャットはありません！",
                            description="またはパスワードが違います。",
                            color=discord.Color.red(),
                        )
                    )

        await interaction.response.send_modal(PrivateGlobalJoin())

    @globalchat.command(
        name="private-leave",
        description="パスワード付きグローバルチャットから脱退します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_private_leave(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].PrivateGlobal
        await db.delete_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="グローバルチャットから脱退しました。", color=discord.Color.red()
            )
        )
        
    async def super_join_global_chat(self, interaction: discord.Interaction):
        wh = await interaction.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "GuildName": interaction.guild.name,
                    "Webhook": wh.url,
                }
            },
            upsert=True,
        )

    async def super_leave_global_chat(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        await db.delete_one({"Guild": interaction.guild.id})
        return True

    async def super_globalchat_check(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def super_globalchat_check_message(self, message: discord.Message):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    """
        @global_join.command(name="sgc", description="スーパーグローバルチャットに参加・脱退します。")
        @commands.cooldown(2, 10, commands.BucketType.guild)
        @commands.has_permissions(manage_channels=True)
        async def sgc_join_leave(self, ctx: commands.Context):
            await ctx.defer()
            if ctx.guild.member_count < 20:
                return await ctx.reply(embed=discord.Embed(title="20人未満のサーバーは参加できません。", color=discord.Color.red()))
            check = await self.super_globalchat_check(ctx)
            if check:
                await self.super_leave_global_chat(ctx)
                return await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットから脱退しました。", color=discord.Color.green()))
            else:
                await self.super_join_global_chat(ctx)
                await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットに参加しました。", color=discord.Color.green()))
    """

    @globalchat.command(
        name="sgc", description="スーパーグローバルチャットに参加します。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_sgc(self, interaction: discord.Interaction):
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このチャンネルでは実行できません。",
                    description="テキストチャンネルでのみグローバルチャットに参加できます。",
                ),
            )

        await interaction.response.defer()
        if interaction.guild.member_count < 20:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="20人未満のサーバーは参加できません。",
                    color=discord.Color.red(),
                )
            )
        check = await self.super_globalchat_check(interaction)
        if check:
            await self.super_leave_global_chat(interaction)
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="スーパーグローバルチャットから脱退しました。",
                    color=discord.Color.green(),
                )
            )
        else:
            await self.super_join_global_chat(interaction)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="スーパーグローバルチャットに参加しました。",
                    color=discord.Color.green(),
                )
            )

    @globalchat.command(
        name="sgc-info",
        description="スーパーグローバルチャットに参加しているBot一覧を見ます。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_sgc_info(self, interaction: discord.Interaction):
        await interaction.response.defer()

        STATUS_EMOJIS = {
            discord.Status.online: "<:online:1407922300535181423>",
            discord.Status.idle: "<:idle:1407922295711727729>",
            discord.Status.dnd: "<:dnd:1407922294130741348>",
            discord.Status.offline: "<:offline:1407922298563854496>",
        }

        res = ""
        rl = self.bot.get_guild(706905953320304772).get_role(773868241713627167)
        for m in self.bot.get_guild(706905953320304772).members:
            if not m.bot:
                continue
            if m.id == 1343156909242454038:
                continue
            if rl in m.roles:
                res += f"{STATUS_EMOJIS.get(m.status, '❔')} {'❌**停止中**' if m.status.__str__() == 'offline' else '✅**稼働中**'} **{m.display_name}**\n"
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="スーパーグローバルチャットの情報", description=res
            ).set_footer(
                text="Discord上に表示されたステータスで判別しているため、\n一部が正確ではない可能性もあります。"
            )
        )

    @globalchat.command(
        name="shiritori", description="グローバルしりとりに参加します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_shiritori(self, interaction: discord.Interaction):
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このチャンネルでは実行できません。",
                    description="テキストチャンネルでのみグローバルチャットに参加できます。",
                ),
            )

        await interaction.response.defer()
        if interaction.guild.member_count < 20:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="20人未満のサーバーは参加できません。"
                )
            )
        wh = await interaction.channel.create_webhook(name="SharkBot-しりとり")
        db = self.bot.async_db["Main"].GlobalShiritori
        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "GuildName": interaction.guild.name,
                    "Webhook": wh.url,
                }
            },
            upsert=True,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="グローバルしりとりに参加しました。",
                description="脱退は、/global leaveを使ってください。",
                color=discord.Color.green(),
            )
        )

    async def globalads_check(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalAds
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def globalads_join(self, interaction: discord.Interaction):
        web = await interaction.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalAds
        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "GuildName": interaction.guild.name,
                    "Webhook": web.url,
                }
            },
            upsert=True,
        )
        return True

    async def globalads_leave(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].NewGlobalAds
        await db.delete_one({"Guild": interaction.guild.id})
        return True

    async def globalads_check_channel(self, message: discord.Message):
        db = self.bot.async_db["Main"].NewGlobalAds
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def send_one_ads_message(
        self, webhook: str, interaction: discord.Interaction, text: str
    ):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(description=text, color=discord.Color.blue())
            em = await self.get_guild_emoji(interaction.guild)
            embed.set_footer(
                text=f"[{em}] {interaction.guild.name}/{interaction.guild.id}"
            )

            bag = await self.badge_build(interaction)

            if interaction.user.avatar:
                embed.set_author(
                    name=f"[{bag}] {interaction.user.name}/{interaction.user.id}",
                    icon_url=interaction.user.avatar.url,
                )
            else:
                embed.set_author(
                    name=f"[{bag}] {interaction.user.name}/{interaction.user.id}",
                    icon_url=interaction.user.default_avatar.url,
                )
            try:
                await webhook_.send(
                    embed=embed,
                    avatar_url=self.bot.user.avatar.url,
                    username="SharkBot-Global",
                )
            except:
                return

    async def send_one_ads(self, webhook: str, message: discord.Message):
        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                description=message.content, color=await self.getColor(message.author)
            )
            em = await self.get_guild_emoji(message.guild)
            embed.set_footer(text=f"[{em}] {message.guild.name}/{message.guild.id}")

            bag = await self.badge_build(message)

            if message.author.avatar:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.avatar.url,
                )
            else:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.default_avatar.url,
                )
            if not message.attachments == []:
                embed.add_field(name="添付ファイル", value=message.attachments[0].url)
            try:
                await webhook_.send(
                    embed=embed,
                    avatar_url=self.bot.user.avatar.url,
                    username="SharkBot-Global",
                )
            except:
                return

    async def send_global_ads(self, message: discord.Message):
        db = self.bot.async_db["Main"].NewGlobalAds
        channels = db.find({})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                await globalchat.send_one_global(
                    self.bot, channel["Webhook"], message, is_ad=True
                )
            else:
                continue

    @globalchat.command(name="ads", description="グローバル宣伝に参加します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_ads(self, interaction: discord.Interaction):
        if interaction.channel.type != discord.ChannelType.text:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このチャンネルでは実行できません。",
                    description="テキストチャンネルでのみグローバルチャットに参加できます。",
                ),
            )

        await interaction.response.defer()
        if interaction.guild.member_count < 20:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="20人未満のサーバーは参加できません。"
                )
            )
        check = await self.globalads_check(interaction)
        if check:
            await self.globalads_leave(interaction)
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="グローバル宣伝から脱退しました。",
                    color=discord.Color.green(),
                )
            )
        else:
            await self.globalads_join(interaction)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="グローバル宣伝に参加しました。",
                    description="グローバル宣伝のルール\n・荒らし系を貼らない\n・r18やグロ関連のものを貼らない\n・sh0p系を貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。",
                    color=discord.Color.green(),
                )
            )

    async def add_sharkpoint(self, interaction: discord.Interaction, coin: int):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        user_data = await db.find_one({"_id": interaction.user.id})
        if user_data:
            await db.update_one({"_id": interaction.user.id}, {"$inc": {"count": coin}})
            return True
        else:
            await db.insert_one({"_id": interaction.user.id, "count": coin})
            return True

    @commands.Cog.listener("on_message")
    async def on_message_global_alert(self, message: discord.Message):
        if not message.channel.id == 1362296899259863112:
            return
        await self.send_global_chat(message)

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_ads(self, message: discord.Message):
        if message.author.bot:
            return

        check = await self.globalads_check_channel(message)

        if not check:
            return

        db = self.bot.async_db["Main"].NewGlobalAds
        channels = await db.find({}).to_list(length=None)

        await globalchat.delete_one_global(self.bot, channels, message.id)

    @commands.Cog.listener("on_message")
    async def on_message_ads(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalads_check_channel(message)

        if not check:
            return

        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        await self.send_global_ads(message)

        try:
            await message.remove_reaction("🔄", self.bot.user)
            await message.add_reaction("✅")
            await asyncio.sleep(3)
            await message.remove_reaction("✅", message.guild.me)
        except:
            pass

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_globalroom(self, message: discord.Message):
        if message.author.bot:
            return

        check = await self.globalchat_room_check(message)

        if not check:
            return

        db = self.bot.async_db["Main"].NewGlobalChatRoom
        channels = await db.find({"Name": check}).to_list(length=None)

        await globalchat.delete_one_global(self.bot, channels, message.id)

    async def is_user_muted(self, room_name: str, user: discord.User):
        db = self.bot.async_db["MainTwo"].GlobalChatRoomSetting
        dbfind = await db.find_one(
            {"Name": room_name}, {"_id": False}
        )
        if not dbfind:
            return False
        
        muted_list = dbfind.get('Mute', [])
        if user.id in muted_list:
            return True
        
        return False

    @commands.Cog.listener("on_message")
    async def on_message_globalroom(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalchat_room_check(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.author.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return
        user_last_message_timegc[message.author.id] = current_time

        is_muted = await self.is_user_muted(check, message.author)
        if is_muted:
            await message.add_reaction("❌")
            return

        await message.add_reaction("🔄")

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat_room(check, message, rmsg)
        else:
            await self.send_global_chat_room(check, message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")
        await asyncio.sleep(3)
        await message.remove_reaction("✅", message.guild.me)

    async def globalchat_users_add(self, user: discord.User, message: discord.Message):
        db = self.bot.async_db["Main"].GlobalChatRuleAgreeUser

        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
            if dbfind is None:
                await message.reply(
                    embed=discord.Embed(
                        title="これがグローバルチャットのルールです。",
                        description="""
荒らしをしない
宣伝をしない (宣伝の場合は宣伝グローバルへ)
r18やグロ関連のものを貼らない
違法なリンクを貼らない・違法な会話をしない
喧嘩などをしない。
その他運営の禁止したものを貼らない

これらルールに違反した場合は
グローバルチャットが利用できなくなります。

同意できる場合は「同意」ボタンを押してください。
""",
                        color=discord.Color.green(),
                    ),
                    view=discord.ui.View().add_item(
                        discord.ui.Button(
                            label="同意",
                            style=discord.ButtonStyle.green,
                            custom_id="globalchat_agree+",
                        )
                    ),
                )
                return True
        except Exception:
            return False

        await db.update_one(
            {"User": user.id},
            {"$set": {"User": user.id, "UserName": user.name}},
            upsert=True,
        )
        return False

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_global(self, message: discord.Message):
        if message.author.bot:
            return

        check = await self.globalchat_check_channel(message)

        if not check:
            return

        db = self.bot.async_db["Main"].NewGlobalChat
        channels = await db.find({}).to_list(length=None)

        await globalchat.delete_one_global(self.bot, channels, message.id)

    @commands.Cog.listener("on_message")
    async def on_message_global(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalchat_check_channel(message)

        if not check:
            return

        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.author.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.author.id] = current_time

        g_u = await self.globalchat_users_add(message.author, message)
        if g_u:
            return

        await message.add_reaction("🔄")

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat(message, rmsg)
        else:
            await self.send_global_chat(message)

        try:
            await message.remove_reaction("🔄", self.bot.user)
            await message.add_reaction("✅")
            await asyncio.sleep(3)
            await message.remove_reaction("✅", message.guild.me)
        except:
            pass

    async def globalshiritori_check_channel(self, message: discord.Message):
        db = self.bot.async_db["Main"].GlobalShiritori
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def send_one_globalshiritori(self, webhook: str, message: discord.Message):
        if not self.filter_global(message):
            return

        async with aiohttp.ClientSession() as session:
            webhook_ = Webhook.from_url(webhook, session=session)
            embed = discord.Embed(
                description=message.content, color=await self.getColor(message.author)
            )
            em = await self.get_guild_emoji(message.guild)
            embed.set_footer(text=f"[{em}] {message.guild.name}/{message.guild.id}")

            bag = await self.badge_build(message)

            if message.author.avatar:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.avatar.url,
                )
            else:
                embed.set_author(
                    name=f"[{bag}] {message.author.name}/{message.author.id}",
                    icon_url=message.author.default_avatar.url,
                )
            if not message.attachments == []:
                embed.add_field(name="添付ファイル", value=message.attachments[0].url)

            try:
                await webhook_.send(
                    embed=embed,
                    avatar_url=self.bot.user.avatar.url,
                    username="SharkBot-Global",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except:
                return

    async def send_global_shiritori(self, message: discord.Message):
        db = self.bot.async_db["Main"].GlobalShiritori
        channels = db.find({})

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                await self.send_one_globalshiritori(channel["Webhook"], message)
            else:
                continue

    @commands.Cog.listener("on_message")
    async def on_message_global_shiritori(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalshiritori_check_channel(message)

        if not check:
            return

        block = await is_ban.is_blockd_by_message(message)

        if not block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        await self.send_global_shiritori(message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")
        await asyncio.sleep(3)
        await message.remove_reaction("✅", message.guild.me)

    async def demo_super_globalchat_check(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        try:
            dbfind = await db.find_one({"Guild": interaction.guild.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def demo_super_globalchat_check_message(self, message: discord.Message):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
            if dbfind is None:
                return False
            return True
        except Exception:
            return False

    async def debug_super_join_global_chat(self, interaction: discord.Interaction):
        wh = await interaction.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        await db.update_one(
            {"Guild": interaction.guild.id},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Channel": interaction.channel.id,
                    "GuildName": interaction.guild.name,
                    "Webhook": wh.url,
                }
            },
            upsert=True,
        )

    async def debug_super_leave_global_chat(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        await db.delete_one({"Guild": interaction.guild.id})
        return True

    @globalchat.command(
        name="dsgc", description="デモスーパーグローバルチャットに参加・脱退します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_dsgc(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.member_count < 20:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="20人未満のサーバーは参加できません。",
                    color=discord.Color.red(),
                )
            )
        check = await self.demo_super_globalchat_check(interaction)
        if check:
            await self.debug_super_leave_global_chat(interaction)
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="デバッグ版スーパーグローバルチャットから脱退しました。",
                    color=discord.Color.green(),
                )
            )
        else:
            await self.debug_super_join_global_chat(interaction)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="デバッグ版スーパーグローバルチャットに参加しました。",
                    color=discord.Color.green(),
                )
            )

    @globalchat.command(
        name="color", description="グローバルチャットでの自分の色を変更します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        色=[
            app_commands.Choice(name="赤", value="red"),
            app_commands.Choice(name="緑", value="green"),
            app_commands.Choice(name="青", value="blue"),
            app_commands.Choice(name="ランダム", value="random"),
        ]
    )
    async def global_color(
        self, interaction: discord.Interaction, 色: app_commands.Choice[str]
    ):
        db = self.bot.async_db["MainTwo"].GlobalColor
        await db.update_one(
            {"User": interaction.user.id},
            {"$set": {"User": interaction.user.id, "Color": 色.value}},
            upsert=True,
        )
        await interaction.response.send_message(
            embed=make_embed.success_embed(
                title="グローバルチャットでの色を変更しました。",
                description="通常グローバルでのみ適用されます。",
            )
            .add_field(name="色", value=色.name, inline=False)
            .set_footer(text=色.value)
        )


async def setup(bot):
    await bot.add_cog(GlobalCog(bot))
