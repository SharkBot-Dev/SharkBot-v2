from pydantic import BaseModel, Field

class AccountInfo(BaseModel):
    user_id: str = Field(..., example="123456789012345678", description="ユーザーId")
    user_name: str = Field(..., example="example", description="ユーザー名")
    avatar_url: str = Field(..., example="example", description="アバターのURL")
    money: int = Field(..., example="100", description="アカウントの所持金")