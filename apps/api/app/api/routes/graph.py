import uuid
import math
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, RepositoryFile
from app.core.exceptions import NotFoundError
from repolens.graph.postgres_adapter import PostgresGraphAdapter

router = APIRouter(prefix="/repositories", tags=["Architecture Knowledge Graph"])
logger = logging.getLogger("repolens.routes.graph")


@router.get("/{id}/graph", status_code=status.HTTP_200_OK)
async def get_repository_graph(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full lists of nodes and edges formatted for React Flow canvas layouts"""
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

    adapter = PostgresGraphAdapter(db)
    nodes = await adapter.get_nodes(str(id))
    edges = await adapter.get_edges(str(id))

    # Apply spiral auto layout coordinates to nodes
    for idx, node in enumerate(nodes):
        angle = idx * (2.0 * math.pi / max(len(nodes), 1))
        r = 250.0 * math.sqrt(idx + 1)
        node["position"] = {
            "x": round(r * math.cos(angle)),
            "y": round(r * math.sin(angle))
        }
        node["data"] = {
            "label": node["name"],
            "type": node["type"]
        }

    return {
        "nodes": nodes,
        "edges": edges
    }


@router.get("/{id}/nodes", status_code=status.HTTP_200_OK)
async def get_repository_nodes(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List raw graph nodes"""
    res = await get_repository_graph(id, current_user, db)
    return res.get("nodes", [])


@router.get("/{id}/edges", status_code=status.HTTP_200_OK)
async def get_repository_edges(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List raw graph edges"""
    res = await get_repository_graph(id, current_user, db)
    return res.get("edges", [])


@router.get("/{id}/metrics", status_code=status.HTTP_200_OK)
async def get_architecture_metrics(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve coupling, cohesion, cyclomatic complexity, circular imports and dead code blocks"""
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

    adapter = PostgresGraphAdapter(db)
    
    # Resolve files list to pass into generator
    files_query = await db.execute(
        select(RepositoryFile.id).where(RepositoryFile.repository_id == id)
    )
    file_ids = [str(r.id) for r in files_query.scalars().all()]
    
    from repolens.graph.builder import GraphBuilder
    metrics = await GraphBuilder._generate_metrics(adapter, str(id), file_ids)
    return metrics


@router.get("/{id}/dependency-graph", status_code=status.HTTP_200_OK)
async def get_dependency_graph(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get subgraph restricted to imports dependencies"""
    graph = await get_repository_graph(id, current_user, db)
    filtered_edges = [e for e in graph["edges"] if e["type"] == "IMPORTS"]
    return {
        "nodes": graph["nodes"],
        "edges": filtered_edges
    }


@router.get("/{id}/call-graph", status_code=status.HTTP_200_OK)
async def get_call_graph(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get subgraph restricted to function calls"""
    graph = await get_repository_graph(id, current_user, db)
    filtered_edges = [e for e in graph["edges"] if e["type"] == "CALLS"]
    return {
        "nodes": graph["nodes"],
        "edges": filtered_edges
    }


@router.get("/{id}/inheritance-graph", status_code=status.HTTP_200_OK)
async def get_inheritance_graph(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get subgraph restricted to class inheritance lines"""
    graph = await get_repository_graph(id, current_user, db)
    filtered_edges = [e for e in graph["edges"] if e["type"] == "EXTENDS"]
    return {
        "nodes": graph["nodes"],
        "edges": filtered_edges
    }


@router.get("/{id}/architecture/flows", status_code=status.HTTP_200_OK)
async def get_architecture_flows(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trace and construct call flows starting from API routes to controller functions down to DB ORM schemas"""
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

    adapter = PostgresGraphAdapter(db)
    nodes = await adapter.get_nodes(str(id))
    edges = await adapter.get_edges(str(id))

    # Helper maps
    nodes_map = {n["id"]: n for n in nodes}
    
    # Trace Route ➔ Function ➔ Model mappings
    flows = []
    
    # 1. Start from all API nodes
    api_nodes = [n for n in nodes if n["type"] == "api"]
    for api_node in api_nodes:
        flow = {
            "api_node_id": api_node["id"],
            "api_name": api_node["name"],
            "route_path": api_node["metadata"].get("route"),
            "method": api_node["metadata"].get("method"),
            "controller_node_id": None,
            "controller_name": None,
            "database_models": []
        }
        
        # Check edges originating from this api node (e.g. ROUTES_TO)
        controller_edges = [e for e in edges if e["source"] == api_node["id"] and e["type"] == "ROUTES_TO"]
        if controller_edges:
            ctrl_id = controller_edges[0]["target"]
            flow["controller_node_id"] = ctrl_id
            if ctrl_id in nodes_map:
                flow["controller_name"] = nodes_map[ctrl_id]["name"]
                
                # Trace USES edge connections from controller to models
                model_edges = [e for e in edges if e["source"] == ctrl_id and e["type"] == "USES"]
                for me in model_edges:
                    model_id = me["target"]
                    if model_id in nodes_map:
                        flow["database_models"].append({
                            "model_id": model_id,
                            "model_name": nodes_map[model_id]["name"]
                        })
                        
        flows.append(flow)
        
    return flows
