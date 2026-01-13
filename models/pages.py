import discord

class JumpModal(discord.ui.Modal, title="ページ移動"):
    page_num = discord.ui.TextInput(
        label="移動先のページ番号を入力してください",
        placeholder="例: 1",
        min_length=1,
        max_length=3
    )

    def __init__(self, view: "Pages"):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_page = int(self.page_num.value) - 1
            
            if 0 <= target_page < len(self.view.embeds):
                self.view.now_page = target_page
                await self.view.update_view(interaction)
            else:
                await interaction.response.send_message(
                    f"1から{len(self.view.embeds)}の間で入力してください。", 
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message("有効な数値を入力してください。", ephemeral=True)

class Pages(discord.ui.View):
    def __init__(self, *, timeout=180, embeds: list[discord.Embed], now_page: int = 0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.now_page = now_page
        self.update_button_states()

    def update_button_states(self):
        self.back.disabled = (self.now_page == 0)
        self.next.disabled = (self.now_page == len(self.embeds) - 1)

    async def update_view(self, interaction: discord.Interaction):
        self.update_button_states()
        await interaction.response.edit_message(embed=self.embeds[self.now_page], view=self)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.gray)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.now_page > 0:
            self.now_page -= 1
            await self.update_view(interaction)

    @discord.ui.button(emoji="🔢", label="ページ指定", style=discord.ButtonStyle.primary)
    async def jump(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(JumpModal(self))

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.now_page < len(self.embeds) - 1:
            self.now_page += 1
            await self.update_view(interaction)