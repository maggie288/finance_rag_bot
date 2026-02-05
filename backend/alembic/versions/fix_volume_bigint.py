"""Change volume to BigInteger for large volume values

Revision ID: fix_volume_bigint
Revises: stock_persistence_v1
Create Date: 2026-02-04 18:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'fix_volume_bigint'
down_revision: Union[str, None] = 'stock_persistence_v1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('stock_quotes', 'volume', type_=sa.BigInteger())
    op.alter_column('stock_klines', 'volume', type_=sa.BigInteger())


def downgrade() -> None:
    op.alter_column('stock_quotes', 'volume', type_=sa.Integer())
    op.alter_column('stock_klines', 'volume', type_=sa.Integer())
