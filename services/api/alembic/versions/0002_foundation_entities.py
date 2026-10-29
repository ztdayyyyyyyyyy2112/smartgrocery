"""Create foundational catalog, users, and inventory tables.

Revision ID: 0002_foundation
Revises: 0001_extensions
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_foundation"
down_revision: Union[str, Sequence[str], None] = "0001_extensions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM("customer", "merchant", "admin", name="user_role", create_type=False)
    batch_status = postgresql.ENUM("available", "depleted", "expired", "quarantined", name="batch_status", create_type=False)
    stock_event_type = postgresql.ENUM("receive", "reserve", "release", "fulfil", "adjust", "quarantine", name="stock_event_type", create_type=False)
    postgresql.ENUM("customer", "merchant", "admin", name="user_role").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("available", "depleted", "expired", "quarantined", name="batch_status").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("receive", "reserve", "release", "fulfil", "adjust", "quarantine", name="stock_event_type").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("timezone", sa.String(64), server_default=sa.text("'Asia/Ho_Chi_Minh'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("image_url", sa.Text()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("unit", sa.String(30), nullable=False),
        sa.Column("selling_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_perishable", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("default_shelf_life_days", sa.Integer()),
        sa.Column("image_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("selling_price >= 0", name="ck_products_selling_price_nonnegative"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_table(
        "inventory_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lot_code", sa.String(100), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(12, 3), nullable=False),
        sa.Column("quantity_reserved", sa.Numeric(12, 3), server_default=sa.text("0"), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expiry_date", sa.Date()),
        sa.Column("unit_cost", sa.Numeric(12, 2)),
        sa.Column("status", batch_status, nullable=False),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_batches_on_hand_nonnegative"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_batches_reserved_nonnegative"),
        sa.CheckConstraint("quantity_on_hand >= quantity_reserved", name="ck_batches_reserved_lte_on_hand"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("store_id", "product_id", "lot_code", name="uq_inventory_batch_lot"),
    )
    op.create_table(
        "stock_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("event_type", stock_event_type, nullable=False),
        sa.Column("quantity_delta", sa.Numeric(12, 3), nullable=False),
        sa.Column("reference_type", sa.String(50)),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("stock_ledger")
    op.drop_table("inventory_batches")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("stores")
    op.drop_table("users")
    for name in ("stock_event_type", "batch_status", "user_role"):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
