from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.account import AccountInfo
from core.database import mongo_client

router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/{userid}", response_model=AccountInfo, summary="アカウントの情報を取得", description="アカウントの情報を取得します。")
async def account_info(userid: str):
    try:
        userId = int(userid)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "指定形式が正しくありません"}
        )

    col = mongo_client["DashboardBot"].Account
    dbfind = await col.find_one({"user_id": userId}, {"_id": False})
    
    if not dbfind:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "アカウントが存在しません。"}
        )
    
    return {
        "user_id": userid,
        "user_name": dbfind.get('user_name'),
        "avatar_url": dbfind.get('avatar_url'),
        "money": dbfind.get('money')
    }
