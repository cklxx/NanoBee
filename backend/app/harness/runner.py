from __future__ import annotations

import asyncio
from pathlib import Path

from ..config import get_settings
from ..llm.dummy import DummyLLM
from .coder import run_coding_session
from .feature_list import load_features
from .initializer import run_initializer
from .models import SessionConfig, TaskSpec, WorkspaceConfig


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


async def run_demo_task() -> Path:
    goal = "Build a minimal todo webapp with add/view/toggle"
    settings = get_settings()
    workspace_root = Path(settings.workspaces_root) / "demo_todo"
    ws = WorkspaceConfig(id="demo", root_dir=str(workspace_root))
    task = TaskSpec(id="task-demo", user_id="demo", goal=goal, workspace_id=ws.id)

    init_result = await run_initializer(task, ws, DummyLLM())

    # Iterate through all failing features so the demo leaves a green state.
    latest_root = init_result.root
    for _ in range(10):
        failing = [f for f in load_features(Path(ws.root_dir)) if f.status != "passing"]
        if not failing:
            break
        coding_result = await run_coding_session(
            task,
            ws,
            DummyLLM(),
            SessionConfig(task_id=task.id, mode="coding", feature_id=failing[0].id),
        )
        latest_root = coding_result.root or latest_root
        if not coding_result.tests_ok:
            break
    return latest_root


def main() -> None:
    asyncio.run(run_demo_task())


if __name__ == "__main__":
    main()
