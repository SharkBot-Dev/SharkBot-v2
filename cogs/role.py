from discord.ext import commands
import discord
import datetime

from discord import app_commands
from models import command_disable, make_embed


class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> RoleCog")

    role = app_commands.Group(name="role", description="ロール系のコマンドです。")

    @role.command(name="add", description="メンバーにロールを追加します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_add(
        self,
        interaction: discord.Interaction,
        メンバー: discord.Member,
        ロール: discord.Role,
    ):
        guild = interaction.guild
        executor = interaction.user
        bot_member = guild.me

        if not bot_member.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="ロール追加失敗",
                    description="Botにロール管理権限がありません。",
                ),
                ephemeral=True,
            )

        if ロール.position >= bot_member.top_role.position:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="ロール追加失敗",
                    description="指定されたロールはBotより上位のため、操作できません。",
                ),
                ephemeral=True,
            )

        if (
            ロール.position >= executor.top_role.position
            and not executor.guild_permissions.administrator
        ):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="ロール追加失敗",
                    description="あなたより上位のロールは追加できません。",
                ),
                ephemeral=True,
            )

        if メンバー.id == executor.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="自分自身にはロールを付与できません。"
                ),
                ephemeral=True,
            )

        await interaction.response.defer(thinking=True)

        try:
            await メンバー.add_roles(ロール, reason=f"実行者: {executor}")
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ロール追加失敗",
                    description="権限不足により、ロールを追加できませんでした。",
                ),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エラーが発生しました。", description=f"詳細: {e}"
                ),
                ephemeral=True,
            )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ロールを追加しました。",
                description=f"{メンバー.mention} に {ロール.mention} を追加しました。",
            )
        )

    @role.command(name="remove", description="メンバーからロールを剥奪します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_remove(
        self,
        interaction: discord.Interaction,
        メンバー: discord.Member,
        ロール: discord.Role,
    ):
        guild = interaction.guild
        executor = interaction.user
        bot_member = guild.me

        if not bot_member.guild_permissions.manage_roles:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="ロール剥奪失敗",
                    description="Botにロール管理権限がありません。",
                ),
                ephemeral=True,
            )

        if ロール.position >= bot_member.top_role.position:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="ロール剥奪失敗",
                    description="指定されたロールはBotより上位のため、操作できません。",
                ),
                ephemeral=True,
            )

        if (
            ロール.position >= executor.top_role.position
            and not executor.guild_permissions.administrator
        ):
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="ロール剥奪失敗",
                    description="あなたより上位のロールは剥奪できません。",
                ),
                ephemeral=True,
            )

        if メンバー.id == executor.id:
            return await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="自分自身からロールを剥奪することはできません。"
                ),
                ephemeral=True,
            )

        await interaction.response.defer(thinking=True)

        try:
            await メンバー.remove_roles(ロール, reason=f"実行者: {executor}")
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="ロール剥奪失敗",
                    description="権限不足により、ロールを剥奪できませんでした。",
                ),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="エラーが発生しました。", description=f"詳細: {e}"
                ),
                ephemeral=True,
            )

        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="ロールを剥奪しました。",
                description=f"{メンバー.mention} から {ロール.mention} を剥奪しました。",
            )
        )

    @role.command(name="color-role", description="色付きロールを作成します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        色=[
            app_commands.Choice(name="赤", value="red"),
            app_commands.Choice(name="青", value="blue"),
            app_commands.Choice(name="黄", value="yellow"),
            app_commands.Choice(name="緑", value="green"),
            app_commands.Choice(name="金", value="gold"),
        ]
    )
    async def color_role(
        self,
        interaction: discord.Interaction,
        ロール名: str,
        色: app_commands.Choice[str],
    ):
        await interaction.response.defer()
        if 色.value == "red":
            role = await interaction.guild.create_role(
                name=ロール名, color=discord.Colour.red()
            )
        elif 色.value == "blue":
            role = await interaction.guild.create_role(
                name=ロール名, color=discord.Colour.blue()
            )
        elif 色.value == "yellow":
            role = await interaction.guild.create_role(
                name=ロール名, color=discord.Colour.yellow()
            )
        elif 色.value == "green":
            role = await interaction.guild.create_role(
                name=ロール名, color=discord.Colour.green()
            )
        elif 色.value == "gold":
            role = await interaction.guild.create_role(
                name=ロール名, color=discord.Colour.gold()
            )
        embed = make_embed.success_embed(
            title="色付きロールを作成しました。",
            description=f"作成したロール: {role.mention}",
        )
        await interaction.followup.send(embed=embed)

    @role.command(name="info", description="ロール情報を確認します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_info(self, interaction: discord.Interaction, ロール: discord.Role):
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
            await interaction.response.defer()
            PERMISSION_TRANSLATIONS = {
                "administrator": "管理者",
                "view_audit_log": "監査ログの表示",
                "view_guild_insights": "サーバーインサイトの表示",
                "manage_guild": "サーバーの管理",
                "manage_roles": "ロールの管理",
                "manage_channels": "チャンネルの管理",
                "kick_members": "メンバーのキック",
                "ban_members": "メンバーのBAN",
                "create_instant_invite": "招待の作成",
                "change_nickname": "ニックネームの変更",
                "manage_nicknames": "ニックネームの管理",
                "manage_emojis_and_stickers": "絵文字とステッカーの管理",
                "manage_webhooks": "Webhookの管理",
                "view_channel": "チャンネルの閲覧",
                "send_messages": "メッセージの送信",
                "send_tts_messages": "TTSメッセージの送信",
                "manage_messages": "メッセージの管理",
                "embed_links": "埋め込みリンクの送信",
                "attach_files": "ファイルの添付",
                "read_message_history": "メッセージ履歴の閲覧",
                "read_messages": "メッセージの閲覧",
                "external_emojis": "絵文字を管理",
                "mention_everyone": "everyone のメンション",
                "use_external_emojis": "外部絵文字の使用",
                "use_external_stickers": "外部ステッカーの使用",
                "add_reactions": "リアクションの追加",
                "connect": "ボイスチャンネルへの接続",
                "speak": "発言",
                "stream": "配信",
                "mute_members": "メンバーのミュート",
                "deafen_members": "メンバーのスピーカーミュート",
                "move_members": "ボイスチャンネルの移動",
                "use_vad": "音声検出の使用",
                "priority_speaker": "優先スピーカー",
                "request_to_speak": "発言リクエスト",
                "manage_events": "イベントの管理",
                "use_application_commands": "アプリケーションコマンドの使用",
                "manage_threads": "スレッドの管理",
                "create_public_threads": "公開スレッドの作成",
                "create_private_threads": "非公開スレッドの作成",
                "send_messages_in_threads": "スレッド内でのメッセージ送信",
                "use_embedded_activities": "アクティビティの使用",
                "moderate_members": "メンバーのタイムアウト",
                "use_soundboard": "サウンドボードの使用",
                "manage_expressions": "絵文字などの管理",
                "create_events": "イベントの作成",
                "create_expressions": "絵文字などの作成",
                "use_external_sounds": "外部のサウンドボードなどの使用",
                "use_external_apps": "外部アプリケーションの使用",
                "view_creator_monetization_analytics": "ロールサブスクリプションの分析情報を表示",
                "send_voice_messages": "ボイスメッセージの送信",
                "send_polls": "投票の作成",
                "external_stickers": "外部のスタンプの使用",
                "use_voice_activation": "ボイスチャンネルでの音声検出の使用",
            }
            user_perms = [
                PERMISSION_TRANSLATIONS.get(perm, perm)
                for perm, value in ロール.permissions
                if value
            ]
            user_perms_str = ", ".join(user_perms)
            embed = make_embed.success_embed(title=f"{ロール.name} の情報")
            await interaction.followup.send(
                embed=embed.add_field(name="ID", value=str(ロール.id), inline=False)
                .add_field(name="名前", value=str(ロール.name), inline=False)
                .add_field(
                    name="ロールを持っている人数",
                    value=str(len(ロール.members)) + "人",
                    inline=False,
                )
                .add_field(
                    name="作成日時",
                    value=str(ロール.created_at.astimezone(JST)),
                    inline=False,
                )
                .add_field(name="色", value=ロール.color.__str__(), inline=False)
                .add_field(
                    name="権限",
                    value=user_perms_str if user_perms_str != "" else "なし",
                    inline=False,
                )
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="ロールの情報を取得できませんでした。",
                    color=discord.Color.red(),
                    description="権限エラーです。",
                )
            )

    @role.command(
        name="can-bot", description="Botが特定ロールを扱えるかをチェックします。"
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_can_bot(
        self, interaction: discord.Interaction, ロール: discord.Role
    ):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="そのロールを扱える？",
                color=discord.Color.green(),
                description=f"{'✅はい' if ロール.is_assignable() else '❌いいえ'}\n\nいいえと表示された場合は、\nこのBotのロールの下にそのロールを持っていこう。",
            )
        )


async def setup(bot):
    await bot.add_cog(RoleCog(bot))
