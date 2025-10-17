from discord.ext import commands
import discord
from discord import app_commands
from models import make_embed

class AutoDownCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> AutoDownCog")

    # スラッシュコマンドグループ
    autodown = app_commands.Group(
        name="autodown", 
        description="オフラインに代わると実行する機能をセットアップします。"
    )

    @autodown.command(
        name="vc-kick",
        description="オフラインになるとVCからキックするように設定します。"
    )
    @app_commands.describe(
        キックするか="Trueで有効化、Falseで無効化します。",
        対象ロール="このロールを持つメンバーのみキック対象にします（省略可）"
    )
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
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
                update_data["$set"] = {"TargetRole": 対象ロール.id}

            await db.update_one(
                {"Guild": interaction.guild.id},
                update_data,
                upsert=True,
            )

            desc = "VCからキックします。"
            if 対象ロール:
                desc += f"\n対象ロール: {対象ロール.mention}"

            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="オフラインになると実行する行動を追加しました。",
                    description=desc
                )
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {
                    "$pull": {"Execution": "VCKICK"},
                    "$unset": {"TargetRole": ""},
                },
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="オフラインになると実行する行動を削除しました。",
                    description="VCからキックしないようにしました。"
                )
            )

    async def procces_event(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return

        db = self.bot.async_db["MainTwo"].AutoDown
        settings = await db.find_one({"Guild": after.guild.id})

        if not settings or "Execution" not in settings or "VCKICK" not in settings["Execution"]:
            return
        
        target_role_id = settings.get("TargetRole")
        if target_role_id:
            role = after.guild.get_role(target_role_id)
            if not role or role not in after.roles:
                return

        if after.status == discord.Status.offline:
            voice_state = after.voice
            if voice_state and voice_state.channel:
                try:
                    await after.move_to(None)
                    print(f"[AutoDown] {after} をVCから切断しました。")
                except discord.Forbidden:
                    print(f"[AutoDown] {after} を切断できません（権限不足）")
                except discord.HTTPException as e:
                    print(f"[AutoDown] HTTPエラー: {e}")

    # presence update イベント
    @commands.Cog.listener("on_presence_update")
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if not after.guild:
            return

        await self.procces_event(before, after)

async def setup(bot):
    await bot.add_cog(AutoDownCog(bot))