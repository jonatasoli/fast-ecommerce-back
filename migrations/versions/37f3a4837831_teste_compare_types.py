"""teste compare types

Revision ID: 37f3a4837831
Revises: 19215b4a119d
Create Date: 2023-09-09 11:26:19.227831
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37f3a4837831'
down_revision: Union[str, None] = '19215b4a119d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'order',
        'customer_id',
        existing_type=sa.INTEGER(),
        type_=sa.String(),
        existing_nullable=False,
    )
    op.execute("ALTER TABLE product ALTER COLUMN description TYPE JSON USING description::json")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'product',
        'description',
        existing_type=sa.JSON(),
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )
    op.alter_column(
        'order',
        'customer_id',
        existing_type=sa.String(),
        type_=sa.INTEGER(),
        existing_nullable=False,
    )
    # ### end Alembic commands ###
