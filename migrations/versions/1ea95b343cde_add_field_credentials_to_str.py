"""add field credentials to str

Revision ID: 1ea95b343cde
Revises: cb1e9209f758
Create Date: 2025-06-10 14:47:01.227383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1ea95b343cde'
down_revision: Union[str, None] = 'cb1e9209f758'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('settings', sa.Column('credentials', sa.String(),server_default='empty', nullable=False))


def downgrade() -> None:
    op.drop_column('settings', 'credentials')
