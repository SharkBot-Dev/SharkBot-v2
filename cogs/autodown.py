from discord.ext import commands
import discord
from discord import app_commands
from models import make_embed

class AutoDownCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoDownCog")

    autodown = app_commands.Group(
        name="autodown",
        description="オフラインに代わると実行する機能をセットアップします。"
    )

    @autodown.command(
        name="settings",
        description="現在の設定を確認します。"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autodown_settings(self, interaction: discord.Interaction):
        db = self.bot.async_db["MainTwo"].AutoDown
        settings = await db.find_one({"Guild": interaction.guild.id})

        if not settings or "Execution" not in settings:
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(title="まだ設定されていません。")
            )

        embed = make_embed.success_embed(title="オフラインになったときの自動実行設定")

        vc_kick_enabled = "VCKICK" in settings["Execution"]
        embed.add_field(
            name="自動VCキックするか",
            value="はい" if vc_kick_enabled else "いいえ",
            inline=False
        )

        target_roles = settings.get("TargetRoles", [])
        if target_roles:
            mentions = " ".join(f"<@&{r}>" for r in target_roles)
            embed.add_field(name="対象ロール", value=mentions, inline=False)
        else:
            embed.add_field(name="対象ロール", value="（指定なし）", inline=False)

        await interaction.response.send_message(embed=embed)

    @autodown.command(
        name="vc-kick",
        description="オフラインになるとVCからキックするように設定します。"
    )
    @app_commands.describe(
        キックするか="Trueで有効化、Falseで無効化します。",
        対象ロール="このロールを持つメンバーのみキック対象にします（複数指定可）"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autodown_vckick(
        self,
        interaction: discord.Interaction,
        キックするか: bool,
        対象ロール: discord.Role | None = None
    ):
        db = self.bot.async_db["MainTwo"].AutoDown

        if キックするか:
            update_data = {"$addToSet": {"Execution": "VCKICK"}}

            if 対象ロール:
                update_data["$addToSet"]["TargetRoles"] = 対象ロール.id

            await db.update_one(
                {"Guild": interaction.guild.id},
                update_data,
                upsert=True,
            )

            desc = "VCからキックします。"
            if 対象ロール:
                mentions = 対象ロール.mention
                desc += f"\n対象ロール: {mentions}"

            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="自動VCキック設定を更新しました。",
                    description=desc
                )
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$pull": {"Execution": "VCKICK"}, "$pull": {"TargetRoles": 対象ロール}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="自動VCキック設定を削除しました。",
                    description="オフライン時にVCからキックしないようにしました。"
                )
            )

    async def process_vckick(self, before: discord.Member, after: discord.Member):
        if after.bot or not after.guild:
            return

        db = self.bot.async_db["MainTwo"].AutoDown
        settings = await db.find_one({"Guild": after.guild.id})
        if not settings or "Execution" not in settings or "VCKICK" not in settings["Execution"]:
            return

        target_roles = settings.get("TargetRoles", [])
        if target_roles:
            member_role_ids = [r.id for r in after.roles]
            if not any(role_id in member_role_ids for role_id in target_roles):
                return

        if after.status in [discord.Status.offline, discord.Status.invisible]:
            voice_state = after.voice
            if voice_state and voice_state.channel:
                try:
                    await after.move_to(None)
                    print(f"[AutoDown] {after} をVCから切断しました。")
                except discord.Forbidden:
                    print(f"[AutoDown] {after} を切断できません（権限不足）")
                except discord.HTTPException as e:
                    print(f"[AutoDown] HTTPエラー: {e}")

    @commands.Cog.listener("on_presence_update")
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        await self.process_vckick(before, after)

async def setup(bot):
    await bot.add_cog(AutoDownCog(bot))