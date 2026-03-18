from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.search import NewsInfo
from core.database import redis_client

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/news", description="最新ニュースを取得する", summary="最新ニュースを取得", response_model=NewsInfo)
async def news_info():
    news = await redis_client.get("news")

    return {
        "news_url": news
    }