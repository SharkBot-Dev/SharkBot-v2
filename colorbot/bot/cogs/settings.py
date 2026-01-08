from discord.ext import commands
from discord import app_commands
import discord

from models import make_embed

class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> SettingsCog")

    settings = app_commands.Group(name="settings", description="設定系のコマンドです。")

    @settings.command(name="lock-message", description="メッセージを固定します。")
    @app_commands.checks.has_permissions(manage_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def lock_message(self, interaction: discord.Interaction, 有効にするか: bool):
        if 有効にするか:

            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="メッセージ固定の設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(
                        label="タイトル",
                        placeholder="タイトルを入力",
                        style=discord.TextStyle.long,
                        required=True,
                    )
                    self.desc = discord.ui.TextInput(
                        label="説明",
                        placeholder="説明を入力",
                        style=discord.TextStyle.long,
                        required=True,
                    )
                    self.add_item(self.etitle)
                    self.add_item(self.desc)

                async def on_submit(self, interaction: discord.Interaction) -> None:
                    view = discord.ui.View()
                    view.add_item(
                        discord.ui.Button(
                            style=discord.ButtonStyle.red,
                            label="削除",
                            custom_id="lockmessage_delete+",
                        )
                    )
                    view.add_item(
                        discord.ui.Button(
                            style=discord.ButtonStyle.blurple,
                            label="編集",
                            custom_id="lockmessage_edit+",
                        )
                    )
                    msg = await interaction.channel.send(
                        embed=discord.Embed(
                            title=self.etitle.value,
                            description=self.desc.value,
                            color=discord.Color.random(),
                        ),
                        view=view,
                    )
                    db = self.db.LockMessage
                    await db.update_one(
                        {
                            "Channel": interaction.channel.id,
                            "Guild": interaction.guild.id,
                        },
                        {
                            "$set": {
                                "Channel": interaction.channel.id,
                                "Guild": interaction.guild.id,
                                "Title": self.etitle.value,
                                "Desc": self.desc.value,
                                "MessageID": msg.id,
                            }
                        },
                        upsert=True,
                    )
                    await interaction.response.send_message(
                        embed=make_embed.success_embed(
                            title="メッセージ固定を有効化しました。"
                        ),
                        ephemeral=True,
                    )

            await interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db.LockMessage
            result = await db.delete_one(
                {
                    "Channel": interaction.channel.id,
                }
            )
            if result.deleted_count == 0:
                return await interaction.response.send_message(
                    embed=make_embed.error_embed(
                        title="メッセージ固定は有効化されていません。"
                    )
                )
            await interaction.response.send_message(
                embed=make_embed.success_embed(
                    title="メッセージ固定を無効化しました。"
                )
            )

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))