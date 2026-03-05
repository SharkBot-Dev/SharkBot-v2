import asyncio

from discord.ext import commands
import discord
from discord import app_commands

from models import make_embed 

class OpenVCCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> OpenVCCog")

    openvc = app_commands.Group(name="openvc", description="ボイスチャットの掲示板関連のコマンドです。")

    @openvc.command(name="register", description="特定のVCを公開設定として登録します。")
    @app_commands.checks.has_permissions(manage_channels=True, create_instant_invite=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def openvc_register(
        self,
        interaction: discord.Interaction,
        vc: discord.VoiceChannel
    ):
        await interaction.response.defer()

        db = self.bot.async_db["MainTwo"].OpenVC

        try:
            invite = await vc.create_invite(reason="OpenVC登録のため", max_age=0)
        except Exception as e:
            return await interaction.followup.send(f"招待リンクの作成に失敗しました")

        await db.update_one(
            {"guild_id": interaction.guild_id},
            {
                "$set": {
                    "guild_name": interaction.guild.name,
                    "guild_icon": interaction.guild.icon.url if interaction.guild.icon else "https://cdn.discordapp.com/embed/avatars/1.png",
                    "last_updated": discord.utils.utcnow()
                },
                "$addToSet": {
                    "channels": {
                        "channel_id": vc.id,
                        "channel_name": vc.name,
                        "invite_url": invite.url,
                        "user_count": len(vc.members),
                        "registered_by": interaction.user.id
                    }
                }
            },
            upsert=True
        )

        embed = make_embed.success_embed(
            title="VC登録完了",
            description=f"チャンネル {vc.mention} を公開リストに登録しました。"
        )

        await interaction.followup.send(embed=embed)

    @openvc.command(name="unregister", description="登録されているVCを解除します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def openvc_unregister(
        self,
        interaction: discord.Interaction,
        vc: discord.VoiceChannel
    ):
        await interaction.response.defer()

        db = self.bot.async_db["MainTwo"].OpenVC

        result = await db.update_one(
            {"guild_id": interaction.guild_id},
            {"$pull": {"channels": {"channel_id": vc.id}}}
        )

        if result.modified_count > 0:
            embed = make_embed.success_embed(
                title="登録解除完了",
                description=f"チャンネル {vc.mention} を公開リストから削除しました。"
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=make_embed.error_embed(title="そのチャンネルは登録されていません。"))

    async def mention_get(self, interaction: discord.Interaction):
        db = self.bot.async_db["Main"].BumpUpMention
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except:
            return "メンションするロールがありません。"
        if dbfind is None:
            return "メンションするロールがありません。"

        try:
            role = interaction.guild.get_role(dbfind.get("Role", None))
            return role.mention
        except:
            return "メンションするロールがありません。"

    @openvc.command(name="up", description="掲示板の掲載順位を上げます。")
    @app_commands.checks.cooldown(1, 3600, key=lambda i: i.guild_id)
    async def openvc_up(self, interaction: discord.Interaction):
        await interaction.response.defer()

        db = self.bot.async_db["MainTwo"].OpenVC
        now = discord.utils.utcnow()

        result = await db.update_one(
            {"guild_id": interaction.guild_id},
            {"$set": {"last_up": now}}
        )

        if result.matched_count > 0:
            embed = make_embed.success_embed(
                title="サーバーをUpしました！",
                description="2時間後に再度Upできます。"
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=make_embed.error_embed(title="まだVCが登録されていないようです。", description="先に `/openvc register` を行ってください。"), ephemeral=True)

        db = self.bot.async_db["MainTwo"].SharkBotChannel
        try:
            dbfind = await db.find_one(
                {"Channel": interaction.channel.id}, {"_id": False}
            )
        except:
            return
        if dbfind is None:
            return

        await asyncio.sleep(1)
        try:
            await self.bot.alert_add(
                "sharkbot_vc",
                interaction.channel_id,
                await self.mention_get(interaction),
                "SharkBotのVC掲示板をUpしてね！",
                "</openvc up:1479026633112293457> でUp。",
                7200,
            )

            await interaction.channel.send(
                embed=make_embed.success_embed(
                    title="Upを検知しました。", description="2時間後に通知します。"
                )
            )
        except:
            return

    @openvc_up.error
    async def up_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(embed=make_embed.error_embed(title="まだUpできません。", description=f"あと {int(error.retry_after / 60)} 分後に実行してください。"), ephemeral=True)

    @openvc.command(name="list", description="登録されているVCの一覧をWebで表示します。")
    async def openvc_list(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(content="以下からアクセスできます。", view=discord.ui.View().add_item(discord.ui.Button(label="アクセスする", url="https://dashboard.sharkbot.xyz/vc")), ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel == after.channel:
            return

        db = self.bot.async_db["MainTwo"].OpenVC
        
        if before.channel:
            await self._update_vc_count_if_registered(db, member.guild.id, before.channel)
            
        if after.channel:
            await self._update_vc_count_if_registered(db, member.guild.id, after.channel)

    async def _update_vc_count_if_registered(self, db, guild_id, channel):
        result = await db.update_one(
            {
                "guild_id": guild_id,
                "channels.channel_id": channel.id
            },
            {
                "$set": {
                    "channels.$.user_count": len(channel.members)
                }
            }
        )

async def setup(bot):
    await bot.add_cog(OpenVCCog(bot))