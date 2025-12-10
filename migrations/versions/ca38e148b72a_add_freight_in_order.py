"""add freight in order

Revision ID: ca38e148b72a
Revises: 8abcd682ce02
Create Date: 2023-11-22 14:53:30.965560
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ca38e148b72a'
down_revision: Union[str, None] = '8abcd682ce02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('order', sa.Column('freight', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('order', 'freight')
