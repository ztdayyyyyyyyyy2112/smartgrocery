"""Publish pending outbox events once; suitable for cron/task scheduler."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal
from app.outbox import noop_publisher, publish_pending_events


def main() -> None:
    with SessionLocal() as db:
        published, failed = publish_pending_events(db, noop_publisher)
    print(f"outbox published={published} failed={failed}")


if __name__ == "__main__":
    main()
