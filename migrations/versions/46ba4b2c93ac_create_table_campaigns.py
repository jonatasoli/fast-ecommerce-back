"""Create table Campaigns

Revision ID: 46ba4b2c93ac
Revises: 4f9af083f31f
Create Date: 2024-10-05 17:52:12.805651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '46ba4b2c93ac'
down_revision: Union[str, None] = '4f9af083f31f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('campaign',
    sa.Column('campaign_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('discount_type', sa.String(), nullable=False),
    sa.Column('discount_value', sa.Numeric(), nullable=True),
    sa.Column('free_shipping', sa.Boolean(), nullable=False),
    sa.Column('min_purchase_value', sa.Numeric(), nullable=True),
    sa.Column('commission_fee_value', sa.Numeric(), nullable=True),
    sa.PrimaryKeyConstraint('campaign_id')
    )


def downgrade() -> None:
    op.drop_table('campaign')
