import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from app.event_publisher import EVENTS_CHANNEL, publish_event_to_redis


def test_publish_event_to_redis_serializes_outbox_event() -> None:
    event = SimpleNamespace(
        id=uuid4(),
        event_type="order.created",
        aggregate_type="order",
        aggregate_id=uuid4(),
        payload={"order_id": "123"},
        created_at=datetime.now(timezone.utc),
    )
    with patch("app.event_publisher.Redis.from_url") as from_url:
        client = from_url.return_value
        publish_event_to_redis(event)
        channel, raw = client.publish.call_args.args
        assert channel == EVENTS_CHANNEL
        assert json.loads(raw)["event_type"] == "order.created"
        client.close.assert_called_once()
