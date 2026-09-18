"""
Redis client for token blacklisting
"""
import redis.asyncio as redis

from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def _blacklist_key(token: str) -> str:
    return f"blacklist:refresh:{token[:16]}"  # Use token prefix as key


async def blacklist_refresh_token(token: str, ttl_seconds: int) -> None:
    """Mark a refresh token as revoked until its natural expiry"""
    if ttl_seconds > 0:
        await redis_client.set(_blacklist_key(token), "1", ex=ttl_seconds)


async def is_refresh_token_blacklisted(token: str) -> bool:
    return bool(await redis_client.exists(_blacklist_key(token)))

