"""Add active date in CreditCardFeeConfig

Revision ID: 88d286691531
Revises: 37b6d9445907
Create Date: 2020-09-03 08:36:08.216793

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88d286691531'
down_revision = '37b6d9445907'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('creditcardfeeconfig', sa.Column('active_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('creditcardfeeconfig', 'active_date')
    # ### end Alembic commands ###