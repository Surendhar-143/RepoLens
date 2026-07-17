"""Phase 3 tables

Revision ID: c4d4d4d4d4d4
Revises: c3f3e9e9e99b
Create Date: 2026-07-17 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d4d4d4d4d4'
down_revision: Union[str, None] = 'c3f3e9e9e99b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create graph_nodes table
    op.create_table(
        'graph_nodes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_graph_nodes_name'), 'graph_nodes', ['name'], unique=False)

    # Create graph_edges table
    op.create_table(
        'graph_edges',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('repository_id', sa.UUID(), nullable=False),
        sa.Column('source_id', sa.UUID(), nullable=False),
        sa.Column('target_id', sa.UUID(), nullable=False),
        sa.Column('edge_type', sa.String(length=50), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['graph_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('graph_edges')
    op.drop_index(op.f('ix_graph_nodes_name'), table_name='graph_nodes')
    op.drop_table('graph_nodes')
