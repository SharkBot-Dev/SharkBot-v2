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

class BaseToggle:
    def __init__(self, name: str, default_boolean: bool, toggled_call_function):
        self.name = name
        self.toggled_call_function = toggled_call_function
        self.value = default_boolean

    async def _execute_toggle(self, interaction: discord.Interaction, target):
        self.value = not self.value

class ContextMessageToggle(BaseToggle):
    async def toggle(self, interaction: discord.Interaction, message: discord.Message):
        await self._execute_toggle(interaction, message)

class ContextUserToggle(BaseToggle):
    async def toggle(self, interaction: discord.Interaction, user):
        await self._execute_toggle(interaction, user)

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
            if type(func) == ContextMessageToggle or type(func) == ContextUserToggle:
                if func.value:
                    section = discord.ui.Section(discord.ui.TextDisplay(func.name), accessory=discord.ui.Button(
                        label="無効化",
                        custom_id=f"context_toggle_{func.name}",
                        style=discord.ButtonStyle.green
                    ))
                else:
                    section = discord.ui.Section(discord.ui.TextDisplay(func.name), accessory=discord.ui.Button(
                        label="有効化",
                        custom_id=f"context_toggle_{func.name}",
                        style=discord.ButtonStyle.red
                    ))
            else:
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

        if cid.startswith("context_toggle_"):
            name = cid.replace("context_toggle_", "")

            for func in self.functions:
                if func.name != name:
                    continue

                if not isinstance(func, (ContextMessageToggle, ContextUserToggle)):
                    continue

                await func.toggle(interaction, self.target)

                self.render()
                await interaction.response.edit_message(view=self)

                await func.toggled_call_function(interaction, self.target, func.value)

                return False

        return True