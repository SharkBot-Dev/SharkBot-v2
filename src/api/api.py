from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import dotenv

from routers import account, api, bot, economy, search, sgc, topgg

dotenv.load_dotenv()

app = FastAPI(title="SharkAPI", description="SharkBotのAPIです。")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account.router)
app.include_router(api.router)
app.include_router(bot.status_router)
app.include_router(economy.router)
app.include_router(search.router)
app.include_router(topgg.router)
app.include_router(sgc.router)

@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/docs")
    
asgi_app = app