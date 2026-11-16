"""Persist a single-store cart per customer account."""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_customer_cart"
down_revision: Union[str, Sequence[str], None] = "0010_supplier_store_scope"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("shopping_cart_items",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_cart_quantity_positive"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.PrimaryKeyConstraint("user_id", "product_id"))
    op.create_index("ix_cart_user_store", "shopping_cart_items", ["user_id", "store_id"])


def downgrade() -> None:
    op.drop_index("ix_cart_user_store", table_name="shopping_cart_items")
    op.drop_table("shopping_cart_items")
