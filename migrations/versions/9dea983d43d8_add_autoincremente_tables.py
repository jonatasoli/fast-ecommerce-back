"""Add autoincremente tables

Revision ID: 9dea983d43d8
Revises: 668931ba29b3
Create Date: 2025-06-07 20:01:26.102878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9dea983d43d8'
down_revision: Union[str, None] = '668931ba29b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    constraints = inspector.get_pk_constraint('image_gallery')
    op.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS image_gallery_media_gallery_id_seq"))
    op.execute(sa.text("ALTER TABLE image_gallery ALTER COLUMN media_gallery_id SET DEFAULT nextval('image_gallery_media_gallery_id_seq'::regclass)"))
    if constraints.get('name') == 'image_gallery_pkey':
        op.drop_constraint('image_gallery_pkey', 'image_gallery', type_='primary')
    
    op.alter_column('image_gallery', 'media_gallery_id',
                   existing_type=sa.INTEGER(),
                   server_default=sa.text("nextval('image_gallery_media_gallery_id_seq'::regclass)"),
                   nullable=False,
                   autoincrement=True)
    
    op.create_primary_key('image_gallery_pkey', 'image_gallery', ['media_gallery_id'])


def downgrade() -> None:
    op.drop_constraint('image_gallery_pkey', 'image_gallery', type_='primary')
    op.alter_column('image_gallery', 'media_gallery_id',
                   existing_type=sa.INTEGER(),
                   server_default=None,
                   nullable=False,
                   autoincrement=False)
    op.create_primary_key('image_gallery_pkey', 'image_gallery', ['media_gallery_id'])
