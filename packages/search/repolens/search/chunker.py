import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class CodeChunk:
    def __init__(
        self,
        repository_id: str,
        file_id: str,
        file_path: str,
        content: str,
        chunk_type: str,
        metadata: Dict[str, Any]
    ):
        self.id = str(uuid.uuid4())
        self.repository_id = repository_id
        self.file_id = file_id
        self.file_path = file_path
        self.content = content
        self.chunk_type = chunk_type
        self.metadata = metadata


class Chunker:
    @staticmethod
    async def build_chunks_for_repository(db: AsyncSession, repo_id_str: str) -> List[CodeChunk]:
        """
        Scan repository tables and compile codebase elements into searchable text chunks.
        """
        chunks: List[CodeChunk] = []

        # 1. Fetch all files (to chunk general files / READMEs)
        files_res = await db.execute(
            text("SELECT id, path, name, content FROM repository_files WHERE repository_id = :repo_id"),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        files = files_res.fetchall()
        
        for f in files:
            file_id_str = str(f.id)
            file_content = f.content or ""
            
            # If it's a markdown or readme file, chunk it as documentation
            if f.name.endswith((".md", ".txt")):
                # Split markdown into paragraphs or headings chunks if too large
                paragraphs = [p.strip() for p in file_content.split("\n\n") if p.strip()]
                for idx, p in enumerate(paragraphs):
                    chunks.append(CodeChunk(
                        repository_id=repo_id_str,
                        file_id=file_id_str,
                        file_path=f.path,
                        content=f"File: {f.path}\n\n{p}",
                        chunk_type="documentation",
                        metadata={"name": f.name, "index": idx}
                    ))
                continue

            # Generic fallback chunk for small files
            if len(file_content) < 1500:
                chunks.append(CodeChunk(
                    repository_id=repo_id_str,
                    file_id=file_id_str,
                    file_path=f.path,
                    content=f"File: {f.path}\nContent:\n{file_content}",
                    chunk_type="file",
                    metadata={"name": f.name}
                ))

        # 2. Fetch all symbols (Classes / Functions)
        symbols_res = await db.execute(
            text("""
                SELECT s.id, s.name, s.kind, s.file_id, s.line_start, s.line_end, s.code_snippet, s.docstring, rf.path
                FROM symbols s
                JOIN repository_files rf ON s.file_id = rf.id
                WHERE rf.repository_id = :repo_id
            """),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        symbols = symbols_res.fetchall()
        for s in symbols:
            content_block = (
                f"File: {s.path}\n"
                f"Symbol type: {s.kind}\n"
                f"Name: {s.name}\n"
                f"Docstring: {s.docstring or 'None'}\n"
                f"Code snippet:\n{s.code_snippet or ''}"
            )
            chunks.append(CodeChunk(
                repository_id=repo_id_str,
                file_id=str(s.file_id),
                file_path=s.path,
                content=content_block,
                chunk_type=s.kind,
                metadata={
                    "name": s.name,
                    "symbol_id": str(s.id),
                    "line_start": s.line_start,
                    "line_end": s.line_end
                }
            ))

        # 3. Fetch all APIs
        apis_res = await db.execute(
            text("""
                SELECT a.id, a.file_id, a.route, a.method, a.controller_func, rf.path
                FROM apis a
                JOIN repository_files rf ON a.file_id = rf.id
                WHERE a.repository_id = :repo_id
            """),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        for a in apis_res.fetchall():
            content_block = (
                f"File: {a.path}\n"
                f"API Endpoint: {a.method} {a.route}\n"
                f"Controller handler: {a.controller_func or 'None'}"
            )
            chunks.append(CodeChunk(
                repository_id=repo_id_str,
                file_id=str(a.file_id),
                file_path=a.path,
                content=content_block,
                chunk_type="api",
                metadata={"route": a.route, "method": a.method, "controller": a.controller_func}
            ))

        # 4. Fetch all ORM database models
        models_res = await db.execute(
            text("""
                SELECT m.id, m.file_id, m.model_name, m.fields_json, m.relationships_json, rf.path
                FROM database_models m
                JOIN repository_files rf ON m.file_id = rf.id
                WHERE m.repository_id = :repo_id
            """),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        for m in models_res.fetchall():
            content_block = (
                f"File: {m.path}\n"
                f"ORM Model: {m.model_name}\n"
                f"Fields defined: {m.fields_json}\n"
                f"Model relationships: {m.relationships_json}"
            )
            chunks.append(CodeChunk(
                repository_id=repo_id_str,
                file_id=str(m.file_id),
                file_path=m.path,
                content=content_block,
                chunk_type="model",
                metadata={"model_name": m.model_name}
            ))

        return chunks
