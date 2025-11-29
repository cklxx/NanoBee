from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Feature:
    id: str
    description: str
    status: str
    notes: str = ""


FEATURE_FILE = "feature_list.json"


def default_features(goal: str) -> List[Feature]:
    del goal  # the fallback list is intentionally goal-agnostic
    return [
        Feature(
            "feat_fibonacci_endpoint",
            "Expose a GET /fib/{n} endpoint that returns the nth Fibonacci number as JSON",
            "failing",
            "TODO: ensure handler wiring stays in sync with FastAPI app startup",
        ),
        Feature(
            "feat_input_validation",
            "Reject invalid or overly large inputs with helpful 400 responses",
            "failing",
            "TODO: extend validation rules based on product requirements",
        ),
        Feature(
            "feat_caching",
            "Cache Fibonacci computations and surface cache hits for repeat requests",
            "failing",
            "TODO: add metrics/export cache stats for observability",
        ),
    ]


def load_features(root: Path) -> List[Feature]:
    path = root / FEATURE_FILE
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Feature(**item) for item in data]


def features_from_json(payload: str) -> List[Feature]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("feature_list.json must be an array")

    parsed: List[Feature] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"feature_list entry at index {idx} is not an object")

        # Enforce required fields and normalize types
        try:
            fid = str(item["id"])
            description = str(item["description"])
        except KeyError as exc:  # pragma: no cover - defensive guardrail
            raise ValueError("feature entries must include id and description") from exc

        status = str(item.get("status", "failing"))
        # At initialization all statuses must be failing.
        normalized_status = "failing" if status != "passing" else "failing"
        notes = str(item.get("notes", ""))

        parsed.append(Feature(fid, description, normalized_status, notes))

    return parsed


def save_features(root: Path, features: List[Feature]) -> None:
    payload = [feature.__dict__ for feature in features]
    (root / FEATURE_FILE).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_feature_status(root: Path, feature_id: str, status: str, notes: str = "") -> None:
    features = load_features(root)
    updated: List[Feature] = []
    for feature in features:
        if feature.id == feature_id:
            updated.append(Feature(feature.id, feature.description, status, notes or feature.notes))
        else:
            updated.append(feature)
    save_features(root, updated)


def all_features_passing(root: Path) -> bool:
    features = load_features(root)
    return bool(features) and all(feature.status == "passing" for feature in features)


def choose_target_feature(features: List[Feature], requested_id: str | None = None) -> Feature:
    if requested_id:
        for feature in features:
            if feature.id == requested_id:
                return feature
    for feature in features:
        if feature.status == "failing":
            return feature
    return features[0]
