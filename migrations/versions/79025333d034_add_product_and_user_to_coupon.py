"""add product and user to coupon

Revision ID: 79025333d034
Revises: da6799c0cebe
Create Date: 2024-03-25 11:31:27.683113
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79025333d034'
down_revision: Union[str, None] = 'da6799c0cebe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('coupons', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column(
        'coupons', sa.Column('product_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(None, 'coupons', 'user', ['user_id'], ['user_id'])
    op.create_foreign_key(
        None, 'coupons', 'product', ['product_id'], ['product_id']
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'coupons', type_='foreignkey')
    op.drop_constraint(None, 'coupons', type_='foreignkey')
    op.drop_column('coupons', 'product_id')
    op.drop_column('coupons', 'user_id')
    # ### end Alembic commands ###
