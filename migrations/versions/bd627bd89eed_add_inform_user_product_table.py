"""Add Inform User Product table

Revision ID: bd627bd89eed
Revises: a40573e8b793
Create Date: 2024-09-04 15:53:00.696112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bd627bd89eed'
down_revision: Union[str, None] = 'a40573e8b793'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('inform_product_user',
    sa.Column('inform_product_user_id', sa.Integer(), nullable=False),
    sa.Column('user_mail', sa.String(), nullable=False),
    sa.Column('user_phone', sa.String(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('product_name', sa.String(), nullable=False),
    sa.Column('sended', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('inform_product_user_id')
    )


def downgrade() -> None:
    op.drop_table('inform_product_user')
