"""Phase 5 tables

Revision ID: c6f6f6f6f6f6
Revises: c5e5e5e5e5e5
Create Date: 2026-07-17 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6f6f6f6f6f6'
down_revision: Union[str, None] = 'c5e5e5e5e5e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create ai_settings table
    op.create_table(
        'ai_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('ai_settings')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')
