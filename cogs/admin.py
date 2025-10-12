import ast
import datetime
from pathlib import Path
from discord.ext import commands
import discord

from models import make_embed, save_commands, translate

from discord import app_commands

import asyncio

import importlib.util

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AdminCog")

    async def get_admins(self, user: discord.User):
        db = self.bot.async_db["Main"].BotAdmins
        user_data = await db.find_one({"User": user.id})

        if not user_data:
            return False
        else:
            return True

    admin = app_commands.Group(
        name="admin", description="SharkBot管理者向けのコマンドです。"
    )

    @admin.command(name="cogs", description="cogの操作をします。")
    @app_commands.choices(
        操作の種類=[
            app_commands.Choice(name="リロード", value="reload"),
            app_commands.Choice(name="モジュールリロード", value="modulereload"),
            app_commands.Choice(name="ロード", value="load"),
        ]
    )
    async def cogs_setting(
        self,
        interaction: discord.Interaction,
        操作の種類: app_commands.Choice[str],
        cog名: str,
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作の種類.value == "reload":
            await self.bot.reload_extension(f"cogs.{cog名}")
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="Cogをリロードしました。"
                )
            )
        elif 操作の種類.value == "load":
            await self.bot.load_extension(f"cogs.{cog名}")
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="Cogをロードしました。"
                )
            )
        elif 操作の種類.value == "modulereload":
            try:
                mod = importlib.import_module(cog名)
                importlib.reload(mod)
            except Exception as e:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="モジュールリロードに失敗しました。", description=f"```{e}```"
                    )
                )
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="モジュールをリロードしました。"
                )
            )

    @admin.command(
        name="ban", description="Botからbanをします。サーバーからはbanされません。"
    )
    @app_commands.choices(
        操作の種類=[
            app_commands.Choice(name="サーバー", value="server"),
            app_commands.Choice(name="ユーザー", value="user"),
        ]
    )
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def ban_bot(
        self,
        interaction: discord.Interaction,
        操作の種類: app_commands.Choice[str],
        操作: app_commands.Choice[str],
        内容: str,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作の種類.value == "user":
            if 操作.value == "add":
                if int(内容) == 1335428061541437531:
                    return
                user = await self.bot.fetch_user(int(内容))
                db = self.bot.async_db["Main"].BlockUser
                await db.update_one({"User": user.id}, {'$set': {"User": user.id}}, upsert=True)
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"{user.name}をBotからBANしました。"
                    )
                )
            elif 操作.value == "remove":
                user = await self.bot.fetch_user(int(内容))
                db = self.bot.async_db["Main"].BlockUser
                await db.delete_one({"User": user.id})
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"{user.name}のBotからのBanを解除しました。"
                    )
                )
        elif 操作の種類.value == "server":
            if 操作.value == "add":
                db = self.bot.async_db["Main"].BlockGuild
                await db.update_one(
                    {"Guild": int(内容)}, {'$set': {"Guild": int(内容)}}, upsert=True
                )
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"サーバーをBotからBANしました。"
                    )
                )
            elif 操作.value == "remove":
                db = self.bot.async_db["Main"].BlockGuild
                await db.delete_one({"Guild": int(内容)})
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title=f"サーバーのBotからのBanを解除しました。"
                    )
                )

    @admin.command(
        name="server", description="Botの入っているサーバーを管理します。(退出など)"
    )
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="退出", value="leave"),
            app_commands.Choice(name="警告", value="warn"),
            app_commands.Choice(name="情報取得", value="getinfo"),
        ]
    )
    async def manage_server(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        内容: str,
        理由: str = None,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作.value == "leave":
            await self.bot.get_guild(int(内容)).leave()
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="サーバーから退出しました。"
                )
            )
        elif 操作.value == "warn":
            if 理由 is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="警告理由を入力してください。"
                    )
                )

            await self.bot.get_guild(int(内容)).owner.send(
                embed=discord.Embed(
                    title=f"{self.bot.get_guild(int(内容))} はSharkBotから警告されました。",
                    description=f"```{理由}```",
                    color=discord.Color.yellow(),
                ).set_footer(text="詳しくはSharkBot公式サポートサーバーまで。")
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="サーバーを警告しました。"
                )
            )
        elif 操作.value == "getinfo":
            guild = self.bot.get_guild(int(内容))

            embed = make_embed.success_embed(title=f"{guild.name}の情報")
            embed.add_field(name="サーバー名", value=guild.name)
            embed.add_field(name="サーバーID", value=str(guild.id))
            embed.add_field(
                name="チャンネル数", value=f"{len(guild.channels)}個"
            )
            embed.add_field(name="絵文字数", value=f"{len(guild.emojis)}個")
            embed.add_field(name="ロール数", value=f"{len(guild.roles)}個")
            embed.add_field(name="ロールリスト", value="`/listing role`\nで見れます。")
            embed.add_field(name="メンバー数", value=f"{guild.member_count}人")
            embed.add_field(
                name="Nitroブースト",
                value=f"{guild.premium_subscription_count}人",
            )
            embed.add_field(
                name="オーナー名",
                value=self.bot.get_user(guild.owner_id).name
                if self.bot.get_user(guild.owner_id)
                else "取得失敗",
            )
            embed.add_field(name="オーナーID", value=str(guild.owner_id))
            JST = datetime.timezone(datetime.timedelta(hours=9))
            embed.add_field(
                name="作成日", value=guild.created_at.astimezone(JST)
            )

            onlines = [
                m for m in guild.members if m.status == discord.Status.online
            ]
            idles = [
                m for m in guild.members if m.status == discord.Status.idle
            ]
            dnds = [m for m in guild.members if m.status == discord.Status.dnd]
            offlines = [
                m for m in guild.members if m.status == discord.Status.offline
            ]

            pcs = [m for m in guild.members if m.client_status.desktop]
            sms = [m for m in guild.members if m.client_status.mobile]
            webs = [m for m in guild.members if m.client_status.web]

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

            if guild.icon:
                await interaction.followup.send(
                    embed=embed.set_thumbnail(url=guild.icon.url)
                )
            else:
                await interaction.followup.send(embed=embed)

    @admin.command(name="debug", description="デバッグコマンドを実行します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="埋め込み解析", value="embedget"),
            app_commands.Choice(name="頭文字リセット", value="prefixreset"),
            app_commands.Choice(name="デバッグメッセージ", value="debugmsg"),
        ]
    )
    async def debug_admin(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        内容: str,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。"
                ),
            )

        await interaction.response.defer()

        if 操作.value == "embedget":
            msg = await interaction.channel.fetch_message(int(内容))
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="埋め込みを解析しました。",
                    description=f"```{msg.embeds[0].to_dict()}```"
                ),
            )
        elif 操作.value == "prefixreset":
            db = self.bot.async_db["DashboardBot"].CustomPrefixBot
            result = await db.delete_one(
                {
                    "Guild": int(内容),
                }
            )
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="頭文字をリセットしました。"
                ),
            )
        else:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.success_embed(
                    title="デバッグしました。"
                ),
            )

    @admin.command(name="member", description="管理者を追加します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def admins_member(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        ユーザー: discord.User,
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )
        db = self.bot.async_db["Main"].BotAdmins
        if 操作.value == "add":
            await db.update_one(
                {"User": ユーザー.id}, {'$set': {"User": ユーザー.id}}, upsert=True
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="管理者を追加しました。"
                )
            )
        else:
            await db.delete_one({"User": ユーザー.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="管理者を削除しました。"
                )
            )

    @admin.command(name="shutdown", description="シャットダウンします。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="再起動", value="reboot"),
            app_commands.Choice(name="シャットダウン", value="shutdown"),
        ]
    )
    async def admin_shutdown(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str]
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )
        
        if 操作.value == "reboot":

            with open("./reboot", "w") as f:
                f.write("Reboot!")
        else:

            with open("./shutdown", "w") as f:
                f.write("Shutdown!")

        await interaction.response.send_message(embed=discord.Embed(title=f"{操作.name} します。", color=discord.Color.red()))

        if 操作.value == "reboot":

            await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="再起動中!!"))

    @admin.command(name="premium", description="プレミアムユーザーを手動で追加します。")
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="追加", value="add"),
            app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def admin_premium(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        ユーザー: discord.User,
    ):
        if interaction.user.id != 1335428061541437531:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。"
                ),
            )

        db = self.bot.async_db["Main"].PremiumUser
        if 操作.value == "add":
            await db.replace_one(
                {"User": ユーザー.id}, {"User": ユーザー.id}, upsert=True
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="プレミアムユーザーを追加しました。"
                )
            )
        else:
            await db.delete_one({"User": ユーザー.id})
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="プレミアムユーザーを削除しました。"
                )
            )

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        # await guild.leave()
        db = self.bot.async_db["Main"].BlockUser
        try:
            profile = await db.find_one({"User": guild.owner.id}, {"_id": False})
            if profile is None:
                return
            else:
                await guild.leave()
                return
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(
            embed=discord.Embed(
                title=f"{guild.name}に参加しました。",
                description=f"{guild.id}",
                color=discord.Color.green(),
            ).set_thumbnail(url=guild.icon.url if guild.icon else None)
        )

    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_log(self, guild: discord.Guild):
        await self.bot.get_channel(1359793645842206912).send(
            embed=discord.Embed(
                title=f"{guild.name}から退出しました。", color=discord.Color.red()
            ).set_thumbnail(url=guild.icon.url if guild.icon else None)
        )


async def setup(bot):
    await bot.add_cog(AdminCog(bot))
