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
    beat_schedule={
        "publish-outbox-every-minute": {"task": "app.worker.run_outbox_batch", "schedule": 60.0},
        "refresh-forecast-jobs-hourly": {"task": "app.worker.refresh_forecast_jobs", "schedule": 3600.0},
    },
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
    from app.event_publisher import publish_event_to_redis
    from app.outbox import publish_pending_events

    with SessionLocal() as db:
        published, failed = publish_pending_events(db, publish_event_to_redis, limit=limit)
    return {"published": published, "failed": failed}


@celery_app.task
def refresh_forecast_jobs() -> dict[str, int]:
    """Dispatch queued forecast jobs as a recovery sweep."""
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.models import ForecastJob, ForecastJobStatus

    with SessionLocal() as db:
        ids = list(db.scalars(select(ForecastJob.id).where(ForecastJob.status == ForecastJobStatus.QUEUED).limit(50)).all())
    for job_id in ids:
        run_forecast_job.delay(str(job_id))
    return {"queued": len(ids)}


@celery_app.task
def run_forecast_job(job_id: str) -> dict:
    """Run real inference, then store forecasts/recommendations through the backend contract."""
    from uuid import UUID
    from sqlalchemy import select
    from app.api.forecast import ForecastJobResult, complete_forecast_job
    from app.db.session import SessionLocal
    from app.intelligence import build_batch, fetch_batch, to_forecast_result
    from app.models import ForecastJob, ForecastJobStatus, Store

    key = UUID(job_id)
    with SessionLocal.begin() as db:
        job = db.scalar(select(ForecastJob).where(ForecastJob.id == key).with_for_update())
        if job is None:
            return {"status": "missing"}
        if job.status != ForecastJobStatus.QUEUED:
            return {"status": job.status.value}
        job.status = ForecastJobStatus.RUNNING

    try:
        with SessionLocal() as db:
            job = db.get(ForecastJob, key)
            store = db.get(Store, job.store_id)
            requests, product_ids = build_batch(db, store, job.horizon_days)
        results = fetch_batch(requests)
        as_of, payload = to_forecast_result(results, product_ids, store.code)
        with SessionLocal() as db:
            job = db.get(ForecastJob, key)
            job.as_of = as_of  # The synthetic dataset's latest observed date is authoritative.
            db.commit()
        with SessionLocal() as db:
            saved = complete_forecast_job(key, ForecastJobResult(**payload), db, None)
        return saved
    except Exception as exc:
        with SessionLocal() as db:
            job = db.get(ForecastJob, key)
            if job is not None and job.status == ForecastJobStatus.RUNNING:
                complete_forecast_job(key, ForecastJobResult(status=ForecastJobStatus.FAILED,
                                      error_message=f"{type(exc).__name__}: {str(exc)[:400]}"), db, None)
        return {"status": "failed", "error": str(exc)[:400]}
