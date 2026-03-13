"""
MongoDB connection — single client instance for the app lifetime.

Usage:
  await connect()            # call on startup
  await disconnect()         # call on shutdown
  db = get_db()              # returns the database handle anywhere
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config.settings import settings

_client: AsyncIOMotorClient | None = None


async def connect() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    # Ping to verify connection at startup
    await _client.admin.command("ping")


async def disconnect() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("Database client is not initialised. Call connect() first.")
    return _client[settings.MONGODB_DB_NAME]
