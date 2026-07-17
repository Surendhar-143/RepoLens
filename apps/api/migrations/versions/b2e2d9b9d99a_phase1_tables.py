"""Phase 1 tables

Revision ID: b2e2d9b9d99a
Revises: a8d8e3b3e34b
Create Date: 2026-07-17 11:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e2d9b9d99a'
down_revision: Union[str, None] = 'a8d8e3b3e34b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter users table to add new columns
    op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('github_username', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('provider', sa.String(length=50), server_default='local', nullable=False))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))

    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_github_username'), 'users', ['github_username'], unique=True)

    # Create github_accounts table
    op.create_table(
        'github_accounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('github_user_id', sa.String(length=100), nullable=False),
        sa.Column('github_username', sa.String(length=100), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('access_token', sa.String(length=255), nullable=False),
        sa.Column('refresh_token', sa.String(length=255), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_user_id'),
        sa.UniqueConstraint('user_id')
    )

    # Create repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('visibility', sa.String(length=50), nullable=False),
        sa.Column('default_branch', sa.String(length=100), nullable=False),
        sa.Column('languages', sa.JSON(), nullable=False),
        sa.Column('clone_url', sa.String(length=500), nullable=True),
        sa.Column('local_path', sa.String(length=500), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('last_commit_hash', sa.String(length=100), nullable=True),
        sa.Column('last_commit_message', sa.String(length=500), nullable=True),
        sa.Column('last_commit_at', sa.DateTime(), nullable=True),
        sa.Column('import_method', sa.String(length=50), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repositories_name'), 'repositories', ['name'], unique=False)

    # Create repository_imports table
    op.create_table(
        'repository_imports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('job_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create repository_settings table
    op.create_table(
        'repository_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('is_auto_sync', sa.Boolean(), nullable=False),
        sa.Column('sync_interval_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id')
    )

    # Create repository_tags table
    op.create_table(
        'repository_tags',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('tag_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('repository_tags')
    op.drop_table('repository_settings')
    op.drop_table('repository_imports')
    op.drop_index(op.f('ix_repositories_name'), table_name='repositories')
    op.drop_table('repositories')
    op.drop_table('github_accounts')

    op.drop_index(op.f('ix_users_github_username'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')

    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'provider')
    op.drop_column('users', 'github_username')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'username')
