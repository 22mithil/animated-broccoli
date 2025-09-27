from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect_db(cls, mongodb_url: str):
        try:
            # Add server selection timeout to fail fast if server is unreachable
            cls.client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)
            # Test the connection
            await cls.client.admin.command('ping')
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            cls.client = None  # Reset client on failure
            raise Exception(f"Failed to connect to MongoDB: {str(e)}")

    @classmethod
    async def close_db(cls):
        if cls.client:
            await cls.client.close()
            print("MongoDB connection closed")

    @classmethod
    def get_db(cls):
        if not cls.client:
            raise Exception("Database connection not available. Please check your MongoDB connection.")
        try:
            return cls.client.get_database("chat_db")
        except Exception as e:
            raise Exception(f"Failed to get database: {str(e)}")
