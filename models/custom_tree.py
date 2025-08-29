import time
import discord

from models import command_disable, channel_command_disable, bot_ban

cooldown_check = {}


class CustomTree(discord.app_commands.CommandTree):
    def _from_interaction(self, interaction: discord.Interaction) -> None:
        async def wrapper():
            try:
                if not await command_disable.command_enabled_check(interaction):
                    current_time = time.time()
                    last_message_time = cooldown_check.get(interaction.user.id, 0)
                    if current_time - last_message_time < 5:
                        return
                    cooldown_check[interaction.user.id] = current_time

                    return await interaction.response.send_message(
                        ephemeral=True, content="そのコマンドは無効化されています。"
                    )

                if not await channel_command_disable.disable_channel(interaction):
                    current_time = time.time()
                    last_message_time = cooldown_check.get(interaction.user.id, 0)
                    if current_time - last_message_time < 5:
                        return
                    cooldown_check[interaction.user.id] = current_time

                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="このチャンネルではコマンドを使用できません。",
                    )

                if not await bot_ban.ban_user_block(interaction):
                    current_time = time.time()
                    last_message_time = cooldown_check.get(interaction.user.id, 0)
                    if current_time - last_message_time < 5:
                        return
                    cooldown_check[interaction.user.id] = current_time

                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="あなた、もしくはサーバーがBotからBanされています。",
                    )

                if not await bot_ban.ban_guild_block(interaction):
                    current_time = time.time()
                    last_message_time = cooldown_check.get(interaction.user.id, 0)
                    if current_time - last_message_time < 5:
                        return
                    cooldown_check[interaction.user.id] = current_time

                    return await interaction.response.send_message(
                        ephemeral=True,
                        content="あなた、もしくはサーバーがBotからBanされています。",
                    )

                await self._call(interaction)

            except discord.app_commands.AppCommandError as e:
                await self._dispatch_error(interaction, e)

        self.client.loop.create_task(wrapper(), name="CommandTree-invoker")
