"""remove transaction comission table

Revision ID: 36ca18941bdf
Revises: a25aed7ec2cd
Create Date: 2023-10-05 09:19:55.102913
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '36ca18941bdf'
down_revision: Union[str, None] = 'a25aed7ec2cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('commissions_transactions')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'commissions_transactions',
        sa.Column(
            'commissions_transactions_id',
            sa.INTEGER(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            'transaction_id', sa.INTEGER(), autoincrement=False, nullable=True
        ),
        sa.Column(
            'commissions', sa.INTEGER(), autoincrement=False, nullable=True
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
            'commissions_transactions_id', name='commissions_transactions_pkey'
        ),
    )
    # ### end Alembic commands ###
