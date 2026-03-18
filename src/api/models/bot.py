from pydantic import BaseModel, Field

class Status(BaseModel):
    guilds_count: str = Field(..., example="100", description="Botの導入数")
    users_count: str = Field(..., example="1000", description="Botの認識できるユーザー数")
    shards_count: str = Field(..., example="0", description="Botのシャード数")
    bot_ping: str = Field(..., example="170", description="BotのPing値")