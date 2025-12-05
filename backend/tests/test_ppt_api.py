from __future__ import annotations

import importlib
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import config


def test_ppt_endpoints_persist_and_read_prompts(tmp_path, monkeypatch):
    monkeypatch.setenv("NANOBEE_WORKSPACES_ROOT", str(tmp_path))

    config.get_settings.cache_clear()
    import app.main as main

    importlib.reload(config)
    importlib.reload(main)

    client = TestClient(main.app)

    search_resp = client.post(
        "/api/ppt/search", json={"topic": "可再生能源", "limit": 4}
    ).json()

    assert search_resp["references"]
    assert search_resp["references"][0]["rank"] == 1

    outline_resp = client.post(
        "/api/ppt/outline",
        json={"topic": "可再生能源", "references": search_resp["references"]},
    ).json()

    slides_resp = client.post(
        "/api/ppt/slides",
        json={
            "topic": "可再生能源",
            "outline": outline_resp["outline"],
            "references": search_resp["references"],
            "style_prompt": "极简商务",
        },
    ).json()

    assert 1 <= len(slides_resp["slides"]) <= 15
    assert slides_resp["slides"][-1]["title"].endswith("参考资料索引")

    images_resp = client.post(
        "/api/ppt/images",
        json={"topic": "可再生能源", "slides": slides_resp["slides"]},
    ).json()

    assert len(images_resp["images"]) == len(slides_resp["slides"])
    assert images_resp["images"][0]["data_url"].startswith("data:image/svg+xml;base64,")

    prompts_resp = client.get(
        "/api/ppt/prompts", params={"topic": "可再生能源", "stage": "slides"}
    ).json()

    assert prompts_resp["prompts"]
    assert all(entry["stage"] == "slides" for entry in prompts_resp["prompts"])
    assert Path(prompts_resp["prompts"][0]["path"]).exists()

    images_notebook = client.get(
        "/api/ppt/prompts", params={"topic": "可再生能源", "stage": "images"}
    ).json()
    assert images_notebook["prompts"]
    assert images_notebook["prompts"][0]["path"].endswith("images.md")
