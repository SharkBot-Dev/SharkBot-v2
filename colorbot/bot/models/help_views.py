import discord
from discord.ext import commands

def chunk_list(data_list, chunk_size):
    if not data_list:
        return [[]]
    return [
        data_list[i:i + chunk_size]
        for i in range(0, len(data_list), chunk_size)
    ]

class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, user_: discord.User):
        super().__init__(timeout=180)
        self.cmds: list[dict] = []
        
        self.category_page = 0
        self.command_page = 0
        
        self.current_category: dict | None = None
        self.current_command: dict | None = None

        self.get_categories(bot)
        self.category_chunks = chunk_list(self.cmds, 10)
        
        self.user_ = user_

        self.update_ui()

    def add_cmd(self, name: str, description: str, sub: list | None = None):
        self.cmds.append({
            "name": name,
            "description": description or "説明なし",
            "sub": sub or []
        })

    def get_categories(self, bot: commands.Bot):
        for cmd in bot.tree.walk_commands(type=discord.AppCommandType.chat_input):
            if isinstance(cmd, discord.app_commands.Command):
                if cmd.parent is None:
                    self.add_cmd(cmd.qualified_name, cmd.description)
            elif isinstance(cmd, discord.app_commands.Group):
                subs = []
                for sub in cmd.commands:
                    subs.append({
                        "name": sub.qualified_name,
                        "description": sub.description or "説明なし",
                        "sub": []
                    })
                self.add_cmd(cmd.qualified_name, cmd.description, subs)

    def update_ui(self):
        self.clear_items()
        
        if self.current_category is None:
            self.add_item(CategorySelect(self))
            self.add_item(HelpOpSelect(self))
            self.add_item(PageButton(self, -1))
            self.add_item(PageButton(self, 1))
        elif self.current_command is None:
            self.add_item(BackButton(self))
            self.add_item(CommandSelect(self))
            self.add_item(PageButton(self, -1))
            self.add_item(PageButton(self, 1))
        else:
            self.add_item(BackButton(self))

    async def build_embed(self):
        if self.current_category is None:
            title = "カテゴリ一覧"
            chunks = self.category_chunks[self.category_page]
            description = "\n".join([f"**{c['name']}**\n└ {c['description']}" for c in chunks])
        
        elif self.current_command is None:
            cat_name = self.current_category["name"]
            title = f"カテゴリ: {cat_name}"
            subs = self.current_category["sub"]
            
            if not subs:
                description = "このカテゴリにサブコマンドはありません。\n(トップレベルコマンドです)"
            else:
                chunks = chunk_list(subs, 10)
                page_cmds = chunks[min(self.command_page, len(chunks)-1)]
                description = "\n".join([f"**{c['name']}**\n└ {c['description']}" for c in page_cmds])
        
        else:
            cmd = self.current_command
            title = f"コマンド詳細: {cmd['name']}"
            description = f"**説明:**\n{cmd['description']}"

        return discord.Embed(title=title, description=description, color=discord.Color.blue())

    async def interaction_check(self, interaction: discord.Interaction):
        if self.user_.id != interaction.user.id:
            return False
        return True

class CategorySelect(discord.ui.Select):
    def __init__(self, view: HelpView):
        self.view_help = view
        chunks = view.category_chunks[view.category_page]
        options = [discord.SelectOption(label=c["name"], description=c["description"][:100]) for c in chunks]
        super().__init__(placeholder="カテゴリを選択してください", options=options)

    async def callback(self, interaction: discord.Interaction):
        cat = next(c for c in self.view_help.cmds if c["name"] == self.values[0])
        self.view_help.current_category = cat
        self.view_help.command_page = 0
        self.view_help.update_ui()
        await interaction.response.edit_message(embed=await self.view_help.build_embed(), view=self.view_help)

class CommandSelect(discord.ui.Select):
    def __init__(self, view: HelpView):
        self.view_help = view
        subs = view.current_category["sub"]
        chunks = chunk_list(subs, 10)
        current_cmds = chunks[min(view.command_page, len(chunks)-1)]
        
        options = [discord.SelectOption(label=c["name"], description=c["description"][:100]) for c in current_cmds]
        super().__init__(placeholder="コマンドを選択して詳細を表示", options=options)

    async def callback(self, interaction: discord.Interaction):
        cmd = next(c for c in self.view_help.current_category["sub"] if c["name"] == self.values[0])
        self.view_help.current_command = cmd
        self.view_help.update_ui()
        await interaction.response.edit_message(embed=await self.view_help.build_embed(), view=self.view_help)

class BackButton(discord.ui.Button):
    def __init__(self, view: HelpView):
        super().__init__(label="戻る", style=discord.ButtonStyle.danger)
        self.view_help = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_help.current_command:
            self.view_help.current_command = None
        elif self.view_help.current_category:
            self.view_help.current_category = None
            
        self.view_help.update_ui()
        await interaction.response.edit_message(embed=await self.view_help.build_embed(), view=self.view_help)

class PageButton(discord.ui.Button):
    def __init__(self, view: HelpView, direction: int):
        self.direction = direction
        emoji = "◀" if direction == -1 else "▶"
        super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
        self.view_help = view

    async def callback(self, interaction: discord.Interaction):
        if self.view_help.current_category is None:
            max_p = len(self.view_help.category_chunks) - 1
            self.view_help.category_page = max(0, min(self.view_help.category_page + self.direction, max_p))
        else:
            chunks = chunk_list(self.view_help.current_category["sub"], 10)
            max_p = len(chunks) - 1
            self.view_help.command_page = max(0, min(self.view_help.command_page + self.direction, max_p))

        self.view_help.update_ui()
        await interaction.response.edit_message(embed=await self.view_help.build_embed(), view=self.view_help)

class HelpOpSelect(discord.ui.Select):
    def __init__(self, view: HelpView):
        super().__init__(placeholder="その他の操作")
        self.view_help = view

        self.add_option(label="この画面を閉じる", value="close")
        self.add_option(label="Botを招待する", value="invite")
        self.add_option(label="ロックする", value="lock")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        val = self.values[0]
        if val == "close":
            await interaction.message.delete()
        elif val == "lock":
            await interaction.message.edit(view=None)
        elif val == "invite":
            await interaction.followup.send(embed=discord.Embed(title="Botを招待する", color=discord.Color.green(), description="以下のボタンから招待できます。"), view=discord.ui.View()
                                            .add_item(discord.ui.Button(label="招待リンク", url=f"https://discord.com/oauth2/authorize?client_id={interaction.client.useer}&permissions=8&integration_type=0&scope=bot+applications.commands")),ephemeral=True)