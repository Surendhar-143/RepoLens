"""Phase 7 tables

Revision ID: c8h8h8h8h8h8
Revises: c7g7g7g7g7g7
Create Date: 2026-07-17 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8h8h8h8h8h8'
down_revision: Union[str, None] = 'c7g7g7g7g7g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create documentations table
    op.create_table(
        'documentations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('doc_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create engineering_reports table
    op.create_table(
        'engineering_reports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create documentation_templates table
    op.create_table(
        'documentation_templates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )


def downgrade() -> None:
    op.drop_table('documentation_templates')
    op.drop_table('engineering_reports')
    op.drop_table('documentations')
