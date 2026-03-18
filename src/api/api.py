import os
import random
from typing import Optional, List

import asyncio
import aiohttp
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

import dotenv
from fastapi import FastAPI, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from discord import Webhook

from routers import account, bot, economy, search, topgg

dotenv.load_dotenv()

app = FastAPI(title="SharkAPI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account.router)
app.include_router(bot.status_router)
app.include_router(economy.router)
app.include_router(search.router)
app.include_router(topgg.router)

@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/docs")
    
asgi_app = app