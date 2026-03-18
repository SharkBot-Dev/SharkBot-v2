from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.bot import Status, Ping
from core.database import redis_client

status_router = APIRouter(prefix="/status", tags=["SystemStatus"])

@status_router.get("/", description="Botのステータスを取得する。", summary="ボットのステータス取得", response_model=Status)
async def status_bot():
    guilds_count = await redis_client.get("guilds_count")
    users_count = await redis_client.get("users_count")
    shards_count = await redis_client.get("shards_count")
    bot_ping = await redis_client.get("bot_ping")
    
    return {
        "guilds_count": guilds_count,
        "users_count": users_count,
        "shards_count": shards_count,
        "bot_ping": bot_ping
    }

@status_router.get("/ping", description="BotのPingを取得する。", summary="ボットのPing取得", response_model=Ping)
async def status_bot_ping():
    bot_ping = await redis_client.get("bot_ping")
    
    return {
        "bot_ping": bot_ping
    }