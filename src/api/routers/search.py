import datetime

from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.search import NewsInfo, SnowflakeInfo
from core.database import redis_client

DISCORD_EPOCH = 1420070400000

def decode_snowflake(snowflake: int):
    timestamp_ms = (snowflake >> 22) + DISCORD_EPOCH
    dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000, tz=datetime.timezone.utc)

    worker_id = (snowflake & 0x3E0000) >> 17
    process_id = (snowflake & 0x1F000) >> 12
    increment = snowflake & 0xFFF

    return {
        "timestamp": dt,
        "worker_id": worker_id,
        "process_id": process_id,
        "increment": increment,
    }

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/news", description="最新ニュースを取得する", summary="最新ニュースを取得", response_model=NewsInfo)
async def news_info():
    news = await redis_client.get("news")

    return {
        "news_url": news
    }

@router.get(
    "/snowflake/{snowflake}", 
    description="DiscordのSnowflake IDを解析して詳細情報を返します", 
    summary="Snowflakeを解析", 
    response_model=SnowflakeInfo
)
async def get_snowflake_info(
    snowflake: str
):
    try:
        snowflake_int = int(snowflake)
    except ValueError:
        raise HTTPException(status_code=400, detail="指定形式が正しくありません")

    result = decode_snowflake(snowflake_int)
    return result