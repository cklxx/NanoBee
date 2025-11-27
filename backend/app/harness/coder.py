from __future__ import annotations

from pathlib import Path

from ..llm.base import LLMClient
from .memory import MemoryStore
from .feature_list import choose_target_feature, load_features, update_feature_status
from .git_tools import get_recent_commits, git_commit_all
from .models import CodingResult, SessionConfig, TaskSpec, WorkspaceConfig
from .progress_log import append_progress_entry, latest_entries
from .shell_tools import run_init_script_and_tests
from .prompts import CODING_SYSTEM_PROMPT, CODING_USER_PROMPT_TEMPLATE


async def run_coding_session(
    task: TaskSpec,
    ws: WorkspaceConfig,
    llm: LLMClient,
    session: SessionConfig,
    memory_store: MemoryStore | None = None,
) -> CodingResult:
    root = Path(ws.root_dir)
    features = load_features(root)
    target = choose_target_feature(features, session.feature_id)

    recent_progress = "\n".join(latest_entries(root, limit=5))
    commits = "\n".join(get_recent_commits(root, limit=3))
    memories = "\n".join(memory_store.query(k=3)) if memory_store else "(memory disabled)"

    user_prompt = CODING_USER_PROMPT_TEMPLATE.format(
        task_spec=task.goal,
        target_feature_block=str(target),
        recent_progress_block=recent_progress or "(none)",
        recent_commits_block=commits or "(none)",
        memory_summary_block=memories or "(none)",
        target_feature_id=target.id,
        target_feature_description=target.description,
    )
    messages = [
        {"role": "system", "content": CODING_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    await llm.chat(messages)

    tests_ok, output = run_init_script_and_tests(root)

    if memory_store:
        memory_store.add_event(
            f"Coding session for {target.id} completed. Tests {'passed' if tests_ok else 'failed'}"
        )

    if tests_ok:
        update_feature_status(root, target.id, "passing", notes="Implemented in demo session")
        append_progress_entry(
            root,
            "CodingAgent",
            f"Implemented {target.id} ({target.description}). Tests passed.\n{output}",
        )
        git_commit_all(root, f"Implement {target.id}")
    else:
        append_progress_entry(
            root,
            "CodingAgent",
            f"Attempted {target.id} but tests failed.\n{output}",
        )
    return CodingResult(
        root=root,
        target_feature_id=target.id,
        tests_ok=tests_ok,
        test_output=output,
        feature_status="passing" if tests_ok else "failing",
    )
