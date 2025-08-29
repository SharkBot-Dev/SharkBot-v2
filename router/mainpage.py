import time
from fastapi import APIRouter, Form, Request
import httpx
from consts import settings, templates
from consts import mongodb
from models import command_disable
from fastapi.responses import RedirectResponse
import html

from fastapi import Depends

def rate_limiter(request: Request):
    return request.app.state.limiter.limit("1/2 seconds")

router = APIRouter()

@router.get("/", dependencies=[Depends(rate_limiter)])
async def index(request: Request):
    return RedirectResponse("https://www.sharkbot.xyz/")

@router.get("/rankcard", dependencies=[Depends(rate_limiter)])
async def rankcard(request: Request):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")
    
    return templates.templates.TemplateResponse(
        "rankcard.html",
        {
            "request": request,
            "user": u
        }
    )

@router.post("/rankcard/set", dependencies=[Depends(rate_limiter)])
async def rankcard_set(request: Request, color: str = Form(...)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")
    
    safe_color = html.escape(color)
    
    db = mongodb.mongo["Main"].RankColor
    await db.replace_one(
            {"User": int(u.get("id", "0"))}, 
            {"User": int(u.get("id", "0")), "Color": safe_color}, 
            upsert=True
        )
    
    return RedirectResponse("/rankcard", status_code=303)