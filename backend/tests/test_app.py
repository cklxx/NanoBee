import sys
from pathlib import Path
from typing import Any, AsyncIterator

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app import agent, skills  # noqa: E402
from app.main import app


@pytest.fixture(autouse=True)
def restore_modules(monkeypatch):
    """Restore patched objects after each test."""

    original_query = agent.query
    original_result_message = agent.ResultMessage
    original_generate_images = skills.image_client.generate_images

    yield

    monkeypatch.setattr(agent, "query", original_query, raising=False)
    monkeypatch.setattr(agent, "ResultMessage", original_result_message, raising=False)
    monkeypatch.setattr(skills.image_client, "generate_images", original_generate_images, raising=False)


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_proxy_health():
    client = TestClient(app)
    response = client.get("/proxy/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["openai_api_configured"] is False


def test_agent_run_endpoint(monkeypatch):
    class FakeResult:
        def __init__(self, total_cost_usd: float | None = None) -> None:
            self.total_cost_usd = total_cost_usd

    async def fake_query(*_args: Any, **_kwargs: Any) -> AsyncIterator[Any]:
        yield "message-1"
        yield FakeResult(0.05)

    monkeypatch.setattr(agent, "query", fake_query)
    monkeypatch.setattr(agent, "ResultMessage", FakeResult)

    client = TestClient(app)
    response = client.post("/agent/run", json={"prompt": "测试"})

    assert response.status_code == 200
    data = response.json()
    assert data["cost"] == 0.05
    assert data["messages"][0] == "'message-1'"
    assert "FakeResult object" in data["messages"][1]
    assert len(data["messages"]) == 2


def test_visuals_endpoint(monkeypatch):
    async def fake_generate_images(prompts: list[str]) -> list[dict[str, Any]]:
        results = []
        for idx, prompt in enumerate(prompts):
            results.append({"prompt": prompt, "url": f"http://example.com/{idx}.png", "raw": {"i": idx}})
        return results

    monkeypatch.setattr(skills.image_client, "generate_images", fake_generate_images)

    client = TestClient(app)
    payload = {"topic": "测试主题", "narrative": "测试叙述", "slides": 2}
    response = client.post("/skills/visuals", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["raw"]
    assert len(data["raw"]) == 2
    assert all(item["url"].startswith("http://example.com/") for item in data["raw"])
