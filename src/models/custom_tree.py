import time
import discord

from models import (
    command_disable,
    channel_command_disable,
    bot_ban,
    translate,
    make_embed,
)

cooldown_check = {}

async def is_can_use_command(interaction: discord.Interaction):
    commands = interaction.client.disabled_command
    
    cmd_name = command_disable.extract_command_name(interaction)

    if cmd_name in commands:
        return False
    
    return True

class CustomTree(discord.app_commands.CommandTree):
    def _from_interaction(self, interaction: discord.Interaction) -> None:
        async def wrapper():
            try:
                if not interaction.guild:
                    return await interaction.response.send_message(
                        embed=make_embed.error_embed(
                            title="DMではスラッシュコマンドを実行できません。"
                        ),
                        ephemeral=True,
                    )
                
                if not await is_can_use_command(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="そのコマンドは使用できません。",
                            description="そのコマンドは**Botの管理者**により\n無効化されています。",
                        ),
                    )

                if not await command_disable.command_enabled_check(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="そのコマンドは使用できません。",
                            description="そのコマンドは**サーバー管理者**により\n無効化されています。",
                        ),
                    )

                if not await channel_command_disable.disable_channel(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="コマンドを使用できません。",
                            description="このチャンネルではコマンドを使用できません。",
                        ),
                    )

                if not await bot_ban.ban_user_block(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="コマンドを使用できません。",
                            description="あなた、もしくはサーバーがBotからBanされています。",
                        ),
                    )

                if not await bot_ban.ban_guild_block(interaction):
                    return await interaction.response.send_message(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="コマンドを使用できません。",
                            description="あなた、もしくはサーバーがBotからBanされています。",
                        ),
                    )

                interaction.extras["lang"] = await translate.get_guild_lang(
                    interaction.guild.id
                )

                await self._call(interaction)

            except discord.app_commands.AppCommandError as e:
                await self._dispatch_error(interaction, e)

        self.client.loop.create_task(wrapper(), name="CommandTree-invoker")
