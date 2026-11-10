from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OutboxEvent


Publisher = Callable[[OutboxEvent], None]


def publish_pending_events(db: Session, publisher: Publisher, *, limit: int = 50) -> tuple[int, int]:
    """Publish a bounded batch of events and return (published, failed).

    Events are locked while being processed so multiple worker instances do not
    publish the same row concurrently. Failed events remain pending and carry
    their attempt count for later retry/backoff policies.
    """
    if limit < 1:
        return 0, 0
    published = failed = 0
    db.rollback()
    with db.begin():
        events = list(
            db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            ).all()
        )
        for event in events:
            event.attempts += 1
            try:
                publisher(event)
            except Exception:
                failed += 1
                continue
            event.published_at = datetime.now(timezone.utc)
            published += 1
    return published, failed


def noop_publisher(event: OutboxEvent) -> None:
    """Default publisher hook used by the local polling script."""
    return None
