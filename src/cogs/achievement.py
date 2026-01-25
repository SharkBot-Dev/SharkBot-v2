import aiohttp
import discord
from discord.ext import commands

from discord import app_commands
import asyncio


class AchievementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def check_achi_enabled(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].AchievementsSettings
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except Exception:
            return False
        return dbfind is not None

    async def get_is_achi(self, member: discord.Member, name: str):
        db = self.bot.async_db["Main"].AchievementsAchi
        try:
            dbfind = await db.find_one(
                {"User": member.id, "Guild": member.guild.id, "Name": name},
                {"_id": False},
            )
        except:
            return False
        if dbfind is None:
            return False
        return True

    async def send_channel(self, message: discord.Message, achi):
        settings_db = self.bot.async_db["Main"].AchievementsChannel
        settings = await settings_db.find_one({"Guild": message.guild.id})
        notify_channel = (
            message.guild.get_channel(settings.get("Channel")) if settings else None
        )
        if notify_channel is None:
            notify_channel = message.channel

        try:
            await notify_channel.send(
                f"{message.author.mention} が実績「{achi.get('Name')}」を達成しました。"
            )
        except Exception:
            pass

    async def send_reaction_channel(
        self, message: discord.Message, user: discord.User, achi
    ):
        settings_db = self.bot.async_db["Main"].AchievementsChannel
        settings = await settings_db.find_one({"Guild": message.guild.id})
        notify_channel = (
            message.guild.get_channel(settings.get("Channel")) if settings else None
        )
        if notify_channel is None:
            notify_channel = message.channel

        try:
            await notify_channel.send(
                f"{user.mention} が実績「{achi.get('Name')}」を達成しました。"
            )
        except Exception:
            pass

    @commands.Cog.listener("on_message")
    async def on_message_say(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if not await self.check_achi_enabled(message.guild):
            return

        db = self.bot.async_db["Main"].AchievementsSay
        user_data = await db.find_one(
            {"Guild": message.guild.id, "User": message.author.id}
        )

        if user_data:
            new_count = user_data.get("count", 0) + 1
            await db.update_one(
                {"Guild": message.guild.id, "User": message.author.id},
                {"$set": {"count": new_count}},
            )
        else:
            new_count = 1
            await db.insert_one(
                {
                    "Guild": message.guild.id,
                    "User": message.author.id,
                    "count": new_count,
                }
            )

        achi_db = self.bot.async_db["Main"].Achievements
        async for achi in achi_db.find({"Guild": message.guild.id, "If": "say"}):
            if new_count >= achi.get("Value", 0):
                already = await self.get_is_achi(message.author, achi.get("Name"))
                if not already:
                    await self.bot.async_db["Main"].AchievementsAchi.insert_one(
                        {
                            "User": message.author.id,
                            "Guild": message.guild.id,
                            "Name": achi.get("Name"),
                        }
                    )

                    if achi.get("Role", 0) != 0:
                        role = message.guild.get_role(achi.get("Role", 0))
                        if role != None:
                            await message.author.add_roles(role)

                    try:
                        await self.send_channel(message, achi)
                    except:
                        pass

                await asyncio.sleep(1)
        return True

    @commands.Cog.listener("on_reaction_add")
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot or not reaction.message.guild:
            return

        guild = reaction.message.guild
        if not await self.check_achi_enabled(guild):
            return

        db = self.bot.async_db["Main"].AchievementsReact
        user_data = await db.find_one({"Guild": guild.id, "User": user.id})

        if user_data:
            new_count = user_data.get("count", 0) + 1
            await db.update_one(
                {"Guild": guild.id, "User": user.id}, {"$set": {"count": new_count}}
            )
        else:
            new_count = 1
            await db.insert_one(
                {"Guild": guild.id, "User": user.id, "count": new_count}
            )

        achi_db = self.bot.async_db["Main"].Achievements
        async for achi in achi_db.find({"Guild": guild.id, "If": "react"}):
            if new_count >= achi.get("Value", 0):
                already = await self.get_is_achi(user, achi.get("Name"))
                if not already:
                    await self.bot.async_db["Main"].AchievementsAchi.insert_one(
                        {"User": user.id, "Guild": guild.id, "Name": achi.get("Name")}
                    )

                    if achi.get("Role", 0) != 0:
                        role = reaction.message.guild.get_role(achi.get("Role", 0))
                        if role != None:
                            await reaction.message.guild.get_member(user.id).add_roles(
                                role
                            )

                    try:
                        await self.send_reaction_channel(reaction.message, user, achi)
                    except:
                        pass

                    await asyncio.sleep(1)

    achievement = app_commands.Group(
        name="achievement", description="実績関連のコマンドです。"
    )

    @achievement.command(name="setting", description="実績を有効化&無効化します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def achievement_setting(self, interaction: discord.Interaction, 有効か: bool):
        db = self.bot.async_db["Main"].AchievementsSettings
        if 有効か:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                ephemeral=True, content="実績を有効化しました。"
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                ephemeral=True, content="実績を無効化しました。"
            )

    @achievement.command(name="create", description="実績を作成します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        をする=[
            # app_commands.Choice(name="レベルになると", value="level"),
            app_commands.Choice(name="回話すと", value="say"),
            app_commands.Choice(name="回リアクションすると", value="react"),
        ]
    )
    async def achievement_create(
        self,
        interaction: discord.Interaction,
        実績名: str,
        値: int,
        をする: app_commands.Choice[str],
        ロール: discord.Role = None,
    ):
        if not await self.check_achi_enabled(interaction.guild):
            return await interaction.response.send_message(
                embed=discord.Embed(title="実績は無効です。", color=discord.Color.red())
            )

        db = self.bot.async_db["Main"].Achievements
        await db.update_one(
            {"Guild": interaction.guild.id, "Name": 実績名},
            {
                "$set": {
                    "Guild": interaction.guild.id,
                    "Name": 実績名,
                    "Value": 値,
                    "If": をする.value,
                    "Role": ロール.id if ロール else 0,
                }
            },
            upsert=True,
        )
        await interaction.response.send_message(
            content=f"{値}{をする.name}と、「{実績名}」が入手できるようにしました。",
            ephemeral=True,
        )

    @achievement.command(name="delete", description="実績を削除します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def achievement_delete(self, interaction: discord.Interaction, 実績名: str):
        if not await self.check_achi_enabled(interaction.guild):
            return await interaction.response.send_message(
                embed=discord.Embed(title="実績は無効です。", color=discord.Color.red())
            )

        db = self.bot.async_db["Main"].Achievements
        result = await db.delete_one({"Guild": interaction.guild.id, "Name": 実績名})
        if result.deleted_count == 0:
            await interaction.response.send_message(
                content=f"何も削除されませんでした。", ephemeral=True
            )
        await interaction.response.send_message(
            content=f"{実績名}を削除しました。", ephemeral=True
        )

    @achievement.command(
        name="channel", description="実績達成通知を送るチャンネルを設定します。"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def achievement_channel(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None
    ):
        if not await self.check_achi_enabled(interaction.guild):
            return await interaction.response.send_message(
                embed=discord.Embed(title="実績は無効です。", color=discord.Color.red())
            )

        db = self.bot.async_db["Main"].AchievementsChannel
        if チャンネル:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id, "Channel": チャンネル.id}},
                upsert=True,
            )
            await interaction.response.send_message(
                f"実績達成通知チャンネルを {チャンネル.mention} に設定しました。",
                ephemeral=True,
            )
        else:
            result = await db.delete_one({"Guild": interaction.guild.id})
            await interaction.response.send_message(
                f"実績達成通知チャンネルを無効化しました。", ephemeral=True
            )

    @achievement.command(name="reset", description="実績をリセットします。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def achievement_reset(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = self.bot.async_db["Main"].AchievementsSay
        result = await db.delete_many({"Guild": interaction.guild.id})

        db = self.bot.async_db["Main"].AchievementsReact
        result = await db.delete_many({"Guild": interaction.guild.id})

        db = self.bot.async_db["Main"].AchievementsAchi
        result = await db.delete_many({"Guild": interaction.guild.id})

        await interaction.followup.send(
            content=f"サーバー内の全実績をリセットしました。", ephemeral=True
        )

    @achievement.command(
        name="show", description="達成した・達成可能な実績一覧を表示します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def achievement_show(
        self, interaction: discord.Interaction, メンバー: discord.User = None
    ):
        await interaction.response.defer()
        if not await self.check_achi_enabled(interaction.guild):
            return await interaction.followup.send(
                embed=discord.Embed(title="実績は無効です。", color=discord.Color.red())
            )

        メンバー = (
            interaction.guild.get_member(メンバー.id) if メンバー else interaction.user
        )
        a_cs = ""
        db = self.bot.async_db["Main"].Achievements
        async for b in db.find({"Guild": interaction.guild.id}):
            achi = await self.get_is_achi(メンバー, b.get("Name", None))
            if achi:
                a_cs += f"{b.get('Name')} - 達成しました。\n"
                continue
            if b.get("If") == "level":
                a_cs += (
                    f"{b.get('Name')} - {b.get('Value', 0)}レベルになると達成できる\n"
                )
            elif b.get("If") == "say":
                a_cs += f"{b.get('Name')} - {b.get('Value', 0)}回話すと達成できる\n"
            elif b.get("If") == "react":
                a_cs += f"{b.get('Name')} - {b.get('Value', 0)}回リアクションすると達成できる\n"
        await interaction.followup.send(
            embed=discord.Embed(
                title="実績リスト", description=a_cs, color=discord.Color.gold()
            )
        )
        return


async def setup(bot):
    await bot.add_cog(AchievementCog(bot))
