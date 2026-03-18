from typing import Optional

from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.api import APIKeyInfo
from core.database import mongo_client

router = APIRouter(prefix="/api", tags=["API"])

@router.get("/key", description="APIキーの情報を表示する", summary="ボットのステータス取得", response_model=APIKeyInfo)
async def status_bot(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    db = mongo_client["SharkAPI"].APIKeys

    find = await db.find_one({
        "apikey": authorization
    })

    if not find:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return {
        "guild_id": find["guild_id"],
        "user_id": find["user_id"],
        "name": find["name"],
        "apikey": find["apikey"]
    }