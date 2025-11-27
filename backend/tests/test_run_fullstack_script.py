from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


def _make_stub_command(path: Path, log_file: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf "%s\n" "$0 $*" >> "${LOG_FILE}"
exit 0
""",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _copy_repo(src: Path, dst: Path) -> None:
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", "*.pyc"),
    )


def test_run_fullstack_copies_env_files(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    workdir = tmp_path / "repo"
    _copy_repo(repo_root, workdir)

    # Ensure targets are absent so the script exercises the copy logic.
    (workdir / ".env").unlink(missing_ok=True)
    (workdir / "frontend" / ".env").unlink(missing_ok=True)

    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"

    _make_stub_command(stub_dir / "uvicorn", log_file)
    _make_stub_command(stub_dir / "npm", log_file)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{stub_dir}:{env['PATH']}",
            "SKIP_BACKEND_INSTALL": "1",
            "SKIP_FRONTEND_INSTALL": "1",
            "LOG_FILE": str(log_file),
        }
    )

    result = subprocess.run(
        ["bash", "scripts/run_fullstack.sh"],
        cwd=workdir,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        pytest.fail(f"Script failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

    root_env = workdir / ".env"
    frontend_env = workdir / "frontend" / ".env"

    assert root_env.exists()
    assert frontend_env.exists()
    assert root_env.read_text(encoding="utf-8") == (workdir / ".env.example").read_text(encoding="utf-8")
    assert frontend_env.read_text(encoding="utf-8") == (
        workdir / "frontend" / ".env.example"
    ).read_text(encoding="utf-8")
