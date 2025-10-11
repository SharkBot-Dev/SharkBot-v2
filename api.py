from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import httpx
import uvicorn
from router import settings as s_r
from router import mainpage
from starlette.middleware.sessions import SessionMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from consts import mongodb
from consts import settings, templates

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSINKEY)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(s_r.router)
app.include_router(mainpage.router)

@app.get("/login")
async def login():
    url = (
        f"{settings.DISCORD_API}/oauth2/authorize"
        f"?client_id={settings.CLIENT_ID}&redirect_uri={settings.REDIRECT_URI}"
        f"&response_type=code&scope=identify%20guilds"
    )
    return RedirectResponse(url)


@app.get("/login/callback")
@limiter.limit("1/minute")
async def callback(request: Request, code: str):
    async with httpx.AsyncClient() as client:
        token = await client.post(
            f"{settings.DISCORD_API}/oauth2/token",
            data={
                "client_id": settings.CLIENT_ID,
                "client_secret": settings.CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        access_token = token.json()["access_token"]

        user = await client.get(
            f"{settings.DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        user_guilds = (
            await client.get(
                f"{settings.DISCORD_API}/users/@me/guilds",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        ).json()

        request.session["user"] = user.json()
        u = user.json()

        await mongodb.mongo["DashboardBot"].user_guilds.replace_one(
            {"User": u.get("id")},
            {"User": u.get("id"), "Guilds": user_guilds},
            upsert=True,
        )

        return RedirectResponse("/login/guilds")


@app.get("/login/guilds")
@limiter.limit("3/10 seconds")
async def guilds(request: Request):
    if request.session.get("user") is None:
        return RedirectResponse("/login")

    u = request.session["user"]

    guilds = await mongodb.mongo["DashboardBot"].user_guilds.find_one(
        {"User": u.get("id", "0")}
    )

    if guilds is None:
        return RedirectResponse("/login")

    return templates.templates.TemplateResponse(
        "guilds.html",
        {
            "request": request,
            "guilds": [g for g in guilds.get("Guilds", []) if g.get("owner")],
            "message": f"{u.get('username', 'ゲスト')}さん、よろしく！",
        },
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5050, log_level="debug")
