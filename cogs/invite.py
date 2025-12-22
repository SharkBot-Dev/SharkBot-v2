from discord.ext import commands
from discord import app_commands
import discord
from models import make_embed
import io


class InviteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_cache = {}
        print("init -> InviteCog")

    @commands.Cog.listener()
    async def on_ready(self):
        col = self.bot.async_db["MainTwo"].InviteTracker
        async for doc in col.find({}, {"_id": False}):
            self.invite_cache[doc["guild_id"]] = doc.get("invites", {})

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        col = self.bot.async_db["MainTwo"].InviteTracker

        doc = await col.find_one({"guild_id": invite.guild.id})
        if doc is None:
            return

        cache = self.invite_cache.setdefault(invite.guild.id, {})
        cache[invite.code] = invite.uses

        await col.update_one(
            {"guild_id": invite.guild.id},
            {"$set": {"invites": cache}},
            upsert=True
        )

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        col = self.bot.async_db["MainTwo"].InviteTracker

        doc = await col.find_one({"guild_id": invite.guild.id})
        if doc is None:
            return

        cache = self.invite_cache.get(invite.guild.id, {})
        cache.pop(invite.code, None)

        await col.update_one(
            {"guild_id": invite.guild.id},
            {"$set": {"invites": cache}},
            upsert=True
        )

    async def send_invite_log(self, guild: discord.Guild, member: discord.Member, invite_code: str):
        col = self.bot.async_db["MainTwo"].InviteTrackerLog

        doc = await col.find_one({"guild_id": guild.id})
        if doc is None:
            return

        channel = guild.get_channel(doc.get('channel_id', 0))
        if not channel:
            return
        
        try:
            
            await channel.send(embed=discord.Embed(title="招待リンクが使用されました。", color=discord.Color.green())
                            .add_field(name="使用された招待リンク", value=invite_code, inline=False)
                            .set_author(name=member.name, icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
                            .set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None))
        except:
            return

    async def execute_invite_track(self, guild: discord.Guild, member: discord.Member, invite_code: str):
        await self.send_invite_log(guild, member, invite_code)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id

        col = self.bot.async_db["MainTwo"].InviteTracker

        doc = await col.find_one({"guild_id": guild_id})
        if doc is None:
            return

        before = self.invite_cache.get(guild_id, {})

        invites = await member.guild.invites()
        after = {i.code: i.uses for i in invites}

        used_code = None
        for code, uses in after.items():
            if uses > before.get(code, 0):
                used_code = code
                break

        if used_code is None:
            return

        self.invite_cache[guild_id] = after

        tracker = self.bot.async_db["MainTwo"].InviteTracker
        stats = self.bot.async_db["MainTwo"].InviteTrackerStat

        await tracker.update_one(
            {"guild_id": guild_id},
            {"$set": {"invites": after}},
            upsert=True
        )

        if used_code:
            inviter_id = next(i.inviter.id for i in invites if i.code == used_code)

            await stats.update_one(
                {"guild_id": guild_id, "inviter_id": inviter_id},
                {"$inc": {"count": 1}},
                upsert=True
            )

            await self.execute_invite_track(member.guild, member, used_code)

    invite = app_commands.Group(name="invite", description="招待リンク関連のコマンドです。", allowed_installs=app_commands.AppInstallationType(guild=True, user=False))

    @invite.command(name="tracker", description="招待リンクの追跡をON/OFFします")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def invite_tracker(self, interaction: discord.Interaction):
        col = self.bot.async_db["MainTwo"].InviteTracker
        guild_id = interaction.guild.id

        doc = await col.find_one({"guild_id": guild_id})

        if doc is None:
            await col.insert_one({
                "guild_id": guild_id,
                "invites": {}
            })
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="招待リンクを追跡します",
                    description="再度実行すると無効化できます"
                )
            )
        else:
            await col.delete_one({"guild_id": guild_id})
            self.invite_cache.pop(guild_id, None)

            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="招待リンク追跡を無効化しました"
                )
            )

    @invite.command(name="log", description="誰がどの招待リンクを使ったかを送信します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def invite_log(self, interaction: discord.Interaction):
        col = self.bot.async_db["MainTwo"].InviteTracker
        guild_id = interaction.guild.id

        doc = await col.find_one({"guild_id": guild_id})

        if doc is None:
            await interaction.response.send_message(
                embed=make_embed.error_embed(
                    title="このログを設定するには以下の設定が必要です！",
                    description="/invite tracker を一回実行してください。"
                ),
                ephemeral=True
            )
        else:
            await interaction.response.defer()
            col = self.bot.async_db["MainTwo"].InviteTrackerLog
            guild_id = interaction.guild.id
            doc = await col.find_one({"guild_id": guild_id})
            if doc is None:
                await col.update_one(
                    {"guild_id": guild_id},
                    {"$set": {"channel_id": interaction.channel_id}},
                    upsert=True
                )
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="招待リンクログを有効化しました。",
                        description="無効化する際は、再度このコマンドを実行してください。"
                    ),
                    ephemeral=True
                )
            else:
                await col.delete_one({"guild_id": guild_id})
                await interaction.followup.send(
                    embed=make_embed.success_embed(
                        title="招待リンクログを無効化しました。"
                    ),
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(InviteCog(bot))
