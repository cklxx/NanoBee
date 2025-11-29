from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _reset_settings(temp_dir: Path) -> None:
    os.environ["NANOBEE_DATABASE_URL"] = f"sqlite:///{temp_dir / 'data.db'}"
    os.environ["NANOBEE_WORKSPACES_ROOT"] = str(temp_dir / "workspaces")
    os.environ["NANOBEE_ALLOW_DUMMY_LLM"] = "1"

    db_path = temp_dir / "data.db"
    db_path.touch()
    db_path.chmod(0o666)

    for module_name in [
        "backend.app.db.models",
        "backend.app.db.base",
        "backend.app.db.session",
        "backend.app.config",
        "backend.app.deps",
    ]:
        sys.modules.pop(module_name, None)

    import backend.app.config as config
    config.get_settings.cache_clear()

    import backend.app.db.session as session  # noqa: F401

    import backend.app.db.base as base
    base.Base.metadata.clear()

    import backend.app.db.models as models  # noqa: F401

    import backend.app.deps as deps  # noqa: F401

    import backend.app.api.tasks as tasks_module  # noqa: F401
    importlib.reload(tasks_module)


def test_full_flow_completes_all_features() -> None:
    temp_dir = Path(tempfile.mkdtemp())
    try:
        _reset_settings(temp_dir)
        from backend.app import main

        importlib.reload(main)

        with TestClient(main.app) as client:
            create_resp = client.post("/api/tasks", json={"goal": "demo todo app"})
            create_resp.raise_for_status()
            payload = create_resp.json()
            task_id = payload["id"]
            workspace_id = payload["workspace_id"]

            init_resp = client.post(f"/api/tasks/{task_id}/run/init")
            init_resp.raise_for_status()

            coding_resp = client.post(f"/api/tasks/{task_id}/run/coding/all")
            coding_resp.raise_for_status()
            data = coding_resp.json()

            assert data["status"] == "succeeded"
            assert data["remaining"] == []

            workspace_root = temp_dir / "workspaces" / workspace_id
            feature_list = (workspace_root / "feature_list.json").read_text(encoding="utf-8")
            assert '"status": "passing"' in feature_list
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_orchestrated_flow_runs_end_to_end() -> None:
    temp_dir = Path(tempfile.mkdtemp())
    try:
        _reset_settings(temp_dir)
        from backend.app import main

        importlib.reload(main)

        with TestClient(main.app) as client:
            create_resp = client.post("/api/tasks", json={"goal": "demo todo app"})
            create_resp.raise_for_status()
            payload = create_resp.json()
            task_id = payload["id"]
            workspace_id = payload["workspace_id"]

            resp = client.post(
                f"/api/tasks/{task_id}/run/full",
                params={"max_sessions": 5, "evaluate": True},
            )
            resp.raise_for_status()
            data = resp.json()

            assert data["status"] in {"running", "succeeded"}
            assert data["sessions"], "orchestrator should run coding sessions"
            assert "evaluation" in data, "evaluation summary should be attached when enabled"

            evals_resp = client.get(f"/api/tasks/{task_id}/evals")
            evals_resp.raise_for_status()
            evals_payload = evals_resp.json()
            assert evals_payload["results"], "evaluation records should be persisted"

            workspace_root = temp_dir / "workspaces" / workspace_id
            assert (workspace_root / "init.sh").exists()
            from backend.app.harness.feature_list import load_features

            remaining = [f for f in load_features(workspace_root) if f.status != "passing"]
            assert len(remaining) <= 1
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_evaluation_endpoint_and_memory_surface_events() -> None:
    temp_dir = Path(tempfile.mkdtemp())
    try:
        _reset_settings(temp_dir)
        from backend.app import main

        importlib.reload(main)

        with TestClient(main.app) as client:
            create_resp = client.post("/api/tasks", json={"goal": "demo todo app"})
            create_resp.raise_for_status()
            payload = create_resp.json()
            task_id = payload["id"]

            client.post(f"/api/tasks/{task_id}/run/init").raise_for_status()
            client.post(f"/api/tasks/{task_id}/run/coding/all").raise_for_status()

            eval_resp = client.post(f"/api/tasks/{task_id}/run/eval")
            eval_resp.raise_for_status()
            eval_payload = eval_resp.json()["evaluation"]

            assert eval_payload["score"]
            assert "details" in eval_payload

            list_resp = client.get(f"/api/tasks/{task_id}/evals")
            list_resp.raise_for_status()
            assert list_resp.json()["results"]

            memory_resp = client.get(f"/api/tasks/{task_id}/memory")
            memory_resp.raise_for_status()
            memory_payload = memory_resp.json()
            assert memory_payload["summaries"], "memory summaries should exist after compaction"
            assert isinstance(memory_payload["buffer"], list)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
