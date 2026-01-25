import io
import time
import aiohttp
import discord
from discord.ext import commands

from discord import app_commands
import datetime

from models import make_embed


class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.col = self.bot.async_db["Premium"].Premium

    async def add_premium_command(self, guild: discord.Guild, payload: dict):
        cmd = await self.bot.http.upsert_guild_command(
            self.bot.user.id, guild.id, payload=payload
        )
        cmd_id = app_commands.AppCommand(data=cmd, state=self.bot.tree._state)
        return cmd_id

    async def is_premium(self, user: discord.User) -> bool:
        find_premium = await self.col.find_one({"user_id": user.id})

        if not find_premium:
            return False

        if not find_premium.get("is_premium", False):
            return False

        now = datetime.datetime.now()

        last_free_time = find_premium.get("last_free_time")
        if last_free_time:
            if now > last_free_time + datetime.timedelta(days=3):
                await self.deactivate_user(user.id)
                return False

        last_time = find_premium.get("last_time")
        if last_time:
            if now > last_time + datetime.timedelta(days=30):
                await self.deactivate_user(user.id)
                return False

        return True

    async def deactivate_user(self, user_id: int):
        await self.col.update_one({"user_id": user_id}, {"$set": {"is_premium": False}})

    premium = app_commands.Group(
        name="premium",
        description="寄付者プランを管理します。",
        allowed_installs=app_commands.AppInstallationType(guild=True, user=False),
    )

    @premium.command(name="activate", description="寄付者限定プランを有効化します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def premium_activate(self, interaction: discord.Interaction):
        await interaction.response.defer()
        is_premium = await self.is_premium(interaction.user)
        if is_premium:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたはすでに寄付者です。",
                    description="寄付をしていただきありがとうございます！",
                ),
            )
            return
        # 書き途中
        return

    @premium.command(name="free", description="3日間の無料トライアルに参加します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def premium_free(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await self.is_premium(interaction.user)

        find_premium = await self.col.find_one({"user_id": interaction.user.id})
        if not find_premium is None:
            if find_premium.get("is_premium"):
                await interaction.followup.send(
                    ephemeral=True,
                    embed=make_embed.error_embed(
                        title="すでに寄付者です。",
                        description="無料トライアルは寄付者以外が使用できます。",
                    ),
                )
                return

            if find_premium.get("is_used_free"):
                await interaction.followup.send(
                    ephemeral=True,
                    embed=make_embed.error_embed(
                        title="すでに参加したことがあるようです",
                        description="無料トライアルは終了しました。",
                    ),
                )
                return

        await self.col.update_one(
            {
                "user_id": interaction.user.id,
            },
            {
                "$set": {
                    "is_premium": True,
                    "is_used_free": True,
                    "last_free_time": datetime.datetime.now(),
                }
            },
        )
        await interaction.followup.send(
            ephemeral=True,
            embed=make_embed.success_embed(
                title="無料トライアルに参加しました。",
                description="三日後にトライアルは終了します。",
            ),
        )
        return

    @premium.command(name="custom", description="Botの見た目をカスタマイズをします。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def premium_custom(
        self,
        interaction: discord.Interaction,
        アバター: discord.Attachment = None,
        バナー: discord.Attachment = None,
        プロフィール説明: str = None,
        名前: str = None,
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        is_premium = await self.is_premium(interaction.user)
        if not is_premium:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="あなたは寄付者ではありません！",
                    description="寄付をすることにより使用できます。",
                ),
            )

        await interaction.response.defer()

        raw = self.bot.raw(bot=self.bot)
        if アバター:
            av_io = io.BytesIO(await アバター.read())
            avatar = await raw.image_to_data_uri(io_=av_io)
            av_io.close()
        else:
            avatar = None
        if バナー:
            bn_io = io.BytesIO(await バナー.read())
            banner = await raw.image_to_data_uri(io_=bn_io)
            bn_io.close()
        else:
            banner = None
        try:
            await raw.modify_current_member(
                str(interaction.guild.id),
                avatarUri=avatar,
                bannerUri=banner,
                nick=名前,
                bio=プロフィール説明,
            )
        except Exception as e:
            return await interaction.followup.send(
                embed=make_embed.error_embed(
                    title="レートリミットです。",
                    description=f"何分かお待ちください。\n\nエラーコード\n```{e}```",
                )
            )
        await interaction.followup.send(
            embed=make_embed.success_embed(
                title="Botのアバターなどをカスタマイズしました。",
                description="次回変更できるようになるには\nしばらく時間がかかります。",
            )
        )
        return


async def setup(bot):
    await bot.add_cog(PremiumCog(bot))
