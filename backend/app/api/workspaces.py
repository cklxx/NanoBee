from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import deps
from ..db import models
from ..harness.models import WorkspaceConfig
from ..harness.workspace import list_workspace_files, read_file

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("/{workspace_id}/files")
def list_files(workspace_id: str, db: Session = Depends(deps.get_db)) -> dict:
    workspace = db.get(models.Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    ws_cfg = WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir)
    return {"files": list_workspace_files(ws_cfg)}


@router.get("/{workspace_id}/files/{path:path}")
def read_workspace_file(workspace_id: str, path: str, db: Session = Depends(deps.get_db)) -> dict:
    workspace = db.get(models.Workspace, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    ws_cfg = WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir)
    return {"path": path, "content": read_file(ws_cfg, path)}
