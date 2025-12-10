"""merge checkout heads

Revision ID: 4d3bd9481e60
Revises: ca574dfbd2d5, checkout_jobs
Create Date: 2025-12-09 10:51:42.980715

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4d3bd9481e60'
down_revision: Union[str, None] = ('ca574dfbd2d5', 'checkout_jobs')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
