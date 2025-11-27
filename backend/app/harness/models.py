from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel


class WorkspaceConfig(BaseModel):
    id: str
    root_dir: str
    repo_url: Optional[str] = None


class TaskSpec(BaseModel):
    id: str
    user_id: str
    goal: str
    workspace_id: str
    status: Literal["pending", "running", "succeeded", "failed"] = "pending"


class SessionConfig(BaseModel):
    task_id: str
    mode: Literal["initializer", "coding"]
    max_steps: int = 8
    feature_id: Optional[str] = None


@dataclass
class InitializerResult:
    root: Path
    files_written: list[str]


@dataclass
class CodingResult:
    root: Path
    target_feature_id: str
    tests_ok: bool
    test_output: str
    feature_status: str
