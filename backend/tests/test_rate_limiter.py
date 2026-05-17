import pytest
from app.core.rate_limiter import RateLimiter
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_rate_limiter_atomicity():
    # Mock redis client with pipeline support
    mock_redis = AsyncMock()
    mock_pipeline = AsyncMock()
    
    # Setup mock pipeline
    from unittest.mock import MagicMock
    mock_redis.redis.pipeline = MagicMock(return_value=mock_pipeline)
    
    # First call: INCR returns 1
    mock_pipeline.execute.return_value = [1, True]
    
    limiter = RateLimiter(mock_redis)
    allowed = await limiter.check_rate_limit("127.0.0.1")
    
    assert allowed is True
    # Verify pipeline was used (atomic operations)
    mock_redis.redis.pipeline.assert_called_once()
    mock_pipeline.incr.assert_called_once()
    mock_pipeline.expire.assert_called_once()
    mock_pipeline.execute.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limiter_exceeded():
    mock_redis = AsyncMock()
    mock_pipeline = AsyncMock()
    from unittest.mock import MagicMock
    mock_redis.redis.pipeline = MagicMock(return_value=mock_pipeline)
    
    # Return 6 for INCR (limit is 5)
    mock_pipeline.execute.return_value = [6, True]
    
    limiter = RateLimiter(mock_redis)
    allowed = await limiter.check_rate_limit("127.0.0.1")
    
    assert allowed is False
