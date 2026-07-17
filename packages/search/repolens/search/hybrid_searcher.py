import math
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from repolens.embeddings.providers import HashedMockEmbeddingProvider
from repolens.search.qdrant_client import QdrantSearchClient


class HybridSearcher:
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        qdrant_api_key: Optional[str] = None,
        embedding_provider: Optional[Any] = None
    ):
        self.qdrant = QdrantSearchClient(host=qdrant_host, port=qdrant_port, api_key=qdrant_api_key)
        self.embedding = embedding_provider or HashedMockEmbeddingProvider()

    async def search(
        self,
        db: AsyncSession,
        repository_id: str,
        query: str,
        limit: int = 15,
        chunk_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Hybrid Search merging Lexical matching, Semantic vectors, and Knowledge Graph degrees.
        """
        print(f"HybridSearcher running hybrid query: '{query}' for repository {repository_id}")
        
        # 1. Semantic Vector Search
        query_vector = await self.embedding.get_embedding(query)
        semantic_hits = []
        try:
            semantic_hits = await self.qdrant.search_similarity(
                repository_id=repository_id,
                query_vector=query_vector,
                limit=limit * 2,
                chunk_type=chunk_type
            )
        except Exception as e:
            print(f"Vector search failed (falling back to lexical): {str(e)}")

        # 2. Lexical Database Search (mimics PostgreSQL Full Text Search)
        # Search repository files content
        lexical_hits = []
        try:
            file_query = text("""
                SELECT id, path, name, content 
                FROM repository_files 
                WHERE repository_id = :repo_id AND (name ILIKE :q OR content ILIKE :q)
                LIMIT :limit
            """)
            file_res = await db.execute(file_query, {"repo_id": uuid.UUID(repository_id), "q": f"%{query}%", "limit": limit})
            for row in file_res.fetchall():
                lexical_hits.append({
                    "id": str(row.id),
                    "file_id": str(row.id),
                    "file_path": row.path,
                    "content": (row.content or "")[:400],
                    "type": "file",
                    "score": 1.0 if query.lower() in row.name.lower() else 0.5,
                    "metadata": {"name": row.name}
                })

            # Search symbols (functions / classes)
            sym_query = text("""
                SELECT s.id, s.name, s.kind, s.file_id, s.code_snippet, rf.path 
                FROM symbols s
                JOIN repository_files rf ON s.file_id = rf.id
                WHERE rf.repository_id = :repo_id AND (s.name ILIKE :q OR s.code_snippet ILIKE :q)
                LIMIT :limit
            """)
            sym_res = await db.execute(sym_query, {"repo_id": uuid.UUID(repository_id), "q": f"%{query}%", "limit": limit})
            for row in sym_res.fetchall():
                lexical_hits.append({
                    "id": str(row.id),
                    "file_id": str(row.file_id),
                    "file_path": row.path,
                    "content": (row.code_snippet or "")[:400],
                    "type": row.kind,
                    "score": 1.0 if query.lower() in row.name.lower() else 0.6,
                    "metadata": {"name": row.name, "symbol_id": str(row.id)}
                })
        except Exception as e:
            print(f"Lexical search failed: {str(e)}")

        # 3. Load Knowledge Graph weights (Degree Centrality: count of incoming links)
        graph_weights = {}
        try:
            weights_query = text("""
                SELECT target_id, count(id) as degree 
                FROM graph_edges 
                WHERE repository_id = :repo_id 
                GROUP BY target_id
            """)
            weights_res = await db.execute(weights_query, {"repo_id": uuid.UUID(repository_id)})
            for row in weights_res.fetchall():
                graph_weights[str(row.target_id)] = row.degree
        except Exception as e:
            print(f"Failed loading graph weights: {str(e)}")

        # 4. Perform Hybrid Fusion & Ranking
        # Dictionary mapping item key -> result
        merged_results: Dict[str, Dict[str, Any]] = {}

        # Merge semantic hits (weight: 0.6)
        for hit in semantic_hits:
            key = hit.get("id") or hit.get("file_path")
            if not key:
                continue
            
            # Extract symbol or node reference
            symbol_id = hit.get("metadata", {}).get("symbol_id")
            entity_id = symbol_id if symbol_id else hit.get("file_id")
            degree = graph_weights.get(entity_id, 0)
            graph_boost = math.log1p(degree) * 0.1

            merged_results[key] = {
                "title": hit["metadata"].get("name") or hit["file_path"].split("/")[-1],
                "type": hit["type"],
                "file_id": hit["file_id"],
                "file_path": hit["file_path"],
                "content_preview": (hit["content"] or "")[:400],
                "score": round((hit["score"] * 0.6) + graph_boost, 3),
                "metadata": hit["metadata"]
            }

        # Merge lexical hits (weight: 0.4)
        for hit in lexical_hits:
            key = hit["id"]
            symbol_id = hit["metadata"].get("symbol_id")
            entity_id = symbol_id if symbol_id else hit["file_id"]
            degree = graph_weights.get(entity_id, 0)
            graph_boost = math.log1p(degree) * 0.1

            lexical_contribution = hit["score"] * 0.4
            
            if key in merged_results:
                # Add lexical contribution if already in semantic
                merged_results[key]["score"] = round(merged_results[key]["score"] + lexical_contribution, 3)
            else:
                merged_results[key] = {
                    "title": hit["metadata"].get("name") or hit["file_path"].split("/")[-1],
                    "type": hit["type"],
                    "file_id": hit["file_id"],
                    "file_path": hit["file_path"],
                    "content_preview": hit["content"],
                    "score": round(lexical_contribution + graph_boost, 3),
                    "metadata": hit["metadata"]
                }

        # Sort and limit
        sorted_results = sorted(merged_results.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:limit]
