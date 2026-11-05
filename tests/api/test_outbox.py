from uuid import uuid4

from sqlalchemy import func, select, update

from app.db.session import SessionLocal
from app.models import OutboxEvent
from app.outbox import publish_pending_events


def test_outbox_publishes_pending_event() -> None:
    event_id = uuid4()
    with SessionLocal() as db:
        db.execute(update(OutboxEvent).where(OutboxEvent.published_at.is_(None)).values(published_at=func.now()))
        db.add(OutboxEvent(id=event_id, event_type="test.published", aggregate_type="test", aggregate_id=uuid4(), payload={"ok": True}))
        db.commit()
        published, failed = publish_pending_events(db, lambda event: None, limit=1)
        assert published == 1
        assert failed == 0
        event = db.scalar(select(OutboxEvent).where(OutboxEvent.id == event_id))
        assert event is not None
        assert event.published_at is not None
        assert event.attempts == 1


def test_outbox_failure_remains_pending_for_retry() -> None:
    event_id = uuid4()
    with SessionLocal() as db:
        db.execute(update(OutboxEvent).where(OutboxEvent.published_at.is_(None)).values(published_at=func.now()))
        db.add(OutboxEvent(id=event_id, event_type="test.failed", aggregate_type="test", aggregate_id=uuid4(), payload={"ok": False}))
        db.commit()

        def failing_publisher(_event: OutboxEvent) -> None:
            raise RuntimeError("broker unavailable")

        published, failed = publish_pending_events(db, failing_publisher, limit=1)
        assert published == 0
        assert failed == 1
        event = db.scalar(select(OutboxEvent).where(OutboxEvent.id == event_id))
        assert event is not None
        assert event.published_at is None
        assert event.attempts == 1
