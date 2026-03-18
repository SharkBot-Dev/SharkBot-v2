from typing import Optional

from pydantic import BaseModel, Field

class APIKeyInfo(BaseModel):
    guild_id: str = Field(..., example="サーバーID", description="APIキーが使えるサーバーID")
    user_id: str = Field(..., example="ユーザーID", description="APIキーを作ったユーザーID")
    name: str = Field(..., example="APIキーの名前", description="APIキーの名前")
    apikey: str = Field(..., example="APIキー", description="APIキー")