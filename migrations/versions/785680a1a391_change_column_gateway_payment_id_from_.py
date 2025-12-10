"""Change column gateway_payment_id from int to str.

Revision ID: 785680a1a391
Revises: 57b325b40728
Create Date: 2025-03-29 15:03:23.631960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '785680a1a391'
down_revision: Union[str, None] = '57b325b40728'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('payment', 'gateway_payment_id',
               existing_type=sa.BIGINT(),
               type_=sa.String(),
               existing_nullable=False,
               existing_server_default=sa.text('0'))


def downgrade() -> None:
    op.alter_column('payment', 'gateway_payment_id',
               existing_type=sa.String(),
               type_=sa.BIGINT(),
               existing_nullable=False,
               existing_server_default=sa.text('0'))
