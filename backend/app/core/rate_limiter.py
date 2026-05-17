import logging

from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting using Redis — all counters use atomic INCR to prevent race conditions."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_requests = 100  # per minute
        self.window = 60  # seconds

    async def _raw_client(self):
        """Return the underlying async Redis client, ensuring connection."""
        if hasattr(self.redis, "redis"):
            if self.redis.redis is None and hasattr(self.redis, "connect"):
                await self.redis.connect()
            return self.redis.redis
        return self.redis

    async def _atomic_increment(self, key: str, window: int) -> int:
        """
        Atomically increment a counter and set TTL on first use.
        Returns the new count. Uses INCR so concurrent requests can never bypass limits.
        """
        raw = await self._raw_client()
        # Pipeline: INCR is atomic; EXPIRE only applied when count == 1 (first request)
        pipe = raw.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        results = await pipe.execute()
        count, ttl = results[0], results[1]
        # Set TTL only on the first request to avoid resetting the window
        if ttl < 0:
            await raw.expire(key, window)
        return count

    async def check_rate_limit(self, identifier: str) -> bool:
        """
        Atomic rate limit check — fails open if Redis is unavailable.
        """
        key = f"rate_limit:{identifier}"
        try:
            count = await self._atomic_increment(key, self.window)
            return count <= self.max_requests
        except (RedisError, OSError) as exc:
            logger.warning("Redis unavailable; skipping rate limit check: %s", exc)
            return True

    async def check_ai_rate_limit(self, identifier: str, is_authenticated: bool = True) -> bool:
        """
        Atomic AI-specific rate limit (hourly window).
        Limits: 30/hour for authenticated users, 5/hour for anonymous IPs.
        """
        window = 3600  # 1 hour
        max_ai_requests = 30 if is_authenticated else 5
        key = f"ai_rate_limit:{identifier}"

        try:
            count = await self._atomic_increment(key, window)
            return count <= max_ai_requests
        except (RedisError, OSError) as exc:
            logger.warning("Redis unavailable; skipping AI rate limit check: %s", exc)
            return True

    async def track_ai_tokens(self, identifier: str, estimated_tokens: int):
        """Track rough token usage for analytics (kept for 30 days)."""
        key = f"ai_token_usage:{identifier}"
        try:
            raw = await self._raw_client()
            pipe = raw.pipeline()
            pipe.incrby(key, estimated_tokens)
            pipe.expire(key, 2592000)  # 30 days — always refresh TTL
            await pipe.execute()
        except (RedisError, OSError):
            pass

