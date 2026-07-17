import os
import sys
import uuid
import shutil
import logging
import asyncio
import zipfile
from datetime import datetime
from arq.connections import RedisSettings, create_pool
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
import git

# Add packages paths dynamically
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../packages/analyzer")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../packages/parsers")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../packages/graph")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../packages/search")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../packages/embeddings")))

from repolens.analyzer.scanner import CodebaseScanner
from repolens.analyzer.languages import LanguageDetector, FrameworkDetector
from repolens.parsers.python import PythonASTParser
from repolens.parsers.javascript import JavaScriptParser
from repolens.analyzer.api_detector import APIDetector
from repolens.analyzer.db_detector import DatabaseDetector
from repolens.graph.builder import GraphBuilder
from repolens.search.chunker import Chunker
from repolens.search.qdrant_client import QdrantSearchClient
from repolens.embeddings.providers import OpenAIEmbeddingProvider, SentenceTransformersProvider

# Load configurations
class WorkerConfig(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    # Postgres database URL (local or docker service endpoint)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "repolens"
    DATABASE_URL: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

config = WorkerConfig()

# Assemble DB url
db_url = config.DATABASE_URL
if not db_url:
    db_url = f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"

# Initialize Database Engine
engine = create_async_engine(db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Utility to calculate repository size and scan file extensions for language stubs
def analyze_repository_folder(path: str) -> tuple[int, dict]:
    total_size = 0  # in KB
    extension_counts = {}
    
    # Map file extensions to languages
    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".cs": "C#",
        ".html": "HTML",
        ".css": "CSS",
        ".php": "PHP",
        ".sh": "Shell"
    }

    for root, dirs, files in os.walk(path):
        # Exclude git internal folder to prevent skewing sizes
        if ".git" in dirs:
            dirs.remove(".git")
            
        for f in files:
            fp = os.path.join(root, f)
            try:
                if os.path.exists(fp) and not os.path.islink(fp):
                    size = os.path.getsize(fp)
                    total_size += size
                    
                    _, ext = os.path.splitext(f)
                    ext = ext.lower()
                    if ext in lang_map:
                        lang = lang_map[ext]
                        extension_counts[lang] = extension_counts.get(lang, 0) + size
            except Exception:
                pass
                
    # Normalize language ratios
    total_lang_bytes = sum(extension_counts.values())
    languages_pct = {}
    if total_lang_bytes > 0:
        for lang, bytes_count in extension_counts.items():
            languages_pct[lang] = round((bytes_count / total_lang_bytes) * 100, 2)
            
    return round(total_size / 1024), languages_pct


# Database helpers
async def update_job_status(db: AsyncSession, import_id: str, status: str, progress: float, error_msg: str | None = None):
    query = text("""
        UPDATE repository_imports 
        SET status = :status, progress = :progress, error_message = :error_msg, updated_at = :now
        WHERE id = :id
    """)
    await db.execute(query, {
        "status": status,
        "progress": progress,
        "error_msg": error_msg,
        "now": datetime.utcnow(),
        "id": uuid.UUID(import_id)
    })
    await db.commit()


async def update_repository_metadata(db: AsyncSession, repo_id: str, size: int, default_branch: str, languages: dict, commit_hash: str | None, commit_msg: str | None, commit_date: datetime | None):
    query = text("""
        UPDATE repositories 
        SET size = :size, default_branch = :default_branch, languages = :languages, 
            last_commit_hash = :commit_hash, last_commit_message = :commit_msg, last_commit_at = :commit_date,
            updated_at = :now
        WHERE id = :id
    """)
    await db.execute(query, {
        "size": size,
        "default_branch": default_branch,
        "languages": __import__("json").dumps(languages),
        "commit_hash": commit_hash,
        "commit_msg": commit_msg,
        "commit_date": commit_date,
        "now": datetime.utcnow(),
        "id": uuid.UUID(repo_id)
    })
    await db.commit()


# ARQ background task functions
async def clone_repository_task(ctx, repo_id_str: str, clone_url: str, local_path: str, import_id_str: str) -> str:
    print(f"Starting repository clone: {clone_url} to {local_path}")
    
    async with AsyncSessionLocal() as db:
        try:
            await update_job_status(db, import_id_str, "running", 20.0)
            
            # Clean directory if already exists
            if os.path.exists(local_path):
                shutil.rmtree(local_path, ignore_errors=True)
                
            # Perform git clone asynchronously
            loop = asyncio.get_event_loop()
            repo = await loop.run_in_executor(
                None, 
                lambda: git.Repo.clone_from(clone_url, local_path, depth=1)
            )
            
            await update_job_status(db, import_id_str, "running", 60.0)
            
            # Fetch last commit details
            commit = repo.head.commit
            commit_hash = commit.hexsha
            commit_msg = commit.message.strip()
            commit_date = datetime.fromtimestamp(commit.committed_date)
            default_branch = repo.active_branch.name

            # Calculate size and parse language ratios
            size, languages = analyze_repository_folder(local_path)
            
            await update_repository_metadata(
                db, repo_id_str, size, default_branch, languages, commit_hash, commit_msg, commit_date
            )
            await update_job_status(db, import_id_str, "completed", 100.0)
            print(f"Clone completed successfully for {clone_url}")
            return f"Cloned {repo_id_str}"
            
        except Exception as e:
            print(f"Clone failed for {clone_url}: {str(e)}")
            await update_job_status(db, import_id_str, "failed", 100.0, f"Git clone failed: {str(e)}")
            # Cleanup partial files
            if os.path.exists(local_path):
                shutil.rmtree(local_path, ignore_errors=True)
            raise e


async def extract_zip_repository_task(ctx, repo_id_str: str, zip_path: str, local_path: str, import_id_str: str) -> str:
    print(f"Starting ZIP extraction: {zip_path} to {local_path}")
    
    async with AsyncSessionLocal() as db:
        try:
            await update_job_status(db, import_id_str, "running", 20.0)
            
            if os.path.exists(local_path):
                shutil.rmtree(local_path, ignore_errors=True)
            os.makedirs(local_path, exist_ok=True)
            
            # Perform extraction with Zip Slip validation check
            with zipfile.ZipFile(zip_path, 'r') as ref:
                for member in ref.infolist():
                    target_file = os.path.abspath(os.path.join(local_path, member.filename))
                    if not target_file.startswith(os.path.abspath(local_path)):
                        raise Exception("Security exception: Zip Slip path traversal attempt detected.")
                
                # Safe to extract
                ref.extractall(local_path)
                
            await update_job_status(db, import_id_str, "running", 60.0)
            
            # Check if extracted folder is wrapped inside a subfolder (common in GitHub downloads)
            extracted_items = os.listdir(local_path)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(local_path, extracted_items[0])):
                # Move contents up one level
                subfolder = os.path.join(local_path, extracted_items[0])
                for item in os.listdir(subfolder):
                    shutil.move(os.path.join(subfolder, item), local_path)
                os.rmdir(subfolder)

            # Check if git is initialized
            commit_hash, commit_msg, commit_date = None, None, None
            default_branch = "main"
            try:
                repo = git.Repo(local_path)
                commit = repo.head.commit
                commit_hash = commit.hexsha
                commit_msg = commit.message.strip()
                commit_date = datetime.fromtimestamp(commit.committed_date)
                default_branch = repo.active_branch.name
            except Exception:
                # Local zip without git index, initialize git to satisfy requirements
                try:
                    repo = git.Repo.init(local_path)
                    repo.index.add("*")
                    # Commit if files exist
                    if len(repo.index.entries) > 0:
                        commit = repo.index.commit("Initial import commit via RepoLens")
                        commit_hash = commit.hexsha
                        commit_msg = commit.message
                        commit_date = datetime.utcnow()
                except Exception:
                    pass

            # Calculate size & scan files
            size, languages = analyze_repository_folder(local_path)
            
            await update_repository_metadata(
                db, repo_id_str, size, default_branch, languages, commit_hash, commit_msg, commit_date
            )
            await update_job_status(db, import_id_str, "completed", 100.0)
            
            # Delete temporary zip archive
            if os.path.exists(zip_path):
                os.remove(zip_path)
                
            print(f"Zip extraction completed successfully for {repo_id_str}")
            return f"Extracted {repo_id_str}"
            
        except Exception as e:
            print(f"Zip extraction failed for {repo_id_str}: {str(e)}")
            await update_job_status(db, import_id_str, "failed", 100.0, f"Zip extraction failed: {str(e)}")
            if os.path.exists(local_path):
                shutil.rmtree(local_path, ignore_errors=True)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise e


async def refresh_repository_task(ctx, repo_id_str: str, clone_url: str | None, local_path: str, import_id_str: str) -> str:
    print(f"Refreshing repository: {repo_id_str}")
    
    async with AsyncSessionLocal() as db:
        try:
            await update_job_status(db, import_id_str, "running", 20.0)
            
            if not os.path.exists(local_path):
                raise Exception("Local repository cache directory not found.")
                
            repo = git.Repo(local_path)
            
            # If GitHub clone, fetch and pull latest branch details
            if clone_url and repo.remotes:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: repo.remotes.origin.pull())
                
            await update_job_status(db, import_id_str, "running", 65.0)
            
            commit = repo.head.commit
            commit_hash = commit.hexsha
            commit_msg = commit.message.strip()
            commit_date = datetime.fromtimestamp(commit.committed_date)
            default_branch = repo.active_branch.name

            # Recalculate size & scans
            size, languages = analyze_repository_folder(local_path)
            
            await update_repository_metadata(
                db, repo_id_str, size, default_branch, languages, commit_hash, commit_msg, commit_date
            )
            await update_job_status(db, import_id_str, "completed", 100.0)
            print(f"Refresh completed successfully for {repo_id_str}")
            return f"Refreshed {repo_id_str}"
            
        except Exception as e:
            print(f"Refresh failed for {repo_id_str}: {str(e)}")
            await update_job_status(db, import_id_str, "failed", 100.0, f"Refresh failed: {str(e)}")
            raise e


async def delete_repository_files_task(ctx, local_path: str) -> str:
    print(f"Purging workspace cache directory: {local_path}")
    try:
        if os.path.exists(local_path):
            shutil.rmtree(local_path, ignore_errors=True)
        return "Deleted successfully"
    except Exception as e:
        print(f"Failed to delete directory {local_path}: {str(e)}")
        return f"Failed: {str(e)}"


async def analyze_repository_task(ctx, repo_id_str: str, import_id_str: str) -> str:
    print(f"Starting repository analysis for {repo_id_str}")
    async with AsyncSessionLocal() as db:
        try:
            # 1. Update job status to running (5.0%)
            await update_job_status(db, import_id_str, "running", 5.0)
            
            # Fetch repository details
            repo_res = await db.execute(text("SELECT name, local_path FROM repositories WHERE id = :id"), {"id": uuid.UUID(repo_id_str)})
            repo = repo_res.fetchone()
            if not repo:
                raise Exception("Repository not found in database.")
                
            local_path = repo.local_path
            if not os.path.exists(local_path):
                raise Exception(f"Local workspace cache path does not exist: {local_path}")
                
            # 2. Scanner run
            folders, files = CodebaseScanner.scan(local_path)
            await update_job_status(db, import_id_str, "running", 15.0)
            
            # 3. Detect languages and frameworks
            lang_stats = LanguageDetector.detect(files)
            frameworks = FrameworkDetector.detect(local_path, files)
            
            # 4. Save/Update folder hierarchy
            # Delete old folders & files first for clean state if not incremental,
            # but for incremental reanalysis let's check existing hashes.
            # To be safe and clean, let's query existing files to match hashes.
            existing_files_res = await db.execute(
                text("SELECT id, path, hash FROM repository_files WHERE repository_id = :repo_id"),
                {"repo_id": uuid.UUID(repo_id_str)}
            )
            existing_files = {row.path: (row.id, row.hash) for row in existing_files_res.fetchall()}
            
            # Clear old folders & statistics (clean refresh for folders)
            await db.execute(text("DELETE FROM repository_folders WHERE repository_id = :repo_id"), {"repo_id": uuid.UUID(repo_id_str)})
            await db.execute(text("DELETE FROM analysis_statistics WHERE repository_id = :repo_id"), {"repo_id": uuid.UUID(repo_id_str)})
            
            # Insert Folders
            folder_ids = {} # maps path to UUID
            for folder in sorted(folders, key=lambda x: x["depth"]):
                folder_uuid = uuid.uuid4()
                # Resolve parent folder
                parent_path = os.path.dirname(folder["path"])
                parent_uuid = folder_ids.get(parent_path) if folder["path"] != "" else None
                
                await db.execute(
                    text("""
                        INSERT INTO repository_folders (id, repository_id, parent_id, path, name, depth, size)
                        VALUES (:id, :repository_id, :parent_id, :path, :name, :depth, :size)
                    """),
                    {
                        "id": folder_uuid,
                        "repository_id": uuid.UUID(repo_id_str),
                        "parent_id": parent_uuid,
                        "path": folder["path"],
                        "name": folder["name"],
                        "depth": folder["depth"],
                        "size": folder["size"]
                    }
                )
                folder_ids[folder["path"]] = folder_uuid
                
            await db.flush()
            
            # 5. Insert Files & Parse AST Symbols
            # We process files one by one. Update progress periodically.
            total_files = len(files)
            processed_count = 0
            total_loc = 0
            
            # Keep a map of file_path -> file_id for dependencies tracing later
            file_path_to_id = {}
            
            for file_idx, f in enumerate(files):
                f_path = f["path"]
                folder_uuid = folder_ids.get(f["folder_path"])
                
                # Check incremental hash matching
                is_skipped = False
                file_uuid = None
                if f_path in existing_files:
                    old_uuid, old_hash = existing_files[f_path]
                    if old_hash == f["hash"]:
                        is_skipped = True
                        file_uuid = old_uuid
                        # Still keep in folder-files relations
                        await db.execute(
                            text("""
                                UPDATE repository_files 
                                SET folder_id = :folder_id, size = :size
                                WHERE id = :id
                            """),
                            {"folder_id": folder_uuid, "size": f["size"], "id": old_uuid}
                        )
                        
                if not is_skipped:
                    # If modified, delete old symbols/imports/apis/models for this file
                    if f_path in existing_files:
                        old_uuid, _ = existing_files[f_path]
                        await db.execute(text("DELETE FROM symbols WHERE file_id = :file_id"), {"file_id": old_uuid})
                        await db.execute(text("DELETE FROM imports WHERE file_id = :file_id"), {"file_id": old_uuid})
                        await db.execute(text("DELETE FROM apis WHERE file_id = :file_id"), {"file_id": old_uuid})
                        await db.execute(text("DELETE FROM database_models WHERE file_id = :file_id"), {"file_id": old_uuid})
                        await db.execute(text("DELETE FROM repository_files WHERE id = :id"), {"id": old_uuid})
                    
                    file_uuid = uuid.uuid4()
                    await db.execute(
                        text("""
                            INSERT INTO repository_files (id, repository_id, folder_id, path, name, size, mime_type, hash, content_summary)
                            VALUES (:id, :repository_id, :folder_id, :path, :name, :size, :mime_type, :hash, :summary)
                        """),
                        {
                            "id": file_uuid,
                            "repository_id": uuid.UUID(repo_id_str),
                            "folder_id": folder_uuid,
                            "path": f_path,
                            "name": f["name"],
                            "size": f["size"],
                            "mime_type": f["mime_type"],
                            "hash": f["hash"],
                            "summary": f"{f['name']} file parsed during analysis"
                        }
                    )
                
                file_path_to_id[f_path] = file_uuid
                
                # Retrieve content and parse if not skipped
                file_abs = os.path.join(local_path, f_path)
                code_content = ""
                file_loc = 0
                if os.path.exists(file_abs):
                    try:
                        with open(file_abs, "r", encoding="utf-8", errors="ignore") as f_in:
                            code_content = f_in.read()
                            file_loc = len(code_content.splitlines())
                            total_loc += file_loc
                    except Exception:
                        pass
                
                if not is_skipped and code_content:
                    parsed_data = None
                    if f_path.endswith(".py"):
                        parsed_data = PythonASTParser.parse_code(code_content)
                    elif f_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                        parsed_data = JavaScriptParser.parse_code(code_content)
                        
                    if parsed_data:
                        # Save imports
                        for imp in parsed_data["imports"]:
                            await db.execute(
                                text("""
                                    INSERT INTO imports (id, file_id, source_module, imported_symbols, is_external)
                                    VALUES (:id, :file_id, :source, :symbols, :is_external)
                                """),
                                {
                                    "id": uuid.uuid4(),
                                    "file_id": file_uuid,
                                    "source": imp["source"],
                                    "symbols": __import__("json").dumps(imp["symbols"]),
                                    "is_external": imp["is_external"]
                                }
                            )
                            
                        # Save symbols (classes)
                        for cls_sym in parsed_data["classes"]:
                            sym_uuid = uuid.uuid4()
                            await db.execute(
                                text("""
                                    INSERT INTO symbols (id, file_id, name, kind, line_start, line_end, code_snippet, docstring)
                                    VALUES (:id, :file_id, :name, :kind, :line_start, :line_end, :snippet, :docstring)
                                """),
                                {
                                    "id": sym_uuid,
                                    "file_id": file_uuid,
                                    "name": cls_sym["name"],
                                    "kind": cls_sym["kind"],
                                    "line_start": cls_sym["line_start"],
                                    "line_end": cls_sym["line_end"],
                                    "snippet": cls_sym["code_snippet"],
                                    "docstring": cls_sym["docstring"]
                                }
                            )
                            await db.execute(
                                text("""
                                    INSERT INTO classes (id, symbol_id, inheritance_list)
                                    VALUES (:id, :symbol_id, :inheritance)
                                """),
                                {
                                    "id": uuid.uuid4(),
                                    "symbol_id": sym_uuid,
                                    "inheritance": __import__("json").dumps(cls_sym["inheritance"])
                                }
                            )
                            
                        # Save symbols (functions)
                        for func_sym in parsed_data["functions"]:
                            sym_uuid = uuid.uuid4()
                            await db.execute(
                                text("""
                                    INSERT INTO symbols (id, file_id, name, kind, line_start, line_end, code_snippet, docstring)
                                    VALUES (:id, :file_id, :name, :kind, :line_start, :line_end, :snippet, :docstring)
                                """),
                                {
                                    "id": sym_uuid,
                                    "file_id": file_uuid,
                                    "name": func_sym["name"],
                                    "kind": func_sym["kind"],
                                    "line_start": func_sym["line_start"],
                                    "line_end": func_sym["line_end"],
                                    "snippet": func_sym["code_snippet"],
                                    "docstring": func_sym["docstring"]
                                }
                            )
                            await db.execute(
                                text("""
                                    INSERT INTO functions (id, symbol_id, parameters, return_type, decorator_list)
                                    VALUES (:id, :symbol_id, :parameters, :return_type, :decorators)
                                """),
                                {
                                    "id": uuid.uuid4(),
                                    "symbol_id": sym_uuid,
                                    "parameters": __import__("json").dumps(func_sym["parameters"]),
                                    "return_type": func_sym["return_type"],
                                    "decorators": __import__("json").dumps(func_sym["decorators"])
                                }
                            )
                            
                    # Scan for API endpoints
                    apis_found = APIDetector.detect_apis(f_path, code_content)
                    for api in apis_found:
                        await db.execute(
                            text("""
                                INSERT INTO apis (id, repository_id, file_id, route, method, parameters, controller_func)
                                VALUES (:id, :repository_id, :file_id, :route, :method, :parameters, :controller)
                            """),
                            {
                                "id": uuid.uuid4(),
                                "repository_id": uuid.UUID(repo_id_str),
                                "file_id": file_uuid,
                                "route": api["route"],
                                "method": api["method"],
                                "parameters": __import__("json").dumps(api["parameters"]),
                                "controller": api["controller_func"]
                            }
                        )
                        
                    # Scan for Database ORM models
                    models_found = DatabaseDetector.detect_models(f_path, code_content)
                    for model in models_found:
                        await db.execute(
                            text("""
                                INSERT INTO database_models (id, repository_id, file_id, model_name, fields_json, relationships_json)
                                VALUES (:id, :repository_id, :file_id, :model_name, :fields, :relationships)
                            """),
                            {
                                "id": uuid.uuid4(),
                                "repository_id": uuid.UUID(repo_id_str),
                                "file_id": file_uuid,
                                "model_name": model["model_name"],
                                "fields": __import__("json").dumps(model["fields"]),
                                "relationships": __import__("json").dumps(model["relationships"])
                            }
                        )
                
                # Periodically sync progress
                processed_count += 1
                if processed_count % 10 == 0 or processed_count == total_files:
                    progress_pct = 15.0 + (processed_count / total_files) * 70.0
                    await update_job_status(db, import_id_str, "running", round(progress_pct, 1))

            await db.commit()
            
            # 6. Trace & link dependencies
            # Clear old dependency links
            await db.execute(
                text("DELETE FROM dependencies WHERE file_id IN (SELECT id FROM repository_files WHERE repository_id = :repo_id)"),
                {"repo_id": uuid.UUID(repo_id_str)}
            )
            
            # Fetch all imports to map local target dependencies
            imports_res = await db.execute(
                text("""
                    SELECT i.file_id, i.source_module, rf.path 
                    FROM imports i
                    JOIN repository_files rf ON i.file_id = rf.id
                    WHERE rf.repository_id = :repo_id
                """),
                {"repo_id": uuid.UUID(repo_id_str)}
            )
            
            for row in imports_res.fetchall():
                src_module = row.source_module
                # Simple resolution checks
                target_file_id = None
                
                # Check direct match with file names or folders
                for test_path, target_id in file_path_to_id.items():
                    # For example, if import is "app.core.config" or "app/core/config.py"
                    # clean path comparison
                    clean_mod = src_module.replace(".", "/").lower()
                    clean_path = test_path.lower().replace("\\", "/")
                    
                    if clean_mod in clean_path or clean_path.startswith(clean_mod):
                        target_file_id = target_id
                        break
                        
                if target_file_id and target_file_id != row.file_id:
                    await db.execute(
                        text("""
                            INSERT INTO dependencies (id, file_id, target_file_id, dependency_type)
                            VALUES (:id, :file_id, :target_file_id, :type)
                        """),
                        {
                            "id": uuid.uuid4(),
                            "file_id": row.file_id,
                            "target_file_id": target_file_id,
                            "type": "imports"
                        }
                    )
            
            # 7. Write Analysis Statistics
            await db.execute(
                text("""
                    INSERT INTO analysis_statistics (id, repository_id, loc, files_count, folders_count, languages_json, frameworks_json)
                    VALUES (:id, :repository_id, :loc, :files, :folders, :languages, :frameworks)
                """),
                {
                    "id": uuid.uuid4(),
                    "repository_id": uuid.UUID(repo_id_str),
                    "loc": total_loc,
                    "files": len(files),
                    "folders": len(folders),
                    "languages": __import__("json").dumps(lang_stats),
                    "frameworks": __import__("json").dumps(frameworks)
                }
            )
            
            # 8. Trigger Graph Synthesis
            try:
                redis_pool = ctx.get('redis')
                if redis_pool:
                    await redis_pool.enqueue_job("build_repository_graph_task", repo_id_str)
                else:
                    await GraphBuilder.build_graph(db, repo_id_str)
            except Exception as e:
                print(f"Failed to auto-trigger graph build in worker context: {str(e)}")
                # Fallback direct build
                await GraphBuilder.build_graph(db, repo_id_str)
                
            # 9. Complete Analysis Job
            await update_job_status(db, import_id_str, "completed", 100.0)
            await db.commit()
            print(f"Analysis completed successfully for {repo_id_str}")
            return f"Analyzed {repo_id_str}"
            
        except Exception as e:
            logger.error(f"Analysis failed for {repo_id_str}: {str(e)}", exc_info=True)
            await update_job_status(db, import_id_str, "failed", 100.0, f"Analysis failure: {str(e)}")
            raise e


async def build_repository_graph_task(ctx, repo_id_str: str) -> str:
    print(f"Executing standalone graph compilation task for repository {repo_id_str}")
    async with AsyncSessionLocal() as db:
        try:
            await GraphBuilder.build_graph(db, repo_id_str)
            
            # Trigger Vector Indexing
            try:
                redis_pool = ctx.get('redis')
                if redis_pool:
                    await redis_pool.enqueue_job("index_repository_embeddings_task", repo_id_str)
                else:
                    await run_indexing_directly(repo_id_str)
            except Exception as ex:
                print(f"Failed to auto-trigger vector indexing: {str(ex)}")
                await run_indexing_directly(repo_id_str)

            return f"Graph synthesized for {repo_id_str}"
        except Exception as e:
            logger.error(f"Failed standalone build_repository_graph_task: {str(e)}", exc_info=True)
            raise e


async def run_indexing_directly(repo_id_str: str) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        provider = OpenAIEmbeddingProvider(api_key=api_key)
    else:
        provider = SentenceTransformersProvider()
        
    async with AsyncSessionLocal() as db:
        chunks = await Chunker.build_chunks_for_repository(db, repo_id_str)
        if not chunks:
            print(f"No chunks created for repository {repo_id_str}")
            return
            
        texts = [c.content for c in chunks]
        embeddings = await provider.get_embeddings(texts)
        
        # Upsert into Qdrant
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        qdrant_client = QdrantSearchClient(host=qdrant_host, port=qdrant_port, api_key=qdrant_api_key)
        await qdrant_client.upsert_chunks(
            repository_id=repo_id_str,
            chunks=chunks,
            embeddings=embeddings,
            dimension=provider.get_dimension()
        )
        print(f"Successfully indexed vectors for {repo_id_str}")


async def index_repository_embeddings_task(ctx, repo_id_str: str) -> str:
    print(f"Executing standalone vector indexing task for repository {repo_id_str}")
    try:
        await run_indexing_directly(repo_id_str)
        return f"Embeddings indexed for {repo_id_str}"
    except Exception as e:
        logger.error(f"Failed standalone index_repository_embeddings_task: {str(e)}", exc_info=True)
        raise e


# ARQ Lifecycle Hooks
async def startup(ctx):
    print("ARQ Background Job Worker initialized successfully.")
    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    ctx['redis'] = await create_pool(redis_settings)


async def shutdown(ctx):
    print("ARQ Background Job Worker shutting down.")
    if 'redis' in ctx:
        await ctx['redis'].close()


# Export arq WorkerSettings
class WorkerSettings:
    functions = [
        clone_repository_task, 
        extract_zip_repository_task, 
        refresh_repository_task,
        delete_repository_files_task,
        analyze_repository_task,
        build_repository_graph_task,
        index_repository_embeddings_task
    ]
    
    try:
        redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    except Exception:
        redis_settings = RedisSettings()

    on_startup = startup
    on_shutdown = shutdown
