import datetime
import math

from discord.ext import commands
from discord import app_commands
import discord
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
from concurrent.futures import ThreadPoolExecutor
import random

from consts import settings
from models import command_disable, make_embed


class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> LevelCog")

    async def check_level_enabled(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        dbfind = await db.find_one({"Guild": guild.id})
        return dbfind is not None

    async def get_user_data(self, guild_id: int, user_id: int):
        db = self.bot.async_db["Main"].Leveling
        data = await db.find_one({"Guild": guild_id, "User": user_id})
        if not data:
            initial_data = {
                "Guild": guild_id,
                "User": user_id,
                "Level": 0, "XP": 0,
                "TextLevel": 0, "TextXP": 0,
                "VoiceLevel": 0, "VoiceXP": 0,
                "last_active": None
            }
            await db.insert_one(initial_data)
            return initial_data
        return data

    async def get_message(self, guild_id: int, category: str):
        db = self.bot.async_db["Main"].LevelingSetting
        dbfind = await db.find_one({"Guild": guild_id})
        
        default = f"`{{user}}`さんの **{{category}}** レベルが「{{newlevel}}」になったよ！"
        if dbfind:
            return dbfind.get(f"{category}Message", default)
        return default
    
    async def update_xp(self, guild: discord.Guild, user: discord.Member, category: str, amount: int):
        db = self.bot.async_db["Main"].Leveling
        data = await self.get_user_data(guild.id, user.id)
        
        timing = await self.get_timing(guild) or 100
        
        new_cat_xp = data.get(f"{category}XP", 0) + amount
        new_cat_lv = data.get(f"{category}Level", 0)
        cat_leveled_up = False
        while new_cat_xp >= timing:
            new_cat_xp -= timing
            new_cat_lv += 1
            cat_leveled_up = True

        new_total_xp = data.get("XP", 0) + amount
        new_total_lv = data.get("Level", 0)
        total_leveled_up = False
        while new_total_xp >= timing:
            new_total_xp -= timing
            new_total_lv += 1
            total_leveled_up = True

        update_fields = {
            f"{category}XP": new_cat_xp,
            f"{category}Level": new_cat_lv,
            "XP": new_total_xp,
            "Level": new_total_lv
        }
        await db.update_one({"Guild": guild.id, "User": user.id}, {"$set": update_fields})

        if cat_leveled_up:
            await self.handle_levelup(guild, user, category, new_cat_lv)
        
        if total_leveled_up:
            await self.handle_levelup(guild, user, "Total", new_total_lv)

    async def handle_levelup(self, guild: discord.Guild, user: discord.Member, category: str, new_lv: int):
        role_id = await self.get_role(guild, category, new_lv)
        if role_id:
            role = guild.get_role(role_id)
            if role and role not in user.roles:
                try:
                    await user.add_roles(role, reason=f"Level up ({category})")
                except Exception as e:
                    print(f"Role grant error: {e}")

        is_silent = await self.get_silent(guild)
        if is_silent:
            return

        msg_template = await self.get_message(guild.id, category)
        cat_display = {"Total": "総合", "Text": "テキスト", "Voice": "ボイス"}.get(category, category)
        
        content = msg_template.replace("{user}", user.display_name)\
                             .replace("{newlevel}", str(new_lv))\
                             .replace("{category}", cat_display)
        
        cha_id = await self.get_channel(guild)
        embed = discord.Embed(description=content, color=discord.Color.yellow())
        
        if cha_id:
            channel = guild.get_channel(cha_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                except:
                    pass

    async def get_timing(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingUpTiming
        dbfind = await db.find_one({"Guild": guild.id})
        return dbfind["Timing"] if dbfind else 100

    async def get_channel(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingUpAlertChannel
        dbfind = await db.find_one({"Guild": guild.id})
        return dbfind["Channel"] if dbfind else None

    async def get_role(self, guild: discord.Guild, category: str, level: int):
        db = self.bot.async_db["Main"].LevelingUpRole
        dbfind = await db.find_one({"Guild": guild.id, "Level": level, "Category": category})
        return dbfind["Role"] if dbfind else None

    async def get_blacklist_role(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        dbfind = await db.find_one({"Guild": guild.id})
        return dbfind.get("Blacklist", []) if dbfind else []

    async def get_silent(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        dbfind = await db.find_one({"Guild": guild.id})
        return dbfind.get("Silent", False) if dbfind else False

    async def get_xp_rate(self, guild_id: int):
        db = self.bot.async_db["Main"].LevelingSetting
        data = await db.find_one({"Guild": guild_id})
        if data:
            return data.get("MinXP", 1), data.get("MaxXP", 3)
        return 1, 3

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        if not await self.check_level_enabled(message.guild): return
        
        blacklist = await self.get_blacklist_role(message.guild)
        if any(role.id in blacklist for role in message.author.roles): return

        min_xp, max_xp = await self.get_xp_rate(message.guild.id)
        gained_xp = random.randint(min_xp, max_xp)

        if gained_xp > 0:
            await self.update_xp(message.guild, message.author, "Text", gained_xp)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        if member.bot or not await self.check_level_enabled(member.guild): return

        blacklist = await self.get_blacklist_role(member.guild)
        if any(role.id in blacklist for role in member.roles): return

        db = self.bot.async_db["Main"].Leveling
        now = datetime.datetime.now()
        
        if before.channel is None and after.channel is not None:
            if not after.afk:
                await db.update_one({"Guild": member.guild.id, "User": member.id}, {"$set": {"last_active": now}}, upsert=True)
        
        elif before.channel is not None and after.channel is None:
            data = await self.get_user_data(member.guild.id, member.id)
            start_time = data.get("last_active")
            if start_time:
                duration = (now - start_time).total_seconds()
                xp_gained = int(math.sqrt(duration / 60) * 5)
                if xp_gained > 0:
                    await self.update_xp(member.guild, member, "Voice", xp_gained)
                await db.update_one({"Guild": member.guild.id, "User": member.id}, {"$set": {"last_active": None}})

    level = app_commands.Group(name="level", description="レベル系のコマンドです。")

    @level.command(name="setting", description="レベルを有効化&無効化します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_setting(self, interaction: discord.Interaction, 有効か: bool):
        db = self.bot.async_db["Main"].LevelingSetting
        if 有効か:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                ephemeral=True, content="レベルを有効化しました。"
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                ephemeral=True, content="レベルを無効化しました。"
            )

    @level.command(name="show", description="現在のレベル詳細（総合・テキスト・ボイス）を表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_show(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(
                embed=make_embed.error_embed(title="レベル機能は無効です。")
            )

        user_data = await self.get_user_data(interaction.guild.id, interaction.user.id)
        
        avatar_url = (
            interaction.user.avatar.url if interaction.user.avatar 
            else interaction.user.default_avatar.url
        )

        total_info = f"レベル: **{user_data.get('Level', 0)}**\nXP: **{user_data.get('XP', 0)}**"
        text_info = f"レベル: **{user_data.get('TextLevel', 0)}**\nXP: **{user_data.get('TextXP', 0)}**"
        voice_info = f"レベル: **{user_data.get('VoiceLevel', 0)}**\nXP: **{user_data.get('VoiceXP', 0)}**"

        embed = make_embed.success_embed(
            title=f"{interaction.user.display_name} のレベルステータス"
        )
        embed.set_thumbnail(url=avatar_url)

        embed.add_field(name="📊 総合（Total）", value=total_info, inline=False)
        embed.add_field(name="💬 テキスト（Text）", value=text_info, inline=True)
        embed.add_field(name="🔊 ボイス（Voice）", value=voice_info, inline=True)

        timing = await self.get_timing(interaction.guild) or 100
        embed.set_footer(text=f"各レベルアップには {timing} XP 必要です")

        await interaction.followup.send(embed=embed)

    async def get_user_color(self, user: discord.User):
        db = self.bot.async_db["Main"].RankColor
        try:
            dbfind = await db.find_one({"User": user.id}, {"_id": False})
        except:
            return (100, 100, 100)
        if dbfind is None:
            return (100, 100, 100)
        if dbfind["Color"] == "red":
            return (125, 52, 75)
        elif dbfind["Color"] == "yellow":
            return (136, 158, 27)
        elif dbfind["Color"] == "blue":
            return (80, 88, 204)
        elif dbfind["Color"] == "green":
            return (66, 245, 96)
        elif dbfind["Color"] == "random":
            return (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
        return (100, 100, 100)

    @level.command(name="card-custom", description="レベルカードをカスタマイズします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        色=[
            app_commands.Choice(name="赤", value="red"),
            app_commands.Choice(name="黄", value="yellow"),
            app_commands.Choice(name="青", value="blue"),
            app_commands.Choice(name="緑", value="green"),
            app_commands.Choice(name="ランダム", value="random"),
            app_commands.Choice(name="灰", value="gray"),
        ]
    )
    async def level_card_custom(
        self, interaction: discord.Interaction, 色: app_commands.Choice[str]
    ):
        db = self.bot.async_db["Main"].RankColor
        await db.update_one(
            {"User": interaction.user.id},
            {"$set": {"User": interaction.user.id, "Color": 色.value}},
            upsert=True,
        )
        await interaction.response.send_message(
            ephemeral=True,
            embed=make_embed.success_embed(
                title="レベルカードをカスタマイズしました。",
                description=f"色: {色.name}",
            ).set_footer(text=f"ID: {色.value}"),
        )

    async def set_channel(self, guild: discord.Guild, channel: discord.TextChannel = None):
        db = self.bot.async_db["Main"].LevelingUpAlertChannel
        if channel:
            await db.update_one({"Guild": guild.id}, {"$set": {"Channel": channel.id}}, upsert=True)
        else:
            await db.delete_one({"Guild": guild.id})

    async def set_role(self, guild: discord.Guild, level: int, role: discord.Role = None):
        db = self.bot.async_db["Main"].LevelingUpRole
        if role:
            await db.update_one({"Guild": guild.id, "Level": level}, {"$set": {"Role": role.id}}, upsert=True)
        else:
            await db.delete_one({"Guild": guild.id, "Level": level})

    async def add_blacklist_role(self, guild: discord.Guild, role: discord.Role):
        db = self.bot.async_db["Main"].LevelingSetting
        await db.update_one({"Guild": guild.id}, {"$addToSet": {"Blacklist": role.id}}, upsert=True)

    async def remove_blacklist_role(self, guild: discord.Guild, role: discord.Role):
        db = self.bot.async_db["Main"].LevelingSetting
        await db.update_one({"Guild": guild.id}, {"$pull": {"Blacklist": role.id}})

    async def set_silent(self, guild: discord.Guild, boolean: bool):
        db = self.bot.async_db["Main"].LevelingSetting
        await db.update_one({"Guild": guild.id}, {"$set": {"Silent": boolean}}, upsert=True)

    @level.command(name="message", description="レベルアップ時の通知メッセージをカテゴリ別に編集します。")
    @app_commands.describe(
        カテゴリ="どのレベルが上がった時のメッセージか選択してください",
        メッセージ="メッセージ内容（{user}, {newlevel}, {category} が使えます）"
    )
    @app_commands.choices(カテゴリ=[
        app_commands.Choice(name="総合 (Total)", value="Total"),
        app_commands.Choice(name="テキスト (Text)", value="Text"),
        app_commands.Choice(name="ボイス (Voice)", value="Voice"),
    ])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def level_message(self, interaction: discord.Interaction, カテゴリ: str, メッセージ: str = None):
        await interaction.response.defer()
        
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(embed=make_embed.error_embed(title="レベル機能は無効です。"))

        db = self.bot.async_db["Main"].LevelingSetting
        field_name = f"{カテゴリ}Message"

        if メッセージ:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {field_name: メッセージ}},
                upsert=True
            )
            
            preview = メッセージ.replace("{user}", interaction.user.display_name)\
                              .replace("{newlevel}", "10")\
                              .replace("{category}", カテゴリ)
            
            embed = make_embed.success_embed(
                title=f"{カテゴリ} の通知メッセージを設定しました",
                description=f"**実際の表示例:**\n{preview}\n\n"
                            f"**使用可能な変数:**\n"
                            f"`{{user}}` : ユーザー名\n"
                            f"`{{newlevel}}` : 到達レベル\n"
                            f"`{{category}}` : カテゴリ名"
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$unset": {field_name: ""}}
            )
            embed = make_embed.success_embed(title=f"{カテゴリ} のメッセージをリセットしました。")

        await interaction.followup.send(embed=embed)

    @level.command(name="channel", description="レベルアップの通知のチャンネルを設定します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def level_channel(self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None):
        await interaction.response.defer()
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(embed=make_embed.error_embed(title="レベルは無効です。"))

        if チャンネル:
            await self.set_channel(interaction.guild, チャンネル)
            title, desc = "レベルアップの通知チャンネルを設定しました。", f"チャンネル: {チャンネル.mention}"
        else:
            await self.set_channel(interaction.guild)
            title, desc = "レベルアップの通知チャンネルを削除しました。", "今後はメッセージが送信されたチャンネルで通知されます。"
        
        await interaction.followup.send(embed=make_embed.success_embed(title=title, description=desc))

    @level.command(name="silent", description="レベルアップの通知を送信しないようにする設定をします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.describe(静かにするか="Falseで送信、Trueで送信しない")
    async def level_silent(self, interaction: discord.Interaction, 静かにするか: bool):
        await interaction.response.defer()
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(embed=make_embed.error_embed(title="レベルは無効です。"))

        await self.set_silent(interaction.guild, 静かにするか)
        msg = "送信しない" if 静かにするか else "送信する"

        await interaction.followup.send(embed=make_embed.success_embed(title="設定を更新しました。", description=f"レベルアップメッセージを{msg}ようにしました。"))

    @level.command(name="role", description="カテゴリごとのレベルアップ報酬ロールを設定します。")
    @app_commands.describe(カテゴリ="報酬を設定する対象", レベル="到達目標レベル", ロール="付与するロール（指定なしで削除）")
    @app_commands.choices(カテゴリ=[
        app_commands.Choice(name="総合 (Total)", value="Total"),
        app_commands.Choice(name="テキスト (Text)", value="Text"),
        app_commands.Choice(name="ボイス (Voice)", value="Voice"),
    ])
    @app_commands.checks.has_permissions(manage_roles=True)
    async def level_role(self, interaction: discord.Interaction, カテゴリ: str, レベル: int, ロール: discord.Role = None):
        await interaction.response.defer()
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send("レベル機能は無効です。")

        db = self.bot.async_db["Main"].LevelingUpRole
        if ロール:
            await db.update_one(
                {"Guild": interaction.guild.id, "Category": カテゴリ, "Level": レベル},
                {"$set": {"Role": ロール.id}},
                upsert=True
            )
            msg = f"**{カテゴリ}** レベル **{レベル}** の報酬に {ロール.mention} を設定しました。"
        else:
            await db.delete_one({"Guild": interaction.guild.id, "Category": カテゴリ, "Level": レベル})
            msg = f"**{カテゴリ}** レベル **{レベル}** の報酬を削除しました。"
        
        await interaction.followup.send(embed=make_embed.success_embed(title="報酬設定の更新", description=msg))

    @level.command(name="blacklist", description="ブラックリストに登録するロールを設定")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def level_blacklist(self, interaction: discord.Interaction, ロール: discord.Role):
        await interaction.response.defer()
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send("レベル機能は無効です。")

        b_role = await self.get_blacklist_role(interaction.guild)
        if ロール.id in b_role:
            msg = f"ブラックリストから{ロール.mention}を削除しました。"
            await self.remove_blacklist_role(interaction.guild, ロール)
        else:
            msg = f"ブラックリストに{ロール.mention}を追加しました。\nそのロールを持つ人がレベルが上がらなくなります。"
            await self.add_blacklist_role(interaction.guild, ロール)

        await interaction.followup.send(embed=make_embed.success_embed(title="ブラックリストの更新", description=msg))

    @level.command(name="blacklists", description="ブラックリストロールをリスト化します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def level_blacklists(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send("レベル機能は無効です。")

        b_role = await self.get_blacklist_role(interaction.guild)
        roles = [f"<@&{_}>" for _ in b_role]

        embed = make_embed.success_embed(title="ブラックリストロール一覧", description="\n".join(roles))

        await interaction.followup.send(embed=embed)

    @level.command(name="edit", description="ユーザーのレベル・XPを直接編集します。")
    @app_commands.describe(カテゴリ="編集する対象を選択してください")
    @app_commands.choices(カテゴリ=[
        app_commands.Choice(name="総合 (Total)", value="Total"),
        app_commands.Choice(name="テキスト (Text)", value="Text"),
        app_commands.Choice(name="ボイス (Voice)", value="Voice"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def level_edit(self, interaction: discord.Interaction, ユーザー: discord.User, カテゴリ: str, レベル: int, xp: int):
        await interaction.response.defer()
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(embed=make_embed.error_embed(title="レベル機能が無効です。"))

        db = self.bot.async_db["Main"].Leveling
        field_lv = "Level" if カテゴリ == "Total" else f"{カテゴリ}Level"
        field_xp = "XP" if カテゴリ == "Total" else f"{カテゴリ}XP"

        await db.update_one(
            {"Guild": interaction.guild.id, "User": ユーザー.id},
            {"$set": {field_lv: レベル, field_xp: xp}},
            upsert=True
        )
        
        await interaction.followup.send(embed=make_embed.success_embed(
            title="レベルを編集しました。",
            description=f"対象: {ユーザー.mention}\nカテゴリ: **{カテゴリ}**\n設定後: Lv.{レベル} / {xp}XP"
        ))

    @level.command(name="timing", description="レベルアップに必要なXP（1レベルあたり）を設定します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def level_timing(self, interaction: discord.Interaction, xp: int):
        await interaction.response.defer()
        if xp < 20:
            return await interaction.followup.send(embed=make_embed.error_embed(title="20XP以上で設定してください。"))
        
        db = self.bot.async_db["Main"].LevelingUpTiming
        await db.update_one({"Guild": interaction.guild.id}, {"$set": {"Timing": xp}}, upsert=True)
        
        await interaction.followup.send(embed=make_embed.success_embed(
            title="レベルアップタイミング設定",
            description=f"現在の設定: **{xp}XP** ごとにレベルアップします。"
        ))

    @level.command(name="rate", description="メッセージ送信時に獲得できるXPの範囲を設定します。")
    @app_commands.describe(最小値="獲得できるXPの下限 (例: 0)", 最大値="獲得できるXPの上限 (例: 5)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def level_rate(self, interaction: discord.Interaction, 最小値: int, 最大値: int):
        await interaction.response.defer()
        
        if 最小値 < 0 or 最大値 < 1:
            return await interaction.followup.send("最小値は0以上、最大値は1以上にしてください。")
        if 最小値 > 最大値:
            return await interaction.followup.send("最小値は最大値より小さく設定してください。")

        db = self.bot.async_db["Main"].LevelingSetting
        await db.update_one(
            {"Guild": interaction.guild.id},
            {"$set": {"MinXP": 最小値, "MaxXP": 最大値}},
            upsert=True
        )

        await interaction.followup.send(embed=make_embed.success_embed(
            title="経験値レートを更新しました",
            description=f"メッセージ送信時の獲得XP: **{最小値} 〜 {最大値} XP**"
        ))

    @level.command(name="rewards", description="現在の報酬リストを表示します。")
    async def level_rewards(self, interaction: discord.Interaction):
        await interaction.response.defer()
        db = self.bot.async_db["Main"].LevelingUpRole
        
        embed = make_embed.success_embed(title="レベルアップ報酬一覧")
        
        for cat_key, cat_name in [("Total", "📊 総合"), ("Text", "💬 テキスト"), ("Voice", "🔊 ボイス")]:
            roles_cursor = db.find({"Guild": interaction.guild.id, "Category": cat_key}).sort("Level", 1)
            roles_list = await roles_cursor.to_list(length=None)
            
            if roles_list:
                lines = []
                for r in roles_list:
                    role = interaction.guild.get_role(r["Role"])
                    role_str = role.mention if role else "不明なロール"
                    lines.append(f"Lv.{r['Level']}: {role_str}")
                embed.add_field(name=cat_name, value="\n".join(lines), inline=False)
            else:
                embed.add_field(name=cat_name, value="報酬なし", inline=False)

        await interaction.followup.send(embed=embed)

    @level.command(name="card", description="総合・テキスト・ボイスのレベルカードを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_card(self, interaction: discord.Interaction):
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="レベル機能は無効です。"), ephemeral=True
            )
        
        await interaction.response.defer()

        def generate_rank_card(
            color,
            username: str,
            avatar_bytes: bytes,
            data: dict,
            next_xp: int = 100
        ) -> io.BytesIO:
            W, H = 600, 240
            base_color = color if isinstance(color, tuple) else (88, 101, 242)

            try:
                font_main = ImageFont.truetype("data/DiscordFont.ttf", 24)
                font_sub = ImageFont.truetype("data/DiscordFont.ttf", 16)
                font_bold = ImageFont.truetype("data/DiscordFont.ttf", 28)
            except:
                font_main = ImageFont.load_default()
                font_sub = ImageFont.load_default()
                font_bold = ImageFont.load_default()

            img = Image.new("RGBA", (W, H), (30, 33, 39, 255))
            draw = ImageDraw.Draw(img)

            draw.rectangle([0, 0, 15, H], fill=base_color)

            with io.BytesIO(avatar_bytes) as a_v:
                avatar = Image.open(a_v).convert("RGBA").resize((100, 100))
            mask = Image.new("L", (100, 100), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 100, 100), fill=255)
            draw.ellipse((37, 37, 143, 143), fill=base_color)
            img.paste(avatar, (40, 40), mask)

            draw.text((160, 30), username, "#FFFFFF", font=font_bold)

            categories = [
                ("TOTAL", data.get("Level", 0), data.get("XP", 0)),
                ("TEXT", data.get("TextLevel", 0), data.get("TextXP", 0)),
                ("VOICE", data.get("VoiceLevel", 0), data.get("VoiceXP", 0))
            ]

            start_y = 75
            for label, lv, xp in categories:
                txt = f"{label} Lv.{lv}"
                draw.text((160, start_y), txt, "#FFFFFF", font=font_main)
                
                xp_txt = f"{xp}/{next_xp} XP"
                draw.text((480, start_y + 5), xp_txt, "#AAAAAA", font=font_sub)

                bar_x, bar_y, bar_w, bar_h = 160, start_y + 30, 400, 10
                progress = min(xp / next_xp, 1.0)
                draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=5, fill=(60, 60, 60))
                if progress > 0:
                    draw.rounded_rectangle([bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + bar_h], radius=5, fill=base_color)
                
                start_y += 50

            output = io.BytesIO()
            img.save(output, format="PNG")
            output.seek(0)
            return output

        target_user = interaction.user
        avatar_bytes = await (target_user.avatar or target_user.default_avatar).read()
        
        user_data = await self.get_user_data(interaction.guild.id, target_user.id)
        timing = await self.get_timing(interaction.guild)
        color = await self.get_user_color(target_user)

        executor = ThreadPoolExecutor()
        loop = asyncio.get_running_loop()
        rank_card_file = await loop.run_in_executor(
            executor,
            generate_rank_card,
            color,
            target_user.name,
            avatar_bytes,
            user_data,
            timing
        )

        await interaction.followup.send(file=discord.File(rank_card_file, "rank_card.png"))
        rank_card_file.close()

    @level.command(name="ranking", description="レベルのランキングを表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.describe(カテゴリ="どのランキングを表示するか選択してください")
    @app_commands.choices(カテゴリ=[
        app_commands.Choice(name="総合 (Total)", value="Level"),
        app_commands.Choice(name="テキスト (Text)", value="TextLevel"),
        app_commands.Choice(name="ボイス (Voice)", value="VoiceLevel"),
    ])
    async def level_ranking(self, interaction: discord.Interaction, カテゴリ: str = "Level"):
        await interaction.response.defer()
        
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(embed=make_embed.error_embed(title="レベル機能は無効です。"))

        db = self.bot.async_db["Main"].Leveling
        top_users = await db.find({"Guild": interaction.guild.id}).sort(カテゴリ, -1).limit(10).to_list(length=10)

        if not top_users:
            return await interaction.followup.send("データがありません。")

        title_map = {"Level": "総合", "TextLevel": "テキスト", "VoiceLevel": "ボイス"}
        msg = ""
        for index, ud in enumerate(top_users, start=1):
            member = interaction.guild.get_member(ud["User"])
            name = f"**{member.display_name}**" if member else f"Unknown({ud['User']})"
            
            lv = ud.get(カテゴリ, 0)
            extra = f" (T: {ud.get('TextLevel',0)} / V: {ud.get('VoiceLevel',0)})" if カテゴリ == "Level" else ""
            
            msg += f"{index}. {name} - {lv}レベル{extra}\n"

        embed = make_embed.success_embed(
            title=f"【{title_map.get(カテゴリ)}】サーバーランキング",
            description=msg
        )
        await interaction.followup.send(embed=embed)

    @level.command(name="reset", description="レベルをリセットします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def level_reset(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = self.bot.async_db["Main"].Leveling
        result = await db.delete_many({"Guild": interaction.guild.id})

        await interaction.followup.send(
            content=f"サーバー内の全レベルをリセットしました。"
        )

    @level.command(name="messages", description="レベルのメッセージ設定を表示します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def level_messages(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not await self.check_level_enabled(interaction.guild):
            return await interaction.followup.send(embed=make_embed.error_embed(title="レベル機能は無効です。"))
        
        embed = make_embed.success_embed(title="レベルのメッセージ設定")

        title_map = {"Total": "総合", "Text": "テキスト", "Voice": "ボイス"}
        for k, v in title_map.items():
            message = await self.get_message(interaction.guild.id, k)
            embed.add_field(name=v, value=message, inline=False)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelCog(bot))
