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

    import backend.app.config as config

    config.get_settings.cache_clear()
    importlib.reload(config)

    import backend.app.db.session as session
    importlib.reload(session)

    import backend.app.db.base as base
    base.Base.metadata.clear()
    importlib.reload(base)

    import backend.app.db.models  # noqa: F401


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
