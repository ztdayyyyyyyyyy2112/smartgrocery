"""Create supplier and purchase order tables.

Revision ID: 0004_procurement
Revises: 0003_orders
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_procurement"
down_revision: Union[str, Sequence[str], None] = "0003_orders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    po_status = postgresql.ENUM("draft", "pending_approval", "approved", "sent", "partially_received", "received", "cancelled", name="purchase_order_status")
    po_status.create(op.get_bind(), checkfirst=True)
    op.create_table("suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("contact_email", sa.String(320)),
        sa.Column("contact_phone", sa.String(40)), sa.Column("lead_time_days", sa.Integer(), server_default=sa.text("2"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_table("supplier_products",
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_sku", sa.String(100)), sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False), sa.Column("min_order_qty", sa.Numeric(12, 3), server_default=sa.text("1"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["product_id"], ["products.id"]), sa.PrimaryKeyConstraint("supplier_id", "product_id"))
    op.create_table("purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM(name="purchase_order_status", create_type=False), nullable=False), sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("approved_by", postgresql.UUID(as_uuid=True)), sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]), sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]), sa.ForeignKeyConstraint(["created_by"], ["users.id"]), sa.ForeignKeyConstraint(["approved_by"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("purchase_order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_ordered", sa.Numeric(12, 3), nullable=False), sa.Column("quantity_received", sa.Numeric(12, 3), server_default=sa.text("0"), nullable=False), sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.CheckConstraint("quantity_ordered > 0", name="ck_po_items_quantity_positive"), sa.CheckConstraint("quantity_received >= 0", name="ck_po_items_received_nonnegative"), sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["product_id"], ["products.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("goods_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("received_by", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]), sa.ForeignKeyConstraint(["received_by"], ["users.id"]), sa.PrimaryKeyConstraint("id"))


def downgrade() -> None:
    for table in ("goods_receipts", "purchase_order_items", "purchase_orders", "supplier_products", "suppliers"):
        op.drop_table(table)
    postgresql.ENUM(name="purchase_order_status").drop(op.get_bind(), checkfirst=True)
