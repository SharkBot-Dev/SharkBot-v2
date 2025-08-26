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