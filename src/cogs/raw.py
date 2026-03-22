from typing import List, Union

import discord
from discord.ext import commands
import aiohttp
import base64
import mimetypes
import io
import asyncio

from models.raw_error import SearchAPIError, SearchIndexNotReady


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
    def __init__(self, bot: commands.Bot = None):
        if not bot:
            raise ValueError("token か bot を指定してください")
        self.token = bot.http.token
        self.bot = bot
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

    async def get_guild_role_member_counts(self, guildId: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/guilds/{guildId}/roles/member-counts",
                headers={"Authorization": f"Bot {self.token}"},
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"Failed to modify member: {response.status} {text}"
                    )
                return await response.json()

    async def create_channel_invite(
        self,
        channelId: str,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
        role_ids: list[int] = None,
        target_type: int = None,
        target_user_id: int = None,
        target_application_id: int = None,
    ):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/channels/{channelId}/invites",
                headers={"Authorization": f"Bot {self.token}"},
                json={
                    "max_age": max_age,
                    "max_uses": max_uses,
                    "temporary": temporary,
                    "unique": unique,
                    "target_type": target_type,
                    "target_user_id": target_user_id,
                    "target_application_id": target_application_id,
                    "role_ids": role_ids,
                },
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"Failed to invite channel: {response.status} {text}"
                    )
                return await response.json()

    async def get_channel_invite_target_user(self, inviteCode: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_base}/invites/{inviteCode}",
                headers={"Authorization": f"Bot {self.token}"},
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"Failed to get invite target user: {response.status} {text}"
                    )
                return await response.json()

    async def search_messages(
        self,
        guild_id: Union[int, str],
        **params
    ) -> List[discord.Message]:
        url = f"{self.api_base}/guilds/{guild_id}/messages/search"
        headers = {"Authorization": f"Bot {self.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                
                if resp.status == 202:
                    data = await resp.json()
                    raise SearchIndexNotReady(
                        message=data.get("message", "Index not yet available"),
                        retry_after=data.get("retry_after", 2.0),
                        documents_indexed=data.get("documents_indexed", 0)
                    )

                if resp.status != 200:
                    error_text = await resp.text()
                    raise SearchAPIError(resp.status, error_text)

                data = await resp.json()
                search_results = data.get("messages", [])
                
                messages = []
                state = self.bot._connection 

                for group in search_results:
                    for msg_dict in group:
                        c_id = int(msg_dict['channel_id'])
                        channel = self.bot.get_channel(c_id) or discord.Object(id=c_id)
                        message = discord.Message(state=state, channel=channel, data=msg_dict)
                        messages.append(message)
                
                return messages

class RawCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.raw = Raw


async def setup(bot):
    await bot.add_cog(RawCog(bot))
