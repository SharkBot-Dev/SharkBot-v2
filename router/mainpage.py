from fastapi import APIRouter, Form, Request
from consts import templates
from consts import mongodb
from fastapi.responses import RedirectResponse, PlainTextResponse
import html
from models import string_id

from fastapi import Depends


def rate_limiter(request: Request):
    return request.app.state.limiter.limit("1/2 seconds")


router = APIRouter()


@router.get("/", dependencies=[Depends(rate_limiter)])
async def index(request: Request):
    return RedirectResponse("https://www.sharkbot.xyz/")


@router.get("/omikuji", dependencies=[Depends(rate_limiter)])
async def omikuji(request: Request):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    return templates.templates.TemplateResponse(
        "omikuji.html", {"request": request, "user": u}
    )

@router.get("/pastebin", dependencies=[Depends(rate_limiter)])
async def paste_bin(request: Request, id: str = None):
    if not id:
        return templates.templates.TemplateResponse("pastebin.html", {"request": request, 'text': 'まだ何もありません。', 'textid': string_id.string_id(20)})
    text = await mongodb.mongo["DashboardBot"].PasteBin.find_one(
        {'TextID': id}
    )
    if not text:
        return templates.templates.TemplateResponse("pastebin.html", {"request": request, 'text': 'まだ何もありません。', 'textid': string_id.string_id(20)})
    return templates.templates.TemplateResponse("pastebin.html", {"request": request, 'text': text.get('Text', 'エラー'), 'textid': id})

@router.post("/pastebin/save", dependencies=[Depends(rate_limiter)])
async def paste_bin_save(request: Request, text: str = Form(...), id: str = Form(...)):
    if len(text) > 301:
        return PlainTextResponse('テキストが大きすぎます。\n300以下にしてください。')
    db = mongodb.mongo["DashboardBot"].PasteBin
    i = html.escape(id)
    check = db.find_one(
        {'TextID': i}
    )
    if not check:
        return PlainTextResponse('そのIDは既に使われています。')
    await db.update_one(
        {'TextID': i},
        {'$set': {'TextID': i, 'Text': html.escape(text)}},
        upsert=True,
    )

    return RedirectResponse(f'/pastebin?id={i}', status_code=303)

@router.get("/pastebin/delete", dependencies=[Depends(rate_limiter)])
async def paste_bin_delete(request: Request, id: str = None):
    if not id:
        return RedirectResponse(f'/pastebin')
    db = mongodb.mongo["DashboardBot"].PasteBin
    i = html.escape(id)
    await db.delete_one({'TextID': i})
    return RedirectResponse(f'/pastebin')

@router.get("/rankcard", dependencies=[Depends(rate_limiter)])
async def rankcard(request: Request):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    return templates.templates.TemplateResponse(
        "rankcard.html", {"request": request, "user": u}
    )


@router.post("/rankcard/set", dependencies=[Depends(rate_limiter)])
async def rankcard_set(request: Request, color: str = Form(...)):
    u = request.session.get("user")
    if u is None:
        return RedirectResponse("/login")

    safe_color = html.escape(color)

    db = mongodb.mongo["Main"].RankColor
    await db.update_one(
        {"User": int(u.get("id", "0"))},
        {'$set': {"User": int(u.get("id", "0")), "Color": safe_color}},
        upsert=True,
    )

    return RedirectResponse("/rankcard", status_code=303)
