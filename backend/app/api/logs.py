from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import deps
from ..db import models

router = APIRouter(prefix="/api/tasks", tags=["events"])


@router.get("/{task_id}/events")
def list_task_events(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    events = (
        db.query(models.TaskEvent)
        .filter(models.TaskEvent.task_id == task_id)
        .order_by(models.TaskEvent.created_at)
        .all()
    )
    return {
        "events": [
            {
                "id": str(e.id),
                "session_type": e.session_type,
                "agent_role": e.agent_role,
                "event_type": e.event_type,
                "payload": e.payload,
                "created_at": e.created_at,
            }
            for e in events
        ]
    }
