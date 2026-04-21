"""add_user_id_to_orders

Revision ID: c1d2e3f4a5b6
Revises: 5be22fd743cf
Create Date: 2026-04-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = '5be22fd743cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('user_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('orders', 'user_id')
