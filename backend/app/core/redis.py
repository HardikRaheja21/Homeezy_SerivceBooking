import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def get(self, key: str):
        """Get value from Redis"""
        if not self.redis:
            await self.connect()
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ex: int = None):
        """Set value in Redis with optional expiry"""
        if not self.redis:
            await self.connect()
        return await self.redis.set(key, value, ex=ex)
    
    async def delete(self, key: str):
        """Delete key from Redis"""
        if not self.redis:
            await self.connect()
        return await self.redis.delete(key)
    
    async def ping(self):
        """Check Redis connection"""
        if not self.redis:
            await self.connect()
        return await self.redis.ping()
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()

redis_client = RedisClient()
