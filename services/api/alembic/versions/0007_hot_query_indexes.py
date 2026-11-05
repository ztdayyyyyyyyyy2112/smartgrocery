"""Add indexes for hot inventory, order, procurement, and forecast queries."""

from typing import Sequence, Union
from alembic import op

revision: str = "0007_hot_query_indexes"
down_revision: Union[str, Sequence[str], None] = "0006_forecast_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_inventory_batches_store_product_status", "inventory_batches", ["store_id", "product_id", "status"])
    op.create_index("ix_orders_customer_created", "orders", ["customer_id", "created_at"])
    op.create_index("ix_purchase_orders_store_created", "purchase_orders", ["store_id", "created_at"])
    op.create_index("ix_forecasts_store_product_date", "demand_forecasts", ["store_id", "product_id", "target_date"])
    op.create_index("ix_recommendations_store_status_created", "replenishment_recommendations", ["store_id", "status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_store_status_created", table_name="replenishment_recommendations")
    op.drop_index("ix_forecasts_store_product_date", table_name="demand_forecasts")
    op.drop_index("ix_purchase_orders_store_created", table_name="purchase_orders")
    op.drop_index("ix_orders_customer_created", table_name="orders")
    op.drop_index("ix_inventory_batches_store_product_status", table_name="inventory_batches")
