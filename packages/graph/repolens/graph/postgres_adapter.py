import json
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from repolens.graph.interface import GraphStorageInterface


class PostgresGraphAdapter(GraphStorageInterface):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def add_node(
        self,
        node_id: str,
        repository_id: str,
        name: str,
        node_type: str,
        parent_id: Optional[str] = None,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        metadata_str = json.dumps(metadata or {})
        
        # Check if node exists
        check_query = text("SELECT id FROM graph_nodes WHERE id = :id")
        check_res = await self.db.execute(check_query, {"id": uuid.UUID(node_id)})
        exists = check_res.fetchone()

        if exists:
            update_query = text("""
                UPDATE graph_nodes 
                SET name = :name, node_type = :node_type, parent_id = :parent_id, 
                    file_path = :file_path, language = :language, metadata_json = :metadata
                WHERE id = :id
            """)
            await self.db.execute(
                update_query,
                {
                    "id": uuid.UUID(node_id),
                    "name": name,
                    "node_type": node_type,
                    "parent_id": uuid.UUID(parent_id) if parent_id else None,
                    "file_path": file_path,
                    "language": language,
                    "metadata": metadata_str
                }
            )
        else:
            insert_query = text("""
                INSERT INTO graph_nodes (id, repository_id, name, node_type, parent_id, file_path, language, metadata_json, created_at)
                VALUES (:id, :repository_id, :name, :node_type, :parent_id, :file_path, :language, :metadata, :now)
            """)
            await self.db.execute(
                insert_query,
                {
                    "id": uuid.UUID(node_id),
                    "repository_id": uuid.UUID(repository_id),
                    "name": name,
                    "node_type": node_type,
                    "parent_id": uuid.UUID(parent_id) if parent_id else None,
                    "file_path": file_path,
                    "language": language,
                    "metadata": metadata_str,
                    "now": __import__("datetime").datetime.utcnow()
                }
            )
            
    async def add_edge(
        self,
        edge_id: str,
        repository_id: str,
        source_id: str,
        target_id: str,
        edge_type: str,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        metadata_str = json.dumps(metadata or {})
        
        # Check duplicate edge
        check_query = text("""
            SELECT id FROM graph_edges 
            WHERE source_id = :source_id AND target_id = :target_id AND edge_type = :edge_type
        """)
        check_res = await self.db.execute(
            check_query, 
            {
                "source_id": uuid.UUID(source_id), 
                "target_id": uuid.UUID(target_id), 
                "edge_type": edge_type
            }
        )
        if check_res.fetchone():
            return

        insert_query = text("""
            INSERT INTO graph_edges (id, repository_id, source_id, target_id, edge_type, strength, metadata_json, created_at)
            VALUES (:id, :repository_id, :source_id, :target_id, :edge_type, :strength, :metadata, :now)
        """)
        await self.db.execute(
            insert_query,
            {
                "id": uuid.UUID(edge_id),
                "repository_id": uuid.UUID(repository_id),
                "source_id": uuid.UUID(source_id),
                "target_id": uuid.UUID(target_id),
                "edge_type": edge_type,
                "strength": strength,
                "metadata": metadata_str,
                "now": __import__("datetime").datetime.utcnow()
            }
        )

    async def get_nodes(self, repository_id: str) -> List[Dict[str, Any]]:
        query = text("""
            SELECT id, name, node_type, parent_id, file_path, language, metadata_json
            FROM graph_nodes 
            WHERE repository_id = :repo_id
        """)
        result = await self.db.execute(query, {"repo_id": uuid.UUID(repository_id)})
        nodes = []
        for row in result.fetchall():
            nodes.append({
                "id": str(row.id),
                "name": row.name,
                "type": row.node_type,
                "parent_id": str(row.parent_id) if row.parent_id else None,
                "file_path": row.file_path,
                "language": row.language,
                "metadata": row.metadata_json if isinstance(row.metadata_json, dict) else json.loads(row.metadata_json or "{}")
            })
        return nodes

    async def get_edges(self, repository_id: str) -> List[Dict[str, Any]]:
        query = text("""
            SELECT id, source_id, target_id, edge_type, strength, metadata_json
            FROM graph_edges 
            WHERE repository_id = :repo_id
        """)
        result = await self.db.execute(query, {"repo_id": uuid.UUID(repository_id)})
        edges = []
        for row in result.fetchall():
            edges.append({
                "id": str(row.id),
                "source": str(row.source_id),
                "target": str(row.target_id),
                "type": row.edge_type,
                "strength": row.strength,
                "metadata": row.metadata_json if isinstance(row.metadata_json, dict) else json.loads(row.metadata_json or "{}")
            })
        return edges

    async def clear_graph(self, repository_id: str) -> None:
        await self.db.execute(text("DELETE FROM graph_edges WHERE repository_id = :id"), {"id": uuid.UUID(repository_id)})
        await self.db.execute(text("DELETE FROM graph_nodes WHERE repository_id = :id"), {"id": uuid.UUID(repository_id)})
