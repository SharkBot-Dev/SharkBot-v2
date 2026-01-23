import re
from discord.ext import commands
from discord import app_commands
import discord

from models import make_embed

COLOR_MAP = {
    "red": discord.Color.red(),
    "赤": discord.Color.red(),
    "blue": discord.Color.blue(),
    "青": discord.Color.red(),
    "green": discord.Color.green(),
    "緑": discord.Color.green(),
    "yellow": discord.Color.yellow(),
    "黄": discord.Color.yellow(),
    "pink": discord.Color.pink(),
    "ピンク": discord.Color.pink(),
    "white": discord.Color.from_str("#FFFFFF"),
    "白": discord.Color.from_str("#FFFFFF"),
    "black": discord.Color.from_str("#000000"),
    "黒": discord.Color.from_str("#000000"),
}

is_url = re.compile(r"https?://[\w!\?/\+\-_~=;\.,\*&@#$%\(\)'\[\]]+")


class EmbedBuilder(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="タイトル", style=discord.ButtonStyle.gray)
    async def title_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="タイトル編集"):
            text = discord.ui.Label(
                text="タイトルを入力",
                description="タイトルを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, max_length=30, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()

                em.title = self.text.component.value
                await ol_m.edit(embed=em)

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="説明", style=discord.ButtonStyle.gray)
    async def desc_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="説明編集"):
            text = discord.ui.Label(
                text="説明を入力",
                description="説明を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.long, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()

                em.description = self.text.component.value
                await ol_m.edit(embed=em)

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="画像", style=discord.ButtonStyle.gray)
    async def image_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="画像URLを追加"):
            text = discord.ui.Label(
                text="画像URL",
                description="画像URLを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    em.set_image(url=self.text.component.value)
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="サムネイル画像", style=discord.ButtonStyle.gray, emoji="🆕"
    )
    async def thum_image_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="サムネイル画像編集"):
            text = discord.ui.Label(
                text="サムネイル画像URL",
                description="サムネイル画像URLを入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    em.set_thumbnail(url=self.text.component.value)
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="フィールド追加", style=discord.ButtonStyle.gray, emoji="🆕", row=2
    )
    async def field_add_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="フィールド追加"):
            title_ = discord.ui.Label(
                text="フィールド名",
                description="フィールド名を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            value = discord.ui.Label(
                text="フィールドの内容",
                description="フィールドの内容を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.long, required=True
                ),
            )

            # inl = discord.ui.Label(
            #     text="Inlineを有効化するか",
            #     description="Inlineを有効化するか",
            #     component=discord.ui.Select(
            #         options=[discord.SelectOption(label="はい", value="yes"), discord.SelectOption(label="いいえ", value="no")], required=True, max_values=1, min_values=1
            #     ),
            # )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.title_.component, discord.ui.TextInput)
                assert isinstance(self.value.component, discord.ui.TextInput)
                # assert isinstance(self.inl.component, discord.ui.Select)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    # inline_bool = (self.inl.component.options[0].value == "yes")

                    em.add_field(
                        name=self.title_.component.value,
                        value=self.value.component.value,
                    )
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(
        label="フィールド削除", style=discord.ButtonStyle.gray, emoji="🆕", row=2
    )
    async def field_remove_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="フィールド削除"):
            title_ = discord.ui.Label(
                text="削除するフィールド名",
                description="削除するフィールド名を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.title_.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    for _, mf in enumerate(em.fields):
                        if mf.name == self.title_.component.value:
                            em.remove_field(_)
                    await ol_m.edit(embed=em)
                except:
                    return

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="色", style=discord.ButtonStyle.blurple, row=3)
    async def footer_edit_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        class EditTitleModal(discord.ui.Modal, title="色を入力"):
            text = discord.ui.Label(
                text="色",
                description="色を入力してください。",
                component=discord.ui.TextInput(
                    style=discord.TextStyle.short, required=True, default="#000000"
                ),
            )

            async def on_submit(self, interaction_: discord.Interaction):
                await interaction_.response.defer(ephemeral=True)

                assert isinstance(self.text.component, discord.ui.TextInput)

                ol_m = await interaction.original_response()

                em = ol_m.embeds[0].copy()
                try:
                    if not self.text.component.value.lower() in COLOR_MAP:
                        em.color = discord.Color.from_str(self.text.component.value)
                    else:
                        em.color = COLOR_MAP[self.text.component.value.lower()]
                    await ol_m.edit(embed=em)
                except:
                    return await interaction.followup.send(
                        ephemeral=True,
                        embed=make_embed.error_embed(
                            title="適切な色を入力してください。",
                            description="例: `#000000`",
                        ),
                    )

        await interaction.response.send_modal(EditTitleModal())

    @discord.ui.button(label="送信", style=discord.ButtonStyle.green, row=3)
    async def embed_send_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer(ephemeral=True)
        ol_m = await interaction.original_response()
        try:
            await interaction.channel.send(embed=ol_m.embeds[0].copy())
        except Exception as e:
            await interaction.followup.send(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="埋め込み送信時にエラーが発生しました。",
                    description=f"```{e}```",
                ),
            )
            return


class EmbedMake(discord.ui.Modal, title="埋め込みを作成"):
    title_ = discord.ui.TextInput(
        label="タイトル",
        placeholder="タイトル！",
        style=discord.TextStyle.short,
    )

    desc = discord.ui.TextInput(
        label="説明",
        placeholder="説明！",
        style=discord.TextStyle.long,
    )

    color = discord.ui.TextInput(
        label="色",
        placeholder="#000000",
        style=discord.TextStyle.short,
        default="#000000",
    )

    button_label = discord.ui.TextInput(
        label="ボタンラベル",
        placeholder="Webサイト",
        style=discord.TextStyle.short,
        required=False,
    )

    button = discord.ui.TextInput(
        label="ボタンurl",
        placeholder="https://www.sharkbot.xyz/",
        style=discord.TextStyle.short,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            view = discord.ui.View()
            if self.button.value:
                if self.button_label.value:
                    view.add_item(
                        discord.ui.Button(
                            label=self.button_label.value, url=self.button.value
                        )
                    )
                else:
                    view.add_item(
                        discord.ui.Button(label="Webサイト", url=self.button.value)
                    )
            await interaction.channel.send(
                embed=discord.Embed(
                    title=self.title_.value,
                    description=self.desc.value,
                    color=discord.Color.from_str(self.color.value),
                )
                .set_author(
                    name=f"{interaction.user.name}",
                    icon_url=interaction.user.avatar.url
                    if interaction.user.avatar
                    else interaction.user.default_avatar.url,
                )
                .set_footer(
                    text=f"{interaction.guild.name} | {interaction.guild.id}",
                    icon_url=interaction.guild.icon.url
                    if interaction.guild.icon
                    else interaction.user.default_avatar.url,
                ),
                view=view,
            )
        except Exception as e:
            return await interaction.followup.send(
                "作成に失敗しました。",
                ephemeral=True,
                embed=discord.Embed(
                    title="エラー内容",
                    description=f"```{e}```",
                    color=discord.Color.red(),
                ),
            )

class ToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("init -> ToolsCog")

    tools = app_commands.Group(name="tools", description="ツール系のコマンドです。")

    @tools.command(name="embed", description="埋め込みを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        操作モード=[
            app_commands.Choice(name="PC・Web", value="pc"),
            app_commands.Choice(name="スマホ・タブレット", value="phone"),
        ]
    )
    async def tools_embed(
        self,
        interaction: discord.Interaction,
        操作モード: app_commands.Choice[str] = None,
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )
        async def send_pc_embed_builder():
            await interaction.response.send_message(
                ephemeral=True,
                embed=discord.Embed(
                    title="埋め込みタイトル",
                    description="埋め込み説明です",
                    color=discord.Color.green(),
                )
                .set_author(
                    name=f"{interaction.user.name}",
                    icon_url=interaction.user.avatar.url
                    if interaction.user.avatar
                    else interaction.user.default_avatar.url,
                )
                .set_footer(
                    text=f"{interaction.guild.name} | {interaction.guild.id}",
                    icon_url=interaction.guild.icon.url
                    if interaction.guild.icon
                    else interaction.user.default_avatar.url,
                ),
                view=EmbedBuilder(),
            )

        if not 操作モード:
            is_pc = interaction.user.client_status.is_on_mobile()
            if not is_pc:
                await send_pc_embed_builder()
            else:
                await interaction.response.send_modal(EmbedMake())
            return

        if 操作モード.value == "pc":
            await send_pc_embed_builder()
        else:
            await interaction.response.send_modal(EmbedMake())

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_button_redirect(self, interaction: discord.Interaction):
        try:
            if interaction.data["component_type"] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if custom_id == "button_redirect+":
                    try:
                        await interaction.response.defer(ephemeral=True, thinking=True)
                        msg_id = interaction.message.id
                        db = interaction.client.async_db.ButtonRedirect
                        docs = await db.find_one({"guild_id": interaction.guild_id, "message_id": msg_id})

                        view = discord.ui.View()
                        view.add_item(discord.ui.Button(label="アクセスする", url=docs.get('url', "https://example.com/")))

                        await interaction.followup.send(embed=discord.Embed(title="説明", description="以下のボタンを押すことで先ほどの\nボタンのページに飛ぶことができます。", color=discord.Color.green())
                                                        .add_field(name="ボタンのページのURL", value=docs.get('url', "https://example.com/"), inline=False), view=view)
                    except Exception as e:
                        return await interaction.followup.send(embed=make_embed.error_embed(title="エラーが発生しました。", description=f"```{e}```"))
        except:
            return

    @tools.command(name="button", description="ボタンを作成します。")
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
    @app_commands.checks.cooldown(2, 10, key=lambda i: i.guild_id)
    @app_commands.choices(
        ボタンの種類=[
            app_commands.Choice(name="URLボタン", value="url"),
            app_commands.Choice(name="グレーボタン", value="gray"),
            app_commands.Choice(name="緑ボタン", value="green"),
            app_commands.Choice(name="赤ボタン", value="red"),
            app_commands.Choice(name="青ボタン", value="blue"),
            app_commands.Choice(name="押せないボタン", value="none"),
        ]
    )
    async def tools_button(
        self, interaction: discord.Interaction, ラベル: str, url: str, ボタンの種類: app_commands.Choice[str]
    ):
        if interaction.is_user_integration() and not interaction.is_guild_integration():
            return await interaction.response.send_message(
                ephemeral=True,
                embed=make_embed.error_embed(
                    title="このコマンドは使用できません。",
                    description="サーバーにBotをインストールして使用してください。",
                ),
            )

        if not is_url.search(url):
            return await interaction.response.send_message(
                ephemeral=True, content="URLを入力してください。"
            )

        view = discord.ui.View()
        if ボタンの種類.value == "url":
            view.add_item(discord.ui.Button(label=ラベル, url=url))
        elif ボタンの種類.value == "gray":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.gray))
        elif ボタンの種類.value == "green":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.green))
        elif ボタンの種類.value == "red":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.red))
        elif ボタンの種類.value == "blue":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.blurple))
        elif ボタンの種類.value == "none":
            view.add_item(discord.ui.Button(label=ラベル, custom_id="button_redirect+", style=discord.ButtonStyle.gray, disabled=True))

        await interaction.response.send_message(
            view=view
        )

        if ボタンの種類.value != "url":

            fet_message = await interaction.original_response()
            await interaction.client.async_db.ButtonRedirect.update_one(
                {"guild_id": interaction.guild.id, "channel_id": interaction.channel_id, "message_id": fet_message.id},
                {'$set': {"guild_id": interaction.guild.id, "channel_id": interaction.channel_id, "message_id": fet_message.id, "url": url}},
                upsert=True,
            )

async def setup(bot):
    await bot.add_cog(ToolsCog(bot))