"""Attach supplier records to the owning store."""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_supplier_store_scope"
down_revision: Union[str, Sequence[str], None] = "0009_store_delivery_privacy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("store_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key("fk_suppliers_store_id", "suppliers", "stores", ["store_id"], ["id"])
    op.create_index("ix_suppliers_store_id", "suppliers", ["store_id"])
    op.execute("UPDATE suppliers SET store_id = (SELECT id FROM stores WHERE code = 'S001') WHERE name = 'SmartGrocery Demo Supplier'")


def downgrade() -> None:
    op.drop_index("ix_suppliers_store_id", table_name="suppliers")
    op.drop_constraint("fk_suppliers_store_id", "suppliers", type_="foreignkey")
    op.drop_column("suppliers", "store_id")
