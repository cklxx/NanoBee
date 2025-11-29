from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ..llm.base import LLMClient
from .feature_list import Feature, default_features, features_from_json
from .git_tools import git_init_and_first_commit
from .models import InitializerResult, TaskSpec, WorkspaceConfig
from .progress_log import append_progress_entry
from .shell_tools import run_init_script_and_tests
from .workspace import ensure_workspace
from .prompts import INITIALIZER_SYSTEM_PROMPT, INITIALIZER_USER_PROMPT_TEMPLATE


def _default_files(goal: str) -> Dict[str, str]:
    init_script = """#!/usr/bin/env bash
set -euo pipefail

if [ -f requirements.txt ]; then
  echo "Installing backend dependencies..."
  python3 -m pip install -r requirements.txt
fi

echo "Running smoke checks via pytest..."
python3 -m pytest -q || echo "No tests yet."
"""
    app_py = """from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Fibonacci Service")


@lru_cache(maxsize=256)
def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n in (0, 1):
        return n
    # TODO (current task): switch to an iterative approach if deeper ranges are required
    return fibonacci(n - 1) + fibonacci(n - 2)


class FibonacciResponse(BaseModel):
    n: int
    value: int
    cached: bool


@app.get("/fib/{n}", response_model=FibonacciResponse)
def get_fibonacci(n: int):
    if n > 100:
        raise HTTPException(status_code=400, detail="n must be <= 100")
    info_before = fibonacci.cache_info()
    try:
        value = fibonacci(n)
    except ValueError as exc:  # pragma: no cover - defensive guardrail
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    info_after = fibonacci.cache_info()
    cached = info_after.hits > info_before.hits
    return {"n": n, "value": value, "cached": cached}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    progress = (
        "Initialized scaffold for: "
        + goal
        + "\nTODO (current task): add cache metrics and persistence once infra is available.\n"
    )
    readme = """# Task

{goal}

## Current TODOs (this task)
- [ ] Expose GET /fib/{{n}} returning the nth Fibonacci number
- [ ] Validate inputs and return clear 400 responses
- [ ] Cache Fibonacci calculations and report cache hits/misses

## Quickstart
- Run ./init.sh to install dependencies and execute tests

## Notes
- This scaffold was created automatically; keep TODOs aligned with the task, not agent internals.
""".format(goal=goal)
    return {
        "README.md": readme,
        "init.sh": init_script,
        "progress.log": progress,
        "requirements.txt": "fastapi==0.115.5\nuvicorn==0.32.1\nhttpx==0.27.2\npytest==8.2.0\n",
        "src/__init__.py": "",
        "src/app.py": app_py,
        "tests/__init__.py": "",
        "tests/test_fibonacci.py": """from fastapi.testclient import TestClient

from src.app import app, fibonacci


def test_fibonacci_base_cases():
    assert fibonacci.cache_clear() is None
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1


def test_fibonacci_positive_case():
    fibonacci.cache_clear()
    assert fibonacci(7) == 13


def test_fibonacci_caching_hits_on_repeat():
    fibonacci.cache_clear()
    fibonacci(10)
    stats_before = fibonacci.cache_info().hits
    fibonacci(10)
    stats_after = fibonacci.cache_info().hits
    assert stats_after > stats_before


def test_fibonacci_endpoint_happy_path():
    fibonacci.cache_clear()
    client = TestClient(app)
    response = client.get("/fib/8")
    assert response.status_code == 200
    payload = response.json()
    assert payload["n"] == 8
    assert payload["value"] == 21
    assert payload["cached"] in (True, False)


def test_fibonacci_endpoint_rejects_invalid_input():
    client = TestClient(app)
    response = client.get("/fib/-2")
    assert response.status_code == 400
    assert "non-negative" in response.json()["detail"]


def test_fibonacci_endpoint_rejects_large_input():
    client = TestClient(app)
    response = client.get("/fib/200")
    assert response.status_code == 400
    assert "<= 100" in response.json()["detail"]
""",
    }


def _extract_files_from_llm(result: Dict) -> Dict[str, str]:
    files = result.get("files")
    if isinstance(files, dict):
        return {k: str(v) for k, v in files.items()}
    return {}


def _strip_json_fences(text: str) -> str:
    if text.strip().startswith("```"):
        try:
            return text.strip().split("```", 2)[1]
        except IndexError:
            return text
    return text


async def _synthesize_features(goal: str, llm: LLMClient) -> List[Feature]:
    messages = [
        {
            "role": "system",
            "content": "You generate feature_list.json entries as pure JSON.",
        },
        {
            "role": "user",
            "content": (
                "Given the task goal, produce an array of feature objects for feature_list.json.\n"
                "Fields: id, description, status, notes. All status values must be 'failing'.\n"
                "Task goal: "
                + goal
            ),
        },
    ]

    try:
        resp = await llm.chat(messages)
    except Exception:
        return []

    content = resp.get("content") if isinstance(resp, dict) else None
    if isinstance(content, str):
        try:
            return features_from_json(_strip_json_fences(content))
        except Exception:
            return []
    return []


def _features_from_result_payload(result: Dict[str, Any]) -> List[Feature]:
    candidates: list[str] = []
    for key in ("content", "text", "message"):
        val = result.get(key)
        if isinstance(val, str):
            candidates.append(val)

    for text in candidates:
        try:
            return features_from_json(_strip_json_fences(text))
        except Exception:
            continue
    return []


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

    fallback = _default_files(task.goal)
    for required in ["init.sh", "progress.log", "README.md", "requirements.txt", "src/app.py", "tests/test_fibonacci.py"]:
        if required not in files:
            files[required] = fallback[required]

    feature_candidates: List[Feature] = []
    feature_source = ""
    if "feature_list.json" in files:
        try:
            feature_candidates = features_from_json(files["feature_list.json"])
            feature_source = "llm-provided feature_list.json"
        except Exception:
            feature_candidates = []

    if not feature_candidates:
        feature_candidates = _features_from_result_payload(result)
        if feature_candidates:
            feature_source = "llm payload (content/text/message)"

    if not feature_candidates:
        feature_candidates = await _synthesize_features(task.goal, llm)
        if feature_candidates:
            feature_source = "synthesized via feature prompt"

    if not feature_candidates:
        feature_candidates = default_features(task.goal)
        feature_source = "static fallback defaults"

    files["feature_list.json"] = json.dumps([f.__dict__ for f in feature_candidates], indent=2)

    written: list[str] = []
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "wb" if isinstance(content, (bytes, bytearray)) else "w"
        with open(target, mode, encoding=None if mode == "wb" else "utf-8") as f:  # type: ignore[arg-type]
            f.write(content)
        written.append(str(target))
    (root / "init.sh").chmod(0o755)

    feature_source_note = feature_source or "unspecified feature source"
    append_progress_entry(
        root,
        "Initializer",
        f"Initialized project scaffold and feature list (source: {feature_source_note}; count: {len(feature_candidates)}).",
    )
    tests_ok, test_output = run_init_script_and_tests(root)
    status_line = "Environment initialized and smoke checks passed." if tests_ok else "Environment setup encountered test failures."
    append_progress_entry(
        root,
        "Initializer",
        f"Ran ./init.sh to warm the environment. {status_line}\n{test_output}",
    )
    if memory_store:
        try:
            memory_store.add_event("Initializer created scaffold and feature list.")
        except Exception:
            pass
    git_init_and_first_commit(root)
    return InitializerResult(root=root, files_written=[Path(p).name for p in written])
