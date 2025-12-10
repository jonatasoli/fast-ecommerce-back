"""add relationship with inventory

Revision ID: 6e29dc3703c0
Revises: 6342d188ed8c
Create Date: 2023-11-19 16:06:04.361082
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6e29dc3703c0'
down_revision: Union[str, None] = '6342d188ed8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'product',
        'currency',
        existing_type=sa.VARCHAR(),
        nullable=False,
        existing_server_default=sa.text("'BRL'::character varying"),
    )


def downgrade() -> None:
    op.alter_column(
        'product',
        'currency',
        existing_type=sa.VARCHAR(),
        nullable=True,
        existing_server_default=sa.text("'BRL'::character varying"),
    )
