from discord.ext import commands
from discord import app_commands
import discord
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
from concurrent.futures import ThreadPoolExecutor
import random

from consts import settings
from models import command_disable


class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("init -> LevelCog")

    async def check_level_enabled(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        else:
            return True

    async def new_user_write(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id},
                {"Guild": guild.id, "User": user.id, "Level": 0, "XP": 1},
                upsert=True,
            )
        except:
            return

    async def user_write(
        self, guild: discord.Guild, user: discord.User, level: int, xp: int
    ):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id},
                {"Guild": guild.id, "User": user.id, "Level": level, "XP": xp},
                upsert=True,
            )
        except:
            return

    async def get_level(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one(
                    {"Guild": guild.id, "User": user.id}, {"_id": False}
                )
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Level"]
        except:
            return

    async def get_xp(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one(
                    {"Guild": guild.id, "User": user.id}, {"_id": False}
                )
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["XP"]
        except:
            return

    async def set_user_image(self, user: discord.User, url: str):
        try:
            db = self.bot.async_db["Main"].LevelingBackImage
            await db.replace_one(
                {"User": user.id}, {"User": user.id, "Image": url}, upsert=True
            )
        except:
            return

    async def get_user_image(self, user: discord.User):
        try:
            db = self.bot.async_db["Main"].LevelingBackImage
            try:
                dbfind = await db.find_one({"User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Image"]
        except:
            return

    async def set_channel(
        self, guild: discord.Guild, channel: discord.TextChannel = None
    ):
        try:
            if channel == None:
                db = self.bot.async_db["Main"].LevelingUpAlertChannel
                await db.delete_one({"Guild": guild.id})
                return
            db = self.bot.async_db["Main"].LevelingUpAlertChannel
            await db.replace_one(
                {"Guild": guild.id, "Channel": channel.id},
                {"Guild": guild.id, "Channel": channel.id},
                upsert=True,
            )
        except:
            return

    async def get_channel(self, guild: discord.Guild):
        try:
            db = self.bot.async_db["Main"].LevelingUpAlertChannel
            try:
                dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Channel"]
        except:
            return

    async def set_role(
        self,
        guild: discord.Guild,
        level: int,
        role: discord.Role = None,
    ):
        db = self.bot.async_db["Main"].LevelingUpRole
        try:
            if role is None:
                await db.delete_one({"Guild": guild.id})
                return

            await db.replace_one(
                {"Guild": guild.id},
                {"Guild": guild.id, "Role": role.id, "Level": level},
                upsert=True,
            )
        except Exception as e:
            print(f"Error in set_role: {e}")

    async def get_role(self, guild: discord.Guild, level: int):
        db = self.bot.async_db["Main"].LevelingUpRole
        try:
            dbfind = await db.find_one(
                {"Guild": guild.id, "Level": level}, {"_id": False}
            )
            return dbfind["Role"] if dbfind else None
        except Exception:
            return None

    async def get_timing(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingUpTiming
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            return dbfind["Timing"] if dbfind else None
        except Exception:
            return None

    @commands.Cog.listener("on_reaction_add")
    async def on_reaction_add_level(
        self, reaction: discord.Reaction, user: discord.Member
    ):
        if user.bot:
            return
        try:
            enabled = await self.check_level_enabled(user.guild)
        except:
            return
        if enabled:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one(
                    {"Guild": user.guild.id, "User": user.id}, {"_id": False}
                )
            except:
                return
            if dbfind is None:
                return await self.new_user_write(user.guild, user)
            else:
                await self.user_write(
                    user.guild,
                    user,
                    dbfind["Level"],
                    dbfind["XP"] + random.randint(0, 2),
                )
                xp = await self.get_xp(user.guild, user)
                timing = await self.get_timing(user.guild)
                tm = 100
                if timing is not None:
                    tm = timing
                if xp > tm:
                    lv = await self.get_level(user.guild, user)
                    await self.user_write(user.guild, user, lv + 1, 0)
                    lvg = await self.get_level(user.guild, user)
                    cha = await self.get_channel(user.guild)
                    role = await self.get_role(user.guild, lvg)
                    if role:
                        grole = user.guild.get_role(role)
                        if grole:
                            await user.add_roles(grole)
                    try:
                        if cha:
                            await self.bot.get_channel(cha).send(
                                embed=discord.Embed(
                                    title=f"`{user.name}`さんの\nレベルが{lvg}になったよ！",
                                    color=discord.Color.gold(),
                                )
                            )
                        else:
                            return await reaction.message.channel.send(
                                f"レベルが「{lvg}レベル」になったよ！"
                            )
                    except:
                        return
        else:
            return

    @commands.Cog.listener("on_message")
    async def on_message_level(self, message: discord.Message):
        if message.author.bot:
            return
        try:
            enabled = await self.check_level_enabled(message.guild)
        except:
            return
        if enabled:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one(
                    {"Guild": message.guild.id, "User": message.author.id},
                    {"_id": False},
                )
            except:
                return
            if dbfind is None:
                return await self.new_user_write(message.guild, message.author)
            else:
                await self.user_write(
                    message.guild,
                    message.author,
                    dbfind["Level"],
                    dbfind["XP"] + random.randint(0, 2),
                )
                xp = await self.get_xp(message.guild, message.author)
                timing = await self.get_timing(message.guild)
                tm = 100
                if timing is not None:
                    tm = timing
                if xp > tm:
                    lv = await self.get_level(message.guild, message.author)
                    await self.user_write(message.guild, message.author, lv + 1, 0)
                    lvg = await self.get_level(message.guild, message.author)
                    cha = await self.get_channel(message.guild)
                    role = await self.get_role(message.guild, lvg)
                    if role:
                        grole = message.guild.get_role(role)
                        if grole:
                            await message.author.add_roles(grole)
                    try:
                        if cha:
                            await self.bot.get_channel(cha).send(
                                embed=discord.Embed(
                                    title=f"`{message.author.name}`さんの\nレベルが{lvg}になったよ！",
                                    color=discord.Color.gold(),
                                )
                            )
                        else:
                            return await message.reply(
                                f"レベルが「{lvg}レベル」になったよ！"
                            )
                    except:
                        return
        else:
            return

    level = app_commands.Group(name="level", description="レベル系のコマンドです。")

    @level.command(name="setting", description="レベルを有効化&無効化します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_setting(self, interaction: discord.Interaction, 有効か: bool):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        db = self.bot.async_db["Main"].LevelingSetting
        if 有効か:
            await db.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id},
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

    @level.command(name="show", description="レベルを確認します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_show(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return
        if interaction.user.avatar:
            avatar = interaction.user.avatar.url
        else:
            avatar = interaction.user.default_avatar.url
        if enabled:
            lv = await self.get_level(interaction.guild, interaction.user)
            if lv == None:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"`{interaction.user.name}`のレベル",
                        description="レベル: 「0レベル」\nXP: 「0XP」",
                        color=discord.Color.blue(),
                    ).set_thumbnail(url=avatar)
                )
            xp = await self.get_xp(interaction.guild, interaction.user)
            if xp == None:
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"`{interaction.user.name}`のレベル",
                        description="レベル: 「0レベル」\nXP: 「0XP」",
                        color=discord.Color.blue(),
                    ).set_thumbnail(url=avatar)
                )
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"`{interaction.user.name}`のレベル",
                    description=f"レベル: 「{lv}レベル」\nXP: 「{xp}XP」",
                    color=discord.Color.blue(),
                ).set_thumbnail(url=avatar)
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )

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

    @level.command(name="card", description="レベルカードを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_card(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if not enabled:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        await interaction.response.defer()

        def generate_rank_card(
            color, username: str, gu_a: bytes, avatar_bytes: bytes, level: int, xp: int
        ) -> io.BytesIO:
            try:
                font = ImageFont.truetype("data/DiscordFont.ttf", 20)
            except:
                font = ImageFont.load_default()

            img = Image.new("RGBA", (500, 150), color)
            draw = ImageDraw.Draw(img)

            draw.text((120, 20), username, "#000000", font=font)
            draw.text((120, 50), f"レベル: {level}", "#000000", font=font)
            draw.text((120, 80), f"XP: {xp}", "#000000", font=font)
            draw.text((150, 110), f"{interaction.guild.name}", "#000000", font=font)

            avatar = (
                Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((100, 100))
            )

            mask = Image.new("L", (100, 100), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 100, 100), fill=255)

            mask_guild = Image.new("L", (20, 20), 0)
            mask_guild_draw = ImageDraw.Draw(mask_guild)
            mask_guild_draw.ellipse((0, 0, 20, 20), fill=255)

            img.paste(avatar, (10, 25), mask)

            g_a = Image.open(io.BytesIO(gu_a)).convert("RGBA").resize((20, 20))

            img.paste(g_a, (120, 115), mask_guild)

            output = io.BytesIO()
            img.save(output, format="PNG")
            output.seek(0)
            return output

        executor = ThreadPoolExecutor()

        target_user = interaction.user
        avatar_bytes = (
            await target_user.avatar.read()
            if target_user.avatar
            else await target_user.default_avatar.read()
        )
        guild_bytes = (
            await interaction.guild.icon.read()
            if interaction.guild.icon
            else await target_user.default_avatar.read()
        )
        level = await self.get_level(interaction.guild, target_user)
        xp = await self.get_xp(interaction.guild, target_user)

        color = await self.get_user_color(target_user)

        rank_card_file = await asyncio.get_running_loop().run_in_executor(
            executor,
            generate_rank_card,
            color,
            interaction.user.name + f"#{interaction.user.discriminator}",
            guild_bytes,
            avatar_bytes,
            level,
            xp,
        )

        await interaction.followup.send(
            file=discord.File(rank_card_file, "rank_card.png"),
            view=discord.ui.View().add_item(
                discord.ui.Button(
                    label="ランクカードを編集",
                    url=f"{settings.DASHBOARD_DOMEIN}/rankcard",
                    emoji="✨",
                )
            ),
        )
        rank_card_file.close()

    @level.command(
        name="channel", description="レベルアップの通知のチャンネルを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def level_channel(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return
        if enabled:
            if チャンネル:
                await self.set_channel(interaction.guild, チャンネル)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="レベルアップの通知チャンネルを設定しました。",
                        color=discord.Color.green(),
                    )
                )
            else:
                await self.set_channel(interaction.guild)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="レベルアップの通知チャンネルを削除しました。",
                        color=discord.Color.green(),
                    )
                )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )

    @level.command(
        name="role", description="レベルアップ時に付与するロールを指定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_roles=True)
    async def level_role(
        self, interaction: discord.Interaction, レベル: int, ロール: discord.Role = None
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        if enabled:
            if not ロール:
                await self.set_role(interaction.guild, レベル)
                return await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{レベル}レベルになってもロールをもらえなくしました。",
                        color=discord.Color.green(),
                    )
                )
            await self.set_role(interaction.guild, レベル, ロール)
            return await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{レベル}レベルになるとロールを付与するようにしました。",
                    color=discord.Color.green(),
                )
            )
        else:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )

    @level.command(name="edit", description="レベルを編集します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def level_edit(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User,
        レベル: int,
        xp: int,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        if not enabled:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        await self.user_write(interaction.guild, ユーザー, レベル, xp)
        return await interaction.followup.send(
            embed=discord.Embed(
                title="レベルを編集しました。",
                description=f"ユーザー: 「{ユーザー.name}」\nレベル: 「{レベル}レベル」\nXP: 「{xp}XP」",
                color=discord.Color.green(),
            )
        )

    @level.command(
        name="timing", description="レベルアップするタイミングを設定します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_channels=True)
    async def level_timing(self, interaction: discord.Interaction, xp: int):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        if not enabled:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        if xp < 21:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルアップするタイミングは20以上でお願いします。",
                    color=discord.Color.green(),
                )
            )
        db = self.bot.async_db["Main"].LevelingUpTiming
        await db.replace_one(
            {"Guild": interaction.guild.id},
            {"Guild": interaction.guild.id, "Timing": xp},
            upsert=True,
        )
        return await interaction.followup.send(
            embed=discord.Embed(
                title="レベルアップするタイミングを設定しました。",
                color=discord.Color.green(),
                description=f"タイミング: {xp}XP",
            )
        )

    @level.command(
        name="rewards", description="レベルアップ時のご褒美をリスト化します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_rewards(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        if not enabled:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        db = self.bot.async_db["Main"].LevelingUpRole
        roles_cursor = db.find({"Guild": interaction.guild.id})
        roles_list = await roles_cursor.to_list(length=None)

        description_lines = []
        for r in roles_list:
            role_id = r.get("Role", 0)
            role = interaction.guild.get_role(role_id)
            role_name = role.name if role else "不明なロール"
            description_lines.append(f"{r.get('Level', '?')}. {role_name}")

        await interaction.followup.send(
            embed=discord.Embed(
                title="レベルアップ時のご褒美リスト", color=discord.Color.yellow()
            ).add_field(name="ご褒美ロール", value="\n".join(description_lines))
        )

    @level.command(name="ranking", description="レベルのランキングを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def level_ranking(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        try:
            enabled = await self.check_level_enabled(interaction.guild)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        if not enabled:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="レベルは無効です。", color=discord.Color.red()
                )
            )
        db = self.bot.async_db["Main"].Leveling
        top_users = (
            await db.find({"Guild": interaction.guild.id})
            .sort("Level", -1)
            .limit(5)
            .to_list(length=5)
        )
        msg = ""
        for index, user_data in enumerate(top_users, start=1):
            member = self.bot.get_user(user_data["User"])
            username = (
                f"{member.display_name}" if member else f"Unknown ({user_data['User']})"
            )
            msg += f"{index}.**{username}** - {user_data['Level']}レベル\n"
        return await interaction.followup.send(
            embed=discord.Embed(
                title="このサーバーでのランキング",
                description=msg,
                color=discord.Color.yellow(),
            )
        )

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

async def setup(bot):
    await bot.add_cog(LevelCog(bot))
