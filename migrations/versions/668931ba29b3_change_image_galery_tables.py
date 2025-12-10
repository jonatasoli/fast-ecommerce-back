"""Change image galery tables

Revision ID: 668931ba29b3
Revises: 785680a1a391
Create Date: 2025-04-29 08:24:21.276156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '668931ba29b3'
down_revision: Union[str, None] = '785680a1a391'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('uploaded_media',
    sa.Column('media_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('uri', sa.String(), nullable=False),
    sa.Column('small', sa.String(), nullable=True),
    sa.Column('thumb', sa.String(), nullable=True),
    sa.Column('alt', sa.String(), nullable=True),
    sa.Column('caption', sa.String(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('image_bucket', sa.String(), nullable=True),
    sa.Column('create_at', sa.DateTime(), nullable=False),
    sa.Column('update_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('media_id')
    )
    op.drop_table('uploaded_image')
    op.add_column('image_gallery', sa.Column('media_gallery_id', sa.Integer(), nullable=False))
    op.add_column('image_gallery', sa.Column('media_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'image_gallery', 'uploaded_media', ['media_id'], ['media_id'])
    op.drop_column('image_gallery', 'category_id')
    op.drop_column('image_gallery', 'url')


def downgrade() -> None:
    op.add_column('image_gallery', sa.Column('url', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('image_gallery', sa.Column('category_id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.drop_constraint(None, 'image_gallery', type_='foreignkey')
    op.drop_column('image_gallery', 'media_id')
    op.drop_column('image_gallery', 'media_gallery_id')
    op.create_table('uploaded_image',
    sa.Column('uploaded_image_id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('original', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('small', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('thumb', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('icon', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('uploaded', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('mimetype', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('size', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('image_bucket', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('uploaded_image_id', name='uploaded_image_pkey')
    )
    op.drop_table('uploaded_media')
