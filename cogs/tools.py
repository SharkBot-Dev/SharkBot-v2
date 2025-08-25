from discord.ext import commands, tasks
import discord
import datetime
from consts import mongodb
from discord import app_commands
from models import command_disable

class EmbedMake(discord.ui.Modal, title='埋め込みを作成'):
    title_ = discord.ui.TextInput(
        label='タイトル',
        placeholder='タイトル！',
        style=discord.TextStyle.short,
    )

    desc = discord.ui.TextInput(
        label='説明',
        placeholder='説明！',
        style=discord.TextStyle.long,
    )

    color = discord.ui.TextInput(
        label='色',
        placeholder='#000000',
        style=discord.TextStyle.short,
        default="#000000"
    )

    button_label = discord.ui.TextInput(
        label='ボタンラベル',
        placeholder='Webサイト',
        style=discord.TextStyle.short,
        required=False
    )

    button = discord.ui.TextInput(
        label='ボタンurl',
        placeholder='https://www.sharkbot.xyz/',
        style=discord.TextStyle.short,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            view = discord.ui.View()
            if self.button.value:
                if self.button_label.value:
                    view.add_item(discord.ui.Button(label=self.button_label.value, url=self.button.value))
                else:
                    view.add_item(discord.ui.Button(label="Webサイト", url=self.button.value))
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.blurple, label="作成者の取得", custom_id="showembedowner"))
            await interaction.channel.send(embed=discord.Embed(title=self.title_.value, description=self.desc.value, color=discord.Color.from_str(self.color.value)).set_author(name=f"{interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url).set_footer(text=f"{interaction.guild.name} | {interaction.guild.id}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.user.default_avatar.url), view=view)
        except Exception as e:
            return await interaction.followup.send("作成に失敗しました。", ephemeral=True, embed=discord.Embed(title="エラー内容", description=f"```{e}```", color=discord.Color.red()))

class ToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"init -> ToolsCog")

    tools = app_commands.Group(name="tools", description="ツール系のコマンドです。")

    @tools.command(name="embed", description="埋め込みを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10)
    async def tools_embed(self, interaction: discord.Interaction):
        if not await command_disable.command_enabled_check(interaction):
            return await interaction.response.send_message(ephemeral=True, content="そのコマンドは無効化されています。")
        await interaction.response.send_modal(EmbedMake())

async def setup(bot):
    await bot.add_cog(ToolsCog(bot))