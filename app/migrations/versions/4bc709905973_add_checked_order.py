"""add checked order

Revision ID: 4bc709905973
Revises: 59e463cfc589
Create Date: 2021-06-23 13:51:09.501045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bc709905973'
down_revision = '59e463cfc589'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('checked', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'checked')
    # ### end Alembic commands ###
