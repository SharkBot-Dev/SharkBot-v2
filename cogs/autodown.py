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
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def autodown_vckick(
        self,
        interaction: discord.Interaction,
        キックするか: bool
    ):
        db = self.bot.async_db["MainTwo"].AutoDown

        if キックするか:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$addToSet": {"Execution": "VCKICK"}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="オフラインになると実行する行動を追加しました。",
                    description="VCからキックします。"
                )
            )
        else:
            await db.update_one(
                {"Guild": interaction.guild.id},
                {"$pull": {"Execution": "VCKICK"}},
                upsert=True,
            )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="オフラインになると実行する行動を削除しました。",
                    description="VCからキックしないようにしました。"
                )
            )

    async def procces_event(self, before: discord.Member, after: discord.Member):
        db = self.bot.async_db["MainTwo"].AutoDown
        settings = await db.find_one({"Guild": after.guild.id})

        if not settings or "Execution" not in settings or "VCKICK" not in settings["Execution"]:
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