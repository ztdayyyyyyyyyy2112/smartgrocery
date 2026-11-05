from redis import Redis

from app.core.config import get_settings


def check_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    """Raise 429 when Redis-backed counter exceeds limit; fail open in dev."""
    from fastapi import HTTPException

    try:
        client = Redis.from_url(get_settings().celery_broker_url, decode_responses=True)
        count = client.incr(key)
        if count == 1:
            client.expire(key, window_seconds)
        if count > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except HTTPException:
        raise
    except Exception:
        if get_settings().app_env.lower() == "production":
            raise HTTPException(status_code=503, detail="Rate limiter unavailable")
