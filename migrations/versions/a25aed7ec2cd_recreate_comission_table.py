"""recreate comission table

Revision ID: a25aed7ec2cd
Revises: 2b604a0e182a
Create Date: 2023-10-05 09:18:32.130999
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a25aed7ec2cd'
down_revision: Union[str, None] = '2b604a0e182a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'sales_commission',
        sa.Column('commissions_wallet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('commission', sa.Numeric(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('released', sa.Boolean(), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('commissions_wallet_id'),
    )
    op.drop_table('commissions_wallet')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'commissions_wallet',
        sa.Column(
            'commissions_wallet_id',
            sa.INTEGER(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            'commissions_total',
            sa.INTEGER(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            'date_created',
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            'released', sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
        sa.Column('paid', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint(
            'commissions_wallet_id', name='commissions_wallet_pkey'
        ),
    )
    op.drop_table('sales_commission')
    # ### end Alembic commands ###
