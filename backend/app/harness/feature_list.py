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
    return [
        Feature("feat_add_item", "User can add a todo item", "failing"),
        Feature("feat_view_items", "User can view todo items", "failing"),
        Feature("feat_toggle_item", "User can toggle completion", "failing"),
    ]


def load_features(root: Path) -> List[Feature]:
    path = root / FEATURE_FILE
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Feature(**item) for item in data]


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
