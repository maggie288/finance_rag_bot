"""add_execution_logs_to_trading_simulations

Revision ID: 17735885df7b
Revises: 876630b87674
Create Date: 2026-02-05 01:15:30.384033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '17735885df7b'
down_revision: Union[str, None] = '876630b87674'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only add the execution_logs column - other drop commands were auto-generated incorrectly
    op.add_column('trading_simulations', sa.Column('execution_logs', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # Only remove the execution_logs column
    op.drop_column('trading_simulations', 'execution_logs')
    # ### end Alembic commands ###
