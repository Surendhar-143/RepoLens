"""Phase 8 tables

Revision ID: c9i9i9i9i9i9
Revises: c8h8h8h8h8h8
Create Date: 2026-07-17 16:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9i9i9i9i9i9'
down_revision: Union[str, None] = 'c8h8h8h8h8h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create rules table
    op.create_table(
        'rules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('thresholds_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('rule_id', sa.UUID(), nullable=False),
        sa.Column('target_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['rule_id'], ['rules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create health_scores table
    op.create_table(
        'health_scores',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('overall', sa.Float(), nullable=False),
        sa.Column('quality', sa.Float(), nullable=False),
        sa.Column('security', sa.Float(), nullable=False),
        sa.Column('architecture', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('health_scores')
    op.drop_table('findings')
    op.drop_table('rules')
