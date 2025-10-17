from discord.ext import commands
from discord import app_commands
import discord
import datetime
from discord import Webhook
import aiohttp

from models import command_disable


class LoggingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> LoggingCog")

    async def get_logging_webhook(self, guild: discord.Guild, event: str | None = None):
        db = self.bot.async_db["Main"].EventLoggingChannel
        try:
            if event:
                dbfind = await db.find_one({"Guild": guild.id, "Event": event}, {"_id": False})
                if dbfind:
                    return dbfind.get("Webhook", None)

            dbfind = await db.find_one({"Guild": guild.id, "Event": {"$exists": False}}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind.get("Webhook", None)

    async def get_logging_channel(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].EventLoggingChannel
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return self.bot.get_channel(dbfind.get("Channel", None))

    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_log(self, message: discord.Message):
        try:
            wh = await self.get_logging_webhook(message.guild, "message_delete")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Minus:1367039494322262096> メッセージが削除されました",
                        description=f"{message.content}",
                        color=discord.Color.red(),
                    )
                    .set_footer(text=f"mid:{message.id}")
                    .set_author(
                        name=f"{message.author.name}",
                        icon_url=message.author.avatar.url
                        if message.author.avatar
                        else message.author.default_avatar.url,
                    ),
                )
        except Exception:
            return

    @commands.Cog.listener("on_member_ban")
    async def on_member_ban_log(self, guild: discord.Guild, member: discord.Member):
        try:
            wh = await self.get_logging_webhook(guild, "member_ban")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Minus:1367039494322262096> メンバーがBANされました",
                        description=f"{member.mention}\nメンバーがBANされました: {datetime.datetime.now()}",
                        color=discord.Color.red(),
                    )
                    .set_footer(text=f"uid:{member.id}")
                    .set_author(
                        name=f"{member.name}",
                        icon_url=member.avatar.url
                        if member.avatar
                        else member.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_log(self, before: discord.Member, after: discord.Member):
        try:
            if before.display_name == after.display_name:
                return
            wh = await self.get_logging_webhook(after.guild, "member_update")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Edit:1367039517868953600> メンバーが編集されました",
                        description=f"編集前の名前: {before.display_name}\nメンバーの編集時間: {datetime.datetime.now()}\n編集後の名前: {after.display_name}",
                        color=discord.Color.yellow(),
                    )
                    .set_footer(text=f"uid:{after.id}")
                    .set_author(
                        name=f"{after.name}",
                        icon_url=after.avatar.url
                        if after.avatar
                        else after.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_timeout_log(
        self, before: discord.Member, after: discord.Member
    ):
        try:
            wh = await self.get_logging_webhook(after.guild, "member_update")
            if not wh:
                return

            if before.timed_out_until is None and after.timed_out_until is not None:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(
                        avatar_url=self.bot.user.avatar.url,
                        embed=discord.Embed(
                            title="<:Plus:1367039505865113670> メンバーがタイムアウトされました。",
                            description=f"メンバー: {after.mention}",
                            color=discord.Color.green(),
                        )
                        .set_footer(text=f"uid:{after.id}")
                        .set_author(
                            name=f"{after.name}",
                            icon_url=after.avatar.url
                            if after.avatar
                            else after.default_avatar.url,
                        ),
                    )
        except:
            return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_role_log(
        self, before: discord.Member, after: discord.Member
    ):
        try:
            before_roles = set(before.roles)
            after_roles = set(after.roles)

            added_roles = after_roles - before_roles
            removed_roles = before_roles - after_roles

            wh = await self.get_logging_webhook(after.guild, "member_update")
            if not wh:
                return

            if added_roles:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(
                        avatar_url=self.bot.user.avatar.url,
                        embed=discord.Embed(
                            title="<:Plus:1367039505865113670> ロールが追加されました",
                            description="メンバー: {}\nロール: {}".format(
                                after.mention,
                                "\n".join([rr.mention for rr in added_roles]),
                            ),
                            color=discord.Color.green(),
                        )
                        .set_footer(text=f"uid:{after.id}")
                        .set_author(
                            name=f"{after.name}",
                            icon_url=after.avatar.url
                            if after.avatar
                            else after.default_avatar.url,
                        ),
                    )

            if removed_roles:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(
                        avatar_url=self.bot.user.avatar.url,
                        embed=discord.Embed(
                            title="<:Minus:1367039494322262096> ロールが削除されました",
                            description="メンバー: {}\nロール: {}".format(
                                after.mention,
                                "\n".join([rr.mention for rr in removed_roles]),
                            ),
                            color=discord.Color.red(),
                        )
                        .set_footer(text=f"uid:{after.id}")
                        .set_author(
                            name=f"{after.name}",
                            icon_url=after.avatar.url
                            if after.avatar
                            else after.default_avatar.url,
                        ),
                    )
        except:
            return

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_log(
        self, before: discord.Message, after: discord.Message
    ):
        try:
            if after.author.id == self.bot.user.id:
                return
            if after.content == "":
                return
            if before.content == after.content:
                return
            wh = await self.get_logging_webhook(after.guild, "message_edit")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Edit:1367039517868953600> メッセージが編集されました",
                        description=f"編集前:\n{before.content}\n編集後:\n{after.content}",
                        color=discord.Color.yellow(),
                    )
                    .set_footer(text=f"mid:{after.id}")
                    .set_author(
                        name=f"{after.author.name}",
                        icon_url=after.author.avatar.url
                        if after.author.avatar
                        else after.author.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener("on_guild_channel_create")
    async def on_guild_channel_create_log(self, channel: discord.abc.GuildChannel):
        try:
            wh = await self.get_logging_webhook(channel.guild, "channel_create")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Plus:1367039505865113670> チャンネルが作成されました",
                        description=f"名前: {channel.name}\n作成時間: {channel.created_at}",
                        color=discord.Color.green(),
                    ).set_footer(text=f"cid:{channel.id}"),
                )
        except:
            return

    @commands.Cog.listener("on_guild_channel_delete")
    async def on_guild_channel_delete_log(self, channel: discord.abc.GuildChannel):
        try:
            wh = await self.get_logging_webhook(channel.guild, "channel_delete")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Minus:1367039494322262096> チャンネルが削除されました",
                        description=f"名前: {channel.name}",
                        color=discord.Color.red(),
                    ).set_footer(text=f"cid:{channel.id}"),
                )
        except:
            return

    @commands.Cog.listener("on_invite_create")
    async def on_invite_create_log(self, invite: discord.Invite):
        try:
            wh = await self.get_logging_webhook(invite.guild, "invite_create")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Plus:1367039505865113670> 招待リンクが作成されました",
                        description=f"チャンネル: {invite.channel.name}\n招待リンク作成時間: {datetime.datetime.now()}\nurl: {invite.url}",
                        color=discord.Color.green(),
                    )
                    .set_footer(text=f"invid:{invite.id}")
                    .set_author(
                        name=f"{invite.inviter.name}",
                        icon_url=invite.inviter.avatar.url
                        if invite.inviter.avatar
                        else invite.inviter.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener("on_guild_role_create")
    async def on_guild_role_create_log(self, role: discord.Role):
        try:
            wh = await self.get_logging_webhook(role.guild, "role_create")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Plus:1367039505865113670> ロールが作成されました",
                        description=f"名前: {role.name}",
                        color=discord.Color.green(),
                    ).set_footer(text=f"rid:{role.id}"),
                )
        except:
            return

    @commands.Cog.listener("on_guild_role_delete")
    async def on_guild_role_delete_log(self, role: discord.Role):
        try:
            wh = await self.get_logging_webhook(role.guild, "role_delete")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Minus:1367039494322262096> ロールが削除されました",
                        description=f"名前: {role.name}",
                        color=discord.Color.red(),
                    ).set_footer(text=f"rid:{role.id}"),
                )
        except:
            return

    @commands.Cog.listener("on_member_join")
    async def on_member_join_log(self, member: discord.Member):
        try:
            wh = await self.get_logging_webhook(member.guild, "member_join")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Plus:1367039505865113670> メンバーが参加しました",
                        description=f"名前: {member.name}\nアカウント作成日: {member.created_at}\n参加時間: {datetime.datetime.now()}",
                        color=discord.Color.green(),
                    )
                    .set_footer(text=f"mid:{member.id}")
                    .set_author(
                        name=f"{member.name}",
                        icon_url=member.avatar.url
                        if member.avatar
                        else member.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener("on_member_remove")
    async def on_member_remove_log(self, member: discord.Member):
        try:
            wh = await self.get_logging_webhook(member.guild, "member_remove")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Minus:1367039494322262096> メンバーが退出しました",
                        description=f"名前: {member.name}\nアカウント作成日: {member.created_at}\n参加時間: {datetime.datetime.now()}",
                        color=discord.Color.red(),
                    )
                    .set_footer(text=f"mid:{member.id}")
                    .set_author(
                        name=f"{member.name}",
                        icon_url=member.avatar.url
                        if member.avatar
                        else member.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener("on_automod_action")
    async def on_automod_action_log(self, execution: discord.AutoModAction):
        try:
            wh = await self.get_logging_webhook(execution.guild, "automod_action")
            if not wh:
                return
            async with aiohttp.ClientSession() as session:
                webhook_ = Webhook.from_url(wh, session=session)
                await webhook_.send(
                    avatar_url=self.bot.user.avatar.url,
                    embed=discord.Embed(
                        title="<:Plus:1367039505865113670> AutoModで処罰されました",
                        description=f"名前: {execution.member.name}\nチャンネル: {execution.channel.name}\n処罰時間: {datetime.datetime.now()}",
                        color=discord.Color.green(),
                    )
                    .set_footer(text=f"mid:{execution.member.id}")
                    .set_author(
                        name=f"{execution.member.name}",
                        icon_url=execution.member.avatar.url
                        if execution.member.avatar
                        else execution.member.default_avatar.url,
                    ),
                )
        except:
            return

    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_join_log(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        try:
            wh = await self.get_logging_webhook(member.guild, "vc_join")
            if not wh:
                return
            
            if before.channel is None and after.channel is not None:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(
                        avatar_url=self.bot.user.avatar.url,
                        embed=discord.Embed(
                            title="<:Plus:1367039505865113670> VCに参加しました。",
                            description=f"名前: {member.name}\nチャンネル: {after.channel.name}\n参加した時間: {datetime.datetime.now()}",
                            color=discord.Color.green(),
                        )
                        .set_footer(text=f"mid:{member.id}")
                        .set_author(
                            name=f"{member.name}",
                            icon_url=member.avatar.url
                            if member.avatar
                            else member.default_avatar.url,
                        ),
                    )
        except:
            return
        
    @commands.Cog.listener(name="on_voice_state_update")
    async def on_voice_state_update_leave_log(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        try:
            wh = await self.get_logging_webhook(member.guild, "vc_leave")
            if not wh:
                return
            
            if before.channel is not None and after.channel is None:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(
                        avatar_url=self.bot.user.avatar.url,
                        embed=discord.Embed(
                            title="<:Minus:1367039494322262096> VCから退出しました。",
                            description=f"名前: {member.name}\nチャンネル: {before.channel.name}\n退出した時間: {datetime.datetime.now()}",
                            color=discord.Color.red(),
                        )
                        .set_footer(text=f"mid:{member.id}")
                        .set_author(
                            name=f"{member.name}",
                            icon_url=member.avatar.url
                            if member.avatar
                            else member.default_avatar.url,
                        ),
                    )
        except:
            return

    @commands.Cog.listener(name="on_audit_log_entry_create")
    async def on_on_audit_log_entry_create_log_bot_join(
        self,
        entry: discord.AuditLogEntry
    ):
        try:
            wh = await self.get_logging_webhook(entry.guild, "bot_join")
            if not wh:
                return
            
            if entry.action == discord.AuditLogAction.bot_add:
                async with aiohttp.ClientSession() as session:
                    webhook_ = Webhook.from_url(wh, session=session)
                    await webhook_.send(
                        avatar_url=self.bot.user.avatar.url,
                        embed=discord.Embed(
                            title="<:Plus:1367039505865113670> Botが追加されました。",
                            description=f"Bot名: {entry.target.name}\nBotID: {entry.target.id}\n参加させた人{entry.user.mention} ({entry.user.id})\n参加した時間: {datetime.datetime.now()}",
                            color=discord.Color.green(),
                        )
                        .set_footer(text=f"mid:{entry.target.id}")
                        .set_author(
                            name=f"{entry.target.name}",
                            icon_url=entry.target.avatar.url
                            if entry.target.avatar
                            else entry.target.default_avatar.url,
                        ),
                    )
        except:
            return

    log = app_commands.Group(name="logging", description="ログ系のコマンドです。")

    @log.command(name="setup", description="イベントごとにログを設定します。")
    @app_commands.describe(event="ログを取りたいイベント（未指定なら全て）")
    @app_commands.choices(event=[
        app_commands.Choice(name="メッセージ削除", value="message_delete"),
        app_commands.Choice(name="メッセージ編集", value="message_edit"),
        app_commands.Choice(name="メンバーBAN", value="member_ban"),
        app_commands.Choice(name="メンバー参加", value="member_join"),
        app_commands.Choice(name="メンバー退出", value="member_remove"),
        app_commands.Choice(name="メンバー更新", value="member_update"),
        app_commands.Choice(name="ロール作成", value="role_create"),
        app_commands.Choice(name="ロール削除", value="role_delete"),
        app_commands.Choice(name="チャンネル作成", value="channel_create"),
        app_commands.Choice(name="チャンネル削除", value="channel_delete"),
        app_commands.Choice(name="招待リンク作成", value="invite_create"),
        app_commands.Choice(name="AutoModアクション", value="automod_action"),
        app_commands.Choice(name="VC参加", value="vc_join"),
        app_commands.Choice(name="VC退出", value="vc_leave"),
        app_commands.Choice(name="Bot導入", value="bot_join"),
    ])
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    async def log_setup(
        self,
        interaction: discord.Interaction,
        event: app_commands.Choice[str] = None
    ):
        db = self.bot.async_db["Main"].EventLoggingChannel
        web = await interaction.channel.create_webhook(name=f"SharkBot-Log-{event.value if event else 'all'}")

        query = {"Guild": interaction.guild.id}
        if event:
            query["Event"] = event.value

        update_data = {
            "$set": {
                "Guild": interaction.guild.id,
                "Channel": interaction.channel.id,
                "Webhook": web.url,
            }
        }
        if event:
            update_data["$set"]["Event"] = event.value

        await db.update_one(query, update_data, upsert=True)

        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{event.name if event else 'すべてのイベント'} のログをセットしました。",
                color=discord.Color.green()
            )
        )

    @log.command(name="disable", description="ログを無効化します。")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(event=[
        app_commands.Choice(name="メッセージ削除", value="message_delete"),
        app_commands.Choice(name="メッセージ編集", value="message_edit"),
        app_commands.Choice(name="メンバーBAN", value="member_ban"),
        app_commands.Choice(name="メンバー参加", value="member_join"),
        app_commands.Choice(name="メンバー退出", value="member_remove"),
        app_commands.Choice(name="メンバー更新", value="member_update"),
        app_commands.Choice(name="ロール作成", value="role_create"),
        app_commands.Choice(name="ロール削除", value="role_delete"),
        app_commands.Choice(name="チャンネル作成", value="channel_create"),
        app_commands.Choice(name="チャンネル削除", value="channel_delete"),
        app_commands.Choice(name="招待リンク作成", value="invite_create"),
        app_commands.Choice(name="AutoModアクション", value="automod_action"),
        app_commands.Choice(name="VC参加", value="vc_join"),
        app_commands.Choice(name="VC退出", value="vc_leave"),
        app_commands.Choice(name="Bot導入", value="bot_join"),
    ])
    async def log_disable(self, interaction: discord.Interaction, event: app_commands.Choice[str] = None):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )
        
        if event:
            db = self.bot.async_db["Main"].EventLoggingChannel
            await db.delete_one({"Guild": interaction.guild.id, "Event": event.value})
        else:
            db = self.bot.async_db["Main"].EventLoggingChannel
            await db.delete_many({"Guild": interaction.guild.id})
        await interaction.response.send_message(
            embed=discord.Embed(
                title="ログを無効化しました。", color=discord.Color.green()
            )
        )


async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
