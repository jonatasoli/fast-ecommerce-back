"""Add checkout_jobs table

Revision ID: checkout_jobs
Revises: 2c29e17bf5b3
Create Date: 2025-12-09 10:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'checkout_jobs'
down_revision: Union[str, None] = '2c29e17bf5b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'checkout_jobs',
        sa.Column('checkout_job_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('cart_uuid', sa.String(), nullable=False),
        sa.Column('payment_gateway', sa.String(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('gateway_payment_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_checkout_jobs_cart_uuid', 'checkout_jobs', ['cart_uuid'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_checkout_jobs_cart_uuid', table_name='checkout_jobs')
    op.drop_table('checkout_jobs')
