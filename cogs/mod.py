from discord.ext import commands
import discord
import datetime
from discord import app_commands
from models import command_disable
import asyncio
import re

timeout_pattern = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_time(timestr: str):
    match = timeout_pattern.fullmatch(timestr.strip().lower())
    if not match:
        raise ValueError("時間の形式が正しくありません")

    days, hours, minutes, seconds = match.groups(default="0")
    return datetime.timedelta(
        days=int(days),
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds),
    )


class BanGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="ban", description="Ban系のコマンド。")

    @app_commands.command(name="ban", description="ユーザーをBanをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ban(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="自分自身はBanできません。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.ban(ユーザー, reason=理由)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Banに失敗しました。",
                    description="権限が足りないかも！？",
                    color=discord.Color.red(),
                )
            )
        return await interaction.followup.send(
            embed=discord.Embed(
                title=f"{ユーザー.name}をBanしました。", color=discord.Color.green()
            )
        )

    @app_commands.command(name="softban", description="ユーザーをSoftBanします。")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def softban(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="自分自身はSoftBanできません。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.ban(ユーザー, reason=理由)

            await asyncio.sleep(2)
            await interaction.guild.unban(ユーザー, reason=理由)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="SoftBanに失敗しました。",
                    description="権限が足りないかも！？",
                    color=discord.Color.red(),
                )
            )
        return await interaction.followup.send(
            embed=discord.Embed(
                title=f"{ユーザー.name}をSoftBanしました。", color=discord.Color.green()
            )
        )

    @app_commands.command(name="massban", description="複数ユーザーを一気にbanします。")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def massban(self, interaction: discord.Interaction, ユーザーidたち: str):
        await interaction.response.defer()

        U_ids = []
        for u in ユーザーidたち.split():
            try:
                uid = int(u.replace("<@", "").replace("<@!", "").replace(">", ""))
                U_ids.append(uid)
            except ValueError:
                continue  # 無効なIDをスキップ

        if not U_ids:
            return await interaction.followup.send(
                "有効なユーザーIDが見つかりませんでした。"
            )

        mentions = []
        for uid in U_ids:
            member = interaction.guild.get_member(uid)
            if member:
                mentions.append(f"{member.name} ({member.id})")
            else:
                mentions.append(f"不明なユーザーID: {uid}")

        await interaction.followup.send(
            "以下のユーザーをBANしてもよろしいですか？（Y/n）\n" + "\n".join(mentions)
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=30.0)
            if msg.content.lower() != "y":
                return await interaction.channel.send("キャンセルしました。")
            await msg.add_reaction("✅")
        except asyncio.TimeoutError:
            return await interaction.channel.send("タイムアウトしました。")

        success = 0
        failed = 0
        for uid in U_ids:
            try:
                user = interaction.client.get_user(uid)
                await interaction.guild.ban(
                    user, reason=f"Banned by {interaction.user.name}"
                )
                await asyncio.sleep(1)  # rate limit対策
                success += 1
            except Exception as e:
                failed += 1
                print(f"Failed to ban {uid}: {e}")
                continue

        await interaction.channel.send(f"{success}人をBANしました。失敗: {failed}人。")


class ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ModCog")

    moderation = app_commands.Group(
        name="moderation", description="モデレーション系のコマンドです。"
    )

    moderation.add_command(BanGroup())

    @moderation.command(name="kick", description="メンバーをキックします。")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def kick(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="自分自身はキックできません。", color=discord.Color.red()
                ),
                ephemeral=True,
            )
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーはキックできません。",
                    color=discord.Color.red(),
                )
            )
        await interaction.response.defer()
        try:
            await interaction.guild.kick(ユーザー, reason=理由)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="キックに失敗しました。",
                    description="権限が足りないかも！？",
                    color=discord.Color.red(),
                )
            )
        return await interaction.followup.send(
            embed=discord.Embed(
                title=f"{ユーザー.name}をKickしました。", color=discord.Color.green()
            )
        )

    @moderation.command(name="timeout", description="メンバーをタイムアウトします。")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def timeout(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User,
        時間: str,
        理由: str,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="自分自身はタイムアウトできません。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーはタイムアウトできません。",
                    color=discord.Color.red(),
                )
            )
        await interaction.response.defer()
        try:
            duration = parse_time(時間)
            await interaction.guild.get_member(ユーザー.id).edit(
                timeout=discord.utils.utcnow() + duration, reason=理由
            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="タイムアウトに失敗しました。",
                    description="権限が足りないかも！？",
                    color=discord.Color.red(),
                )
            )
        return await interaction.followup.send(
            embed=discord.Embed(
                title=f"{ユーザー.name}をタイムアウトしました。",
                color=discord.Color.green(),
            )
        )

    @moderation.command(name="max-timeout", description="最大までタイムアウトします。")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def max_timeout(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="自分自身はタイムアウトできません。",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーはタイムアウトできません。",
                    color=discord.Color.red(),
                )
            )
        await interaction.response.defer()
        try:
            await interaction.guild.get_member(ユーザー.id).edit(
                timeout=discord.utils.utcnow() + datetime.datetime(day=28), reason=理由
            )
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="タイムアウトに失敗しました。",
                    description="権限が足りないかも！？",
                    color=discord.Color.red(),
                )
            )
        return await interaction.followup.send(
            embed=discord.Embed(
                title=f"{ユーザー.name}を最大までタイムアウトしました。",
                color=discord.Color.green(),
            )
        )

    @moderation.command(name="clear", description="メッセージを一斉削除します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def clear(self, interaction: discord.Interaction, メッセージ数: int):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)

        now = discord.utils.utcnow()
        two_weeks = datetime.timedelta(days=14)

        def check(msg: discord.Message):
            return (now - msg.created_at) < two_weeks

        deleted = await interaction.channel.purge(limit=メッセージ数, check=check)
        await interaction.followup.send(
            ephemeral=True, content=f"{len(deleted)} 件のメッセージを削除しました"
        )

    @moderation.command(name="warn", description="メンバーを警告します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def warn(
        self, interaction: discord.Interaction, メンバー: discord.User, 理由: str
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer()
        if interaction.guild.get_member(メンバー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーは警告できません。",
                    color=discord.Color.red(),
                )
            )

        await メンバー.send(
            embed=discord.Embed(
                title=f"あなたは`{interaction.guild.name}`\nで警告されました。",
                color=discord.Color.yellow(),
                description=f"理由: {理由}",
            )
        )

        await interaction.followup.send(
            ephemeral=True,
            embed=discord.Embed(title="警告しました。", color=discord.Color.green()),
        )

    @moderation.command(name="remake", description="チャンネルを再生成します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def remake(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ch = await interaction.channel.clone()
        await ch.edit(position=interaction.channel.position + 1)
        await interaction.channel.delete()
        await asyncio.sleep(1)
        await ch.send("<:Success:1362271281302601749> 再生成しました。")

    @moderation.command(name="lock", description="チャンネルをロックします。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def lock(
        self,
        interaction: discord.Interaction,
        スレッド作成可能か: bool = False,
        リアクション可能か: bool = False,
    ):
        await interaction.response.defer()
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        overwrite.create_polls = False
        overwrite.use_application_commands = False
        overwrite.attach_files = False
        if スレッド作成可能か:
            overwrite.create_public_threads = True
            overwrite.create_private_threads = True
        else:
            overwrite.create_public_threads = False
            overwrite.create_private_threads = False
        if リアクション可能か:
            overwrite.add_reactions = True
        else:
            overwrite.add_reactions = False
        await interaction.channel.set_permissions(
            interaction.guild.default_role, overwrite=overwrite
        )
        await interaction.followup.send(content="🔒チャンネルをロックしました。")

    @moderation.command(name="unlock", description="チャンネルを開放します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def unlock(self, interaction: discord.Interaction):
        await interaction.response.defer()
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        overwrite.create_polls = True
        overwrite.use_application_commands = True
        overwrite.attach_files = True
        overwrite.create_public_threads = True
        overwrite.create_private_threads = True
        overwrite.add_reactions = True
        await interaction.channel.set_permissions(
            interaction.guild.default_role, overwrite=overwrite
        )
        await interaction.followup.send(content="🔓チャンネルを開放しました。")

    @moderation.command(
        name="report", description="レポートチャンネルをセットアップします。"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def report_channel(
        self, interaction: discord.Interaction, チャンネル: discord.TextChannel = None
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.defer(ephemeral=True)
        db = self.bot.async_db["Main"].ReportChannel
        if チャンネル:
            await db.replace_one(
                {"Guild": interaction.guild.id},
                {"Guild": interaction.guild.id, "Channel": チャンネル.id},
                upsert=True,
            )
            await interaction.followup.send(
                embed=discord.Embed(
                    title="通報チャンネルをセットアップしました。",
                    color=discord.Color.green(),
                )
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.followup.send(
                embed=discord.Embed(
                    title="通報チャンネルを無効化しました。",
                    color=discord.Color.green(),
                )
            )

    @moderation.command(
        name="serverban",
        description="web認証時に特定のサーバーに参加してる場合に、認証できなくします。",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def server_ban(self, interaction: discord.Interaction, サーバーid: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        db = self.bot.async_db["Main"].GuildBAN
        await db.replace_one(
            {"Guild": str(interaction.guild.id), "BANGuild": サーバーid},
            {"Guild": str(interaction.guild.id), "BANGuild": サーバーid},
            upsert=True,
        )
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="<:Success:1362271281302601749> サーバーをBANしました。",
                color=discord.Color.green(),
            )
        )

    @moderation.command(
        name="serverunban",
        description="web認証時に特定のサーバーに参加してる場合に、認証できなくするのを解除します。",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def server_unban(self, interaction: discord.Interaction, サーバーid: str):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        db = self.bot.async_db["Main"].GuildBAN
        await db.delete_one(
            {"Guild": str(interaction.guild.id), "BANGuild": サーバーid}
        )
        return await interaction.response.send_message(
            embed=discord.Embed(
                title="<:Success:1362271281302601749> サーバーをunBANしました。",
                color=discord.Color.green(),
            )
        )


async def setup(bot):
    await bot.add_cog(ModCog(bot))
