"""convert field credentials to str or none

Revision ID: 505773b1f8a5
Revises: 1ea95b343cde
Create Date: 2025-06-28 11:17:24.043538

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '505773b1f8a5'
down_revision: Union[str, None] = '1ea95b343cde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('settings', 'credentials',
               existing_type=sa.VARCHAR(),
               nullable=True,
               existing_server_default=sa.text("'empty'::character varying"))


def downgrade() -> None:
    op.alter_column('settings', 'credentials',
               existing_type=sa.VARCHAR(),
               nullable=False,
               existing_server_default=sa.text("'empty'::character varying"))
