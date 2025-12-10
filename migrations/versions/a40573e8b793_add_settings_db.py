"""Add settings db

Revision ID: a40573e8b793
Revises: 79025333d034
Create Date: 2024-04-12 09:36:37.782536

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a40573e8b793'
down_revision: Union[str, None] = '79025333d034'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('settings',
    sa.Column('settings_id', sa.Integer(), nullable=False),
    sa.Column('field', sa.String(), nullable=False),
    sa.Column('value', sa.JSON(), nullable=False),
    sa.Column('settings_category_id', sa.Integer(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('settings_id')
    )


def downgrade() -> None:
    op.drop_table('settings')
