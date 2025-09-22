from discord.ext import commands
import discord
import time
import asyncio
import json
from discord import Webhook
from discord import app_commands
import aiohttp
from google import genai
import urllib.parse

from models import command_disable
import re

from consts import settings

COOLDOWN_TIMEGC = 5
user_last_message_timegc = {}
user_last_message_time_ad = {}

user_last_message_time_mute = {}

cooldown_transfer = {}
cooldown_up = {}

invite_only_check = re.compile(
    r"^(https?://)?(www\.)?(discord\.gg/|discord\.com/invite/)[a-zA-Z0-9]+$"
)


class GlobalCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> GlobalCog")

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

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                await self.send_one_join_globalchat(channel["Webhook"], ctx)
            else:
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
        await db.replace_one(
            {"Guild": ctx.guild.id},
            {
                "Guild": ctx.guild.id,
                "Channel": ctx.channel.id,
                "GuildName": ctx.guild.name,
                "Webhook": web.url,
            },
            upsert=True,
        )
        return True

    async def globalchat_join_newch(self, channel: discord.TextChannel):
        web = await channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].NewGlobalChat
        await db.replace_one(
            {"Guild": channel.guild.id},
            {
                "Guild": channel.guild.id,
                "Channel": channel.id,
                "GuildName": channel.guild.name,
                "Webhook": web.url,
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
                description=message.content, color=discord.Color.blue()
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
                    username="SharkBot-Global",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            except:
                return

    async def send_global_chat(
        self, message: discord.Message, ref_msg: discord.Message = None
    ):
        db = self.bot.async_db["Main"].NewGlobalChat
        channels = db.find({})

        count = 0

        async for channel in channels:
            if channel["Channel"] == message.channel.id:
                continue

            target_channel = self.bot.get_channel(channel["Channel"])
            if target_channel:
                if not ref_msg:
                    await self.send_one_globalchat(channel["Webhook"], message)
                else:
                    await self.send_one_globalchat(channel["Webhook"], message, ref_msg)
            else:
                continue

            count += 1
            if count > 3:
                await asyncio.sleep(1)
                count = 0

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
                    await self.send_one_globalchat(channel["Webhook"], message)
                else:
                    await self.send_one_globalchat(channel["Webhook"], message, ref_msg)
            else:
                continue

            await asyncio.sleep(1)

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
        await db.replace_one(
            {"Guild": ctx.guild.id, "Channel": ctx.channel.id},
            {
                "Guild": ctx.guild.id,
                "Channel": ctx.channel.id,
                "GuildName": ctx.guild.name,
                "Webhook": web.url,
                "Name": roomname,
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

    @globalchat.command(name="join", description="グローバルチャットに参加します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_join(self, interaction: discord.Interaction, 部屋名: str = None):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        if not 部屋名:
            if interaction.guild.member_count < 20:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="20人未満のサーバーは参加できません。",
                        color=discord.Color.red(),
                    )
                )
            check_room = await self.globalchat_room_check(interaction)
            if check_room:
                await self.globalchat_room_leave(interaction)
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="グローバルチャットから脱退しました。",
                        color=discord.Color.green(),
                    )
                )
            check = await self.globalchat_check(interaction)
            if check:
                await self.globalchat_leave(interaction)
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="グローバルチャットから脱退しました。",
                        color=discord.Color.green(),
                    )
                )

                await self.send_global_chat_leave(interaction)
            else:
                await self.globalchat_join(interaction)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="グローバルチャットに参加しました。",
                        description="グローバルチャットのルール\n・荒らしをしない\n・宣伝をしない\n・r18やグロ関連のものを貼らない\n・その他運営の禁止したものを貼らない\n以上です。守れない場合は、処罰することもあります。\nご了承ください。",
                        color=discord.Color.green(),
                    )
                )

                await self.send_global_chat_join(interaction)

        else:
            check = await self.globalchat_room_check(interaction)
            if check:
                await self.globalchat_room_leave(interaction)
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title="グローバルチャットから脱退しました。",
                        color=discord.Color.green(),
                    )
                )
            else:
                await self.globalchat_room_join(interaction, 部屋名)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="グローバルチャットに参加しました。",
                        color=discord.Color.green(),
                    )
                )

    async def globalshiritori_leave(self, ctx: discord.Interaction):
        db = self.bot.async_db["Main"].GlobalShiritori
        await db.delete_one({"Channel": ctx.channel.id})
        return True

    @globalchat.command(name="leave", description="グローバルチャットから脱退します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_leave(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        await self.globalchat_leave_channel(interaction)
        await self.globalchat_room_leave(interaction)
        await self.globalshiritori_leave(interaction)
        await interaction.followup.send(
            embed=discord.Embed(
                title="グローバルチャットから脱退しました。",
                color=discord.Color.green(),
            )
        )

    async def set_emoji_guild(self, emoji: str, guild: discord.Guild):
        db = self.bot.async_db["Main"].NewGlobalChatEmoji
        await db.replace_one(
            {"Guild": guild.id}, {"Guild": guild.id, "Emoji": emoji}, upsert=True
        )

    @globalchat.command(
        name="emoji",
        description="グローバルチャットで使われるサーバー特有の絵文字を設定します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_emoji(self, interaction: discord.Interaction, 絵文字: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

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
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.send_message(
            embed=discord.Embed(
                title="サーバー掲示板",
                description="以下のurlからアクセスできます。\nhttps://www.sharkbot.xyz/server",
                color=discord.Color.blue(),
            )
        )

    @globalchat.command(name="register", description="サーバー掲示板に登録します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_register(self, interaction: discord.Interaction, 説明: str):
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
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {
                "Guild": interaction.guild.id,
                "Name": interaction.guild.name,
                "Description": 説明,
                "Invite": inv.url,
                "Icon": interaction.guild.icon.url,
            },
            upsert=True,
        )
        await interaction.followup.send(
            embed=discord.Embed(
                title="サーバーを掲載しました。", color=discord.Color.green()
            )
        )

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

    @globalchat.command(name="up", description="サーバー掲示板でUpします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_up(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if interaction.guild.icon == None:
            return await interaction.response.send_message(
                "Upをするにはアイコンを設定する必要があります。"
            )

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(interaction.guild.id, 0)
        if current_time - last_message_time < 7200:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(
                    title="まだUpできません。",
                    color=discord.Color.red(),
                    description="2時間待ってください。",
                ),
            )
        user_last_message_timegc[interaction.guild.id] = current_time

        db = self.bot.async_db["Main"].Register
        inv, desc = await self.get_reg(interaction)
        if inv == "https://discord.com":
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="まだ登録されていません。",
                    color=discord.Color.red(),
                    description="/global registerで登録してください。",
                )
            )
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {
                "Guild": interaction.guild.id,
                "Name": interaction.guild.name,
                "Description": desc,
                "Invite": inv,
                "Icon": interaction.guild.icon.url,
                "Up": str(time.time()),
            },
            upsert=True,
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="サーバーをUpしました！",
                description="2時間後に再度Upできます。",
                color=discord.Color.green(),
            )
        )

    @globalchat.command(
        name="private-create",
        description="プライベートグローバルチャットを作成します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_private(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        class PrivateGlobalCreate(
            discord.ui.Modal, title="プライベートグローバルチャットを作成する"
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
                dbfind = await db.find_one({"Name": self.name.value}, {"_id": False})
                if dbfind is None:
                    web = await interaction.channel.create_webhook(
                        name="SharkBot-PrivateGlobal"
                    )
                    await db.replace_one(
                        {"Guild": interaction.guild.id, "Name": self.name.value},
                        {
                            "Guild": interaction.guild.id,
                            "Name": self.name.value,
                            "Password": self.password.value,
                            "Owner": interaction.user.id,
                            "Channel": interaction.channel.id,
                            "Webhook": web.url,
                        },
                        upsert=True,
                    )
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="プライベートグローバルチャットを作成しました。",
                            color=discord.Color.green(),
                        )
                    )
                else:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title=f"その名前 `{self.name.value}` は既に使われています！",
                            description="別の名前を使用してください。",
                            color=discord.Color.red(),
                        )
                    )

        await interaction.response.send_modal(PrivateGlobalCreate())

    @globalchat.command(
        name="private-join",
        description="プライベートなグローバルチャットに参加します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_private_join(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
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
                    await db.replace_one(
                        {"Guild": interaction.guild.id, "Name": self.name.value},
                        {
                            "Guild": interaction.guild.id,
                            "Name": self.name.value,
                            "Password": self.password.value,
                            "Owner": dbfind.get("Owner"),
                            "Channel": interaction.channel.id,
                            "Webhook": web.url,
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
        description="プライベートなグローバルチャットから脱退します。",
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_private_leave(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        db = self.bot.async_db["Main"].PrivateGlobal
        await db.delete_one(
            {"Guild": interaction.guild.id, "Channel": interaction.channel.id}
        )
        await interaction.response.send_message(
            embed=discord.Embed(
                title="グローバルチャットから脱退しました。", color=discord.Color.red()
            )
        )

    @globalchat.command(
        name="pass-check",
        description="プライベートグローバルチャットのパスワードをチェックします。",
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def global_private_leave(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        db = self.bot.async_db["Main"].PrivateGlobal
        dbfind = await db.find_one(
            {"Channel": interaction.channel.id, "Owner": interaction.user.id},
            {"_id": False},
        )
        if dbfind is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このチャンネルはプライベートグローバルチャットではありません。",
                    description="または、オーナーではありません。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        else:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このグローバルチャットのパスワード",
                    description=f"パスワード: `{dbfind.get('Password', 'エラー')}`",
                    color=discord.Color.blue(),
                ),
                ephemeral=True,
            )

    async def sgc_make_json(self, message: discord.Message):
        dic = {}

        dic.update({"type": "message"})
        dic.update({"userId": str(message.author.id)})
        dic.update({"userName": message.author.name})
        dic.update({"x-userGlobal_name": message.author.global_name})
        dic.update({"userDiscriminator": message.author.discriminator})
        if hasattr(message.author.avatar, "key"):
            dic.update({"userAvatar": message.author.avatar.key})
        else:
            dic.update({"userAvatar": None})
        dic.update({"isBot": message.author.bot})
        dic.update({"guildId": str(message.guild.id)})
        dic.update({"guildName": message.guild.name})
        if hasattr(message.guild.icon, "key"):
            dic.update({"guildIcon": message.guild.icon.key})
        else:
            dic.update({"guildIcon": None})
        dic.update({"channelId": str(message.channel.id)})
        dic.update({"channelName": message.channel.name})
        dic.update({"messageId": str(message.id)})
        dic.update({"content": message.content.replace("@", "＠")})

        if message.attachments != []:
            arr = []
            for attachment in message.attachments:
                arr.append(attachment.url)
            dic.update({"attachmentsUrl": arr})

        if message.author.primary_guild.tag:
            dic.update({"x-userTag": message.author.primary_guild.tag})

            dic.update({"x-userPrimaryGuild": {
                'tag': message.author.primary_guild.tag
            }})

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

        jsondata = json.dumps(dic, ensure_ascii=False)

        return jsondata

    async def send_super_global_chat_room(
        self, message: discord.Message, ref_msg: discord.Message = None
    ):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        channels = db.find()

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)

        count = 0

        async with aiohttp.ClientSession() as session:
            async for channel in channels:
                if channel["Channel"] == message.channel.id:
                    continue

                target_channel = self.bot.get_channel(channel["Channel"])

                if target_channel:
                    embed = discord.Embed(
                        description=message.content, color=discord.Color.blue()
                    )
                    embed.set_footer(text=f"mID:{message.id} / SharkBot")
                    bag = await self.badge_build(message)
                    if message.author.avatar:
                        embed.set_author(
                            name=f"[{bag}] {message.author.name}/{message.author.id} [{message.author.primary_guild.tag if message.author.primary_guild.tag else 'なし'}]",
                            icon_url=message.author.avatar.url,
                        )
                    else:
                        embed.set_author(
                            name=f"[{bag}] {message.author.name}/{message.author.id} [{message.author.primary_guild.tag if message.author.primary_guild.tag else 'なし'}]",
                            icon_url=message.author.default_avatar.url,
                        )
                    embed_2 = discord.Embed(color=discord.Color.red()).set_footer(
                        text=f"{message.guild.name} | {message.guild.id}",
                        icon_url=message.guild.icon.url if message.guild.icon else None,
                    )
                    if not message.attachments == []:
                        for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                            if kaku in message.attachments[0].filename:
                                embed.set_image(url=message.attachments[0].url)
                                break
                        embed.add_field(
                            name="添付ファイル",
                            value=message.attachments[0].url,
                            inline=False,
                        )
                    if message.reference:
                        if rmsg.application_id != self.bot.user.id:
                            embed.add_field(
                                name=f"返信 ({rmsg.author.name}#{rmsg.author.discriminator})",
                                inline=False,
                                value=f"{rmsg.content}",
                            )
                        elif rmsg.application_id == self.bot.user.id:
                            embed.add_field(
                                name=f"返信 ({rmsg.embeds[0].author.name.split(']')[1].split('/')[0].replace(' ', '')})",
                                inline=False,
                                value=f"{rmsg.embeds[0].description}",
                            )
                    try:
                        webhook_ = Webhook.from_url(
                            channel.get("Webhook", None), session=session
                        )
                        await webhook_.send(
                            embeds=[embed, embed_2],
                            username="SharkBot-SGC",
                            avatar_url=self.bot.user.avatar.url,
                        )
                    except:
                        continue
                    count += 1
                    if count > 3:
                        await asyncio.sleep(1)
                        count = 0

    async def super_join_global_chat(self, interaction: discord.Interaction):
        wh = await interaction.channel.create_webhook(name="SharkBot-Global")
        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {
                "Guild": interaction.guild.id,
                "Channel": interaction.channel.id,
                "GuildName": interaction.guild.name,
                "Webhook": wh.url,
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

    @commands.Cog.listener("on_message")
    async def on_message_superglobal_getjson(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if not message.channel.id == 707158257818664991:
            return

        try:
            dic = json.loads(message.content)
        except json.decoder.JSONDecodeError:
            return

        if "type" in dic and dic["type"] != "message":
            return

        db = self.bot.async_db["Main"].AlpheSuperGlobalChat
        async with aiohttp.ClientSession() as session:
            async for ch in db.find():
                target_channel = self.bot.get_channel(ch["Channel"])
                if target_channel:
                    embed = discord.Embed(
                        description=dic["content"], color=discord.Color.blue()
                    )
                    embed.set_footer(
                        text=f"mID:{dic['messageId']} / {message.author.display_name}"
                    )
                    bag = await self.badge_build(message)
                    if dic["userAvatar"]:
                        embed.set_author(
                            name=f"[{bag}] {dic['userName']}/{dic['userId']} [{dic.get('x-userPrimaryGuild', {}).get('tag', None) if dic.get('x-userPrimaryGuild', {}).get('tag', None) != None else 'なし'}]",
                            icon_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(
                                dic["userId"], dic["userAvatar"]
                            ),
                        )
                    else:
                        embed.set_author(
                            name=f"[{bag}] {dic['userName']}/{dic['userId']} [{dic.get('x-userPrimaryGuild', {}).get('tag', None) if dic.get('x-userPrimaryGuild', {}).get('tag', None) != None else 'なし'}]",
                            icon_url=message.author.default_avatar.url,
                        )
                    if not dic.get("attachmentsUrl") == []:
                        try:
                            embed.add_field(
                                name="添付ファイル", value=dic["attachmentsUrl"][0]
                            )
                            for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                                if kaku in dic["attachmentsUrl"][0]:
                                    embed.set_image(
                                        url=urllib.parse.unquote(
                                            dic["attachmentsUrl"][0]
                                        )
                                    )
                                    break
                        except:
                            pass
                    if message.reference:
                        rmsg = await message.channel.fetch_message(
                            message.reference.message_id
                        )
                        embed.add_field(
                            name=f"返信 ({rmsg.author.name} - {rmsg.author.id})",
                            inline=False,
                            value=f"{rmsg.content}",
                        )
                    else:
                        try:
                            reference_mid = dic["reference"]  # 返信元メッセージID

                            reference_message_content = (
                                ""  # 返信元メッセージ用変数を初期化
                            )
                            reference_message_author = (
                                ""  # 返信元ユーザータグ用変数を初期化
                            )
                            past_dic = (
                                None  # 返信元メッセージの辞書型リスト用変数を初期化
                            )
                            async for past_message in message.channel.history(
                                limit=1000
                            ):  # JSONチャンネルの過去ログ1000件をループ
                                try:  # JSONのエラーを監視
                                    past_dic = json.loads(
                                        past_message.content
                                    )  # 過去ログのJSONを辞書型リストに変換
                                except json.decoder.JSONDecodeError:  # JSON読み込みエラー→そもそもJSONでは無い可能性があるのでスルー
                                    continue
                                if (
                                    "type" in past_dic and past_dic["type"] != "message"
                                ):  # メッセージでは無い時はスルー
                                    continue

                                if (
                                    "messageId" not in past_dic
                                ):  # キーにメッセージIDが存在しない時はスルー
                                    continue

                                if (
                                    str(past_dic["messageId"]) == str(reference_mid)
                                ):  # 過去ログのメッセージIDが返信元メッセージIDと一致したとき
                                    reference_message_author = "{}#{}".format(
                                        past_dic["userName"],
                                        past_dic["userDiscriminator"],
                                    )  # ユーザータグを取得
                                    reference_message_content = past_dic[
                                        "content"
                                    ]  # メッセージ内容を取得
                                    embed.add_field(
                                        name=f"返信 ({reference_message_author})",
                                        inline=False,
                                        value=f"{reference_message_content}",
                                    )
                                    break
                        except:
                            pass
                    embed_2 = discord.Embed(color=discord.Color.red()).set_footer(
                        text=f"{dic.get('guildName', '不明なサーバー')} | {dic.get('guildId', '不明')}",
                        icon_url="https://media.discordapp.net/icons/{}/{}.png?size=1024".format(
                            dic.get("guildId", "0"), dic.get("guildIcon", "")
                        ),
                    )
                    try:
                        webhook_ = Webhook.from_url(
                            ch.get("Webhook", None), session=session
                        )
                        await webhook_.send(
                            embeds=[embed, embed_2],
                            username="SharkBot-SGC",
                            avatar_url=self.bot.user.avatar.url,
                        )
                    except:
                        continue
                    await asyncio.sleep(1)
        await message.add_reaction("✅")

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

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        js = await self.sgc_make_json(message)
        await self.bot.get_channel(707158257818664991).send(
            content=js, allowed_mentions=discord.AllowedMentions.none()
        )

        await self.send_super_global_chat_room(message)
        await message.remove_reaction("🔄", self.bot.user)

        await message.add_reaction("✅")

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
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
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
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

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
                res += f"{m.display_name} {STATUS_EMOJIS.get(m.status, '❔')} ({m.status})\n"
        await interaction.followup.send(
            embed=discord.Embed(
                title="SGCのBot情報", color=discord.Color.green(), description=res
            )
        )

    @globalchat.command(
        name="shiritori", description="グローバルしりとりに参加します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_shiritori(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )
        await interaction.response.defer()
        if interaction.guild.member_count < 20:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="20人未満のサーバーは参加できません。",
                    color=discord.Color.red(),
                )
            )
        wh = await interaction.channel.create_webhook(name="SharkBot-しりとり")
        db = self.bot.async_db["Main"].GlobalShiritori
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {
                "Guild": interaction.guild.id,
                "Channel": interaction.channel.id,
                "GuildName": interaction.guild.name,
                "Webhook": wh.url,
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
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {
                "Guild": interaction.guild.id,
                "Channel": interaction.channel.id,
                "GuildName": interaction.guild.name,
                "Webhook": web.url,
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
                description=message.content, color=discord.Color.blue()
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
                await self.send_one_ads(channel["Webhook"], message)
            else:
                continue

            await asyncio.sleep(1)

    @globalchat.command(name="ads", description="グローバル宣伝に参加します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def global_ads(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.guild.member_count < 20:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="20人未満のサーバーは参加できません。",
                    color=discord.Color.red(),
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

    @commands.Cog.listener("on_message")
    async def on_message_ads(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalads_check_channel(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        if invite_only_check.fullmatch(message.content):
            db = self.bot.async_db["Main"].PremiumUser
            try:
                dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
                if not dbfind is None:
                    msg = await message.reply(
                        embed=discord.Embed(
                            title="宣伝文を作成しますか？",
                            description="その招待リンクにあった宣伝文をAIが作成してくれます。",
                            color=discord.Color.yellow(),
                        )
                    )
                    await msg.add_reaction("✅")
                    await msg.add_reaction("❌")

                    try:
                        r, m = await self.bot.wait_for(
                            "reaction_add",
                            check=lambda r, u: r.message.id == msg.id
                            and not u.bot
                            and message.author.id == u.id,
                            timeout=30,
                        )

                        if r.emoji == "✅":
                            await asyncio.sleep(1)

                            await msg.delete()

                            await asyncio.sleep(1)

                            invite = await self.bot.fetch_invite(message.content)

                            gem_token = settings.GEMINI_APIKEY

                            client = genai.Client(api_key=gem_token)

                            response = await client.aio.models.generate_content(
                                model="gemini-2.5-flash-lite",
                                contents=f"以下の条件に合わせて回答を出力して。\n・discordサーバーの宣伝文を作る。\n・宣伝文以外を出力しない。\n・サーバー名は、「{invite.guild.name}」\n・招待リンクは「{message.content}」",
                            )

                            message.content = response.text

                            await self.send_global_ads(message)

                            await message.remove_reaction("🔄", self.bot.user)
                            await message.add_reaction("✅")
                            return
                        else:
                            await msg.delete()
                            pass
                    except:
                        pass
            except Exception:
                pass

        await self.send_global_ads(message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")

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
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat_room(check, message, rmsg)
        else:
            await self.send_global_chat_room(check, message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")

    async def globalchat_users_add(self, user: discord.User, message: discord.Message):
        db = self.bot.async_db["Main"].GlobalChatRuleAgreeUser

        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
            if dbfind is None:
                await message.reply(embed=discord.Embed(title="これがグローバルチャットのルールです。", description="""
荒らしをしない
宣伝をしない (宣伝の場合は宣伝グローバルへ)
r18やグロ関連のものを貼らない
違法なリンクを貼らない・違法な会話をしない
喧嘩などをしない。
その他運営の禁止したものを貼らない

これらルールに違反した場合は
グローバルチャットが利用できなくなります。

同意できる場合は「同意」ボタンを押してください。
""", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="同意", style=discord.ButtonStyle.green, custom_id="globalchat_agree+")))
                return True
        except Exception:
            return False

        await db.replace_one(
            {"User": user.id},
            {
                "User": user.id,
                "UserName": user.name
            },
            upsert=True,
        )
        return False

    @commands.Cog.listener("on_message")
    async def on_message_global(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalchat_check_channel(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        g_u = await self.globalchat_users_add(message.author, message)
        if g_u:
            return

        await message.add_reaction("🔄")

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)
            await self.send_global_chat(message, rmsg)
        else:
            await self.send_global_chat(message)

        await message.remove_reaction("🔄", self.bot.user)
        await message.add_reaction("✅")

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
                description=message.content, color=discord.Color.blue()
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

            await asyncio.sleep(1)

    @commands.Cog.listener("on_message")
    async def on_message_global_shiritori(self, message: discord.Message):
        if message.author.bot:
            return

        if type(message.channel) == discord.DMChannel:
            return

        check = await self.globalshiritori_check_channel(message)

        if not check:
            return

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
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
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {
                "Guild": interaction.guild.id,
                "Channel": interaction.channel.id,
                "GuildName": interaction.guild.name,
                "Webhook": wh.url,
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
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )
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

    async def sgc_make_json_debug(self, message: discord.Message):
        dic = {}

        dic.update({"type": "message"})
        dic.update({"userId": str(message.author.id)})
        dic.update({"userName": message.author.name})
        dic.update({"x-userGlobal_name": message.author.global_name})
        dic.update({"userDiscriminator": message.author.discriminator})
        if hasattr(message.author.avatar, "key"):
            dic.update({"userAvatar": message.author.avatar.key})
        else:
            dic.update({"userAvatar": None})
        dic.update({"isBot": message.author.bot})
        dic.update({"guildId": str(message.guild.id)})
        dic.update({"guildName": message.guild.name})
        if hasattr(message.guild.icon, "key"):
            dic.update({"guildIcon": message.guild.icon.key})
        else:
            dic.update({"guildIcon": None})
        dic.update({"channelId": str(message.channel.id)})
        dic.update({"channelName": message.channel.name})
        dic.update({"messageId": str(message.id)})
        dic.update({"content": message.content.replace("@", "＠")})

        if message.attachments != []:
            arr = []
            for attachment in message.attachments:
                arr.append(attachment.url)
            dic.update({"attachmentsUrl": arr})

        if message.author.primary_guild.tag:
            dic.update({"x-userTag": message.author.primary_guild.tag})

            dic.update({"x-userPrimaryGuild": {
                'tag': message.author.primary_guild.tag
            }})

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

        jsondata = json.dumps(dic, ensure_ascii=False)

        return jsondata

    async def send_super_global_chat_room_debug(
        self, message: discord.Message, ref_msg: discord.Message = None
    ):
        db = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        channels = db.find()

        if message.reference:
            rmsg = await message.channel.fetch_message(message.reference.message_id)

        count = 0

        async with aiohttp.ClientSession() as session:
            async for channel in channels:
                if channel["Channel"] == message.channel.id:
                    continue

                target_channel = self.bot.get_channel(channel["Channel"])

                if target_channel:
                    embed = discord.Embed(
                        description=message.content, color=discord.Color.blue()
                    )
                    embed.set_footer(text=f"mID:{message.id} / SharkBot")
                    bag = await self.badge_build(message)
                    if message.author.avatar:
                        embed.set_author(
                            name=f"[{bag}] {message.author.name}/{message.author.id} [{message.author.primary_guild.tag if message.author.primary_guild.tag else 'なし'}]",
                            icon_url=message.author.avatar.url,
                        )
                    else:
                        embed.set_author(
                            name=f"[{bag}] {message.author.name}/{message.author.id} [{message.author.primary_guild.tag if message.author.primary_guild.tag else 'なし'}]",
                            icon_url=message.author.default_avatar.url,
                        )
                    embed_2 = discord.Embed(color=discord.Color.red()).set_footer(
                        text=f"{message.guild.name} | {message.guild.id}",
                        icon_url=message.guild.icon.url if message.guild.icon else None,
                    )
                    if not message.attachments == []:
                        for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                            if kaku in message.attachments[0].filename:
                                embed.set_image(url=message.attachments[0].url)
                                break
                        embed.add_field(
                            name="添付ファイル",
                            value=message.attachments[0].url,
                            inline=False,
                        )
                    if message.reference:
                        if rmsg.application_id != self.bot.user.id:
                            embed.add_field(
                                name=f"返信 ({rmsg.author.name}#{rmsg.author.discriminator})",
                                inline=False,
                                value=f"{rmsg.content}",
                            )
                        elif rmsg.application_id == self.bot.user.id:
                            embed.add_field(
                                name=f"返信 ({rmsg.embeds[0].author.name.split(']')[1].split('/')[0].replace(' ', '')})",
                                inline=False,
                                value=f"{rmsg.embeds[0].description}",
                            )
                    webhook_ = Webhook.from_url(
                        channel.get("Webhook", None), session=session
                    )
                    await webhook_.send(
                        embeds=[embed, embed_2],
                        username="SharkBot-SGC",
                        avatar_url=self.bot.user.avatar.url,
                    )
                    count += 1
                    if count > 3:
                        await asyncio.sleep(1)
                        count = 0

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

        block = await self.user_block(message)

        if block:
            current_time = time.time()
            last_message_time = user_last_message_time_mute.get(message.guild.id, 0)
            if current_time - last_message_time < 30:
                return
            user_last_message_time_mute[message.guild.id] = current_time
            return

        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return print("クールダウン中です。")
        user_last_message_timegc[message.guild.id] = current_time

        await message.add_reaction("🔄")

        js = await self.sgc_make_json_debug(message)
        await self.bot.get_channel(707158343952629780).send(
            content=js, allowed_mentions=discord.AllowedMentions.none()
        )

        await self.send_super_global_chat_room_debug(message)
        await message.remove_reaction("🔄", self.bot.user)

        await message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_superglobal_getjson_debug(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if type(message.channel) == discord.DMChannel:
            return

        if not message.channel.id == 707158343952629780:
            return

        try:
            dic = json.loads(message.content)
        except json.decoder.JSONDecodeError:
            return

        if "type" in dic and dic["type"] != "message":
            return

        db = self.bot.async_db["Main"].AlpheSuperGlobalChatDebug
        async with aiohttp.ClientSession() as session:
            async for ch in db.find():
                target_channel = self.bot.get_channel(ch["Channel"])
                if target_channel:
                    embed = discord.Embed(
                        description=dic["content"], color=discord.Color.blue()
                    )
                    embed.set_footer(
                        text=f"mID:{dic['messageId']} / {message.author.display_name}"
                    )
                    bag = await self.badge_build(message)
                    if dic["userAvatar"]:
                        embed.set_author(
                            name=f"[{bag}] {dic['userName']}/{dic['userId']} [{dic.get('x-userPrimaryGuild', {}).get('tag', None) if dic.get('x-userPrimaryGuild', {}).get('tag', None) != None else 'なし'}]",
                            icon_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(
                                dic["userId"], dic["userAvatar"]
                            ),
                        )
                    else:
                        embed.set_author(
                            name=f"[{bag}] {dic['userName']}/{dic['userId']} [{dic.get('x-userPrimaryGuild', {}).get('tag', None) if dic.get('x-userPrimaryGuild', {}).get('tag', None) != None else 'なし'}]",
                            icon_url=message.author.default_avatar.url,
                        )
                    if not dic.get("attachmentsUrl") == []:
                        try:
                            embed.add_field(
                                name="添付ファイル", value=dic["attachmentsUrl"][0]
                            )
                            for kaku in [".png", ".jpg", ".jpeg", ".gif", ".webm"]:
                                if kaku in dic["attachmentsUrl"][0]:
                                    embed.set_image(
                                        url=urllib.parse.unquote(
                                            dic["attachmentsUrl"][0]
                                        )
                                    )
                                    break
                        except:
                            pass
                    if message.reference:
                        rmsg = await message.channel.fetch_message(
                            message.reference.message_id
                        )
                        embed.add_field(
                            name=f"返信 ({rmsg.author.name} - {rmsg.author.id})",
                            inline=False,
                            value=f"{rmsg.content}",
                        )
                    else:
                        try:
                            reference_mid = dic["reference"]  # 返信元メッセージID

                            reference_message_content = (
                                ""  # 返信元メッセージ用変数を初期化
                            )
                            reference_message_author = (
                                ""  # 返信元ユーザータグ用変数を初期化
                            )
                            past_dic = (
                                None  # 返信元メッセージの辞書型リスト用変数を初期化
                            )
                            async for past_message in message.channel.history(
                                limit=1000
                            ):  # JSONチャンネルの過去ログ1000件をループ
                                try:  # JSONのエラーを監視
                                    past_dic = json.loads(
                                        past_message.content
                                    )  # 過去ログのJSONを辞書型リストに変換
                                except json.decoder.JSONDecodeError:  # JSON読み込みエラー→そもそもJSONでは無い可能性があるのでスルー
                                    continue
                                if (
                                    "type" in past_dic and past_dic["type"] != "message"
                                ):  # メッセージでは無い時はスルー
                                    continue

                                if (
                                    "messageId" not in past_dic
                                ):  # キーにメッセージIDが存在しない時はスルー
                                    continue

                                if (
                                    str(past_dic["messageId"]) == str(reference_mid)
                                ):  # 過去ログのメッセージIDが返信元メッセージIDと一致したとき
                                    reference_message_author = "{}#{}".format(
                                        past_dic["userName"],
                                        past_dic["userDiscriminator"],
                                    )  # ユーザータグを取得
                                    reference_message_content = past_dic[
                                        "content"
                                    ]  # メッセージ内容を取得
                                    embed.add_field(
                                        name=f"返信 ({reference_message_author})",
                                        inline=False,
                                        value=f"{reference_message_content}",
                                    )
                                    break
                        except:
                            pass
                    embed_2 = discord.Embed(color=discord.Color.red()).set_footer(
                        text=f"{dic.get('guildName', '不明なサーバー')} | {dic.get('guildId', '不明')}",
                        icon_url="https://media.discordapp.net/icons/{}/{}.png?size=1024".format(
                            dic.get("guildId", "0"), dic.get("guildIcon", "")
                        ),
                    )
                    webhook_ = Webhook.from_url(
                        ch.get("Webhook", None), session=session
                    )
                    await webhook_.send(
                        embeds=[embed, embed_2],
                        username="SharkBot-SGC",
                        avatar_url=self.bot.user.avatar.url,
                    )
                    await asyncio.sleep(1)
        await message.add_reaction("✅")


async def setup(bot):
    await bot.add_cog(GlobalCog(bot))
