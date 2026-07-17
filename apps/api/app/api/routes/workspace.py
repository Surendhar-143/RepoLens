import uuid
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, status, Query, Body, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, WorkspaceState, Annotation, Bookmark
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/workspace", tags=["Workspace & Collaboration"])
logger = logging.getLogger("repolens.routes.workspace")


@router.get("/{repository_id}", status_code=status.HTTP_200_OK)
async def get_workspace_state(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve saved workspace state or initialize a default state"""
    # Verify owner
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == current_user.id
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    query = select(WorkspaceState).where(
        WorkspaceState.repository_id == repository_id,
        WorkspaceState.user_id == current_user.id
    )
    res = await db.execute(query)
    state = res.scalar_one_or_none()

    if not state:
        state = WorkspaceState(
            repository_id=repository_id,
            user_id=current_user.id,
            active_layout="spiral",
            zoom=1.0,
            pan_x=0.0,
            pan_y=0.0,
            active_filters_json={}
        )
        db.add(state)
        await db.commit()
        await db.refresh(state)

    return {
        "active_layout": state.active_layout,
        "zoom": state.zoom,
        "pan_x": state.pan_x,
        "pan_y": state.pan_y,
        "active_filters": state.active_filters_json
    }


@router.patch("/{repository_id}", status_code=status.HTTP_200_OK)
async def update_workspace_state(
    repository_id: uuid.UUID,
    active_layout: Optional[str] = Body(None),
    zoom: Optional[float] = Body(None),
    pan_x: Optional[float] = Body(None),
    pan_y: Optional[float] = Body(None),
    active_filters: Optional[dict] = Body(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current layout and viewport settings for a workspace"""
    query = select(WorkspaceState).where(
        WorkspaceState.repository_id == repository_id,
        WorkspaceState.user_id == current_user.id
    )
    res = await db.execute(query)
    state = res.scalar_one_or_none()

    if not state:
        raise NotFoundError("WorkspaceState")

    if active_layout is not None:
        state.active_layout = active_layout
    if zoom is not None:
        state.zoom = zoom
    if pan_x is not None:
        state.pan_x = pan_x
    if pan_y is not None:
        state.pan_y = pan_y
    if active_filters is not None:
        state.active_filters_json = active_filters

    await db.commit()
    return {"success": True}


# ANNOTATIONS CRUD ENDPOINTS
@router.get("/annotations/list", status_code=status.HTTP_200_OK)
async def list_annotations(
    repository_id: uuid.UUID = Query(...),
    note_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List codebase code bookmarks or nodes annotations comments"""
    query = select(Annotation).where(
        Annotation.repository_id == repository_id,
        Annotation.user_id == current_user.id
    )
    if note_type:
        query = query.where(Annotation.note_type == note_type)
        
    res = await db.execute(query.order_by(Annotation.created_at.desc()))
    annotations = []
    for ann in res.scalars().all():
        annotations.append({
            "id": str(ann.id),
            "target_id": ann.target_id,
            "note_type": ann.note_type,
            "content": ann.content,
            "created_at": ann.created_at
        })
    return annotations


@router.post("/annotations", status_code=status.HTTP_201_CREATED)
async def create_annotation(
    repository_id: uuid.UUID = Body(...),
    target_id: str = Body(...),
    note_type: str = Body(...),
    content: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pin a note comment to a file, symbol or graph node"""
    annotation = Annotation(
        repository_id=repository_id,
        user_id=current_user.id,
        target_id=target_id,
        note_type=note_type,
        content=content
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    return {"id": str(annotation.id), "success": True}


@router.delete("/annotations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a saved annotation"""
    query = select(Annotation).where(
        Annotation.id == id,
        Annotation.user_id == current_user.id
    )
    res = await db.execute(query)
    annotation = res.scalar_one_or_none()
    if not annotation:
        raise NotFoundError("Annotation")

    await db.execute(delete(Annotation).where(Annotation.id == id))
    await db.commit()


# BOOKMARKS CRUD ENDPOINTS
@router.get("/bookmarks/list", status_code=status.HTTP_200_OK)
async def list_bookmarks(
    repository_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List bookmarked saved graph layout views"""
    query = select(Bookmark).where(
        Bookmark.repository_id == repository_id,
        Bookmark.user_id == current_user.id
    )
    res = await db.execute(query.order_by(Bookmark.created_at.desc()))
    bookmarks = []
    for bm in res.scalars().all():
        bookmarks.append({
            "id": str(bm.id),
            "name": bm.name,
            "view_state": bm.view_state_json,
            "created_at": bm.created_at
        })
    return bookmarks


@router.post("/bookmarks", status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    repository_id: uuid.UUID = Body(...),
    name: str = Body(...),
    view_state: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save active zoom level, layout coordinates, and filters as a bookmark"""
    bookmark = Bookmark(
        repository_id=repository_id,
        user_id=current_user.id,
        name=name,
        view_state_json=view_state
    )
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    return {"id": str(bookmark.id), "success": True}


@router.delete("/bookmarks/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a saved bookmark view"""
    query = select(Bookmark).where(
        Bookmark.id == id,
        Bookmark.user_id == current_user.id
    )
    res = await db.execute(query)
    bookmark = res.scalar_one_or_none()
    if not bookmark:
        raise NotFoundError("Bookmark")

    await db.execute(delete(Bookmark).where(Bookmark.id == id))
    await db.commit()


# EXPORT EXPORTER ENDPOINT
@router.post("/export", status_code=status.HTTP_200_OK)
async def export_workspace_graph(
    format: str = Body(...), # dot, graphml, json
    nodes: List[Dict[str, Any]] = Body(...),
    edges: List[Dict[str, Any]] = Body(...)
):
    """Compile active canvas nodes and connections list into DOT or GraphML structural files"""
    if format == "dot":
        dot_str = "digraph CodebaseGraph {\n"
        dot_str += "  node [shape=box, style=filled, color=lightgrey];\n"
        for node in nodes:
            dot_str += f'  "{node["id"]}" [label="{node.get("label", node["id"])}"];\n'
        for edge in edges:
            dot_str += f'  "{edge["source"]}" -> "{edge["target"]}" [label="{edge.get("label", "")}"];\n'
        dot_str += "}\n"
        return Response(content=dot_str, media_type="text/vnd.graphviz", headers={"Content-Disposition": "attachment; filename=graph.dot"})

    elif format == "graphml":
        gml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n'
            '  <graph id="G" edgedefault="directed">\n'
        )
        for node in nodes:
            gml += f'    <node id="{node["id"]}"/>\n'
        for edge in edges:
            gml += f'    <edge source="{edge["source"]}" target="{edge["target"]}"/>\n'
        gml += '  </graph>\n</graphml>'
        return Response(content=gml, media_type="application/xml", headers={"Content-Disposition": "attachment; filename=graph.graphml"})

    # Default to json
    json_bytes = json.dumps({"nodes": nodes, "edges": edges}, indent=2)
    return Response(content=json_bytes, media_type="application/json", headers={"Content-Disposition": "attachment; filename=graph.json"})
