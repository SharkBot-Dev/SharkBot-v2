import asyncio
from functools import partial
import json
import ssl
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from discord.ext import commands
import discord
import datetime

import requests
from discord import app_commands
from models import command_disable

import pytesseract
from PIL import Image
import io

async def ocr_async(image_: io.BytesIO):

    image = await asyncio.to_thread(Image.open, image_)

    text = await asyncio.to_thread(pytesseract.image_to_string, image)

    return text

STATUS_EMOJIS = {
    discord.Status.online: "<:online:1407922300535181423>",
    discord.Status.idle: "<:idle:1407922295711727729>",
    discord.Status.dnd: "<:dnd:1407922294130741348>",
    discord.Status.offline: "<:offline:1407922298563854496>",
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class NomTranslater:
    def __init__(self):
        self.se = requests.Session()
        self.index = self.se.get("https://racing-lagoon.info/nomu/translate.php").text
        self.bs = BeautifulSoup(self.index, "html.parser")
        self.token = self.bs.find({"input": {"name": "token"}})["value"]

    def translare(self, text: str):
        data = {
            "token": self.token,
            "before": text,
            "level": "2",
            "options": "nochk",
            "transbtn": "翻訳",
            "after1": "",
            "options_permanent": "",
            "new_japanese": "",
            "new_nomulish": "",
            "new_setugo": "",
            "setugo": "settou",
        }

        nom_index = self.se.post(
            "https://racing-lagoon.info/nomu/translate.php", data=data
        )

        bs = BeautifulSoup(nom_index.text, "html.parser")

        return bs.find_all(
            {"textarea": {"class": "maxfield outputfield form-control selectAll"}}
        )[1].get_text()


class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> SearchCog")

    async def get_user_savedata(self, user: discord.User):
        db = self.bot.async_db["Main"].LoginData
        try:
            dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind

    async def get_user_point(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotInstallPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        return dbfind["count"]

    async def get_user_tag_(self, user: discord.User):
        db = self.bot.async_db["Main"].UserTag
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return "称号なし"
        if dbfind is None:
            return "称号なし"
        return dbfind["Tag"]

    async def get_user_color(self, user: discord.User):
        db = self.bot.async_db["Main"].UserColor
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return discord.Color.green()
        if dbfind is None:
            return discord.Color.green()
        if dbfind["Color"] == "red":
            return discord.Color.red()
        elif dbfind["Color"] == "yellow":
            return discord.Color.yellow()
        elif dbfind["Color"] == "blue":
            return discord.Color.blue()
        elif dbfind["Color"] == "random":
            return discord.Color.random()
        return discord.Color.green()

    async def get_connect_data(self, user: discord.User):
        db = self.bot.async_db["Main"].LoginConnectData
        try:
            dbfind = await db.find_one({"UserID": str(user.id)}, {"_id": False})
        except:
            return {"Youtube": "取得できません。", "Twitter": "取得できません。"}
        if dbfind is None:
            return {"Youtube": "取得できません。", "Twitter": "取得できません。"}
        return {"Youtube": dbfind["youtube"], "Twitter": dbfind["X"]}

    async def gold_user_data(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotGoldPoint
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        try:
            return dbfind.get("count", 0)
        except:
            return 0

    async def pfact_user_data(self, user: discord.User):
        db = self.bot.async_db["Main"].SharkBotPointFactory
        try:
            dbfind = await db.find_one({"_id": user.id}, {"_id": False})
        except:
            return 0
        try:
            return dbfind.get("count", 0)
        except:
            return 0

    async def get_bot_adder_from_audit_log(
        self, guild: discord.Guild, bot_user: discord.User
    ):
        if not bot_user.bot:
            return "Botではありません。"
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.bot_add, limit=None
            ):
                if entry.target == bot_user:
                    return f"{entry.user.display_name} ({entry.user.id})"
            return "取得失敗しました"
        except discord.Forbidden:
            return "監査ログを閲覧する権限がありません。"
        except Exception as e:
            return f"監査ログの確認中にエラーが発生しました: {e}"

    async def roles_get(self, guild: discord.Guild, user: discord.User):
        try:
            mem = await guild.fetch_member(user.id)
            return "**ロール一覧**: " + " ".join([f"{r.mention}" for r in mem.roles])
        except:
            return "**ロール一覧**: このサーバーにいません。"

    search = app_commands.Group(name="search", description="検索系コマンドです。")

    @search.command(name="user", description="ユーザーを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def user_search(self, interaction: discord.Interaction, user: discord.User):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
            isguild = None
            isbot = None
            if interaction.guild.get_member(user.id):
                isguild = "います。"
            else:
                isguild = "いません。"
            if user.bot:
                isbot = "はい"
            else:
                isbot = "いいえ"
            permissions = "ユーザー"
            try:
                if (
                    self.bot.get_guild(1343124570131009579).get_role(
                        1344470846995169310
                    )
                    in self.bot.get_guild(1343124570131009579).get_member(user.id).roles
                ):
                    permissions = "モデレーター"
                if user.id == 1335428061541437531:
                    permissions = "管理者"
                if user.id == 1346643900395159572:
                    permissions = "SharkBot"
            except:
                pass
            add_bot_user = await self.get_bot_adder_from_audit_log(
                interaction.guild, user
            )
            col = await self.get_user_color(user)
            embed = discord.Embed(
                title=f"{user.display_name}の情報 (ページ1)", color=col
            )
            embed.add_field(
                name="基本情報",
                value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**\n認証Bot？: **{'はい' if user.public_flags.verified_bot else 'いいえ'}**",
            ).add_field(name="サービス情報", value=f"権限: **{permissions}**")
            userdata = await self.get_user_savedata(user)
            if userdata:
                logininfo = f"**言語**: {userdata['Lang']}\n"
                embed.add_field(name="ログイン情報", value=logininfo, inline=False)
                pre = userdata["Nitro"]
                if pre == 0:
                    embed.add_field(name="Nitro", value="なし", inline=False)
                elif pre == 1:
                    embed.add_field(name="Nitro", value="Nitro Classic", inline=False)
                elif pre == 2:
                    embed.add_field(name="Nitro", value="Nitro", inline=False)
                elif pre == 3:
                    embed.add_field(name="Nitro", value="Nitro Basic", inline=False)
            if not user.bot:
                p_g = user.primary_guild
                if p_g != None:
                    t_name = p_g.tag
                    t_bag = p_g.badge
                else:
                    t_name = "なし"
                    t_bag = "なし"
            else:
                t_name = "なし"
                t_bag = "リクエストなし"

            if interaction.guild.get_member(user.id):
                mem_status = interaction.guild.get_member(user.id)

                text = ""

                emoji = STATUS_EMOJIS.get(mem_status.status, "❔")

                text += f"ステータス: {emoji} ({mem_status.status})\n"

                text += (
                    f"スマホか？: {'はい' if mem_status.is_on_mobile() else 'いいえ'}\n"
                )

                if mem_status.activity and isinstance(
                    mem_status.activity, discord.CustomActivity
                ):
                    custom_status = mem_status.activity.name
                    if mem_status.activity.emoji:
                        text += f"カスタムステータス: {mem_status.activity.emoji} {custom_status}\n"
                    else:
                        text += f"カスタムステータス: {custom_status}\n"

                embed.add_field(name="ステータス情報", value=text, inline=False)
            embed.add_field(
                name="その他のAPIからの情報",
                value=f"""
スパムアカウントか？: {"✅" if user.public_flags.spammer else "❌"}
HypeSquadEventsメンバーか？: {"✅" if user.public_flags.hypesquad else "❌"}
早期チームユーザーか？: {"✅" if user.public_flags.team_user else "❌"}
サーバータグ: {t_name} ({t_bag})
Botを追加したユーザーは？: {add_bot_user}
""",
                inline=False,
            )
            bag = ""
            if user.public_flags.active_developer:
                bag += "<:developer:1399747643260797091> "
            if user.public_flags.staff:
                bag += "<:staff:1399747719186088036> "
            if user.public_flags.partner:
                bag += "<:part:1399748417999077557> "
            if user.public_flags.bug_hunter:
                bag += "<:bag1:1399748326395478196> "
            if user.public_flags.bug_hunter_level_2:
                bag += "<:bag2:1399748401096294441> "
            if user.public_flags.verified_bot_developer:
                bag += "<:soukidev:1399748801220317225> "
            if user.public_flags.discord_certified_moderator:
                bag += "<:mod:1399749105248370728> "
            if user.public_flags.system:
                bag += "<:discord_icon:1399750113156403281> "
            if user.public_flags.early_supporter:
                bag += "<:fast_support:1399750316660101172> "
            if user.public_flags.hypesquad_bravery:
                bag += "<:HouseofBravery:1399751204430675968> "
            if user.public_flags.hypesquad_brilliance:
                bag += "<:HypeSquadBrilliance:1399751490049933322> "
            if user.public_flags.hypesquad_balance:
                bag += "<:HypeSquadBalance:1399751701669478511> "
            if bag != "":
                embed.add_field(name="バッジ", value=bag, inline=False)
            embed.set_image(url=user.banner.url if user.banner else None)
            roles = await self.roles_get(interaction.guild, user)
            embed2 = discord.Embed(
                title=f"{user.display_name}の情報 (ページ2)",
                color=discord.Color.green(),
                description=roles,
            )
            pages = [embed, embed2]

            class PaginatorView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.current_page = 0
                    self.message = None

                async def update_message(self, interaction: discord.Interaction):
                    await interaction.response.edit_message(
                        embed=pages[self.current_page], view=self
                    )

                @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
                async def prev_page(
                    self, interaction: discord.Interaction, button: discord.ui.Button
                ):
                    if self.current_page > 0:
                        self.current_page -= 1
                        await self.update_message(interaction)

                @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
                async def next_page(
                    self, interaction: discord.Interaction, button: discord.ui.Button
                ):
                    if self.current_page < len(pages) - 1:
                        self.current_page += 1
                        await self.update_message(interaction)

            view = PaginatorView()
            view.add_item(
                discord.ui.Button(
                    label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"
                )
            )
            if user.avatar:
                await interaction.followup.send(
                    embed=embed.set_thumbnail(url=user.avatar.url), view=view
                )
            else:
                await interaction.followup.send(
                    embed=embed.set_thumbnail(url=user.default_avatar.url), view=view
                )
        except:
            return

    @search.command(name="server", description="サーバー情報を確認します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def server_info(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        embed = discord.Embed(
            title=f"{interaction.guild.name}の情報", color=discord.Color.green()
        )
        embed.add_field(name="サーバー名", value=interaction.guild.name)
        embed.add_field(name="サーバーID", value=str(interaction.guild.id))
        embed.add_field(
            name="チャンネル数", value=f"{len(interaction.guild.channels)}個"
        )
        embed.add_field(name="絵文字数", value=f"{len(interaction.guild.emojis)}個")
        embed.add_field(name="ロール数", value=f"{len(interaction.guild.roles)}個")
        embed.add_field(name="ロールリスト", value="`/listing role`\nで見れます。")
        embed.add_field(name="メンバー数", value=f"{interaction.guild.member_count}人")
        embed.add_field(
            name="Nitroブースト",
            value=f"{interaction.guild.premium_subscription_count}人",
        )
        embed.add_field(
            name="オーナー名",
            value=self.bot.get_user(interaction.guild.owner_id).name
            if self.bot.get_user(interaction.guild.owner_id)
            else "取得失敗",
        )
        embed.add_field(name="オーナーID", value=str(interaction.guild.owner_id))
        JST = datetime.timezone(datetime.timedelta(hours=9))
        embed.add_field(
            name="作成日", value=interaction.guild.created_at.astimezone(JST)
        )

        onlines = [
            m for m in interaction.guild.members if m.status == discord.Status.online
        ]
        idles = [
            m for m in interaction.guild.members if m.status == discord.Status.idle
        ]
        dnds = [m for m in interaction.guild.members if m.status == discord.Status.dnd]
        offlines = [
            m for m in interaction.guild.members if m.status == discord.Status.offline
        ]

        pcs = [m for m in interaction.guild.members if m.client_status.desktop]
        sms = [m for m in interaction.guild.members if m.client_status.mobile]
        webs = [m for m in interaction.guild.members if m.client_status.web]

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

        if interaction.guild.icon:
            await interaction.followup.send(
                embed=embed.set_thumbnail(url=interaction.guild.icon.url)
            )
        else:
            await interaction.followup.send(embed=embed)

    async def get_ban_user_from_audit_log(
        self, guild: discord.Guild, user: discord.User
    ):
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.ban, limit=None
            ):
                if entry.target.id == user.id:
                    return f"{entry.user.display_name} ({entry.user.id})"
            return "取得失敗しました"
        except discord.Forbidden:
            return "監査ログを閲覧する権限がありません。"
        except Exception as e:
            return f"監査ログの確認中にエラーが発生しました"

    @search.command(name="ban", description="banされたメンバーを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_info(self, interaction: discord.Interaction, ユーザー: discord.User):
        await interaction.response.defer()
        try:
            ban_user = await interaction.guild.fetch_ban(ユーザー)
            embed = discord.Embed(
                title="BANされたユーザーの情報", color=discord.Color.green()
            )
            embed.add_field(
                name="ユーザー名",
                value=f"{ban_user.user.display_name} ({ban_user.user.id})",
                inline=False,
            )
            embed.add_field(
                name="ユーザーid", value=f"{ban_user.user.id}", inline=False
            )
            embed.add_field(
                name="BANされた理由",
                value=ban_user.reason if ban_user.reason else "理由なし",
            )
            User = await self.get_ban_user_from_audit_log(interaction.guild, ユーザー)
            embed.add_field(name="BANした人", value=User, inline=False)
            embed.set_thumbnail(
                url=ban_user.user.avatar.url
                if ban_user.user.avatar
                else ban_user.user.default_avatar.url
            )
            embed.set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}")
            await interaction.followup.send(embed=embed)
        except discord.NotFound:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="その人はBANされていません。", color=discord.Color.red()
                )
            )

    async def get_bot_inviter(self, guild: discord.Guild, user: discord.User):
        try:
            async for entry in guild.audit_logs(
                action=discord.AuditLogAction.bot_add, limit=100
            ):
                if entry.target.id == user.id:
                    JST = datetime.timezone(datetime.timedelta(hours=9))
                    return (
                        f"{entry.user.display_name} ({entry.user.id})",
                        f"{entry.created_at.astimezone(JST)}",
                    )
            return "取得失敗しました", "取得失敗しました"
        except discord.Forbidden:
            return (
                "監査ログを閲覧する権限がありません。",
                "監査ログを閲覧する権限がありません。",
            )
        except Exception as e:
            return (
                f"監査ログの確認中にエラーが発生しました",
                "監査ログの確認中にエラーが発生しました",
            )

    @search.command(name="bot", description="導入されたbotを検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def bot_info(self, interaction: discord.Interaction, bot: discord.User):
        await interaction.response.defer()
        embed = discord.Embed(title="Botの情報", color=discord.Color.green())
        embed.add_field(name="Bot名", value=bot.display_name, inline=False)
        embed.add_field(name="ユーザーid", value=f"{bot.id}", inline=False)
        bot_inv, time = await self.get_bot_inviter(interaction.guild, bot)
        embed.add_field(name="Botを入れた人", value=bot_inv, inline=False)
        embed.add_field(name="Botが入れられた時間", value=time, inline=False)
        embed.set_thumbnail(
            url=bot.avatar.url if bot.avatar else bot.default_avatar.url
        )
        embed.set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}")
        await interaction.followup.send(embed=embed)

    @search.command(name="invite", description="招待リンク情報を取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def invite_info(self, interaction: discord.Interaction, 招待リンク: str):
        await interaction.response.defer()
        JST = datetime.timezone(datetime.timedelta(hours=9))
        invite = await self.bot.fetch_invite(招待リンク)
        if not invite:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="招待リンクが見つかりません。", color=discord.Color.green()
                )
            )
        embed = (
            discord.Embed(title="招待リンクの情報", color=discord.Color.green())
            .add_field(name="サーバー名", value=f"{invite.guild.name}", inline=False)
            .add_field(name="サーバーid", value=f"{invite.guild.id}", inline=False)
            .add_field(
                name="招待リンク作成者",
                value=f"{invite.inviter.display_name if invite.inviter else '不明'} ({invite.inviter.id if invite.inviter else '不明'})",
                inline=False,
            )
            .add_field(
                name="招待リンクの使用回数",
                value=f"{invite.uses if invite.uses else '0'} / {invite.max_uses if invite.max_uses else '無限'}",
                inline=False,
            )
        )
        embed.add_field(
            name="チャンネル",
            value=f"{invite.channel.name if invite.channel else '不明'} ({invite.channel.id if invite.channel else '不明'})",
            inline=False,
        )
        embed.add_field(
            name="メンバー数",
            value=f"{invite.approximate_member_count if invite.approximate_member_count else '不明'}",
            inline=False,
        )
        embed.add_field(
            name="オンライン数",
            value=f"{invite.approximate_presence_count if invite.approximate_presence_count else '不明'}",
            inline=False,
        )
        embed.add_field(
            name="作成時刻",
            value=f"{invite.created_at.astimezone(JST) if invite.created_at else '不明'}",
            inline=False,
        )
        if invite.guild.icon:
            embed.set_thumbnail(url=invite.guild.icon.url)
        await interaction.followup.send(embed=embed)

    @search.command(name="avatar", description="アバターを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def avatar(self, interaction: discord.Interaction, ユーザー: discord.User):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        if ユーザー.avatar == None:

            class AvatarLayout(discord.ui.LayoutView):
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"### {ユーザー.name}さんのアバター",
                    ),
                    discord.ui.TextDisplay(
                        f"ダウンロード\n[.png]({ユーザー.default_avatar.with_format('png').url})",
                    ),
                    discord.ui.Separator(),
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(ユーザー.default_avatar.url)
                    ),
                    accent_colour=discord.Colour.green(),
                )

            await interaction.followup.send(view=AvatarLayout())

        else:

            class AvatarLayout(discord.ui.LayoutView):
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        f"### {ユーザー.name}さんのアバター",
                    ),
                    discord.ui.TextDisplay(
                        f"ダウンロード\n[.png]({ユーザー.avatar.with_format('png').url}) [.jpg]({ユーザー.avatar.with_format('jpg').url}) [.webp]({ユーザー.avatar.with_format('webp').url})",
                    ),
                    discord.ui.Separator(),
                    discord.ui.MediaGallery(
                        discord.MediaGalleryItem(ユーザー.avatar.url)
                    ),
                    discord.ui.Separator(),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            label="デフォルトアバターURL",
                            url=ユーザー.default_avatar.url,
                        )
                    ),
                    accent_colour=discord.Colour.green(),
                )

            await interaction.followup.send(view=AvatarLayout())

        return

    @search.command(name="emoji", description="絵文字を検索します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def emoji(self, interaction: discord.Interaction, 絵文字: str):
        await interaction.response.defer()
        for e in interaction.guild.emojis:
            if 絵文字 == e.__str__():
                await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{e.name} の情報", color=discord.Color.green()
                    )
                    .set_image(url=e.url)
                    .add_field(name="名前", value=e.name, inline=False)
                    .add_field(name="id", value=str(e.id), inline=False)
                    .add_field(name="作成日時", value=str(e.created_at), inline=False)
                    .add_field(
                        name="絵文字が動くか",
                        value="はい" if e.animated else "いいえ",
                        inline=False,
                    )
                )
                return
        await interaction.followup.send(
            embed=discord.Embed(
                title=f"絵文字が見つかりません。", color=discord.Color.red()
            )
        )

    @search.command(name="translate", description="翻訳をします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        翻訳先=[
            app_commands.Choice(name="日本語へ", value="ja"),
            app_commands.Choice(name="英語へ", value="en"),
            app_commands.Choice(name="中国語へ", value="zh-CN"),
            app_commands.Choice(name="韓国語へ", value="ko"),
            app_commands.Choice(name="ロシア語へ", value="ru"),
            app_commands.Choice(name="ノムリッシュ語へ", value="nom"),
        ]
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        翻訳先: app_commands.Choice[str],
        テキスト: str = None,
        画像: discord.Attachment = None
    ):
        await interaction.response.defer()

        if テキスト:

            if 翻訳先.value == "nom":
                loop = asyncio.get_running_loop()
                nom = await loop.run_in_executor(None, partial(NomTranslater))
                text = await loop.run_in_executor(None, partial(nom.translare, テキスト))

                embed = discord.Embed(
                    title="翻訳 (ノムリッシュ語へ)",
                    description=f"```{text}```",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                return

            try:
                translator = GoogleTranslator(source="auto", target=翻訳先.value)
                translated_text = translator.translate(テキスト)

                embed = discord.Embed(
                    title=f"翻訳 ({翻訳先.value} へ)",
                    description=f"```{translated_text}```",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)

            except Exception:
                embed = discord.Embed(
                    title="翻訳に失敗しました",
                    description="指定された言語コードが正しいか確認してください。",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)
        else:
            if not 画像:
                return await interaction.followup.send(content="テキストか画像、どちらかを指定してください。")
            if not 画像.filename.endswith(('.png', '.jpg', '.jpeg')):
                return await interaction.followup.send(content="`.png`と`.jpg`のみ対応しています。")
            i = io.BytesIO(await 画像.read())
            text_ocrd = await ocr_async(i)
            i.close()

            if text_ocrd == "":
                return await interaction.followup.send(content="画像にはテキストがありません。")

            if 翻訳先.value == "nom":
                loop = asyncio.get_running_loop()
                nom = await loop.run_in_executor(None, partial(NomTranslater))
                text = await loop.run_in_executor(None, partial(nom.translare, text_ocrd))

                embed = discord.Embed(
                    title="翻訳 (ノムリッシュ語へ)",
                    description=f"```{text}```",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                return

            try:
                translator = GoogleTranslator(source="auto", target=翻訳先.value)
                translated_text = translator.translate(text_ocrd)

                embed = discord.Embed(
                    title=f"翻訳 ({翻訳先.value} へ)",
                    description=f"```{translated_text}```",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="翻訳に失敗しました",
                    description=f"エラーコード: {e}",
                    color=discord.Color.red(),
                )
                await interaction.followup.send(embed=embed)

    @search.command(name="news", description="ニュースを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def news(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://mainichi.jp/", ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), "html.parser")
                title = soup.find_all("div", class_="toppickup")[0]
                url = title.find_all("a")[0]
                await interaction.followup.send(f"https:{url['href']}")

    @search.command(name="wikipedia", description="ウィキペディアから取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def wikipedia(self, interaction: discord.Interaction, 検索ワード: str):
        await interaction.response.defer()

        wikipedia_api_url = "https://ja.wikipedia.org/w/api.php"

        params = {
            "action": "query",
            "format": "json",
            "titles": 検索ワード,
            "prop": "info",
            "inprop": "url",
        }

        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(wikipedia_api_url, params=params) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                await interaction.followup.send("Wikipedia記事が見つかりませんでした。")
                return

            page_id, page_info = next(iter(pages.items()))
            if page_id == "-1":
                await interaction.followup.send("Wikipedia記事が見つかりませんでした。")
                return

            short_url = f"https://ja.wikipedia.org/w/index.php?curid={page_id}"
            await interaction.followup.send(f"🔗 Wikipedia短縮リンク: {short_url}")

        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}")

    @search.command(name="safeweb", description="サイトの安全性を調べます。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def wikipedia(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://findredirect.com/api/redirects", json={"url": url}
            ) as response_expand:
                js_short = await response_expand.json()

        async with aiohttp.ClientSession() as session_safeweb:
            if not js_short[0].get("redirect", False):
                q = urlparse(url).netloc
                async with session_safeweb.get(
                    f"https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0",
                    ssl=ssl_context,
                ) as response:
                    js = json.loads(await response.text())
                    if js["rating"] == "b":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは危険です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.red(),
                            )
                        )
                    elif js["rating"] == "w":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは注意が必要です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.yellow(),
                            )
                        )
                    elif js["rating"] == "g":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは評価されていません。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.blue(),
                            )
                        )
                    else:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは多分安全です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.green(),
                            )
                        )
            else:
                q = urlparse(js_short[0].get("redirect", False)).netloc
                async with session_safeweb.get(
                    f"https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0",
                    ssl=ssl_context,
                ) as response:
                    js = json.loads(await response.text())
                    if js["rating"] == "b":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは危険です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.red(),
                            )
                        )
                    elif js["rating"] == "w":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは注意が必要です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.yellow(),
                            )
                        )
                    elif js["rating"] == "g":
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは評価されていません。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.blue(),
                            )
                        )
                    else:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="このサイトは多分安全です。",
                                description=f"URLの評価: {js['communityRating']}",
                                color=discord.Color.green(),
                            )
                        )


async def setup(bot):
    await bot.add_cog(SearchCog(bot))
