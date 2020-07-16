"""create user - image - role  tables

Revision ID: ab3d59d98d1a
Revises: 
Create Date: 2020-06-05 19:43:41.328413

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab3d59d98d1a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('role',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('role', sa.String(length=64), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('uploadedimage',
    sa.Column('id', sa.String(length=512), nullable=False),
    sa.Column('original', sa.String(length=512), nullable=True),
    sa.Column('small', sa.String(length=512), nullable=True),
    sa.Column('thumb', sa.String(length=512), nullable=True),
    sa.Column('icon', sa.String(length=512), nullable=True),
    sa.Column('uploaded', sa.Boolean(), nullable=True),
    sa.Column('mimetype', sa.String(length=48), nullable=True),
    sa.Column('name', sa.String(length=512), nullable=True),
    sa.Column('size', sa.String(length=24), nullable=True),
    sa.Column('image_bucket', sa.String(length=48), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=512), nullable=True),
    sa.Column('document', sa.String(length=32), nullable=True),
    sa.Column('document_type', sa.String(length=32), server_default='CPF', nullable=True),
    sa.Column('birth_date', sa.DateTime(), nullable=True),
    sa.Column('gender', sa.String(length=32), nullable=True),
    sa.Column('email', sa.String(length=128), nullable=True),
    sa.Column('phone', sa.String(length=128), nullable=True),
    sa.Column('user_timezone', sa.String(length=50), server_default='America/Sao_Paulo', nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('update_email_on_next_login', sa.Boolean(), server_default='0', nullable=True),
    sa.Column('update_password_on_next_login', sa.Boolean(), server_default='0', nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document'),
    sa.UniqueConstraint('email')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_table('uploadedimage')
    op.drop_table('role')
    # ### end Alembic commands ###