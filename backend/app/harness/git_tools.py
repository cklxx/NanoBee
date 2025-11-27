from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)


def git_init_and_first_commit(root: Path) -> None:
    _git(root, "init")
    _git(root, "config", "user.email", "agent@example.com")
    _git(root, "config", "user.name", "Auto Agent")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "Initial scaffold")


def git_commit_all(root: Path, message: str) -> None:
    _git(root, "add", ".")
    _git(root, "commit", "-m", message)


def get_recent_commits(root: Path, limit: int = 5) -> List[str]:
    result = _git(root, "log", f"-{limit}", "--oneline")
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]
