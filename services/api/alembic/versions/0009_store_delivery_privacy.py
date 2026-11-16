"""Scope merchants to stores and persist private customer delivery details."""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_store_delivery_privacy"
down_revision: Union[str, Sequence[str], None] = "0008_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(40)))
    op.add_column("users", sa.Column("default_address", sa.Text()))
    op.add_column("users", sa.Column("privacy_consent_at", sa.DateTime(timezone=True)))
    op.add_column("stores", sa.Column("merchant_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key("fk_stores_merchant_id", "stores", "users", ["merchant_id"], ["id"])
    op.create_unique_constraint("uq_stores_merchant_id", "stores", ["merchant_id"])
    op.add_column("orders", sa.Column("recipient_name", sa.String(200)))
    op.add_column("orders", sa.Column("delivery_phone", sa.String(40)))
    op.add_column("orders", sa.Column("delivery_address", sa.Text()))


def downgrade() -> None:
    op.drop_column("orders", "delivery_address")
    op.drop_column("orders", "delivery_phone")
    op.drop_column("orders", "recipient_name")
    op.drop_constraint("uq_stores_merchant_id", "stores", type_="unique")
    op.drop_constraint("fk_stores_merchant_id", "stores", type_="foreignkey")
    op.drop_column("stores", "merchant_id")
    op.drop_column("users", "privacy_consent_at")
    op.drop_column("users", "default_address")
    op.drop_column("users", "phone")
