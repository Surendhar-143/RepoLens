"""Phase 6 tables

Revision ID: c7g7g7g7g7g7
Revises: c6f6f6f6f6f6
Create Date: 2026-07-17 16:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7g7g7g7g7g7'
down_revision: Union[str, None] = 'c6f6f6f6f6f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create workspace_states table
    op.create_table(
        'workspace_states',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('active_layout', sa.String(length=50), nullable=False),
        sa.Column('zoom', sa.Float(), nullable=False),
        sa.Column('pan_x', sa.Float(), nullable=False),
        sa.Column('pan_y', sa.Float(), nullable=False),
        sa.Column('active_filters_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create annotations table
    op.create_table(
        'annotations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('note_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('view_state_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('bookmarks')
    op.drop_table('annotations')
    op.drop_table('workspace_states')
