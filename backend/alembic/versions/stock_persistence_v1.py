"""Add stock data persistence tables

Revision ID: stock_persistence_v1
Revises: 095e84eaf322
Create Date: 2026-02-04 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'stock_persistence_v1'
down_revision: Union[str, None] = '095e84eaf322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('stock_quotes',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('market', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('price', sa.Float(), nullable=False, default=0),
        sa.Column('change', sa.Float(), nullable=True),
        sa.Column('change_percent', sa.Float(), nullable=True),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('high', sa.Float(), nullable=True),
        sa.Column('low', sa.Float(), nullable=True),
        sa.Column('open', sa.Float(), nullable=True),
        sa.Column('prev_close', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('symbol', 'market'),
    )
    op.create_index('ix_stock_quotes_symbol_market', 'stock_quotes', ['symbol', 'market'], unique=False)

    op.create_table('stock_klines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('market', sa.String(length=10), nullable=False),
        sa.Column('interval', sa.String(length=10), nullable=False),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open', sa.Float(), nullable=False, default=0),
        sa.Column('high', sa.Float(), nullable=False, default=0),
        sa.Column('low', sa.Float(), nullable=False, default=0),
        sa.Column('close', sa.Float(), nullable=False, default=0),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'market', 'interval', 'datetime', name='uq_stock_kline_symbol_market_interval_datetime'),
    )
    op.create_index('ix_stock_klines_symbol_interval', 'stock_klines', ['symbol', 'interval'], unique=False)

    op.create_table('stock_fundamentals',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('market', sa.String(length=10), nullable=False),
        sa.Column('pe_ratio', sa.Float(), nullable=True),
        sa.Column('pb_ratio', sa.Float(), nullable=True),
        sa.Column('roe', sa.Float(), nullable=True),
        sa.Column('debt_ratio', sa.Float(), nullable=True),
        sa.Column('revenue_growth', sa.Float(), nullable=True),
        sa.Column('net_profit_margin', sa.Float(), nullable=True),
        sa.Column('market_cap', sa.Float(), nullable=True),
        sa.Column('dividend_yield', sa.Float(), nullable=True),
        sa.Column('eps', sa.Float(), nullable=True),
        sa.Column('revenue', sa.Float(), nullable=True),
        sa.Column('net_income', sa.Float(), nullable=True),
        sa.Column('total_debt', sa.Float(), nullable=True),
        sa.Column('total_cash', sa.Float(), nullable=True),
        sa.Column('operating_cash_flow', sa.Float(), nullable=True),
        sa.Column('free_cash_flow', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('symbol', 'market'),
    )
    op.create_index('ix_stock_fundamentals_symbol_market', 'stock_fundamentals', ['symbol', 'market'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_stock_fundamentals_symbol_market', table_name='stock_fundamentals')
    op.drop_table('stock_fundamentals')
    op.drop_index('ix_stock_klines_symbol_interval', table_name='stock_klines')
    op.drop_table('stock_klines')
    op.drop_index('ix_stock_quotes_symbol_market', table_name='stock_quotes')
    op.drop_table('stock_quotes')
