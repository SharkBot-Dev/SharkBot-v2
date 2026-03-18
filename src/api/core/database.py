import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient
import os

redis_client = redis.from_url("redis://localhost", decode_responses=True)

mongo_client = AsyncIOMotorClient("mongodb://localhost:27017/")