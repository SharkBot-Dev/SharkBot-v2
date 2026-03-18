from pydantic import BaseModel, Field

class NewsInfo(BaseModel):
    news_url: str = Field(..., example="ニュースのURL", description="ニュースのURL")