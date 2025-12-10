"""add relationship with inventory

Revision ID: 8abcd682ce02
Revises: 7af5746beb61
Create Date: 2023-11-22 14:30:03.272053
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8abcd682ce02'
down_revision: Union[str, None] = '7af5746beb61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'payment',
        sa.Column(
            'freight_amount', sa.Numeric(), server_default='0', nullable=False
        ),
    )
    op.add_column(
        'transaction', sa.Column('freight', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('transaction', 'freight')
    op.drop_column('payment', 'freight_amount')
