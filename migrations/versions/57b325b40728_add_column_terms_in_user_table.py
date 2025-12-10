"""Add column terms in user table.

Revision ID: 57b325b40728
Revises: 1dba810f2de3
Create Date: 2025-01-30 21:43:30.855387

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '57b325b40728'
down_revision: Union[str, None] = '1dba810f2de3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('terms', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('user', 'terms')
