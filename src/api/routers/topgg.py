import random
from typing import Optional

import aiohttp
from fastapi import APIRouter, FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from discord import Webhook
import os

from core.database import mongo_client

router = APIRouter(prefix="/topgg", include_in_schema=False)

async def add_topgg(user_id: str):
    col = mongo_client["Main"]["TOPGGVote"]

    user_data = await col.find_one({"_id": int(user_id)})
    if user_data:
        await col.update_one({"_id": int(user_id)}, {"$inc": {"count": 1}})
    else:
        await col.insert_one({"_id": int(user_id), "count": 1})
    return True

async def add_account_money(user_id: str):
    col = mongo_client["DashboardBot"].Account

    user_data = await col.find_one({"user_id": int(user_id)})
    if user_data:
        await col.update_one({"user_id": int(user_id)}, {"$inc": {"money": random.randint(300, 1300)}})
    return True

@router.post("/webhook", include_in_schema=False)
async def topgg_vote_webhook(request: Request, authorization: Optional[str] = Header(None)):
    target_apikey = os.environ.get("APIKEY")
    if authorization != target_apikey:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    if not data or "user" not in data:
        raise HTTPException(status_code=400, detail="No data")

    try:
        await add_topgg(data["user"])
        await add_account_money(data["user"])
        
        webhook_url = os.environ.get("WEBHOOK")
        if webhook_url:
            async with aiohttp.ClientSession() as session:
                web = Webhook.from_url(webhook_url, session=session)
                await web.send(content=f"<@{data['user']}> さんがVoteをしてくれました！")
            
        return {"status": "received"}
    except Exception as e:
        print(f"Vote Error: {e}")
        raise HTTPException(status_code=500, detail="VoteError")