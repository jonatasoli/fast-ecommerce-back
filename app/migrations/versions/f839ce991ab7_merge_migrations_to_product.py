"""merge migrations to product

Revision ID: f839ce991ab7
Revises: 558effa87e2e, 6f91dc2c2189
Create Date: 2020-11-26 11:44:12.928088

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f839ce991ab7'
down_revision = ('558effa87e2e', '6f91dc2c2189')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
