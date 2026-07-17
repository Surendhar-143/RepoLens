"""Phase 4 tables

Revision ID: c5e5e5e5e5e5
Revises: c4d4d4d4d4d4
Create Date: 2026-07-17 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e5e5e5e5e5'
down_revision: Union[str, None] = 'c4d4d4d4d4d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create search_histories table
    op.create_table(
        'search_histories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('search_histories')
