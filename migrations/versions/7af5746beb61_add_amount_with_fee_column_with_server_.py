"""add amount_with_fee column with server default

Revision ID: 7af5746beb61
Revises: 6e29dc3703c0
Create Date: 2023-11-22 10:17:56.344870
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7af5746beb61'
down_revision: Union[str, None] = '6e29dc3703c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'payment',
        sa.Column(
            'amount_with_fee', sa.Numeric(), server_default='0', nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column('payment', 'amount_with_fee')
