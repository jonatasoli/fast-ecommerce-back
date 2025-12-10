"""Add cancelled status in sales commission

Revision ID: 1dba810f2de3
Revises: 46ba4b2c93ac
Create Date: 2024-10-06 15:16:19.236795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1dba810f2de3'
down_revision: Union[str, None] = '46ba4b2c93ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sales_commission', sa.Column('cancelled', sa.Boolean(), server_default='0', nullable=False))
    op.add_column('sales_commission', sa.Column('cancelled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('sales_commission', 'cancelled_at')
    op.drop_column('sales_commission', 'cancelled')
