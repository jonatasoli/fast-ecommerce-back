"""inicial migration

Revision ID: b8365f3e274c
Revises:
Create Date: 2023-10-17 10:41:49.231532
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8365f3e274c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'category',
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('path', sa.String(), nullable=False),
        sa.Column('menu', sa.Boolean(), nullable=False),
        sa.Column('showcase', sa.Boolean(), nullable=False),
        sa.Column('image_path', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('category_id'),
    )
    op.create_table(
        'credit_card_fee_config',
        sa.Column('credit_card_fee_config_id', sa.Integer(), nullable=False),
        sa.Column('min_installment_with_fee', sa.Integer(), nullable=False),
        sa.Column('max_installments', sa.Integer(), nullable=False),
        sa.Column('fee', sa.Numeric(), nullable=False),
        sa.Column('active_date', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('credit_card_fee_config_id'),
    )
    op.create_table(
        'franchise',
        sa.Column('franchise_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('communication_name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('franshisee_name', sa.String(), nullable=True),
        sa.Column('franshisee_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('franchise_id'),
    )
    op.create_table(
        'order',
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('affiliate_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('order_date', sa.DateTime(), nullable=False),
        sa.Column('cart_uuid', sa.String(), nullable=False),
        sa.Column('discount', sa.Numeric(), nullable=False),
        sa.Column('tracking_number', sa.String(), nullable=True),
        sa.Column('order_status', sa.String(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('checked', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('order_id'),
    )
    op.create_table(
        'payment',
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column(
            'gateway_payment_id',
            sa.Integer(),
            server_default='0',
            nullable=False,
        ),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('authorization', sa.String(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=False),
        sa.Column('payment_gateway', sa.String(), nullable=False),
        sa.Column('installments', sa.Integer(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.PrimaryKeyConstraint('payment_id'),
    )
    op.create_table(
        'role',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('role_id'),
    )
    op.create_table(
        'uploaded_image',
        sa.Column('uploaded_image_id', sa.Integer(), nullable=False),
        sa.Column('original', sa.String(), nullable=False),
        sa.Column('small', sa.String(), nullable=False),
        sa.Column('thumb', sa.String(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False),
        sa.Column('uploaded', sa.Boolean(), nullable=False),
        sa.Column('mimetype', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('image_bucket', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('uploaded_image_id'),
    )
    op.create_table(
        'user',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('document', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('user_timezone', sa.String(), nullable=True),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=True),
        sa.Column('customer_id', sa.String(), nullable=True),
        sa.Column('card_id', sa.String(), nullable=True),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('franchise_id', sa.String(), nullable=True),
        sa.Column('update_email_on_next_login', sa.Boolean(), nullable=False),
        sa.Column(
            'update_password_on_next_login',
            sa.Boolean(),
            server_default='0',
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('document'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
    )
    op.create_table(
        'address',
        sa.Column('address_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('neighborhood', sa.String(), nullable=False),
        sa.Column('street', sa.String(), nullable=False),
        sa.Column('street_number', sa.String(), nullable=False),
        sa.Column('address_complement', sa.String(), nullable=False),
        sa.Column('zipcode', sa.String(), nullable=False),
        sa.Column('uuid', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('address_id'),
    )
    op.create_table(
        'coupons',
        sa.Column('coupon_id', sa.Integer(), nullable=False),
        sa.Column('affiliate_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('discount', sa.Numeric(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['affiliate_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('coupon_id'),
    )
    op.create_table(
        'customer',
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('customer_uuid', sa.String(), nullable=False),
        sa.Column('payment_gateway', sa.String(), nullable=False),
        sa.Column('payment_method', sa.String(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('issuer_id', sa.String(), nullable=False),
        sa.Column('status', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('customer_id'),
    )
    op.create_table(
        'order_status_steps',
        sa.Column('order_status_steps_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('sending', sa.Boolean(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.PrimaryKeyConstraint('order_status_steps_id'),
    )
    op.create_table(
        'product',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('uri', sa.String(), nullable=False),
        sa.Column('price', sa.Numeric(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('direct_sales', sa.Boolean(), nullable=False),
        sa.Column('description', sa.JSON(), nullable=True),
        sa.Column('image_path', sa.String(), nullable=True),
        sa.Column('installments_config', sa.Integer(), nullable=False),
        sa.Column('installments_list', sa.JSON(), nullable=True),
        sa.Column('discount', sa.Integer(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('showcase', sa.Boolean(), nullable=False),
        sa.Column('feature', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('show_discount', sa.Boolean(), nullable=False),
        sa.Column('height', sa.Numeric(), nullable=True),
        sa.Column('width', sa.Numeric(), nullable=True),
        sa.Column('weight', sa.Numeric(), nullable=True),
        sa.Column('length', sa.Numeric(), nullable=True),
        sa.Column('diameter', sa.Numeric(), nullable=True),
        sa.Column('sku', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ['category_id'],
            ['category.category_id'],
        ),
        sa.PrimaryKeyConstraint('product_id'),
    )
    op.create_table(
        'sales_commission',
        sa.Column('commissions_wallet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('commission', sa.Numeric(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=False),
        sa.Column('released', sa.Boolean(), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('commissions_wallet_id'),
    )
    op.create_table(
        'user_reset_password',
        sa.Column('user_reset_password_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('used_token', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('user_reset_password_id'),
    )
    op.create_table(
        'image_gallery',
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['product_id'],
            ['product.product_id'],
        ),
        sa.PrimaryKeyConstraint('category_id'),
    )
    op.create_table(
        'inventory',
        sa.Column('inventory_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.ForeignKeyConstraint(
            ['product_id'],
            ['product.product_id'],
        ),
        sa.PrimaryKeyConstraint('inventory_id'),
    )
    op.create_table(
        'order_items',
        sa.Column('order_items_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(), nullable=False),
        sa.Column('discount_price', sa.Numeric(), nullable=False),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.ForeignKeyConstraint(
            ['product_id'],
            ['product.product_id'],
        ),
        sa.PrimaryKeyConstraint('order_items_id'),
    )
    op.create_table(
        'transaction',
        sa.Column('transaction_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('affiliate', sa.Integer(), nullable=True),
        sa.Column('affiliate_quota', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['affiliate'],
            ['user.user_id'],
        ),
        sa.ForeignKeyConstraint(
            ['order_id'],
            ['order.order_id'],
        ),
        sa.ForeignKeyConstraint(
            ['payment_id'],
            ['payment.payment_id'],
        ),
        sa.ForeignKeyConstraint(
            ['product_id'],
            ['product.product_id'],
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['user.user_id'],
        ),
        sa.PrimaryKeyConstraint('transaction_id'),
    )


def downgrade() -> None:
    op.drop_table('transaction')
    op.drop_table('order_items')
    op.drop_table('inventory')
    op.drop_table('image_gallery')
    op.drop_table('user_reset_password')
    op.drop_table('sales_commission')
    op.drop_table('product')
    op.drop_table('order_status_steps')
    op.drop_table('customer')
    op.drop_table('coupons')
    op.drop_table('address')
    op.drop_table('user')
    op.drop_table('uploaded_image')
    op.drop_table('role')
    op.drop_table('payment')
    op.drop_table('order')
    op.drop_table('franchise')
    op.drop_table('credit_card_fee_config')
    op.drop_table('category')
