import discord
from discord.ext import commands
import aiohttp


class Container:
    def __init__(self, bot: commands.Bot):
        self.token = bot.http.token
        self.bot = bot
        self.comp = []

    def text(self, content: str):
        return {"type": 10, "content": content}

    def separator(self):
        return {"type": 14}

    def labeled_link(self, button_label: str, url: str):
        return {"type": 2, "style": 5, "label": button_label, "url": url}

    def labeled_customid_button(
        self, button_label: str, custom_id: str, style: int = 4
    ):
        return {
            "type": 2,
            "style": style,
            "label": button_label,
            "custom_id": custom_id,
        }

    def labeled_button(self, label: str, button: dict):
        return {
            "type": 9,
            "components": [{"type": 10, "content": label}],
            "accessory": button,
        }

    def media(self, url: str):
        return {
            "type": 12,
            "items": [
                {"media": {"url": url}},
            ],
        }

    def action_row(self, components: list):
        return {"type": 1, "components": components}

    def add_view(self, view: dict):
        self.comp.append(view)

    async def send(self, color: int, channel: int):
        url = f"https://discord.com/api/v10/channels/{channel}/messages"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "flags": 32768,
            "components": [
                {"type": 17, "accent_color": color, "components": self.comp}
            ],
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                return await resp.json()

    async def follow_up(self, color: int, interation_token: str):
        url = f"https://discord.com/api/v10/webhooks/{self.bot.user.id}/{interation_token}/messages/@original"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }
        data = {
            "flags": 32768,
            "components": [
                {"type": 17, "accent_color": color, "components": self.comp}
            ],
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=data) as resp:
                return await resp.json()

    async def edit(self, message: discord.Message, channel: int):
        url = f"https://discord.com/api/v10/channels/{channel}/messages/{message.id}"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }
        data = {"flags": 32768, "components": [{"type": 17, "components": self.comp}]}

        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers, json=data) as resp:
                return await resp.json()

    async def fetch(self, message: discord.Message, channel: int):
        url = f"https://discord.com/api/v10/channels/{channel}/messages/{message.id}"
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp_ = await resp.json()
                return resp_.get("components", None)


class ContainerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.container = Container


async def setup(bot):
    await bot.add_cog(ContainerCog(bot))
