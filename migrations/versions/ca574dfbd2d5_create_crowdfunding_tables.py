"""Create crowdfunding tables

Revision ID: ca574dfbd2d5
Revises: 2c29e17bf5b3
Create Date: 2025-12-03 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ca574dfbd2d5'
down_revision: Union[str, None] = '2c29e17bf5b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create crowdfunding_project table
    op.create_table(
        'crowdfunding_project',
        sa.Column('project_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('short_description', sa.String(), nullable=True),
        sa.Column('story', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('risks_and_challenges', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('main_image', sa.String(), nullable=True),
        sa.Column('video_url', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('goal_amount', sa.Numeric(), nullable=False),
        sa.Column('current_amount', sa.Numeric(), server_default='0', nullable=False),
        sa.Column('backers_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('published', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
        sa.PrimaryKeyConstraint('project_id'),
        sa.UniqueConstraint('slug'),
    )

    # Create crowdfunding_tier table
    op.create_table(
        'crowdfunding_tier',
        sa.Column('tier_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('recurring_interval', sa.String(), nullable=True),
        sa.Column('max_backers', sa.Integer(), nullable=True),
        sa.Column('current_backers', sa.Integer(), server_default='0', nullable=False),
        sa.Column('estimated_delivery', sa.Date(), nullable=True),
        sa.Column('active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['crowdfunding_project.project_id'], ),
        sa.PrimaryKeyConstraint('tier_id'),
    )

    # Create crowdfunding_contribution table
    op.create_table(
        'crowdfunding_contribution',
        sa.Column('contribution_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('tier_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('is_recurring', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('recurring_subscription_id', sa.String(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending', nullable=False),
        sa.Column('anonymous', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payment.payment_id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['crowdfunding_project.project_id'], ),
        sa.ForeignKeyConstraint(['tier_id'], ['crowdfunding_tier.tier_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
        sa.PrimaryKeyConstraint('contribution_id'),
    )

    # Create crowdfunding_goal table
    op.create_table(
        'crowdfunding_goal',
        sa.Column('goal_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('target_amount', sa.Numeric(), nullable=False),
        sa.Column('current_amount', sa.Numeric(), server_default='0', nullable=False),
        sa.Column('achieved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('achieved_at', sa.DateTime(), nullable=True),
        sa.Column('order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['crowdfunding_project.project_id'], ),
        sa.PrimaryKeyConstraint('goal_id'),
    )

    # Create crowdfunding_monthly_goal table
    op.create_table(
        'crowdfunding_monthly_goal',
        sa.Column('monthly_goal_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('target_amount', sa.Numeric(), nullable=False),
        sa.Column('current_amount', sa.Numeric(), server_default='0', nullable=False),
        sa.Column('achieved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('achieved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['crowdfunding_project.project_id'], ),
        sa.PrimaryKeyConstraint('monthly_goal_id'),
    )


def downgrade() -> None:
    op.drop_table('crowdfunding_monthly_goal')
    op.drop_table('crowdfunding_goal')
    op.drop_table('crowdfunding_contribution')
    op.drop_table('crowdfunding_tier')
    op.drop_table('crowdfunding_project')
