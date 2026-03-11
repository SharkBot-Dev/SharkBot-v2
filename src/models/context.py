import discord
import math

class ContextMessageFunction:
    def __init__(self, name: str, function):
        self.name = name
        self.function = function

    async def execute(self, origin_interaction: discord.Interaction, interaction: discord.Interaction, message: discord.Message):
        await self.function(origin_interaction, interaction, message)

class ContextUserFunction:
    def __init__(self, name: str, function):
        self.name = name
        self.function = function

    async def execute(self, origin_interaction: discord.Interaction, interaction: discord.Interaction, user):
        await self.function(origin_interaction, interaction, user)

class ContextMoreView(discord.ui.LayoutView):
    def __init__(self, interaction: discord.Interaction, functions: list, target):
        super().__init__(timeout=180)

        self.interaction = interaction
        self.functions = functions
        self.target = target

        if isinstance(target, discord.Message):
            self.target_type = "message"
        else:
            self.target_type = "user"

        self.page = 0
        self.per_page = 5
        self.max_page = math.ceil(len(functions) / self.per_page) - 1

        self.render()

    def render(self):
        self.clear_items()

        container = discord.ui.Container()

        start = self.page * self.per_page
        end = start + self.per_page

        for func in self.functions[start:end]:
            section = discord.ui.Section(discord.ui.TextDisplay(func.name), accessory=discord.ui.Button(
                label="実行",
                custom_id=f"context_func_{func.name}",
                style=discord.ButtonStyle.blurple
            ))

            container.add_item(section)

        self.add_item(container)

        nav_row = discord.ui.ActionRow()

        nav_row.add_item(
            discord.ui.Button(
                label="◀",
                custom_id="context_prev_page",
                disabled=self.page == 0
            )
        )

        nav_row.add_item(
            discord.ui.Button(
                label=f"{self.page+1}/{self.max_page+1}",
                disabled=True
            )
        )

        nav_row.add_item(
            discord.ui.Button(
                label="▶",
                custom_id="context_next_page",
                disabled=self.page == self.max_page
            )
        )

        self.add_item(nav_row)

    async def interaction_check(self, interaction: discord.Interaction):

        cid = interaction.data["custom_id"]

        if cid == "context_prev_page":
            self.page -= 1
            self.render()
            await interaction.response.edit_message(view=self)
            return False

        if cid == "context_next_page":
            self.page += 1
            self.render()
            await interaction.response.edit_message(view=self)
            return False

        if cid.startswith("context_func_"):
            name = cid.replace("context_func_", "")

            for func in self.functions:
                if func.name == name:

                    if self.target_type == "message":
                        await func.execute(self.interaction, interaction, self.target)

                    elif self.target_type == "user":
                        await func.execute(self.interaction, interaction, self.target)

                    return False

        return True