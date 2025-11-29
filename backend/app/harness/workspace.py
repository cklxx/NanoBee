from __future__ import annotations

import os
from pathlib import Path
from typing import List

from .models import WorkspaceConfig


def ensure_workspace(ws: WorkspaceConfig) -> Path:
    root = Path(ws.root_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def is_workspace_initialized(root: Path | WorkspaceConfig) -> bool:
    """Check whether the key harness files exist for a workspace."""

    base_path = root if isinstance(root, Path) else Path(root.root_dir)
    required = ["init.sh", "feature_list.json", "progress.log"]
    return all((base_path / name).exists() for name in required)


def list_workspace_files(ws: WorkspaceConfig) -> List[str]:
    root = Path(ws.root_dir)
    files: List[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        # Skip git internals for safety/noise reduction
        if any(part == ".git" for part in p.parts):
            continue
        files.append(str(p.relative_to(root)))
    return files


def read_file(ws: WorkspaceConfig, rel_path: str) -> str:
    root = Path(ws.root_dir)
    with open(root / rel_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(ws: WorkspaceConfig, rel_path: str, content: str) -> None:
    root = Path(ws.root_dir)
    full_path = root / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
