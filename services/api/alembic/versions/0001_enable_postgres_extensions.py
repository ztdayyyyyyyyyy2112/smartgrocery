"""Enable PostgreSQL extensions used by later schema PRs.

Revision ID: 0001_extensions
Revises:
Create Date: 2026-10-28

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001_extensions"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext";')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS "citext";')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
