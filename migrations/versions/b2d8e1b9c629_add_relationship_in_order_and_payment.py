"""add relationship in order and payment

Revision ID: b2d8e1b9c629
Revises: b8365f3e274c
Create Date: 2023-10-17 10:44:36.494797
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2d8e1b9c629'
down_revision: Union[str, None] = 'b8365f3e274c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order', sa.Column('user_id', sa.Integer(), nullable=False))
    op.add_column(
        'order', sa.Column('payment_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        None, 'order', 'payment', ['payment_id'], ['payment_id']
    )
    op.create_foreign_key(None, 'order', 'user', ['user_id'], ['user_id'])
    op.add_column(
        'payment', sa.Column('user_id', sa.Integer(), nullable=False)
    )
    op.create_foreign_key(None, 'payment', 'user', ['user_id'], ['user_id'])


def downgrade() -> None:
    op.drop_constraint(None, 'payment', type_='foreignkey')
    op.drop_column('payment', 'user_id')
    op.drop_constraint(None, 'order', type_='foreignkey')
    op.drop_constraint(None, 'order', type_='foreignkey')
    op.drop_column('order', 'payment_id')
    op.drop_column('order', 'user_id')
