import discord
from discord.ext import commands
import aiohttp
import base64
import mimetypes
import io
import asyncio


def image_to_data_uri_sync(
    image_path: str = None, io_: io.BytesIO = None, mime_type: str = None
) -> str:
    if image_path:
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            raise ValueError("MIMEタイプを判定できませんでした")
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

    elif io_:
        if mime_type is None:
            mime_type = "image/png"
        encoded = base64.b64encode(io_.getvalue()).decode("utf-8")

    else:
        raise ValueError("image_pathかio_のどちらかを指定してください。")

    return f"data:{mime_type};base64,{encoded}"


class Raw:
    def __init__(self, token: str = None, bot: commands.Bot = None):
        if not token:
            if not bot:
                raise ValueError("token か bot を指定してください")
            self.token = bot.http.token
        else:
            self.token = token
        self.api_base = "https://discord.com/api/v10"

    async def image_to_data_uri(
        self, image_path: str = None, io_: io.BytesIO = None, mime_type: str = None
    ):
        return await asyncio.to_thread(
            image_to_data_uri_sync, image_path, io_, mime_type
        )

    async def modify_current_member(
        self,
        guildId: str,
        bannerUri: str = None,
        avatarUri: str = None,
        nick: str = None,
        bio: str = None,
    ):
        payload = {}
        if bannerUri is not None:
            payload["banner"] = bannerUri
        else:
            payload["banner"] = None
        if avatarUri is not None:
            payload["avatar"] = avatarUri
        else:
            payload["avatar"] = None
        if bio is not None:
            payload["bio"] = bio
        else:
            payload["bio"] = None
        if nick is not None:
            payload["nick"] = nick
        else:
            payload["nick"] = None

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                f"{self.api_base}/guilds/{guildId}/members/@me",
                headers={"Authorization": f"Bot {self.token}"},
                json=payload,
            ) as response:
                if response.status == 400:
                    raise discord.RateLimited(30.0)
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"Failed to modify member: {response.status} {text}"
                    )
                return await response.json()


class RawCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.raw = Raw


async def setup(bot):
    await bot.add_cog(RawCog(bot))
