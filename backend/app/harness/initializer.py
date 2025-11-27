from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

from ..llm.base import LLMClient
from .feature_list import Feature, default_features, save_features
from .git_tools import git_init_and_first_commit
from .models import InitializerResult, TaskSpec, WorkspaceConfig
from .progress_log import append_progress_entry
from .workspace import ensure_workspace
from .prompts import INITIALIZER_SYSTEM_PROMPT, INITIALIZER_USER_PROMPT_TEMPLATE


def _default_files(goal: str) -> Dict[str, str]:
    features = default_features(goal)
    feature_json = json.dumps([f.__dict__ for f in features], indent=2)
    init_script = """#!/usr/bin/env bash
set -e

if [ -f requirements.txt ]; then
  python3 -m pip install -r requirements.txt
fi

echo "Running smoke checks..."
pytest -q || echo "No tests yet."
"""
    app_py = """def add_todo(items: list[str], text: str) -> list[str]:
    return items + [text]


def list_todos(items: list[str]) -> list[str]:
    return items


def toggle_todo(items: list[dict], index: int) -> list[dict]:
    updated = items.copy()
    if 0 <= index < len(updated):
        entry = updated[index].copy()
        entry["done"] = not entry.get("done", False)
        updated[index] = entry
    return updated


if __name__ == "__main__":
    print("Todo helpers ready")
"""
    progress = "Initialized scaffold for: " + goal + "\n"
    return {
        "README.md": f"# Task\n\n{goal}\n\nThis repository was scaffolded by the initializer agent.\n",
        "init.sh": init_script,
        "feature_list.json": feature_json,
        "progress.log": progress,
        "requirements.txt": "pytest==8.2.0\n",
        "src/__init__.py": "",
        "src/app.py": app_py,
        "tests/__init__.py": "",
        "tests/test_helpers.py": """from src.app import add_todo, list_todos, toggle_todo


def test_add_todo():
    assert add_todo([], "task") == ["task"]


def test_list_todos():
    assert list_todos(["a"]) == ["a"]


def test_toggle():
    items = [{"text": "a", "done": False}]
    result = toggle_todo(items, 0)
    assert result[0]["done"] is True
""",
    }


def _extract_files_from_llm(result: Dict) -> Dict[str, str]:
    files = result.get("files")
    if isinstance(files, dict):
        return {k: str(v) for k, v in files.items()}
    return {}


async def run_initializer(
    task: TaskSpec, ws: WorkspaceConfig, llm: LLMClient, memory_store: object | None = None
) -> InitializerResult:
    root = ensure_workspace(ws)

    user_prompt = INITIALIZER_USER_PROMPT_TEMPLATE.format(task_spec=task.goal)
    messages = [
        {"role": "system", "content": INITIALIZER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    result = await llm.chat(messages)
    files = _extract_files_from_llm(result)
    if not files:
        files = _default_files(task.goal)
    else:
        fallback = _default_files(task.goal)
        for required in ["init.sh", "feature_list.json", "progress.log"]:
            if required not in files:
                files[required] = fallback[required]

    written: list[str] = []
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
        with open(target, mode, encoding=None if mode == "wb" else "utf-8") as f:  # type: ignore[arg-type]
            f.write(content)
        written.append(str(target))
    (root / "init.sh").chmod(0o755)

    if not (root / "feature_list.json").exists():
        save_features(root, default_features(task.goal))

    append_progress_entry(root, "Initializer", "Initialized project scaffold and feature list.")
    if memory_store:
        try:
            memory_store.add_event("Initializer created scaffold and feature list.")
        except Exception:
            pass
    git_init_and_first_commit(root)
    return InitializerResult(root=root, files_written=[Path(p).name for p in written])
