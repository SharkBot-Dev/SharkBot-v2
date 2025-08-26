import time
from fastapi import APIRouter, Form, Request
import httpx
from consts import settings, templates
from consts import mongodb
from models import command_disable
from fastapi.responses import RedirectResponse
import html

router = APIRouter()

@router.get("/")
async def index(request: Request):
    return templates.templates.TemplateResponse("index.html", {
        "request": request
    })