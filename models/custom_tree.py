import time
import discord

from models import command_disable, channel_command_disable, bot_ban, translate

cooldown_check = {}


class CustomTree(discord.app_commands.CommandTree):
    def _from_interaction(self, interaction: discord.Interaction) -> None:
        async def wrapper():
            try:
                if not interaction.guild:
                    return await interaction.response.send_message(
                        embed=discord.Embed(
                            title="DMではスラッシュコマンドを実行できません。",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True,
                    )

                if not await command_disable.command_enabled_check(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True, content="そのコマンドは無効化されています。"
                    )

                if not await channel_command_disable.disable_channel(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="このチャンネルではコマンドを使用できません。",
                    )

                if not await bot_ban.ban_user_block(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="あなた、もしくはサーバーがBotからBanされています。",
                    )

                if not await bot_ban.ban_guild_block(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="あなた、もしくはサーバーがBotからBanされています。",
                    )
                
                interaction.extras["lang"] = await translate.get_guild_lang(interaction.guild.id)

                await self._call(interaction)

            except discord.app_commands.AppCommandError as e:
                await self._dispatch_error(interaction, e)

        self.client.loop.create_task(wrapper(), name="CommandTree-invoker")
