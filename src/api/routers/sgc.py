import os

from fastapi import APIRouter, FastAPI, Path, Request, Header, HTTPException, Body, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from core.database import redis_client

router = APIRouter(prefix="/sgc", tags=["SuperGlobalChat"])

SNOWFLAKE_VALIDATOR = Path(..., regex="^\d{17,20}$", description="DiscordのメッセージID")

@router.get("/json/{messageid}", description="スーパーグローバルチャットのJsonを取得すr", summary="SGCのjson取得")
async def sgc_json_get(messageid: str = SNOWFLAKE_VALIDATOR):
    redis_key = f"message:sgc:{messageid}"

    data = await redis_client.hgetall(redis_key)

    if not data:
        raise HTTPException(
            status_code=404, 
            detail="Message not found or expired"
        )

    return data

@router.post("/json/{messageid}", include_in_schema=False)
async def sgc_json_create(messageid: str = SNOWFLAKE_VALIDATOR, data: dict = Body(...), authorization: str = Header(None)):
    if authorization != os.environ.get('SGCAPIKEY'):
        raise HTTPException(status_code=401, detail="Unauthorized")

    redis_key = f"message:sgc:{messageid}"

    try:
        clean_data = {k: (str(v) if v is not None else "") for k, v in data.items()}
        print(clean_data)
        
        await redis_client.hset(redis_key, mapping=clean_data)
        await redis_client.expire(redis_key, 86400)

        return {"status": "success", "message_id": messageid}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error.")