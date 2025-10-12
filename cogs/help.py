from discord.ext import commands
import discord
from consts import settings
from discord import app_commands
from models import command_disable, make_embed


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> HelpCog")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandNotFound):
            a = None
            return a
        elif isinstance(error, commands.CommandOnCooldown):
            a = None
            return a

    @app_commands.command(name="help", description="ヘルプを表示します")
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ヘルプの表示形態=[
            app_commands.Choice(name="見やすくなったヘルプ", value="new"),
            app_commands.Choice(name="カテゴリ別のヘルプ", value="category"),
        ]
    )
    async def help(self, interaction: discord.Interaction, ヘルプの表示形態: app_commands.Choice[str] = None):
        await interaction.response.defer()

        if ヘルプの表示形態 == app_commands.Choice(name="見やすくなったヘルプ", value="new"):
            embeds = []

            commands_list = list(self.bot.tree.get_commands())

            def new_embed():
                return make_embed.success_embed(
                    title="SharkBotのヘルプ (スラッシュコマンド版)",
                    description="スラッシュコマンド版のヘルプです。\n頭文字コマンド用ヘルプは `!.help` を使用してください。"
                )

            embed = new_embed()
            field_count = 0

            for c in commands_list:
                if isinstance(c, app_commands.Command):
                    name = f"/{c.name}"
                    desc = c.description or "説明なし"
                    embed.add_field(name=name, value=desc, inline=False)
                    field_count += 1

                elif isinstance(c, app_commands.Group):
                    for cc in c.commands:
                        name = f"/{c.name} {cc.name}"
                        desc = cc.description or "説明なし"
                        embed.add_field(name=name, value=desc, inline=False)
                        field_count += 1

                        if field_count >= 10:
                            embeds.append(embed)
                            embed = new_embed()
                            field_count = 0

                if field_count >= 10:
                    embeds.append(embed)
                    embed = new_embed()
                    field_count = 0

            if field_count > 0:
                embeds.append(embed)

            class Help_view(discord.ui.View):
                def __init__(self, get_commands):
                    super().__init__()
                    self.get_commands = get_commands
                    self.current_page = 0
                    self.update_buttons()

                def update_buttons(self):
                    self.clear_items()
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏮️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prex_skip_beta",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="◀️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prev_beta",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            label=f"{self.current_page + 1}/{len(embeds)}",
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="▶️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next_beta",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏭️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next_skip_beta",
                        )
                    )

                async def interaction_check(self, interaction: discord.Interaction) -> bool:
                    try:
                        if interaction.data["custom_id"] == "help_prev_beta":
                            if self.current_page > 0:
                                self.current_page -= 1
                        elif interaction.data["custom_id"] == "help_next_beta":
                            if self.current_page < len(embeds) - 1:
                                self.current_page += 1
                            else:
                                self.current_page = 0
                        elif interaction.data["custom_id"] == "help_next_skip_beta":
                            self.current_page = len(embeds) - 1
                        elif interaction.data["custom_id"] == "help_prex_skip_beta":
                            self.current_page = 0
                        self.update_buttons()
                        await interaction.response.edit_message(
                            embed=embeds[self.current_page], view=self
                        )
                        return True
                    except:
                        return True

            view = Help_view(self.get_commands)
            await interaction.followup.send(embed=embeds[0], view=view)
        else:
            pages = []

            pages.append(discord.Embed(title="カテゴリ別のヘルプ", description="▶️ ボタンでメインのヘルプを閲覧できます。", color=discord.Color.blue()).add_field(name="このヘルプについて", value="スラッシュコマンド版のヘルプです。\n頭文字コマンド用ヘルプは !.help を使用してください。", inline=False))

            for c in self.bot.tree.get_commands():
                if type(c) == app_commands.Command:
                    pages.append(
                        discord.Embed(
                            title=f"/{c.name}",
                            description=f"{c.description}",
                            color=discord.Color.blue(),
                        )
                    )
                elif type(c) == app_commands.Group:
                    embed = discord.Embed(title=f"/{c.name} ({c.description})", color=discord.Color.blue())
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
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏮️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prex_skip",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="◀️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_prev",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            label=f"{self.current_page + 1}/{len(pages)}",
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="▶️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next",
                        )
                    )
                    self.add_item(
                        discord.ui.Button(
                            emoji="⏭️",
                            style=discord.ButtonStyle.green,
                            custom_id="help_next_skip",
                        )
                    )

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
                        elif interaction.data["custom_id"] == "help_next_skip":
                            self.current_page = len(pages) - 1
                        elif interaction.data["custom_id"] == "help_prex_skip":
                            self.current_page = 0
                        self.update_buttons()
                        await interaction.response.edit_message(
                            embed=pages[self.current_page], view=self
                        )
                        return True
                    except:
                        return True

            view = Help_view(self.get_commands)
            await interaction.followup.send(embed=pages[0], view=view)

    @app_commands.command(
        name="dashboard", description="ダッシュボードのリンクを取得します。"
    )
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    async def dashboard(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(
                ephemeral=True, content="そのコマンドは無効化されています。"
            )

        await interaction.response.send_message(
            f"以下のリンクからアクセスできます。\n{settings.DASHBOARD_URL}",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
