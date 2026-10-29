"""ORM models will be added in feat/be-database. Import them here so Alembic sees them."""

from app.db.base import Base

__all__ = ["Base"]
