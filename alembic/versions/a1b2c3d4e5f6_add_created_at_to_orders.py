"""add_created_at_to_orders

Revision ID: a1b2c3d4e5f6
Revises: 66a4beac4f38
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '66a4beac4f38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table('orders') as batch_op:
        batch_op.drop_column('created_at')
