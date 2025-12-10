"""fix_image_gallery_autoincrement

Revision ID: 1e7bc63d3fb7
Revises: 9dea983d43d8
Create Date: 2025-06-07 20:28:19.412992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1e7bc63d3fb7'
down_revision: Union[str, None] = '9dea983d43d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
