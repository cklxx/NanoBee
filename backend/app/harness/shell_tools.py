from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Tuple


def run_init_script_and_tests(root: Path) -> Tuple[bool, str]:
    script = root / "init.sh"
    if not script.exists():
        return False, "init.sh not found"
    result = subprocess.run(["bash", str(script)], cwd=root, capture_output=True, text=True)
    success = result.returncode == 0
    output = result.stdout + result.stderr
    return success, output
