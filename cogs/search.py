import asyncio
from functools import partial
import io
import re
import socket
import aiohttp
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
import discord
import datetime

import pyshorteners
from consts import mongodb
from discord import app_commands
from models import command_disable

STATUS_EMOJIS = {
    discord.Status.online: "<:online:1407922300535181423>",
    discord.Status.idle: "<:idle:1407922295711727729>",
    discord.Status.dnd: "<:dnd:1407922294130741348>",
    discord.Status.offline: "<:offline:1407922298563854496>"
}

class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> SearchCog")

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

    async def get_bot_adder_from_audit_log(self, guild: discord.Guild, bot_user: discord.User):
        if not bot_user.bot:
            return "Botではありません。"
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=None):
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
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def user_search(self, interaction: discord.Interaction, user: discord.User):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

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
                if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(user.id).roles:
                    permissions = "モデレーター"
                if user.id == 1335428061541437531:
                    permissions = "管理者"
                if user.id == 1346643900395159572:
                    permissions = "SharkBot"
            except:
                pass
            add_bot_user = await self.get_bot_adder_from_audit_log(interaction.guild, user)
            tag = await self.get_user_tag_(user)
            col = await self.get_user_color(user)
            embed = discord.Embed(title=f"{user.display_name}の情報 (ページ1)", color=col)
            embed.add_field(name="基本情報", value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**\n認証Bot？: **{"はい" if user.public_flags.verified_bot else "いいえ"}**").add_field(name="サービス情報", value=f"権限: **{permissions}**")
            userdata = await self.get_user_savedata(user)
            if userdata:
                guild = int(userdata["Guild"])
                logininfo = f"**言語**: {userdata["Lang"]}\n"
                if self.bot.get_guild(guild):
                    gu = self.bot.get_guild(guild)
                    logininfo += f"**最後に認証したサーバーの名前**: {gu.name}\n"
                    logininfo += f"**最後に認証したサーバーのid**: {gu.id}"
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

                text += f"スマホか？: {"はい" if mem_status.is_on_mobile() else "いいえ"}\n"

                if mem_status.activity and isinstance(mem_status.activity, discord.CustomActivity):
                    custom_status = mem_status.activity.name
                    if mem_status.activity.emoji:
                        text += f"カスタムステータス: {mem_status.activity.emoji} {custom_status}\n"
                    else:
                        text += f"カスタムステータス: {custom_status}\n"

                embed.add_field(name="ステータス情報", value=text, inline=False)
            embed.add_field(name="その他のAPIからの情報", value=f"""
スパムアカウントか？: {"✅" if user.public_flags.spammer else "❌"}
HypeSquadEventsメンバーか？: {"✅" if user.public_flags.hypesquad else "❌"}
早期チームユーザーか？: {"✅" if user.public_flags.team_user else "❌"}
サーバータグ: {t_name} ({t_bag})
Botを追加したユーザーは？: {add_bot_user}
""", inline=False)
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
            embed2 = discord.Embed(title=f"{user.display_name}の情報 (ページ2)", color=col)
            point_check = await self.get_user_point(user)
            embed2.add_field(name="Sharkポイント", value=f"{point_check}P", inline=True)
            embed2.add_field(name="称号", value=f"{tag}", inline=True)
            embed2.set_image(url=user.banner.url if user.banner else None)
            roles = await self.roles_get(interaction.guild, user)
            embed3 = discord.Embed(title=f"{user.display_name}の情報 (ページ3)", color=discord.Color.green(), description=roles)
            pages = [embed, embed2, embed3]
            class PaginatorView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.current_page = 0
                    self.message = None

                async def update_message(self, interaction: discord.Interaction):
                    await interaction.response.edit_message(embed=pages[self.current_page], view=self)

                @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
                async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_page > 0:
                        self.current_page -= 1
                        await self.update_message(interaction)

                @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
                async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if self.current_page < len(pages) - 1:
                        self.current_page += 1
                        await self.update_message(interaction)

            view = PaginatorView()
            view.add_item(discord.ui.Button(label="/shopでSharkポイントを使って装飾アイテムを買えます。", disabled=True))
            view.add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/mUyByHYMGk"))
            if user.avatar:
                await interaction.followup.send(embed=embed.set_thumbnail(url=user.avatar.url), view=view)
            else:
                await interaction.followup.send(embed=embed.set_thumbnail(url=user.default_avatar.url), view=view)
        except:
            return

    @search.command(name="server", description="サーバー情報を確認します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def server_info(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        embed = discord.Embed(title=f"{interaction.guild.name}の情報", color=discord.Color.green())
        embed.add_field(name="サーバー名", value=interaction.guild.name)
        embed.add_field(name="サーバーID", value=str(interaction.guild.id))
        embed.add_field(name="チャンネル数", value=f"{len(interaction.guild.channels)}個")
        embed.add_field(name="絵文字数", value=f"{len(interaction.guild.emojis)}個")
        embed.add_field(name="ロール数", value=f"{len(interaction.guild.roles)}個")
        embed.add_field(name="ロールリスト", value="`/listing role`\nで見れます。")
        embed.add_field(name="メンバー数", value=f"{interaction.guild.member_count}人")
        embed.add_field(name="Nitroブースト", value=f"{interaction.guild.premium_subscription_count}人")
        embed.add_field(name="オーナー名", value=self.bot.get_user(interaction.guild.owner_id).name if self.bot.get_user(interaction.guild.owner_id) else "取得失敗")
        embed.add_field(name="オーナーID", value=str(interaction.guild.owner_id))
        JST = datetime.timezone(datetime.timedelta(hours=9))
        embed.add_field(name="作成日", value=interaction.guild.created_at.astimezone(JST))
        
        onlines = [m for m in interaction.guild.members if m.status == discord.Status.online]
        idles = [m for m in interaction.guild.members if m.status == discord.Status.idle]
        dnds = [m for m in interaction.guild.members if m.status == discord.Status.dnd]
        offlines = [m for m in interaction.guild.members if m.status == discord.Status.offline]

        pcs = [m for m in interaction.guild.members if m.client_status.desktop]
        sms = [m for m in interaction.guild.members if m.client_status.mobile]
        webs = [m for m in interaction.guild.members if m.client_status.web]

        embed.add_field(name="ステータス情報", value=f"""
<:online:1407922300535181423> {len(onlines)}人
<:idle:1407922295711727729> {len(idles)}人
<:dnd:1407922294130741348> {len(dnds)}人
<:offline:1407922298563854496> {len(offlines)}人
💻 {len(pcs)}人
📱 {len(sms)}人
🌐 {len(webs)}人
""", inline=False)

        if interaction.guild.icon:
            await interaction.followup.send(embed=embed.set_thumbnail(url=interaction.guild.icon.url))
        else:
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SearchCog(bot))