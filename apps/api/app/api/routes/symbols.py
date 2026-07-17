import uuid
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import (
    User, 
    Repository, 
    RepositoryFile, 
    Symbol, 
    Class, 
    Function, 
    Dependency, 
    API, 
    DatabaseModel
)
from app.core.exceptions import NotFoundError

router = APIRouter(tags=["Symbols & Analysis Details"])
logger = logging.getLogger("repolens.routes.symbols")


@router.get("/repositories/{id}/symbols", status_code=status.HTTP_200_OK)
async def get_repository_symbols(
    id: uuid.UUID,
    kind: str | None = Query(None, description="Filter symbols by kind [class, function, variable, interface]"),
    search: str | None = Query(None, description="Keyword search symbol name"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List code symbols scanned in a repository"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Fetch symbols with files
    query = (
        select(Symbol, RepositoryFile.path)
        .join(RepositoryFile, Symbol.file_id == RepositoryFile.id)
        .where(RepositoryFile.repository_id == id)
    )

    if kind:
        query = query.where(Symbol.kind == kind)
    if search:
        query = query.where(Symbol.name.ilike(f"%{search}%"))

    result = await db.execute(query)
    symbols = result.all()

    return [
        {
            "id": str(sym.Symbol.id),
            "file_id": str(sym.Symbol.file_id),
            "file_path": sym.path,
            "name": sym.Symbol.name,
            "kind": sym.Symbol.kind,
            "line_start": sym.Symbol.line_start,
            "line_end": sym.Symbol.line_end,
            "docstring": sym.Symbol.docstring
        } for sym in symbols
    ]


@router.get("/symbols/{id}", status_code=status.HTTP_200_OK)
async def get_symbol_details(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed inheritance lists or functional parameters of a specific code symbol"""
    # Fetch symbol and verify repository ownership
    query = (
        select(Symbol, RepositoryFile.path)
        .join(RepositoryFile, Symbol.file_id == RepositoryFile.id)
        .join(Repository, RepositoryFile.repository_id == Repository.id)
        .where(
            Symbol.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    res = await db.execute(query)
    sym_row = res.first()
    if not sym_row:
        raise NotFoundError("Symbol")

    sym = sym_row.Symbol
    file_path = sym_row.path

    # Gather additional class or function definitions
    class_info = None
    func_info = None

    if sym.kind == "class":
        cls_query = await db.execute(select(Class).where(Class.symbol_id == id))
        cls_record = cls_query.scalar_one_or_none()
        if cls_record:
            class_info = {"inheritance": cls_record.inheritance_list}
            
    elif sym.kind == "function":
        fn_query = await db.execute(select(Function).where(Function.symbol_id == id))
        fn_record = fn_query.scalar_one_or_none()
        if fn_record:
            func_info = {
                "parameters": fn_record.parameters,
                "return_type": fn_record.return_type,
                "decorators": fn_record.decorator_list
            }

    return {
        "id": str(sym.id),
        "file_path": file_path,
        "name": sym.name,
        "kind": sym.kind,
        "line_start": sym.line_start,
        "line_end": sym.line_end,
        "docstring": sym.docstring,
        "code_snippet": sym.code_snippet,
        "class_details": class_info,
        "function_details": func_info
    }


@router.get("/repositories/{id}/dependencies", status_code=status.HTTP_200_OK)
async def get_repository_dependencies(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve external package references and internal file import maps"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Fetch file dependency links
    query = (
        select(Dependency, RepositoryFile.path, sa_alias := sa_type.alias(sa_name := "target_rf").path)
        .join(RepositoryFile, Dependency.file_id == RepositoryFile.id)
        .join(__import__("sqlalchemy").aliased(RepositoryFile, name="target_rf"), Dependency.target_file_id == text("target_rf.id"))
        .where(RepositoryFile.repository_id == id)
    )
    # To keep simple and clean without alias complex triggers
    simple_query = sa_sel := select(Dependency).where(
        Dependency.file_id.in_(
            select(RepositoryFile.id).where(RepositoryFile.repository_id == id)
        )
    )
    result = await db.execute(simple_query)
    deps = result.scalars().all()

    # Build path mappings
    files_query = await db.execute(
        select(RepositoryFile.id, RepositoryFile.path).where(RepositoryFile.repository_id == id)
    )
    paths_map = {str(row.id): row.path for row in files_query.all()}

    return [
        {
            "id": str(d.id),
            "file_id": str(d.file_id),
            "file_path": paths_map.get(str(d.file_id)),
            "target_file_id": str(d.target_file_id),
            "target_file_path": paths_map.get(str(d.target_file_id)),
            "type": d.dependency_type
        } for d in deps if str(d.file_id) in paths_map and str(d.target_file_id) in paths_map
    ]


@router.get("/repositories/{id}/apis", status_code=status.HTTP_200_OK)
async def get_repository_apis(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve REST endpoints detected structurally in code files"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    query = (
        select(API, RepositoryFile.path)
        .join(RepositoryFile, API.file_id == RepositoryFile.id)
        .where(API.repository_id == id)
    )
    result = await db.execute(query)
    apis = result.all()

    return [
        {
            "id": str(row.API.id),
            "route": row.API.route,
            "method": row.API.method,
            "parameters": row.API.parameters,
            "controller_func": row.API.controller_func,
            "file_path": row.path
        } for row in apis
    ]


@router.get("/repositories/{id}/models", status_code=status.HTTP_200_OK)
async def get_repository_database_models(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve ORM database structures parsed inside code files"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    query = (
        select(DatabaseModel, RepositoryFile.path)
        .join(RepositoryFile, DatabaseModel.file_id == RepositoryFile.id)
        .where(DatabaseModel.repository_id == id)
    )
    result = await db.execute(query)
    models = result.all()

    return [
        {
            "id": str(row.DatabaseModel.id),
            "model_name": row.DatabaseModel.model_name,
            "fields": row.DatabaseModel.fields_json,
            "relationships": row.DatabaseModel.relationships_json,
            "file_path": row.path
        } for row in models
    ]
