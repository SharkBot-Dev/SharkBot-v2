from discord.ext import commands
import discord

from models import save_commands

from discord import app_commands


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
                embed=discord.Embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。",
                    color=discord.Color.red(),
                ),
            )

        await interaction.response.defer()

        if 操作の種類.value == "reload":
            await self.bot.reload_extension(f"cogs.{cog名}")
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Cogをリロードしました。", color=discord.Color.green()
                )
            )
        elif 操作の種類.value == "load":
            await self.bot.load_extension(f"cogs.{cog名}")
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Cogをロードしました。", color=discord.Color.green()
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
                embed=discord.Embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。",
                    color=discord.Color.red(),
                ),
            )

        await interaction.response.defer()

        if 操作の種類.value == "user":
            if 操作.value == "add":
                if int(内容) == 1335428061541437531:
                    return
                user = await self.bot.fetch_user(int(内容))
                db = self.bot.async_db["Main"].BlockUser
                await db.replace_one({"User": user.id}, {"User": user.id}, upsert=True)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{user.name}をBotからBANしました。",
                        color=discord.Color.green(),
                    )
                )
            elif 操作.value == "remove":
                user = await self.bot.fetch_user(int(内容))
                db = self.bot.async_db["Main"].BlockUser
                await db.delete_one({"User": user.id})
                await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"{user.name}のBotからのBanを解除しました。",
                        color=discord.Color.red(),
                    )
                )
        elif 操作の種類.value == "server":
            if 操作.value == "add":
                db = self.bot.async_db["Main"].BlockGuild
                await db.replace_one(
                    {"Guild": int(内容)}, {"Guild": int(内容)}, upsert=True
                )
                await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"サーバーをBotからBANしました。",
                        color=discord.Color.green(),
                    )
                )
            elif 操作.value == "remove":
                db = self.bot.async_db["Main"].BlockUser
                await db.delete_one({"Guild": int(内容)})
                await interaction.followup.send(
                    embed=discord.Embed(
                        title=f"サーバーのBotからのBanを解除しました。",
                        color=discord.Color.red(),
                    )
                )

    @admin.command(
        name="server", description="Botの入っているサーバーを管理します。(退出など)"
    )
    @app_commands.choices(
        操作=[
            app_commands.Choice(name="退出", value="leave"),
            app_commands.Choice(name="警告", value="warn"),
        ]
    )
    async def manage_server(
        self,
        interaction: discord.Interaction,
        操作: app_commands.Choice[str],
        内容: str,
        理由: str,
    ):
        isadmin = await self.get_admins(interaction.user)

        if not isadmin:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。",
                    color=discord.Color.red(),
                ),
            )

        await interaction.response.defer()

        if 操作.value == "leave":
            await self.bot.get_guild(int(内容)).leave()
            await interaction.followup.send(
                embed=discord.Embed(
                    title="サーバーから退出しました。", color=discord.Color.green()
                )
            )
        elif 操作.value == "warn":
            await self.bot.get_guild(int(内容)).owner.send(
                embed=discord.Embed(
                    title=f"{self.bot.get_guild(int(内容))} はSharkBotから警告されました。",
                    description=f"```{理由}```",
                    color=discord.Color.yellow(),
                ).set_footer(text="詳しくはSharkBot公式サポートサーバーまで。")
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="サーバーを警告しました。", color=discord.Color.green()
                )
            )

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
                embed=discord.Embed(
                    title="あなたはSharkBotの管理者ではないため実行できません。",
                    color=discord.Color.red(),
                ),
            )

        await interaction.response.defer()

        if 操作.value == "embedget":
            msg = await interaction.channel.fetch_message(int(内容))
            await interaction.followup.send(
                ephemeral=True,
                embed=discord.Embed(
                    title="埋め込みを解析しました。",
                    description=f"```{msg.embeds[0].to_dict()}```",
                    color=discord.Color.green(),
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
                embed=discord.Embed(
                    title="頭文字をリセットしました。", color=discord.Color.green()
                ),
            )
        else:
            await interaction.followup.send(
                ephemeral=True,
                embed=discord.Embed(
                    title="デバッグしました。", color=discord.Color.green()
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
                embed=discord.Embed(
                    title="あなたはSharkBotのオーナーではないため実行できません。",
                    color=discord.Color.red(),
                ),
            )
        db = self.bot.async_db["Main"].BotAdmins
        if 操作.value == "add":
            await db.replace_one(
                {"User": ユーザー.id}, {"User": ユーザー.id}, upsert=True
            )
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="管理者を追加しました。", color=discord.Color.green()
                )
            )
        else:
            await db.delete_one({"User": ユーザー.id})
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="管理者を削除しました。", color=discord.Color.green()
                )
            )

    @commands.command(name="reload", aliases=["r"], hidden=True)
    async def reload(self, ctx: commands.Context, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")

    @commands.command(name="sync_slash", aliases=["sy"], hidden=True)
    async def sync_slash(self, ctx: commands.Context):
        if ctx.author.id == 1335428061541437531:
            await self.bot.tree.sync()
            await ctx.reply("スラッシュコマンドを同期しました。")

    @commands.command(name="load", hidden=True)
    async def load_admin(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.load_extension(f"cogs.{cogname}")
            await ctx.reply(f"LoadOK .. `cogs.{cogname}`")

    @commands.command(name="save", hidden=True)
    async def save(self, ctx):
        if ctx.author.id == 1335428061541437531:
            await save_commands.clear_commands()

            count = 0
            for cmd in self.bot.tree.get_commands():
                await save_commands.save_command(cmd)
                count += 1

            for g in self.bot.guilds:
                await self.bot.async_db["DashboardBot"].bot_joind_guild.replace_one(
                    {"Guild": g.id}, {"Guild": g.id}, upsert=True
                )

            await ctx.reply(f"コマンドをセーブしました。\n{count}件。")

    @commands.command(name="ban_user", hidden=True)
    async def banuser(self, ctx, user: discord.User):
        if (
            self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles
        ):
            if user.id == 1335428061541437531:
                return
            db = self.bot.async_db["Main"].BlockUser
            await db.replace_one({"User": user.id}, {"User": user.id}, upsert=True)
            await ctx.reply(
                embed=discord.Embed(
                    title=f"{user.name}をBotからBANしました。",
                    color=discord.Color.red(),
                )
            )

    @commands.command(name="unban_user", hidden=True)
    async def unban_user(self, ctx, user: discord.User):
        if (
            self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles
        ):
            if user.id == 1335428061541437531:
                return
            db = self.bot.async_db["Main"].BlockUser
            await db.delete_one({"User": user.id})
            await ctx.reply(
                embed=discord.Embed(
                    title=f"{user.name}のBotからのBANを解除しました。",
                    color=discord.Color.red(),
                )
            )

    @commands.command(name="ban_guild", hidden=True)
    async def ban_guild(self, ctx, guild: discord.Guild):
        if (
            self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles
        ):
            db = self.bot.async_db["Main"].BlockGuild
            await db.replace_one({"Guild": guild.id}, {"Guild": guild.id}, upsert=True)
            await ctx.reply(
                embed=discord.Embed(
                    title=f"{guild.name}をBotからBANしました。",
                    color=discord.Color.red(),
                )
            )

    @commands.command(name="unban_guild", hidden=True)
    async def unban_guild(self, ctx, guild: discord.Guild):
        if (
            self.bot.get_guild(1343124570131009579).get_role(1344470846995169310)
            in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles
        ):
            db = self.bot.async_db["Main"].BlockGuild
            await db.delete_one({"Guild": guild.id})
            await ctx.reply(
                embed=discord.Embed(
                    title=f"{guild.name}のBotからのBANを解除しました。",
                    color=discord.Color.red(),
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
