import motor.motor_asyncio

MONGO_URI = "mongodb://localhost:27017"
mongo = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
