from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.rate_limit import check_rate_limit


def test_rate_limit_raises_after_threshold() -> None:
    fake = type("FakeRedis", (), {"incr": lambda self, key: 6, "expire": lambda self, key, seconds: True})()
    with patch("app.rate_limit.Redis.from_url", return_value=fake), pytest.raises(HTTPException) as exc:
        check_rate_limit("test:key", limit=5, window_seconds=60)
    assert exc.value.status_code == 429
