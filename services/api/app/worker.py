from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "smartgrocery",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def run_outbox_batch(self, limit: int = 50) -> dict[str, int]:
    """Process one outbox batch; broker/worker retries transient failures."""
    from app.db.session import SessionLocal
    from app.outbox import noop_publisher, publish_pending_events

    with SessionLocal() as db:
        published, failed = publish_pending_events(db, noop_publisher, limit=limit)
    return {"published": published, "failed": failed}
