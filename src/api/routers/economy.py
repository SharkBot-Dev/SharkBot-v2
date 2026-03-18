from typing import List, Optional

from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from models.economy import EconomyInfo, LeaderboardEntry, UpdateMoneyPayload, UserBalance
from core.database import mongo_client

db_main = mongo_client["Main"]
db_api = mongo_client["SharkAPI"]

router = APIRouter(prefix="/economy", tags=["Economy"])

@router.get("/{guildid}", description="経済の情報を取得する。", summary="経済の情報を取得", response_model=EconomyInfo)
async def economy_getinfo(guildid: str):
    col = db_main["ServerMoneyCurrency"]

    dbfind = await col.find_one({"_id": guildid}, {"_id": False})
    
    currency = dbfind.get("Name", "コイン") if dbfind else "コイン"
    return {"currency": currency}

@router.get("/{guildid}/leaderboard", description="サーバー内の所持金ランキングトップ10を取得する。", summary="所持金ランキング取得", response_model=List[LeaderboardEntry])
async def economy_leaderboard(guildid: str):
    col = db_main["ServerMoney"]
    cursor = col.find({"_id": {"$regex": f"^{guildid}-"}}).sort("count", -1).limit(10)
    
    results = []
    async for doc in cursor:
        try:
            u_id = doc["_id"].split("-")[1]
            results.append(LeaderboardEntry(user_id=u_id, money=doc.get("count", 0), bank=doc.get("bank", 0)))
        except IndexError:
            continue
    
    return results

@router.get("/{guildid}/{userid}", description="特定ユーザーがどのぐらいコインを持っているかを取得する。", summary="経済内のユーザー情報を取得する", response_model=UserBalance)
async def economy_getmoney(guildid: str, userid: str):
    col = db_main["ServerMoney"]
    user_data = await col.find_one({"_id": f"{guildid}-{userid}"}, {"_id": False})
    
    if not user_data:
        return {"money": 0, "bank": 0}
    
    return {
        "money": user_data.get('count', 0),
        "bank": user_data.get('bank', 0)
    }

@router.patch("/{guildid}/{userid}", description="特定のユーザーのコインの数を操作する", summary="特定のユーザーのコインの数を操作する")
async def economy_patchmoney(
    guildid: str, 
    userid: str, 
    payload: UpdateMoneyPayload,
    authorization: Optional[str] = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        g_id = int(guildid)
    except ValueError:
        raise HTTPException(status_code=400, detail="指定形式が正しくありません")

    apikey_col = db_api["APIKeys"]
    key_record = await apikey_col.find_one({"guild_id": g_id})
    
    if not key_record or authorization != key_record.get('apikey'):
        raise HTTPException(status_code=401, detail="Unauthorized")

    update_fields = {}
    try:
        if 'money' in payload:
            update_fields["count"] = int(payload["money"])
        if 'bank' in payload:
            update_fields["bank"] = int(payload["bank"])
    except ValueError:
        raise HTTPException(status_code=400, detail="数値形式が正しくありません")

    if not update_fields:
        raise HTTPException(status_code=400, detail="更新する項目がありません")

    col = db_main["ServerMoney"]
    result = await col.update_one(
        {"_id": f"{guildid}-{userid}"},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="指定されたユーザーが見つかりません")

    return {"success": True}