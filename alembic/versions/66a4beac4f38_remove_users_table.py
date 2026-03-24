"""remove_users_table

Revision ID: 66a4beac4f38
Revises: 52b4cd9af355
Create Date: 2026-03-24 15:30:45.449865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66a4beac4f38'
down_revision: Union[str, Sequence[str], None] = '52b4cd9af355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Explicit table definition used by batch mode to avoid reflecting a broken
# FK (user_id -> users) when the users table no longer exists.
_orders_with_user_id = sa.Table(
    'orders',
    sa.MetaData(),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('total_price', sa.Float(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
)


def upgrade() -> None:
    # SQLite cannot DROP COLUMN or DROP CONSTRAINT directly.
    # Use batch mode with an explicit table copy to drop user_id.
    with op.batch_alter_table('orders', copy_from=_orders_with_user_id) as batch_op:
        batch_op.drop_column('user_id')

    op.drop_table('users', if_exists=True)


def downgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.VARCHAR(), nullable=False),
        sa.Column('role', sa.VARCHAR(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('orders') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.VARCHAR(), nullable=False))
        batch_op.create_foreign_key('fk_orders_user_id', 'users', ['user_id'], ['id'])
