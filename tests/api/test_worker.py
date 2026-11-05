from app.worker import celery_app, run_outbox_batch


def test_celery_worker_is_configured_for_retries() -> None:
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert run_outbox_batch.max_retries == 3
