from typing import Optional

from pydantic import BaseModel, Field

class EconomyInfo(BaseModel):
    currency: str = Field(..., example="コイン", description="サーバー固有の通貨名")

class UserBalance(BaseModel):
    money: int = Field(..., example=1000, description="所持金")
    bank: int = Field(..., example=5000, description="銀行残高")

class UpdateMoneyPayload(BaseModel):
    money: Optional[int] = Field(None, example=500, description="設定する所持金の額")
    bank: Optional[int] = Field(None, example=1000, description="設定する銀行の額")

class LeaderboardEntry(BaseModel):
    user_id: str = Field(..., example="123456789012345678", description="ユーザーID")
    money: int = Field(..., example=1000, description="所持金")
    bank: int = Field(..., example=5000, description="銀行残高")