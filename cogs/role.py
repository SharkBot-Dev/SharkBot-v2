from discord.ext import commands
import discord
import datetime

from discord import app_commands
from models import command_disable


class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> RoleCog")

    role = app_commands.Group(name="role", description="ロール系のコマンドです。")

    @role.command(name="add", description="ロールを追加します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_add(
        self,
        interaction: discord.Interaction,
        メンバー: discord.User,
        ロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if interaction.guild.get_member(メンバー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーにはロールを追加できません。",
                    color=discord.Color.red(),
                )
            )

        await interaction.response.defer()

        try:
            await interaction.guild.get_member(メンバー.id).add_roles(ロール)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="ロールを追加できませんでした。",
                    color=discord.Color.red(),
                    description="権限エラーです。",
                )
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title="ロールを追加しました。", color=discord.Color.green()
            )
        )

    @role.command(name="remove", description="ロールを剥奪します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_remove(
        self,
        interaction: discord.Interaction,
        メンバー: discord.User,
        ロール: discord.Role,
    ):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        if interaction.guild.get_member(メンバー.id) is None:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    title="このサーバーにいないメンバーにはロールを追加できません。",
                    color=discord.Color.red(),
                )
            )

        await interaction.response.defer()

        try:
            await interaction.guild.get_member(メンバー.id).remove_roles(ロール)
        except:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="ロールを剥奪できませんでした。",
                    color=discord.Color.red(),
                    description="権限エラーです。",
                )
            )

        await interaction.followup.send(
            embed=discord.Embed(
                title="ロールを剥奪しました。", color=discord.Color.green()
            )
        )

    @role.command(name="info", description="ロール情報を確認します。")
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def role_info(self, interaction: discord.Interaction, ロール: discord.Role):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

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
            await interaction.followup.send(
                embed=discord.Embed(
                    title=f"{ロール.name} の情報", color=discord.Color.blue()
                )
                .add_field(name="ID", value=str(ロール.id), inline=False)
                .add_field(name="名前", value=str(ロール.name), inline=False)
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


async def setup(bot):
    await bot.add_cog(RoleCog(bot))
