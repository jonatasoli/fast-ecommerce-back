"""add fields to cancel reason and currency

Revision ID: 6342d188ed8c
Revises: b2d8e1b9c629
Create Date: 2023-11-14 10:04:37.347309
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6342d188ed8c'
down_revision: Union[str, None] = 'b2d8e1b9c629'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'order', sa.Column('cancelled_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'order', sa.Column('cancelled_reason', sa.String(), nullable=True)
    )
    op.add_column(
        'order_status_steps',
        sa.Column('description', sa.String(), nullable=True),
    )
    op.add_column(
        'product',
        sa.Column(
            'currency', sa.String(), nullable=True, default_server='BRL'
        ),
    )
    op.execute('ALTER TABLE product ALTER COLUMN currency SET DEFAULT \'BRL\'')


def downgrade() -> None:
    op.drop_column('product', 'currency')
    op.drop_column('order_status_steps', 'description')
    op.drop_column('order', 'cancelled_reason')
    op.drop_column('order', 'cancelled_at')
