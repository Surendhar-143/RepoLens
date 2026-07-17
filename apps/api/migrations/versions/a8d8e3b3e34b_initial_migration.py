"""Initial migration

Revision ID: a8d8e3b3e34b
Revises: 
Create Date: 2026-07-17 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8d8e3b3e34b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('github_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_github_id'), 'users', ['github_id'], unique=True)

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('theme', sa.String(length=20), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('settings')
    op.drop_index(op.f('ix_users_github_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
