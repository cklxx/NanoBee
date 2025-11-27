from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

PROGRESS_FILE = "progress.log"


def read_progress_log(root: Path) -> str:
    path = root / PROGRESS_FILE
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def append_progress_entry(root: Path, author: str, message: str) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    entry = f"[{timestamp}] {author}: {message}\n"
    path = root / PROGRESS_FILE
    existing = read_progress_log(root)
    path.write_text(existing + entry, encoding="utf-8")


def latest_entries(root: Path, limit: int = 5) -> List[str]:
    log = read_progress_log(root)
    lines = [line for line in log.strip().splitlines() if line.strip()]
    return lines[-limit:]
