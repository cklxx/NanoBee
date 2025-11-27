from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..db import models
from ..llm.base import LLMClient
from .feature_list import load_features
from .progress_log import latest_entries


@dataclass
class EvalOutcome:
    score: int
    details: str


async def evaluate_task_result(
    task_id: str,
    task_goal: str,
    workspace_root: Path,
    llm: LLMClient | None,
) -> EvalOutcome:
    features = load_features(workspace_root)
    progress = "\n".join(latest_entries(workspace_root, limit=10))
    status_summary = "\n".join(f"- {f.id}: {f.status}" for f in features)

    if llm:
        messages = [
            {
                "role": "system",
                "content": "You are an evaluator. Score task completeness from 0-100 based on features and progress.",
            },
            {
                "role": "user",
                "content": f"Task goal: {task_goal}\nFeatures:\n{status_summary}\nRecent progress:\n{progress or '(none)'}",
            },
        ]
        try:
            resp = await llm.chat(messages)
            raw_content: Any = resp.get("content") if isinstance(resp, dict) else None
            if isinstance(raw_content, str):
                score = _extract_score(raw_content)
                return EvalOutcome(score=score, details=raw_content)
        except Exception:
            pass

    passing = all(f.status == "passing" for f in features)
    score = 100 if passing else 60
    details = "All features passing." if passing else "Some features still failing."
    return EvalOutcome(score=score, details=details)


def persist_eval_result(db_session, task_id: str, outcome: EvalOutcome) -> models.EvalResult:
    result = models.EvalResult(
        task_id=task_id,
        score=outcome.score,
        details=outcome.details,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)
    return result


def _extract_score(text: str) -> int:
    for token in text.split():
        if token.rstrip('%').isdigit():
            value = int(token.rstrip('%'))
            return max(0, min(100, value))
    return 75
