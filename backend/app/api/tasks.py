from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import deps
from ..config import get_settings
from ..db import base as db_base
from ..db import models
from ..harness.models import CodingResult, InitializerResult, SessionConfig, TaskSpec, WorkspaceConfig
from ..harness.runner import run_coding_session, run_full_workflow, run_initializer
from ..harness.evaluation import EvalOutcome, evaluate_task_result, persist_eval_result
from ..harness.feature_list import all_features_passing, load_features
from ..harness.memory import MemoryStore
from ..harness.progress_log import read_progress_log
from ..harness.workspace import ensure_workspace
from ..llm.base import LLMClient

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskRequest(BaseModel):
    goal: str
    user_id: str | None = None
    task_id: str | None = None


def _record_event(
    db: Session,
    task_id: str,
    session_type: str,
    event_type: str,
    agent_role: str = "system",
    payload: dict | None = None,
) -> None:
    event = models.TaskEvent(
        task_id=task_id,
        session_type=session_type,
        agent_role=agent_role,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    db.commit()


def _truncate(text: str, limit: int = 500) -> str:
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


class InstrumentedLLM(LLMClient):
    """Wraps an LLM client to emit timeline events for requests/responses."""

    def __init__(
        self,
        inner: LLMClient,
        on_start: Callable[[list[dict[str, Any]]], None] | None = None,
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.inner = inner
        self.on_start = on_start
        self.on_success = on_success
        self.on_error = on_error

    async def chat(self, messages: list[dict[str, Any]], tools: list | None = None) -> dict:
        if self.on_start:
            try:
                self.on_start(messages)
            except Exception:
                pass
        try:
            resp = await self.inner.chat(messages, tools=tools)
            if self.on_success:
                try:
                    self.on_success(resp)
                except Exception:
                    pass
            return resp
        except Exception as exc:  # pragma: no cover - observational only
            if self.on_error:
                try:
                    self.on_error(exc)
                except Exception:
                    pass
            raise


def _instrument_llm(
    base_llm: LLMClient,
    db: Session,
    task_id: str,
    session_type: str,
    agent_role: str,
    context: dict | None = None,
) -> LLMClient:
    context = context or {}

    def _payload(extra: dict) -> dict:
        merged = dict(context)
        merged.update(extra)
        return merged

    return InstrumentedLLM(
        base_llm,
        on_start=lambda messages: _record_event(
            db,
            task_id,
            session_type,
            "llm_request",
            agent_role=agent_role,
            payload=_payload(
                {"prompt_preview": _truncate(str(messages[-1].get("content", ""))) if messages else ""}
            ),
        ),
        on_success=lambda resp: _record_event(
            db,
            task_id,
            session_type,
            "llm_response",
            agent_role=agent_role,
            payload=_payload(
                {"content_preview": _truncate(str(resp.get("content", ""))) if isinstance(resp, dict) else ""}
            ),
        ),
        on_error=lambda exc: _record_event(
            db,
            task_id,
            session_type,
            "llm_error",
            agent_role=agent_role,
            payload=_payload({"error": str(exc)}),
        ),
    )


@router.post("", response_model=dict)
async def create_task(body: CreateTaskRequest, db: Session = Depends(deps.get_db)):
    # Ensure tables exist for freshly initialized test/demo environments.
    db_base.Base.metadata.create_all(bind=db.get_bind())

    settings = get_settings()
    workspace_id = body.task_id or f"task-{int(datetime.now(timezone.utc).timestamp())}"
    workspace_root = settings.workspaces_root / workspace_id

    ensure_workspace(WorkspaceConfig(id=workspace_id, root_dir=str(workspace_root)))
    workspace = models.Workspace(id=workspace_id, root_dir=str(workspace_root))
    db.add(workspace)

    task = models.Task(
        id=body.task_id or workspace_id,
        user_id=body.user_id,
        goal=body.goal,
        workspace_id=workspace.id,
        status="pending",
    )
    db.add(task)
    db.commit()

    return {"id": task.id, "workspace_id": workspace.id}


@router.get("")
def list_tasks(db: Session = Depends(deps.get_db)) -> list[dict]:
    tasks = db.query(models.Task).all()
    return [
        {
            "id": t.id,
            "goal": t.goal,
            "status": t.status,
            "workspace_id": t.workspace_id,
            "created_at": t.created_at,
        }
        for t in tasks
    ]


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "goal": task.goal,
        "status": task.status,
        "workspace_id": task.workspace_id,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


@router.post("/{task_id}/run/init")
async def run_init_session(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=400, detail="Workspace missing")

    ensure_workspace(WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir))
    base_llm = deps.get_llm_client()
    memory_store = MemoryStore(db, task.id, llm=base_llm)
    _record_event(db, task.id, "initializer", "start", agent_role="Initializer")
    llm = _instrument_llm(base_llm, db, task.id, "initializer", "Initializer")
    try:
        result: InitializerResult = await run_initializer(
            TaskSpec(id=task.id, user_id=task.user_id or "", goal=task.goal, workspace_id=task.workspace_id),
            WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir),
            llm,
            memory_store=memory_store,
        )
    except Exception as exc:
        _record_event(
            db,
            task.id,
            "initializer",
            "error",
            agent_role="Initializer",
            payload={"error": str(exc)},
        )
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")
    task.status = "running"
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    memory_store.add_event("Initializer finished writing scaffold and feature list.")
    _record_event(
        db,
        task.id,
        "initializer",
        "finished",
        agent_role="Initializer",
        payload={"files_written": result.files_written},
    )
    return {"status": "initialized", "files": result.files_written}


@router.post("/{task_id}/run/coding")
async def run_coding(task_id: str, feature_id: str | None = None, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=400, detail="Workspace missing")

    llm = deps.get_llm_client()
    ws_cfg = WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir)
    ensure_workspace(ws_cfg)
    memory_store = MemoryStore(db, task.id, llm=llm)
    result, status = await _execute_coding_session(
        db,
        task,
        workspace,
        llm,
        SessionConfig(task_id=task.id, mode="coding", feature_id=feature_id),
        memory_store,
    )
    return {
        "status": status,
        "feature_id": result.target_feature_id,
        "tests_ok": result.tests_ok,
        "output": result.test_output,
    }


@router.post("/{task_id}/run/coding/all")
async def run_coding_until_done(
    task_id: str, max_sessions: int = 5, db: Session = Depends(deps.get_db)
) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=400, detail="Workspace missing")

    llm = deps.get_llm_client()
    ws_cfg = WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir)
    ensure_workspace(ws_cfg)

    sessions: list[dict] = []
    final_status = task.status
    memory_store = MemoryStore(db, task.id, llm=llm)
    for _ in range(max_sessions):
        features = load_features(Path(workspace.root_dir))
        failing = [f for f in features if f.status != "passing"]
        if not failing:
            break

        result, final_status = await _execute_coding_session(
            db,
            task,
            workspace,
            llm,
            SessionConfig(task_id=task.id, mode="coding", feature_id=failing[0].id),
            memory_store,
        )
        sessions.append(
            {
                "feature_id": result.target_feature_id,
                "tests_ok": result.tests_ok,
                "output": result.test_output,
                "feature_status": result.feature_status,
            }
        )
        if not result.tests_ok:
            break

    remaining = [f.id for f in load_features(Path(workspace.root_dir)) if f.status != "passing"]
    return {"status": final_status, "sessions": sessions, "remaining": remaining}


@router.post("/{task_id}/run/full")
async def run_full_workflow_endpoint(
    task_id: str,
    max_sessions: int = 5,
    evaluate: bool = True,
    db: Session = Depends(deps.get_db),
) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=400, detail="Workspace missing")

    ws_cfg = WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir)
    ensure_workspace(ws_cfg)

    base_llm = deps.get_llm_client()
    memory_store = MemoryStore(db, task.id, llm=base_llm)

    _record_event(
        db,
        task.id,
        "orchestrator",
        "start",
        agent_role="Orchestrator",
        payload={"max_sessions": max_sessions, "evaluate": evaluate},
    )

    initializer_llm = _instrument_llm(base_llm, db, task.id, "initializer", "Initializer")
    coding_llm = _instrument_llm(base_llm, db, task.id, "coding", "CodingAgent")
    eval_llm = _instrument_llm(base_llm, db, task.id, "eval", "EvalAgent") if evaluate else None

    workflow = await run_full_workflow(
        TaskSpec(id=task.id, user_id=task.user_id or "", goal=task.goal, workspace_id=task.workspace_id),
        ws_cfg,
        initializer_llm,
        coding_llm,
        memory_store=memory_store,
        max_sessions=max_sessions,
        eval_llm=eval_llm,
    )

    task.status = "succeeded" if all_features_passing(Path(workspace.root_dir)) else "running"
    task.updated_at = datetime.now(timezone.utc)
    db.commit()

    response = {
        "status": task.status,
        "initialized": workflow.initialized,
        "sessions": [
            {
                "feature_id": s.target_feature_id,
                "tests_ok": s.tests_ok,
                "feature_status": s.feature_status,
                "output": s.test_output,
            }
            for s in workflow.sessions
        ],
        "remaining": [
            f.id for f in load_features(Path(workspace.root_dir)) if f.status != "passing"
        ],
    }

    if workflow.evaluation:
        record = persist_eval_result(db, task.id, workflow.evaluation)
        response["evaluation"] = {
            "id": record.id,
            "score": workflow.evaluation.score,
            "details": workflow.evaluation.details,
            "created_at": record.created_at.isoformat(),
        }
        memory_store.add_event(
            f"EvalAgent scored task at {workflow.evaluation.score} during orchestrated run."
        )
        _record_event(
            db,
            task.id,
            "eval",
            "finished",
            agent_role="EvalAgent",
            payload=response["evaluation"],
        )

    _record_event(
        db,
        task.id,
        "orchestrator",
        "finished",
        agent_role="Orchestrator",
        payload={
            "status": task.status,
            "sessions_ran": len(workflow.sessions),
            "initialized": workflow.initialized,
        },
    )

    return response


@router.post("/{task_id}/run/eval")
async def run_eval(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=400, detail="Workspace missing")

    base_llm = deps.get_llm_client()
    eval_llm = _instrument_llm(base_llm, db, task.id, "eval", "EvalAgent")
    memory_store = MemoryStore(db, task.id, llm=base_llm)

    _record_event(db, task.id, "eval", "start", agent_role="EvalAgent")

    outcome: EvalOutcome = await evaluate_task_result(
        task.id, task.goal, Path(workspace.root_dir), eval_llm
    )
    record = persist_eval_result(db, task.id, outcome)
    memory_store.add_event(f"EvalAgent scored task at {outcome.score} with notes: {outcome.details}")

    _record_event(
        db,
        task.id,
        "eval",
        "finished",
        agent_role="EvalAgent",
        payload={"score": outcome.score, "details": outcome.details},
    )

    return {"evaluation": {"id": record.id, "score": outcome.score, "details": outcome.details}}


async def _execute_coding_session(
    db: Session,
    task: models.Task,
    workspace: models.Workspace,
    llm: LLMClient,
    session_config: SessionConfig,
    memory_store: MemoryStore,
) -> tuple[CodingResult, str]:
    _record_event(
        db,
        task.id,
        "coding",
        "start",
        agent_role="CodingAgent",
        payload={"feature_id": session_config.feature_id},
    )
    logging_llm = _instrument_llm(
        llm,
        db,
        task.id,
        "coding",
        "CodingAgent",
        context={"feature_id": session_config.feature_id},
    )
    try:
        result: CodingResult = await run_coding_session(
            TaskSpec(id=task.id, user_id=task.user_id or "", goal=task.goal, workspace_id=task.workspace_id),
            WorkspaceConfig(id=workspace.id, root_dir=workspace.root_dir),
            logging_llm,
            session_config,
            memory_store,
        )
    except Exception as exc:
        _record_event(
            db,
            task.id,
            "coding",
            "error",
            agent_role="CodingAgent",
            payload={"feature_id": session_config.feature_id, "error": str(exc)},
        )
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")
    task.status = "succeeded" if result.tests_ok and all_features_passing(Path(workspace.root_dir)) else "running"
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    _record_event(
        db,
        task.id,
        "coding",
        "tests",
        agent_role="CodingAgent",
        payload={
            "feature_id": result.target_feature_id,
            "tests_ok": result.tests_ok,
            "output": result.test_output,
            "feature_status": result.feature_status,
        },
    )
    memory_store.add_event(
        f"Coding session for {result.target_feature_id} concluded with tests {'passing' if result.tests_ok else 'failing'}"
    )
    return result, task.status


@router.get("/{task_id}/features")
def get_features(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    features = load_features(Path(workspace.root_dir))
    return {"features": [f.__dict__ for f in features]}


@router.get("/{task_id}/memory")
def get_memory(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Workspace is not strictly required to inspect memory, but ensure the task exists.
    memory_store = MemoryStore(db, task.id)
    return {"buffer": memory_store.buffer_events(), "summaries": memory_store.summaries()}


@router.get("/{task_id}/progress")
def get_progress(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    log = read_progress_log(Path(workspace.root_dir))
    return {"progress": log}


@router.get("/{task_id}/evals")
def list_evaluations(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    results = (
        db.query(models.EvalResult)
        .filter(models.EvalResult.task_id == task_id)
        .order_by(models.EvalResult.created_at.desc())
        .all()
    )
    return {
        "results": [
            {"id": r.id, "score": r.score, "details": r.details, "created_at": r.created_at}
            for r in results
        ]
    }


@router.post("/{task_id}/evaluate")
async def evaluate_task(task_id: str, db: Session = Depends(deps.get_db)) -> dict:
    task = db.get(models.Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    workspace = db.get(models.Workspace, task.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    base_llm = deps.get_llm_client()
    workspace_root = Path(workspace.root_dir)
    _record_event(db, task.id, "eval", "start", agent_role="EvalAgent")
    llm = _instrument_llm(base_llm, db, task.id, "eval", "EvalAgent")
    outcome: EvalOutcome = await evaluate_task_result(task.id, task.goal, workspace_root, llm)
    result = persist_eval_result(db, task.id, outcome)
    _record_event(
        db,
        task.id,
        "eval",
        "finished",
        agent_role="EvalAgent",
        payload={"score": result.score, "details": result.details},
    )
    return {"score": result.score, "details": result.details}
