"""Add forecast jobs, forecasts, and replenishment recommendations."""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_forecast_jobs"
down_revision: Union[str, Sequence[str], None] = "0005_outbox"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM("queued", "running", "succeeded", "failed", name="job_status").create(bind, checkfirst=True)
    postgresql.ENUM("pending", "approved", "rejected", "converted", name="recommendation_status").create(bind, checkfirst=True)
    op.create_table("forecast_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM(name="job_status", create_type=False), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False), sa.Column("as_of", sa.Date(), nullable=False),
        sa.Column("error_message", sa.Text()), sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"]), sa.ForeignKeyConstraint(["created_by"], ["users.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("demand_forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("predicted_qty", sa.Numeric(12, 3), nullable=False), sa.Column("model_name", sa.String(100), nullable=False), sa.Column("model_version", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["forecast_jobs.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["store_id"], ["stores.id"]), sa.ForeignKeyConstraint(["product_id"], ["products.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_table("replenishment_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suggested_qty", sa.Numeric(12, 3), nullable=False), sa.Column("safety_stock", sa.Numeric(12, 3), nullable=False), sa.Column("reorder_point", sa.Numeric(12, 3), nullable=False), sa.Column("meu_score", sa.Numeric(12, 6)), sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", postgresql.ENUM(name="recommendation_status", create_type=False), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["forecast_jobs.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["store_id"], ["stores.id"]), sa.ForeignKeyConstraint(["product_id"], ["products.id"]), sa.PrimaryKeyConstraint("id"))


def downgrade() -> None:
    op.drop_table("replenishment_recommendations")
    op.drop_table("demand_forecasts")
    op.drop_table("forecast_jobs")
    postgresql.ENUM(name="recommendation_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="job_status").drop(op.get_bind(), checkfirst=True)
