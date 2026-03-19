import datetime

from pydantic import BaseModel, Field

class NewsInfo(BaseModel):
    news_url: str = Field(..., example="ニュースのURL", description="ニュースのURL")

class SnowflakeInfo(BaseModel):
    timestamp: datetime.datetime
    worker_id: int
    process_id: int
    increment: int