"""fix_image_gallery_primary_key

Revision ID: cb1e9209f758
Revises: 1e7bc63d3fb7
Create Date: 2025-06-07 21:02:59.817764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cb1e9209f758'
down_revision: Union[str, None] = '1e7bc63d3fb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS image_gallery_media_gallery_id_seq")
    
    op.execute("""
        SELECT setval('image_gallery_media_gallery_id_seq', 
                     COALESCE((SELECT MAX(media_gallery_id) FROM image_gallery), 0) + 1)
    """)
    
    op.execute("""
        ALTER TABLE image_gallery 
        ALTER COLUMN media_gallery_id 
        SET DEFAULT nextval('image_gallery_media_gallery_id_seq'::regclass);
    """)


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS image_gallery_media_gallery_id_seq")
