import os
from typing import Optional, List

import asyncio
import aiohttp
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

import dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Body
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from discord import Webhook

from pydantic import BaseModel, Field

dotenv.load_dotenv()

app = FastAPI(title="SharkAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="Templates")

redis_client = redis.from_url("redis://localhost", decode_responses=True)

mongo_client = AsyncIOMotorClient("mongodb://localhost:27017/")
db_main = mongo_client["Main"]
db_api = mongo_client["SharkAPI"]

async def add_topgg(user_id: str):
    col = db_main["TOPGGVote"]

    user_data = await col.find_one({"_id": int(user_id)})
    if user_data:
        await col.update_one({"_id": int(user_id)}, {"$inc": {"count": 1}})
    else:
        await col.insert_one({"_id": int(user_id), "count": 1})
    return True

@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/docs")

class Status(BaseModel):
    guilds_count: str = Field(..., example="100", description="Botの導入数")
    shards_count: str = Field(..., example="0", description="Botのシャード数")
    bot_ping: str = Field(..., example="170", description="BotのPing値")

@app.get("/status", description="Botのステータスを取得する。", tags=["System"], summary="ボットのステータス取得", response_model=Status)
async def status_bot():
    guilds_count = await redis_client.get("guilds_count")
    shards_count = await redis_client.get("shards_count")
    bot_ping = await redis_client.get("bot_ping")
    
    return {
        "guilds_count": guilds_count,
        "shards_count": shards_count,
        "bot_ping": bot_ping
    }

class EconomyInfo(BaseModel):
    currency: str = Field(..., example="コイン", description="サーバー固有の通貨名")

class UserBalance(BaseModel):
    money: int = Field(..., example=1000, description="所持金")
    bank: int = Field(..., example=5000, description="銀行残高")

class UpdateMoneyPayload(BaseModel):
    money: Optional[int] = Field(None, example=500, description="設定する所持金の額")
    bank: Optional[int] = Field(None, example=1000, description="設定する銀行の額")

class LeaderboardEntry(BaseModel):
    user_id: str = Field(..., example="123456789012345678", description="ユーザーID")
    money: int = Field(..., example=1000, description="所持金")
    bank: int = Field(..., example=5000, description="銀行残高")

@app.get("/economy/{guildid}", description="経済の情報を取得する。", summary="経済の情報を取得", response_model=EconomyInfo, tags=["Economy"])
async def economy_getinfo(guildid: str):
    col = db_main["ServerMoneyCurrency"]

    dbfind = await col.find_one({"_id": guildid}, {"_id": False})
    
    currency = dbfind.get("Name", "コイン") if dbfind else "コイン"
    return {"currency": currency}

@app.get("/economy/{guildid}/leaderboard", description="サーバー内の所持金ランキングトップ10を取得する。", summary="所持金ランキング取得", response_model=List[LeaderboardEntry], tags=["Economy"])
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

@app.get("/economy/{guildid}/{userid}", description="特定ユーザーがどのぐらいコインを持っているかを取得する。", summary="経済内のユーザー情報を取得する", response_model=UserBalance, tags=["Economy"])
async def economy_getmoney(guildid: str, userid: str):
    col = db_main["ServerMoney"]
    user_data = await col.find_one({"_id": f"{guildid}-{userid}"}, {"_id": False})
    
    if not user_data:
        return {"money": 0, "bank": 0}
    
    return {
        "money": user_data.get('count', 0),
        "bank": user_data.get('bank', 0)
    }

@app.patch("/economy/{guildid}/{userid}", description="特定のユーザーのコインの数を操作する", summary="特定のユーザーのコインの数を操作する", tags=["Economy"])
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

class NewsInfo(BaseModel):
    news_url: str = Field(..., example="ニュースのURL", description="ニュースのURL")

@app.get("/news", description="最新ニュースを取得する", summary="最新ニュースを取得", response_model=NewsInfo, tags=["Search"])
async def news_info():
    news = await redis_client.get("news")

    return {
        "news_url": news
    }

@app.post("/topgg/webhook", include_in_schema=False)
async def topgg_vote_webhook(request: Request, authorization: Optional[str] = Header(None)):
    target_apikey = os.environ.get("APIKEY")
    if authorization != target_apikey:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    if not data or "user" not in data:
        raise HTTPException(status_code=400, detail="No data")

    try:
        await add_topgg(data["user"])
        
        webhook_url = os.environ.get("WEBHOOK")
        if webhook_url:
            async with aiohttp.ClientSession() as session:
                web = Webhook.from_url(webhook_url, session=session)
                await web.send(content=f"<@{data['user']}> さんがVoteをしてくれました！")
            
        return {"status": "received"}
    except Exception as e:
        print(f"Vote Error: {e}")
        raise HTTPException(status_code=500, detail="VoteError")
    
asgi_app = app