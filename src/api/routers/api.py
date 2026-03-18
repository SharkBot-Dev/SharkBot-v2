from hmac import compare_digest
from typing import Optional

from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.api import APIKeyInfo
from core.database import mongo_client

router = APIRouter(prefix="/api", tags=["API"])

@router.get(
    "/key/{guildid}", 
    description="APIキーの情報を表示する", 
    summary="ボットのステータス取得", 
    response_model=APIKeyInfo
)
async def status_bot(
    guildid: str, 
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="認証に失敗しました。APIキーを確認してください")

    try:
        g_id = int(guildid)
    except ValueError:
        raise HTTPException(status_code=400, detail="指定形式が正しくありません")

    apikey_col = mongo_client["SharkAPI"]["APIKeys"]
    find = await apikey_col.find_one({"guild_id": g_id})

    if not find or not find.get('apikey', '') == authorization:
        raise HTTPException(status_code=401, detail="認証に失敗しました。APIキーを確認してください")

    return {
        "guild_id": str(find["guild_id"]),
        "user_id": str(find["user_id"]),
        "name": find["name"],
        "apikey": find["apikey"]
    }