from uuid import UUID

from sqlalchemy.orm import Session

from app.models import OutboxEvent


def enqueue_event(
    db: Session,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    payload: dict,
) -> OutboxEvent:
    """Queue an event in the current transaction for reliable later delivery."""
    event = OutboxEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
    )
    db.add(event)
    return event
