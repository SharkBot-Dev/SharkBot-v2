from discord.ext import commands, tasks
import discord
import datetime
from consts import settings
from discord import app_commands
from models import command_disable

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> HelpCog")

    @app_commands.command(name="help", description="ヘルプを表示します")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def help(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.defer()
        pages = []

        for c in self.bot.tree.get_commands():
            if type(c) == app_commands.Command:
                pages.append(discord.Embed(title=f"/{c.name}", description=f"{c.description}", color=discord.Color.blue()))
            elif type(c) == app_commands.Group:
                embed = discord.Embed(title=f"/{c.name}", color=discord.Color.blue())
                text = ""
                for cc in c.commands:
                    text += f"{cc.name} .. {cc.description}\n"
                embed.description = text
                pages.append(embed)

        class Help_view(discord.ui.View):
            def __init__(self, get_commands):
                super().__init__()
                self.get_commands = get_commands
                self.current_page = 0
                self.update_buttons()

            def update_buttons(self):
                self.clear_items()
                self.add_item(discord.ui.Button(emoji="◀️", style=discord.ButtonStyle.secondary, custom_id="help_prev"))
                self.add_item(discord.ui.Button(label=f"{self.current_page + 1}/{len(pages)}", style=discord.ButtonStyle.secondary, disabled=True))
                self.add_item(discord.ui.Button(emoji="▶️", style=discord.ButtonStyle.secondary, custom_id="help_next"))
                self.add_item(discord.ui.Button(label="カスタムコマンド", style=discord.ButtonStyle.red, custom_id="help_custom"))

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                try:
                    if interaction.data["custom_id"] == "help_prev":
                        if self.current_page > 0:
                            self.current_page -= 1
                    elif interaction.data["custom_id"] == "help_next":
                        if self.current_page < len(pages) - 1:
                            self.current_page += 1
                        else:
                            self.current_page = 0
                    elif interaction.data["custom_id"] == "help_custom":
                        cmds = await self.get_commands(interaction.guild)
                        await interaction.response.edit_message(embed=discord.Embed(title="カスタムコマンドヘルプ", description=f"""
    {"\n".join(cmds)}
    """, color=discord.Color.red()))
                        return
                    self.update_buttons()
                    await interaction.response.edit_message(embed=pages[self.current_page], view=self)
                    return True
                except:
                    return True

        view = Help_view(self.get_commands)
        await interaction.followup.send(embed=pages[0], view=view)

    @app_commands.command(name="dashboard", description="ダッシュボードのリンクを取得します。")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dashboard(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")

        await interaction.response.send_message(f"以下のリンクからアクセスできます。\n{settings.DASHBOARD_URL}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))