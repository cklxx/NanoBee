from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from ..config import get_settings
from ..llm.base import LLMClient
from ..llm.dummy import DummyLLM
from .coder import run_coding_session
from .evaluation import EvalOutcome, evaluate_task_result
from .feature_list import all_features_passing, load_features
from .initializer import run_initializer
from .progress_log import append_progress_entry
from .memory import MemoryStore
from .models import CodingResult, SessionConfig, TaskSpec, WorkspaceConfig
from .workspace import ensure_workspace, is_workspace_initialized


@dataclass
class WorkflowResult:
    root: Path
    initialized: bool
    sessions: List[CodingResult] = field(default_factory=list)
    evaluation: EvalOutcome | None = None


async def run_session(session_type: str, task: TaskSpec, ws: WorkspaceConfig) -> Path:
    llm = DummyLLM()
    if session_type == "initializer":
        result = await run_initializer(task, ws, llm)
        return result.root
    if session_type == "coding":
        session = SessionConfig(task_id=task.id, mode="coding")
        result = await run_coding_session(task, ws, llm, session)
        return result.root
    raise ValueError(f"Unsupported session type: {session_type}")


async def run_full_workflow(
    task: TaskSpec,
    ws: WorkspaceConfig,
    initializer_llm: LLMClient,
    coding_llm: LLMClient,
    memory_store: MemoryStore | None = None,
    max_sessions: int = 5,
    eval_llm: LLMClient | None = None,
) -> WorkflowResult:
    """Run initializer (if needed) then coding sessions until features pass."""

    root = ensure_workspace(ws)
    initialized = False
    if memory_store:
        memory_store.add_event(
            "Orchestrator starting full workflow run (initializer + coding + optional eval)."
        )

    if not is_workspace_initialized(root):
        await run_initializer(task, ws, initializer_llm, memory_store=memory_store)
        initialized = True
        append_progress_entry(
            root,
            "Orchestrator",
            "Completed initializer as part of full workflow orchestration.",
        )
        if memory_store:
            memory_store.add_event("Initializer completed during orchestrated run.")
    else:
        append_progress_entry(
            root,
            "Orchestrator",
            "Workspace already initialized; resuming coding sessions.",
        )
        if memory_store:
            memory_store.add_event("Workspace already initialized; skipping initializer.")

    sessions: list[CodingResult] = []
    for _ in range(max_sessions):
        features = load_features(root)
        remaining = [f for f in features if f.status != "passing"]
        if not remaining:
            break

        target = remaining[0]
        session_cfg = SessionConfig(
            task_id=task.id,
            mode="coding",
            feature_id=target.id,
        )
        append_progress_entry(
            root,
            "Orchestrator",
            f"Dispatching coding session for {target.id}: {target.description}",
        )
        result = await run_coding_session(task, ws, coding_llm, session_cfg, memory_store)
        sessions.append(result)
        if not result.tests_ok:
            append_progress_entry(
                root,
                "Orchestrator",
                f"Coding session for {result.target_feature_id} finished with failing tests; stopping early.",
            )
            break
        append_progress_entry(
            root,
            "Orchestrator",
            f"Coding session for {result.target_feature_id} completed with tests passing.",
        )

    evaluation: EvalOutcome | None = None
    if eval_llm:
        evaluation = await evaluate_task_result(task.id, task.goal, root, eval_llm)
        append_progress_entry(
            root,
            "Orchestrator",
            f"Evaluation finished with score {evaluation.score}.",
        )
        if memory_store:
            memory_store.add_event(
                f"Evaluation agent scored {evaluation.score} with details: {evaluation.details}"
            )

    if memory_store:
        try:
            status_line = "all features passing" if all_features_passing(root) else "some features failing"
            memory_store.add_event(
                f"Workflow concluded with {len(sessions)} coding sessions; {status_line}."
            )
        except Exception:
            pass

    append_progress_entry(
        root,
        "Orchestrator",
        "Full workflow complete; check feature_list.json and progress.log for details.",
    )

    return WorkflowResult(root=root, initialized=initialized, sessions=sessions, evaluation=evaluation)


async def run_demo_task() -> Path:
    goal = "Build a minimal todo webapp with add/view/toggle"
    settings = get_settings()
    workspace_root = Path(settings.workspaces_root) / "demo_todo"
    ws = WorkspaceConfig(id="demo", root_dir=str(workspace_root))
    task = TaskSpec(id="task-demo", user_id="demo", goal=goal, workspace_id=ws.id)

    workflow = await run_full_workflow(
        task,
        ws,
        initializer_llm=DummyLLM(),
        coding_llm=DummyLLM(),
        memory_store=None,
        max_sessions=10,
        eval_llm=None,
    )

    if workflow.sessions:
        return workflow.sessions[-1].root
    return workflow.root


def main() -> None:
    asyncio.run(run_demo_task())


if __name__ == "__main__":
    main()
