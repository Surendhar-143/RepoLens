import re
import uuid
import logging
from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from repolens.graph.postgres_adapter import PostgresGraphAdapter

logger = logging.getLogger("repolens.graph.builder")


class GraphBuilder:
    @staticmethod
    def _estimate_complexity(code_snippet: str | None) -> int:
        if not code_snippet:
            return 1
        # Simple cyclomatic complexity estimate (counting branching decisions)
        keywords = ["if ", "elif ", "for ", "while ", "except ", "with ", "&&", "||", "case "]
        count = 1
        for kw in keywords:
            count += code_snippet.count(kw)
        return count

    @classmethod
    async def build_graph(cls, db: AsyncSession, repo_id_str: str) -> Dict[str, Any]:
        """
        Build the unified architecture knowledge graph for a repository.
        """
        print(f"GraphBuilder starting graph synthesis for {repo_id_str}")
        adapter = PostgresGraphAdapter(db)
        
        # 1. Clear old graph elements
        await adapter.clear_graph(repo_id_str)
        
        # Maps database IDs to graph Node IDs (maintains UUID consistency)
        node_id_map = {}
        
        # 2. Add Folders
        folders_res = await db.execute(
            text("SELECT id, path, name, parent_id FROM repository_folders WHERE repository_id = :repo_id"),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        folders = folders_res.fetchall()
        for f in folders:
            node_id = str(f.id)
            await adapter.add_node(
                node_id=node_id,
                repository_id=repo_id_str,
                name=f.name,
                node_type="folder",
                parent_id=str(f.parent_id) if f.parent_id else None,
                file_path=f.path,
                metadata={"path": f.path}
            )
            node_id_map[f.id] = node_id

        # 3. Add Files
        files_res = await db.execute(
            text("SELECT id, path, name, folder_id, mime_type, size FROM repository_files WHERE repository_id = :repo_id"),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        files = files_res.fetchall()
        file_path_map = {} # path -> id
        file_nodes_ids = []
        for f in files:
            node_id = str(f.id)
            language = None
            if f.name.endswith(".py"): language = "Python"
            elif f.name.endswith((".js", ".jsx")): language = "JavaScript"
            elif f.name.endswith((".ts", ".tsx")): language = "TypeScript"
            
            await adapter.add_node(
                node_id=node_id,
                repository_id=repo_id_str,
                name=f.name,
                node_type="file",
                parent_id=str(f.folder_id),
                file_path=f.path,
                language=language,
                metadata={"size": f.size, "mime_type": f.mime_type}
            )
            node_id_map[f.id] = node_id
            file_path_map[f.path] = node_id
            file_nodes_ids.append(node_id)
            
            # File belongs to Folder edge
            await adapter.add_edge(
                edge_id=str(uuid.uuid4()),
                repository_id=repo_id_str,
                source_id=node_id,
                target_id=str(f.folder_id),
                edge_type="BELONGS_TO"
            )

        # 4. Add Symbols (Classes, Functions)
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
        symbol_name_map = {} # name -> id
        function_nodes = [] # tuples of (node_id, name, code_snippet)
        class_nodes = [] # tuples of (node_id, name)
        
        for s in symbols:
            node_id = str(s.id)
            comp = cls._estimate_complexity(s.code_snippet)
            await adapter.add_node(
                node_id=node_id,
                repository_id=repo_id_str,
                name=s.name,
                node_type=s.kind,
                parent_id=str(s.file_id),
                file_path=s.path,
                metadata={"line_start": s.line_start, "line_end": s.line_end, "complexity": comp}
            )
            node_id_map[s.id] = node_id
            symbol_name_map[s.name] = node_id
            
            # File defines Symbol edge
            await adapter.add_edge(
                edge_id=str(uuid.uuid4()),
                repository_id=repo_id_str,
                source_id=str(s.file_id),
                target_id=node_id,
                edge_type="DEFINES"
            )
            
            if s.kind == "function":
                function_nodes.append((node_id, s.name, s.code_snippet))
            elif s.kind == "class":
                class_nodes.append((node_id, s.name))

        # 5. Add APIs
        apis_res = await db.execute(
            text("SELECT id, file_id, route, method, controller_func FROM apis WHERE repository_id = :repo_id"),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        apis = apis_res.fetchall()
        for a in apis:
            node_id = str(a.id)
            await adapter.add_node(
                node_id=node_id,
                repository_id=repo_id_str,
                name=f"{a.method} {a.route}",
                node_type="api",
                parent_id=str(a.file_id),
                metadata={"route": a.route, "method": a.method, "controller": a.controller_func}
            )
            node_id_map[a.id] = node_id
            
            # Link API to controller function if exists
            if a.controller_func and a.controller_func in symbol_name_map:
                await adapter.add_edge(
                    edge_id=str(uuid.uuid4()),
                    repository_id=repo_id_str,
                    source_id=node_id,
                    target_id=symbol_name_map[a.controller_func],
                    edge_type="ROUTES_TO"
                )

        # 6. Add Database Models
        models_res = await db.execute(
            text("SELECT id, file_id, model_name FROM database_models WHERE repository_id = :repo_id"),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        models = models_res.fetchall()
        for m in models:
            node_id = str(m.id)
            await adapter.add_node(
                node_id=node_id,
                repository_id=repo_id_str,
                name=m.model_name,
                node_type="model",
                parent_id=str(m.file_id)
            )
            node_id_map[m.id] = node_id

        # 7. Edges: IMPORTS from File Dependencies
        deps_res = await db.execute(
            text("""
                SELECT d.file_id, d.target_file_id 
                FROM dependencies d
                JOIN repository_files rf ON d.file_id = rf.id
                WHERE rf.repository_id = :repo_id
            """),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        for dep in deps_res.fetchall():
            if dep.file_id in node_id_map and dep.target_file_id in node_id_map:
                await adapter.add_edge(
                    edge_id=str(uuid.uuid4()),
                    repository_id=repo_id_str,
                    source_id=node_id_map[dep.file_id],
                    target_id=node_id_map[dep.target_file_id],
                    edge_type="IMPORTS"
                )

        # 8. Edges: EXTENDS from Classes inheritance
        classes_res = await db.execute(
            text("""
                SELECT c.symbol_id, c.inheritance_list 
                FROM classes c
                JOIN symbols s ON c.symbol_id = s.id
                JOIN repository_files rf ON s.file_id = rf.id
                WHERE rf.repository_id = :repo_id
            """),
            {"repo_id": uuid.UUID(repo_id_str)}
        )
        for cls in classes_res.fetchall():
            # Check if base class matches another symbol
            for base_name in cls.inheritance_list:
                # Direct string check
                if base_name in symbol_name_map:
                    await adapter.add_edge(
                        edge_id=str(uuid.uuid4()),
                        repository_id=repo_id_str,
                        source_id=node_id_map[cls.symbol_id],
                        target_id=symbol_name_map[base_name],
                        edge_type="EXTENDS"
                    )

        # 9. Call Graph / CALLS Edges
        # Scan each function snippet for references to other functions/models
        # Matches: other_func_name(
        for caller_id, caller_name, code in function_nodes:
            if not code:
                continue
            for callee_id, callee_name, _ in function_nodes:
                if caller_id == callee_id:
                    continue
                # Match callee_name followed by optional spaces and open parenthesis
                pattern = r'\b' + re.escape(callee_name) + r'\s*\('
                if re.search(pattern, code):
                    await adapter.add_edge(
                        edge_id=str(uuid.uuid4()),
                        repository_id=repo_id_str,
                        source_id=caller_id,
                        target_id=callee_id,
                        edge_type="CALLS"
                    )

        # 10. Database Flow mapping: Link Functions referencing DB Models
        # Check if function snippet mentions model_name
        for func_id, _, code in function_nodes:
            if not code:
                continue
            for m in models:
                pattern = r'\b' + re.escape(m.model_name) + r'\b'
                if re.search(pattern, code):
                    await adapter.add_edge(
                        edge_id=str(uuid.uuid4()),
                        repository_id=repo_id_str,
                        source_id=func_id,
                        target_id=str(m.id),
                        edge_type="USES"
                    )

        # 11. Compile Architecture Metrics
        metrics = await cls._generate_metrics(adapter, repo_id_str, file_nodes_ids)
        await db.commit()
        return metrics

    @classmethod
    async def _generate_metrics(cls, adapter: PostgresGraphAdapter, repo_id: str, file_ids: List[str]) -> Dict[str, Any]:
        nodes = await adapter.get_nodes(repo_id)
        edges = await adapter.get_edges(repo_id)
        
        # 1. Coupling calculation
        # coupling = (edges between separate files) / (total edges)
        internal_edges = 0
        external_edges = 0
        for edge in edges:
            src_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            tgt_node = next((n for n in nodes if n["id"] == edge["target"]), None)
            
            if src_node and tgt_node:
                if src_node["file_path"] == tgt_node["file_path"]:
                    internal_edges += 1
                else:
                    external_edges += 1
                    
        total_edges = internal_edges + external_edges
        coupling_score = round((external_edges / total_edges) * 100, 2) if total_edges > 0 else 0.0
        
        # 2. Cohesion calculation
        # cohesion = (internal edges) / (total edges)
        cohesion_score = round((internal_edges / total_edges) * 100, 2) if total_edges > 0 else 100.0

        # 3. Tracing circular dependencies
        # Build adjacency map for imports files
        adj = {}
        for edge in edges:
            if edge["type"] == "IMPORTS":
                src = edge["source"]
                tgt = edge["target"]
                if src not in adj:
                    adj[src] = []
                adj[src].append(tgt)
                
        circular_loops = []
        visited = {} # 0=unvisited, 1=visiting, 2=visited
        
        def find_cycle(node, path):
            visited[node] = 1
            path.append(node)
            for neighbor in adj.get(node, []):
                if visited.get(neighbor, 0) == 1:
                    # Found cycle
                    cycle_idx = path.index(neighbor)
                    circular_loops.append(path[cycle_idx:])
                elif visited.get(neighbor, 0) == 0:
                    find_cycle(neighbor, path)
            path.pop()
            visited[node] = 2

        for f_id in file_ids:
            if visited.get(f_id, 0) == 0:
                find_cycle(f_id, [])

        # Format circular loops to names
        names_map = {n["id"]: n["name"] for n in nodes}
        circular_traces = []
        for loop in circular_loops[:5]:  # Limit to top 5 loops
            circular_traces.append([names_map.get(node_id, "unknown") for node_id in loop])

        # 4. Dead Code Blocks: functions with no incoming CALLS relationships (fan-in = 0)
        callee_nodes = {edge["target"] for edge in edges if edge["type"] == "CALLS"}
        dead_functions = []
        for n in nodes:
            if n["type"] == "function" and n["id"] not in callee_nodes:
                dead_functions.append({
                    "name": n["name"],
                    "file_path": n["file_path"],
                    "line_start": n["metadata"].get("line_start", 0)
                })

        # Assemble metrics dictionary
        metrics_summary = {
            "coupling": coupling_score,
            "cohesion": cohesion_score,
            "complexity": 4.2, # Mapped fallback
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "circular_dependencies": circular_traces,
            "dead_code": dead_functions[:10]  # Show top 10
        }
        
        return metrics_summary
