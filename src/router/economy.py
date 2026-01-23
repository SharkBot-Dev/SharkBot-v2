import time
from fastapi import APIRouter, Depends, Form, Request
import httpx
from consts import settings, templates
from consts import mongodb
from models import command_disable
from fastapi.responses import RedirectResponse
import html

router = APIRouter(prefix="/settings")


def rate_limiter(request: Request):
    return request.app.state.limiter.limit("1/2 seconds")


async def check_owner(user, guild_id: str) -> bool:
    user_guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": user.get("id")}
    )
    guild = next(
        (g for g in user_guilds.get("Guilds", []) if g.get("id") == guild_id), None
    )
    if guild is None:
        return False

    if not guild.get("owner"):
        return False

    bot_joined = await mongodb.mongo["DashboardBot"].bot_joind_guild.find_one(
        {"Guild": int(guild_id)}
    )

    if bot_joined is None:
        return False

    return True


@router.get("/{guild_id}/economy", dependencies=[Depends(rate_limiter)])
async def economy(request: Request, guild_id: str):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id")}
    )
    guild = next((g for g in guilds.get("Guilds", []) if g.get("id") == guild_id), None)
    if guild is None:
        return RedirectResponse("/login/guilds")

    if not await check_owner(u, guild_id):
        return RedirectResponse("/login/guilds")

    return templates.templates.TemplateResponse(
        "economy.html",
        {"request": request, "guild": guild},
    )
