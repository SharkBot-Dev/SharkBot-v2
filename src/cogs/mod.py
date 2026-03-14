import io
import random
import aiohttp
from discord.ext import commands
import discord
import datetime
from discord import app_commands
from models import command_disable, make_embed
import asyncio
import re

timeout_pattern = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")
PASTEBIN_RE = re.compile(r"https?://(?:www\.)?pastebin\.com/(?:raw/)?([a-zA-Z0-9]+)")
SERVER_ID_RE = re.compile(r"\d{17,20}")

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

async def resolve_server_ids(input_str):
    paste_match = PASTEBIN_RE.search(input_str)
    
    if paste_match:
        paste_id = paste_match.group(1)
        raw_url = f"https://pastebin.com/raw/{paste_id}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(raw_url) as response:
                    if response.status == 200:
                        text = await response.text()
                        return SERVER_ID_RE.findall(text)
                    else:
                        return []
            except Exception as e:
                return []

    else:
        return SERVER_ID_RE.findall(input_str)

class PauseGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="pause", description="セキュリティ処置用のコマンド")

    @app_commands.command(
        name="invite", description="サーバー招待の一時停止状態を切り替えます"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def pause_invite(
        self, interaction: discord.Interaction, 一時停止するか: bool, 時間: str = None
    ):
        await interaction.response.defer()
        if 一時停止するか:
            if not 時間:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="時間を指定する必要があります。",
                        description="指定方法の例: `1d3h5m`",
                    )
                )
            try:
                time = parse_time(時間)
            except ValueError:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="正しい時間を指定する必要があります。",
                        description="指定方法の例: `1d3h5m`",
                    )
                )
            try:
                await interaction.guild.edit(
                    reason="招待停止コマンド実行のため。",
                    invites_disabled_until=discord.utils.utcnow() + time,
                )
            except:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="サーバー招待を停止できませんでした。",
                        description="権限を確認、または最大停止時間を超えていないかを確認してください。\n\nちなみに、最大1日まで停止できます。",
                    )
                )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="サーバー招待を停止しました。")
            )
        else:
            await interaction.guild.edit(
                reason="招待停止解除コマンド実行のため。", invites_disabled_until=None
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="サーバー招待を再開しました。")
            )

    @app_commands.command(
        name="dm", description="このサーバーからのDMの一時停止状態を切り替えます"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def pause_dm(
        self, interaction: discord.Interaction, 一時停止するか: bool, 時間: str = None
    ):
        await interaction.response.defer()
        if 一時停止するか:
            if not 時間:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="時間を指定する必要があります。",
                        description="指定方法の例: `1d3h5m`",
                    )
                )
            try:
                time = parse_time(時間)
            except ValueError:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="正しい時間を指定する必要があります。",
                        description="指定方法の例: `1d3h5m`",
                    )
                )
            try:
                await interaction.guild.edit(
                    reason="DM停止コマンド実行のため。",
                    dms_disabled_until=discord.utils.utcnow() + time,
                )
            except Exception as e:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="DMを停止できませんでした。",
                        description=f"権限を確認、または最大停止時間を超えていないかを確認してください。\n\nちなみに、最大1日まで停止できます。",
                    )
                )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="DMを停止しました。")
            )
        else:
            await interaction.guild.edit(
                reason="DM停止コマンド実行のため。", dms_disabled_until=None
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="DMを再開しました。")
            )

    @app_commands.command(
        name="both", description="このサーバーの招待リンクとDM、どちらも停止します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def pause_both(
        self, interaction: discord.Interaction, 一時停止するか: bool, 時間: str = None
    ):
        await interaction.response.defer()
        if 一時停止するか:
            if not 時間:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="時間を指定する必要があります。",
                        description="指定方法の例: `1d3h5m`",
                    )
                )
            try:
                time = parse_time(時間)
            except ValueError:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="正しい時間を指定する必要があります。",
                        description="指定方法の例: `1d3h5m`",
                    )
                )
            try:
                await interaction.guild.edit(
                    reason="Dmと正体リンク停止コマンド実行のため。",
                    dms_disabled_until=discord.utils.utcnow() + time,
                    invites_disabled=discord.utils.utcnow() + time,
                )
            except Exception as e:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="どちらも停止できませんでした。",
                        description=f"権限を確認、または最大停止時間を超えていないかを確認してください。\n\nちなみに、最大1日まで停止できます。",
                    )
                )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="DMとサーバー招待を停止しました。")
            )
        else:
            await interaction.guild.edit(
                reason="Dmと正体リンク停止コマンド実行のため。",
                dms_disabled_until=None,
                invites_disabled=None,
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(title="DMとサーバー招待を再開しました。")
            )


class MuteGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="mute", description="ミュート系のコマンド")

    @app_commands.command(name="add", description="メンバーをミュートします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def muterole_add(
        self,
        interaction: discord.Interaction,
        メンバー: discord.User,
        理由: str = "なし",
    ):
        await interaction.response.defer()
        db = interaction.client.async_db["MainTwo"].MuteRole
        finded = await db.find_one({"guild_id": interaction.guild.id})

        if not finded:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ミュートロールがありません。",
                    description="/moderation mute create を実行してください。",
                )
            )

        member = interaction.guild.get_member(メンバー.id)
        if not member:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="メンバーが見つかりません。",
                    description="サーバーメンバーにのみ使用できます。",
                )
            )

        role = interaction.guild.get_role(finded.get("role_id"))
        if not role:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ミュートロールがありません。",
                    description="/moderation mute create を実行してください。",
                )
            )

        await member.add_roles(role, reason=f"{interaction.user.id}により実行: " + 理由)

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ミュートしました。",
                description=メンバー.mention + "をミュートしました。",
            )
        )

    @app_commands.command(name="remove", description="メンバーのミュートを解除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def muterole_remove(
        self,
        interaction: discord.Interaction,
        メンバー: discord.User,
        理由: str = "なし",
    ):
        await interaction.response.defer()
        db = interaction.client.async_db["MainTwo"].MuteRole
        finded = await db.find_one({"guild_id": interaction.guild.id})

        if not finded:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ミュートロールがありません。",
                    description="/moderation mute create を実行してください。",
                )
            )

        member = interaction.guild.get_member(メンバー.id)
        if not member:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="メンバーが見つかりません。",
                    description="サーバーメンバーにのみ使用できます。",
                )
            )

        role = interaction.guild.get_role(finded.get("role_id"))
        if not role:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ミュートロールがありません。",
                    description="/moderation mute create を実行してください。",
                )
            )

        await member.remove_roles(
            role, reason=f"{interaction.user.id}により実行: " + 理由
        )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ミュートを解除しました。",
                description=メンバー.mention + "のミュートを解除しました。",
            )
        )

    @app_commands.command(name="update", description="ミュートロールを更新します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_roles=True, manage_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def muterole_update(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = interaction.client.async_db["MainTwo"].MuteRole
        finded = await db.find_one({"guild_id": interaction.guild.id})

        if not finded:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ミュートロールがありません。",
                    description="/moderation mute create を実行してください。",
                )
            )

        role = interaction.guild.get_role(finded.get("role_id"))
        if not role:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ミュートロールがありません。",
                    description="/moderation mute create を実行してください。",
                )
            )

        guild = interaction.guild

        ch_count = 0

        for channel in guild.channels:
            if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                continue

            try:
                await channel.set_permissions(
                    role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False,
                    reason="ミュートロールの更新のため",
                )
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                pass

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ミュートロールを更新しました。",
                description=f"{ch_count} 個のチャンネルを更新しました。",
            )
        )

    @app_commands.command(name="create", description="ミュートロールを作成します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(manage_roles=True, manage_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def muterole_create(
        self, interaction: discord.Interaction, ロール名: str = "ミュート済み"
    ):
        await interaction.response.defer()

        mute_role = await interaction.guild.create_role(
            name=ロール名,
            reason="ミュートロールの作成のため",
            colour=discord.Color.dark_red(),
        )

        guild = interaction.guild

        for channel in guild.channels:
            if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                continue

            try:
                await channel.set_permissions(
                    mute_role,
                    send_messages=False,
                    speak=False,
                    add_reactions=False,
                    reason="ミュートロールの作成のため",
                )
            except discord.Forbidden:
                pass
            except discord.HTTPException as e:
                pass

        await interaction.client.async_db["MainTwo"].MuteRole.update_one(
            {"guild_id": guild.id},
            {
                "$set": {
                    "role_id": mute_role.id,
                    "created_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ミュートロールを作成しました。", description=mute_role.mention
            )
        )

class ModCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ModCog")

    moderation = app_commands.Group(
        name="moderation", description="モデレーション系のコマンドです。"
    )

    moderation.add_command(MuteGroup())
    moderation.add_command(PauseGroup())

    @app_commands.command(name="kick", description="メンバーをキックします。")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def top_kick(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str = None
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身はキックできません。"),
                ephemeral=True,
            )
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="このサーバーにいないメンバーはキックできません。"
                )
            )
        await interaction.response.defer()
        try:
            await interaction.guild.kick(
                ユーザー,
                reason=理由
                if 理由
                else "なし" + f"\n{interaction.user.id} によってKick",
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="キックに失敗しました。", description="権限が足りないかも！？"
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{ユーザー.name}をKickしました。",
                description=f"理由: {理由 if 理由 else 'なし'}"
                + f"\n{interaction.user.id} によってKick",
            )
        )

    @moderation.command(name="kick", description="メンバーをキックします。")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def kick(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str = None
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身はキックできません。"),
                ephemeral=True,
            )
        if interaction.guild.get_member(ユーザー.id) is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="このサーバーにいないメンバーはキックできません。"
                )
            )
        await interaction.response.defer()
        try:
            await interaction.guild.kick(
                ユーザー,
                reason=理由
                if 理由
                else "なし" + f"\n{interaction.user.id} によってKick",
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="キックに失敗しました。", description="権限が足りないかも！？"
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{ユーザー.name}をKickしました。",
                description=f"理由: {理由 if 理由 else 'なし'}"
                + f"\n{interaction.user.id} によってKick",
            )
        )
    
    @app_commands.command(name="ban", description="ユーザーをBanをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def top_ban(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身はBanできません。"),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.ban(
                ユーザー, reason=理由 + f"\n{interaction.user.id} によってBAN"
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="Banに失敗しました。", description="権限が足りないかも！？"
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{ユーザー.name}をBanしました。"
            ).add_field(
                name="理由",
                value=理由 + f"\n{interaction.user.id} によってBAN",
                inline=False,
            )
        )

    @moderation.command(name="ban", description="ユーザーをBanをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def ban(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身はBanできません。"),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.ban(
                ユーザー, reason=理由 + f"\n{interaction.user.id} によってBAN"
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="Banに失敗しました。", description="権限が足りないかも！？"
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{ユーザー.name}をBanしました。"
            ).add_field(
                name="理由",
                value=理由 + f"\n{interaction.user.id} によってBAN",
                inline=False,
            )
        )

    @moderation.command(name="unban", description="ユーザーのBanを解除します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def unban(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身のBanは解除できません。"),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.unban(
                ユーザー, reason=理由 + f"\n{interaction.user.id} によってBAN解除"
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="Ban解除に失敗しました。",
                    description="権限が足りないかも！？",
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{ユーザー.name}のBanを解除しました。"
            ).add_field(
                name="理由",
                value=理由 + f"\n{interaction.user.id} によってBAN解除",
                inline=False,
            )
        )

    @moderation.command(
        name="silentban", description="メッセージを削除せずにメンバーをbanをします。"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def silentban(
        self, interaction: discord.Interaction, メンバー: discord.User, 理由: str
    ):
        if not interaction.guild.get_member(メンバー.id):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="このサーバーにいない人はbanできません。"
                ),
                ephemeral=True,
            )
        if メンバー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身はBanできません。"),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.ban(
                メンバー,
                reason=理由 + f"\n{interaction.user.id} によってBAN",
                delete_message_days=0,
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="Botに権限がありません。", description="Banの権限が必要です。"
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{メンバー.name}をBanしました。",
                description="メッセージは削除されません。",
            ).add_field(
                name="理由",
                value=理由 + f"\n{interaction.user.id} によってBAN",
                inline=False,
            )
        )

    @moderation.command(name="softban", description="ユーザーをSoftBanします。")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def softban(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(title="自分自身はSoftBanできません。"),
                ephemeral=True,
            )
        await interaction.response.defer()
        try:
            await interaction.guild.ban(
                ユーザー, reason=理由 + f"\n{interaction.user.id} によってBAN"
            )

            await asyncio.sleep(2)
            await interaction.guild.unban(
                ユーザー, reason=理由 + f"\n{interaction.user.id} によってBAN解除"
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="SoftBanに失敗しました。",
                    description="権限が足りないかも！？",
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(title=f"{ユーザー.name}をSoftBanしました。")
        )

    @moderation.command(name="massban", description="複数ユーザーを一気にbanします。")
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

        if len(U_ids) > 10:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="10以上のメンバーを一気にbanできません。",
                    color=discord.Color.red(),
                )
            )

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
            msg = await interaction.client.wait_for(
                "message", check=check, timeout=30.0
            )
            if msg.content.lower() != "y":
                return await interaction.channel.send("キャンセルしました。")
            await msg.add_reaction("✅")
        except asyncio.TimeoutError:
            return await interaction.channel.send("タイムアウトしました。")

        b = await interaction.guild.bulk_ban(
            U_ids, reason=f"Banned by {interaction.user.name}"
        )

        await interaction.channel.send(
            f"{b.banned}人をBANしました。失敗: {b.failed}人。"
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
        理由: str = None,
    ):
        if ユーザー.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="自分自身はタイムアウトできません。"
                ),
                ephemeral=True,
            )
        member = interaction.guild.get_member(ユーザー.id)
        if member is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="このサーバーにいないメンバーはタイムアウトできません。"
                )
            )

        if (
            member.top_role >= interaction.user.top_role
            and interaction.user != interaction.guild.owner
        ):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="タイムアウトできません。",
                    description=f"{member.mention} はあなたより上位、または同等の権限を持っています。",
                ),
                ephemeral=True,
            )

        await interaction.response.defer()
        try:
            duration = parse_time(時間)
            await member.edit(
                timed_out_until=discord.utils.utcnow() + duration, reason=理由
            )
        except:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="タイムアウトに失敗しました。",
                    description="権限が足りないかも！？",
                )
            )
        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"タイムアウトしました。",
                description=f"{member.mention} のタイムアウトをしました。",
            )
        )

    @moderation.command(name="untimeout", description="タイムアウトを解除します。")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def untimeout(
        self,
        interaction: discord.Interaction,
        ユーザー: discord.User,
        理由: str = None,
    ):
        member = interaction.guild.get_member(ユーザー.id)

        if member is None:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="メンバーが見つかりません。",
                    description="このサーバーにいないユーザーのタイムアウトは解除できません。",
                ),
                ephemeral=True,
            )

        if (
            member.top_role >= interaction.user.top_role
            and interaction.user != interaction.guild.owner
        ):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="タイムアウト解除できません。",
                    description=f"{member.mention} はあなたより上位、または同等の権限を持っています。",
                ),
                ephemeral=True,
            )

        await interaction.response.defer()

        try:
            await member.edit(timed_out_until=None, reason=理由)
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="タイムアウト解除に失敗しました。",
                    description="Botに十分な権限がない可能性があります。",
                ),
                ephemeral=True,
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="予期せぬエラーが発生しました。", description=f"```{e}```"
                ),
                ephemeral=True,
            )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="タイムアウトを解除しました。",
                description=f"{member.mention} のタイムアウトを解除しました。",
            ),
            ephemeral=False,
        )

    @moderation.command(name="max-timeout", description="最大までタイムアウトします。")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def max_timeout(
        self, interaction: discord.Interaction, ユーザー: discord.User, 理由: str
    ):
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

    @app_commands.command(name="clear", description="メッセージを一斉削除します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def top_clear(
        self,
        interaction: discord.Interaction,
        メッセージ数: int,
        ユーザー: discord.User = None,
    ):
        await interaction.response.defer(ephemeral=True)

        now = discord.utils.utcnow()
        two_weeks = datetime.timedelta(days=14)

        def check(msg: discord.Message):
            if (now - msg.created_at) > two_weeks:
                return False
            if ユーザー is not None and msg.author.id != ユーザー.id:
                return False
            return True

        deleted = await interaction.channel.purge(limit=メッセージ数, check=check)

        if len(deleted) == 0:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title=f"メッセージを一個も削除できませんでした。"
                ),
            )
            return

        await interaction.followup.send(
            ephemeral=True,
            embed=make_embed.success_embed(
                title=f"{len(deleted)}個のメッセージを削除しました。"
            ),
        )

    @moderation.command(name="clear", description="メッセージを一斉削除します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def clear(
        self,
        interaction: discord.Interaction,
        メッセージ数: int,
        ユーザー: discord.User = None,
    ):
        await interaction.response.defer(ephemeral=True)

        now = discord.utils.utcnow()
        two_weeks = datetime.timedelta(days=14)

        def check(msg: discord.Message):
            if (now - msg.created_at) > two_weeks:
                return False
            if ユーザー is not None and msg.author.id != ユーザー.id:
                return False
            return True

        deleted = await interaction.channel.purge(limit=メッセージ数, check=check)

        if len(deleted) == 0:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title=f"メッセージを一個も削除できませんでした。"
                ),
            )
            return

        await interaction.followup.send(
            ephemeral=True,
            embed=make_embed.success_embed(
                title=f"{len(deleted)}個のメッセージを削除しました。"
            ),
        )

    @moderation.command(name="warn", description="メンバーを警告します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def warn(
        self, interaction: discord.Interaction, メンバー: discord.User, 理由: str
    ):
        await interaction.response.defer()
        if interaction.guild.get_member(メンバー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーは警告できません。",
                    color=discord.Color.red(),
                )
            )

        try:
            await メンバー.send(
                embed=discord.Embed(
                    title=f"あなたは`{interaction.guild.name}`\nで警告されました。",
                    color=discord.Color.yellow(),
                    description=f"```{理由}```",
                )
                .set_footer(
                    text=f"{interaction.guild.name} / {interaction.guild.id}",
                    icon_url=interaction.guild.icon.url
                    if interaction.guild.icon
                    else None,
                )
                .set_author(
                    name=f"{interaction.user.name} / {interaction.user.id}",
                    icon_url=interaction.user.avatar.url
                    if interaction.user.avatar
                    else interaction.user.default_avatar.url,
                )
            )
        except:
            return await interaction.followup.send(
                ephemeral=True,
                embed=discord.Embed(
                    title="警告に失敗しました。",
                    color=discord.Color.red(),
                    description="Dmを送信できませんでした。",
                ),
            )

        db = self.bot.async_db["Main"].Warns
        await db.update_one(
            {"Guild": interaction.guild.id, "User": メンバー.id},
            {"$push": {"Reason": 理由}},
            upsert=True,
        )

        await db.update_one(
            {"Guild": interaction.guild.id, "User": メンバー.id},
            {"$push": {"Mod": interaction.user.name}},
            upsert=True,
        )

        await db.update_one(
            {"Guild": interaction.guild.id, "User": メンバー.id},
            {"$inc": {"Count": 1}},
            upsert=True,
        )

        await interaction.followup.send(
            ephemeral=True,
            embed=discord.Embed(
                title="警告しました。",
                description=f"理由```{理由}```",
                color=discord.Color.green(),
            ),
        )

    @moderation.command(
        name="warns", description="メンバーの警告理由・回数を取得します。"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def warns(self, interaction: discord.Interaction, メンバー: discord.User):
        db = self.bot.async_db["Main"].Warns

        try:
            dbfind = await db.find_one(
                {"Guild": interaction.guild.id, "User": メンバー.id},
                {"_id": False},
            )
        except:
            return await interaction.response.send_message(
                ephemeral=True, content="取得に失敗しました。"
            )

        if dbfind is None:
            return await interaction.response.send_message(
                ephemeral=True, content="まだ処罰されていないようです。"
            )

        mods = dbfind.get("Mod", [])
        reason = dbfind.get("Reason", [])
        text = ""
        for _, mod in enumerate(mods):
            text += f"{reason[_]} by {mod}\n"

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{メンバー.name} さんの警告リスト", color=discord.Color.green()
            )
            .add_field(
                name="合計警告回数",
                value=str(dbfind.get("Count", 0)) + "回",
                inline=False,
            )
            .add_field(name="理由・処罰者", value=text, inline=True)
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
        await ch.send(
            embed=make_embed.success_embed(
                title="チャンネルを再生成しました。",
                description=f"実行者: <@{interaction.user.id}>",
            )
        )

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
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$set": {"Guild": interaction.guild.id, "Channel": チャンネル.id}},
                upsert=True,
            )
            await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="通報チャンネルをセットアップしました。"
                )
            )
        else:
            await db.delete_one({"Guild": interaction.guild.id})
            await interaction.followup.send(
                embed=make_embed.success_embed(title="通報チャンネルを無効化しました。")
            )

    @moderation.command(
        name="serverban",
        description="web認証時に特定のサーバーに参加してる場合に、認証できなくします。",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def server_ban(self, interaction: discord.Interaction, サーバーid: str):
        await interaction.response.defer()
        serverids = await resolve_server_ids(サーバーid)

        _ = 0

        db = self.bot.async_db["Main"].GuildBAN

        for s_id in serverids:
            await db.update_one(
                {"Guild": str(interaction.guild.id), "BANGuild": s_id},
                {"$set": {"Guild": str(interaction.guild.id), "BANGuild": s_id}},
                upsert=True,
            )

            _ += 1

            if _ < 10:
                await asyncio.sleep(0.5)

        return await interaction.followup.send(
            embed=make_embed.success_embed(
                title=f"{_}個のサーバーをBANしました。",
                description="次からそのサーバーに入っているユーザーを認証できなくします。",
            )
        )

    @moderation.command(
        name="serverunban",
        description="web認証時に特定のサーバーに参加してる場合に、認証できなくするのを解除します。",
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    async def server_unban(self, interaction: discord.Interaction, サーバーid: str):
        await interaction.response.defer()
        serverids = await resolve_server_ids(サーバーid)

        _ = 0

        db = self.bot.async_db["Main"].GuildBAN

        for s_id in serverids:
            try:
                await db.delete_one(
                    {"Guild": str(interaction.guild.id), "BANGuild": int(s_id)}
                )
            except:
                pass
            await db.delete_one(
                {"Guild": str(interaction.guild.id), "BANGuild": s_id}
            )
            _ += 1

            if _ < 10:
                await asyncio.sleep(0.5)

        return await interaction.followup.send(
            embed=make_embed.success_embed(title=f"{_}個のサーバーのBANを解除しました。")
        )

    @moderation.command(
        name="auditlog",
        description="監査ログを検索します。",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        監査ログタイプ=[
            app_commands.Choice(name="チャンネル削除", value="channel_delete"),
            app_commands.Choice(name="メンバーBan", value="ban"),
            app_commands.Choice(name="メンバーBan解除", value="unban"),
            app_commands.Choice(name="Bot追加", value="bot_add"),
        ]
    )
    async def auditlog_search(
        self, interaction: discord.Interaction, 監査ログタイプ: app_commands.Choice[str]
    ):
        await interaction.response.defer()
        text = ""
        if 監査ログタイプ.value == "ban":
            async for entry in interaction.guild.audit_logs(
                action=discord.AuditLogAction.ban, limit=50
            ):
                text += f"{entry.target.name} - {entry.user.name} .. {entry.reason if entry.reason else 'なし'}\n"
        elif 監査ログタイプ.value == "unban":
            async for entry in interaction.guild.audit_logs(
                action=discord.AuditLogAction.unban, limit=50
            ):
                text += f"{entry.target.name} - {entry.user.name} .. {entry.reason if entry.reason else 'なし'}\n"
        elif 監査ログタイプ.value == "bot_add":
            async for entry in interaction.guild.audit_logs(
                action=discord.AuditLogAction.bot_add, limit=50
            ):
                text += f"{entry.target.name} - {entry.user.name} .. {entry.reason if entry.reason else 'なし'}\n"
        elif 監査ログタイプ.value == "channel_delete":
            async for entry in interaction.guild.audit_logs(
                action=discord.AuditLogAction.channel_delete, limit=50
            ):
                try:
                    text += f"{entry.before.name} - {entry.user.name} .. {entry.reason if entry.reason else 'なし'}\n"
                except:
                    continue
        t = io.StringIO(text)
        await interaction.followup.send(file=discord.File(t, "auditlog.txt"))
        t.close()

    @moderation.command(
        name="lottery",
        description="抽選をします。",
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        選ぶ先=[
            app_commands.Choice(name="ロールから", value="role"),
            app_commands.Choice(name="リアクションから", value="reaction"),
            app_commands.Choice(
                name="テキストチャンネルのメッセージから", value="messages"
            ),
        ]
    )
    async def lottery(
        self,
        interaction: discord.Interaction,
        何個選ぶか: int,
        選ぶ先: app_commands.Choice[str],
        ロール: discord.Role = None,
        メッセージ: str = None,
        絵文字: str = None,
        テキストチャンネル: discord.TextChannel = None,
    ):
        await interaction.response.defer(thinking=True)

        if 選ぶ先.value == "role":
            if ロール is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="引数を指定してください。",
                        description="ロールを指定してください。",
                    ),
                    ephemeral=True,
                )

            members = [m for m in ロール.members]
            if not members:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="抽選失敗です",
                        description="指定されたロールに有効なメンバーがいません。",
                    )
                )

            winners = random.sample(members, min(何個選ぶか, len(members)))
            desc = "\n".join([m.mention for m in winners])
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="抽選結果です (ロールから)", description=desc
                )
            )

        elif 選ぶ先.value == "reaction":
            if メッセージ is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="引数を指定してください。",
                        description="メッセージIDを指定してください。",
                    ),
                    ephemeral=True,
                )
            if 絵文字 is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="引数を指定してください。",
                        description="絵文字を指定してください。",
                    ),
                    ephemeral=True,
                )

            channel = テキストチャンネル or interaction.channel
            try:
                message = await channel.fetch_message(int(メッセージ))
            except Exception:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="取得失敗です",
                        description="指定されたメッセージが見つかりませんでした。",
                    )
                )

            reaction = discord.utils.get(message.reactions, emoji=絵文字)
            if reaction is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="エラーです",
                        description=f"指定の絵文字({絵文字})のリアクションが見つかりませんでした。",
                    )
                )

            users = [u async for u in reaction.users()]
            if not users:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="抽選失敗です",
                        description="リアクションしているユーザーがいません。",
                    )
                )

            winners = random.sample(users, min(何個選ぶか, len(users)))
            desc = "\n".join([u.mention for u in winners])
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="抽選結果です (リアクションから)", description=desc
                )
            )
        elif 選ぶ先.value == "messages":
            if テキストチャンネル is None:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="引数を指定してください。",
                        description="テキストチャンネルを指定してください。",
                    ),
                    ephemeral=True,
                )

            try:
                messages = [m async for m in テキストチャンネル.history(limit=100)]
            except discord.Forbidden:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="権限エラーです。",
                        description="メッセージ履歴を取得できません。権限を確認してください。",
                    )
                )

            authors = list({m.author for m in messages})
            if not authors:
                return await interaction.followup.send(
                    embed=make_embed.error_embed(
                        title="抽選失敗です。",
                        description="対象チャンネルに有効なメッセージ送信者がいません。",
                    )
                )

            winners = random.sample(authors, min(何個選ぶか, len(authors)))
            desc = "\n".join([a.mention for a in winners])
            return await interaction.followup.send(
                embed=make_embed.success_embed(
                    title="抽選結果です (テキストチャンネルのメッセージから)",
                    description=desc,
                )
            )


async def setup(bot):
    await bot.add_cog(ModCog(bot))
