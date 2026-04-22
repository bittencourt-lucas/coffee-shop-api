"""float_to_numeric

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column(
            'base_price',
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=10, scale=2),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'price_change',
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=10, scale=2),
            existing_nullable=False,
        )

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column(
            'total_price',
            existing_type=sa.Float(),
            type_=sa.Numeric(precision=10, scale=2),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column(
            'total_price',
            existing_type=sa.Numeric(precision=10, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.alter_column(
            'price_change',
            existing_type=sa.Numeric(precision=10, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'base_price',
            existing_type=sa.Numeric(precision=10, scale=2),
            type_=sa.Float(),
            existing_nullable=False,
        )
