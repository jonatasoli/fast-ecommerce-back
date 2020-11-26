"""add order_status ans last_updated

Revision ID: fbb5bca28974
Revises: dad47228ad42
Create Date: 2020-11-11 14:45:01.511562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbb5bca28974'
down_revision = 'dad47228ad42'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('last_updated', sa.DateTime(), nullable=True))
    op.add_column('order', sa.Column('order_status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'order_status')
    op.drop_column('order', 'last_updated')
    # ### end Alembic commands ###
