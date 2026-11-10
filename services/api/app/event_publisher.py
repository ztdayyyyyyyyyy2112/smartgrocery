import json

from redis import Redis

from app.core.config import get_settings
from app.models import OutboxEvent


EVENTS_CHANNEL = "smartgrocery:events"


def publish_event_to_redis(event: OutboxEvent) -> None:
    """Publish one outbox event to the shared Redis events channel."""
    payload = {
        "id": str(event.id),
        "event_type": event.event_type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": str(event.aggregate_id),
        "payload": event.payload,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }
    client = Redis.from_url(get_settings().celery_broker_url, decode_responses=True)
    try:
        client.publish(EVENTS_CHANNEL, json.dumps(payload, separators=(",", ":")))
    finally:
        client.close()
