"""Phase 2 tables

Revision ID: c3f3e9e9e99b
Revises: b2e2d9b9d99a
Create Date: 2026-07-17 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f3e9e9e99b'
down_revision: Union[str, None] = 'b2e2d9b9d99a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create repository_folders table
    op.create_table(
        'repository_folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['repository_folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create repository_files table
    op.create_table(
        'repository_files',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('folder_id', sa.UUID(), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('hash', sa.String(length=100), nullable=False),
        sa.Column('content_summary', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['folder_id'], ['repository_folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create symbols table
    op.create_table(
        'symbols',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('kind', sa.String(length=50), nullable=False),
        sa.Column('line_start', sa.Integer(), nullable=False),
        sa.Column('line_end', sa.Integer(), nullable=False),
        sa.Column('code_snippet', sa.String(length=2000), nullable=True),
        sa.Column('docstring', sa.String(length=1000), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_symbols_name'), 'symbols', ['name'], unique=False)

    # Create classes table
    op.create_table(
        'classes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol_id', sa.UUID(), nullable=False),
        sa.Column('inheritance_list', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['symbol_id'], ['symbols.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol_id')
    )

    # Create functions table
    op.create_table(
        'functions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol_id', sa.UUID(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('return_type', sa.String(length=100), nullable=True),
        sa.Column('decorator_list', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['symbol_id'], ['symbols.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol_id')
    )

    # Create imports table
    op.create_table(
        'imports',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('source_module', sa.String(length=255), nullable=False),
        sa.Column('imported_symbols', sa.JSON(), nullable=False),
        sa.Column('is_external', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create dependencies table
    op.create_table(
        'dependencies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('target_file_id', sa.UUID(), nullable=False),
        sa.Column('dependency_type', sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create apis table
    op.create_table(
        'apis',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('route', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('controller_func', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_apis_route'), 'apis', ['route'], unique=False)

    # Create database_models table
    op.create_table(
        'database_models',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('file_id', sa.UUID(), nullable=False),
        sa.Column('model_name', sa.String(length=255), nullable=False),
        sa.Column('fields_json', sa.JSON(), nullable=False),
        sa.Column('relationships_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_database_models_model_name'), 'database_models', ['model_name'], unique=False)

    # Create analysis_statistics table
    op.create_table(
        'analysis_statistics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('loc', sa.Integer(), nullable=False),
        sa.Column('files_count', sa.Integer(), nullable=False),
        sa.Column('folders_count', sa.Integer(), nullable=False),
        sa.Column('languages_json', sa.JSON(), nullable=False),
        sa.Column('frameworks_json', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id')
    )


def downgrade() -> None:
    op.drop_table('analysis_statistics')
    op.drop_index(op.f('ix_database_models_model_name'), table_name='database_models')
    op.drop_table('database_models')
    op.drop_index(op.f('ix_apis_route'), table_name='apis')
    op.drop_table('apis')
    op.drop_table('dependencies')
    op.drop_table('imports')
    op.drop_table('functions')
    op.drop_table('classes')
    op.drop_index(op.f('ix_symbols_name'), table_name='symbols')
    op.drop_table('symbols')
    op.drop_table('repository_files')
    op.drop_table('repository_folders')
