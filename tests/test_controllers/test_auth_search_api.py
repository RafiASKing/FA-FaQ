from fastapi import FastAPI
from fastapi.testclient import TestClient

from config.middleware import setup_middleware
from config.settings import settings
from routes.api.v1 import router as api_v1_router


def _build_test_client(monkeypatch):
    app = FastAPI()
    setup_middleware(app)
    app.include_router(api_v1_router)

    monkeypatch.setattr(
        "app.controllers.search_controller.SearchService.search_for_web",
        lambda query, filter_tag=None, top_n=3: [],
    )
    return TestClient(app)


def test_search_requires_api_key_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "pilot-secret")
    client = _build_test_client(monkeypatch)

    resp = client.get("/api/v1/search", params={"q": "login"})

    assert resp.status_code == 401
    assert "Invalid or missing API key" in resp.json().get("detail", "")


def test_search_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "pilot-secret")
    client = _build_test_client(monkeypatch)

    resp = client.get(
        "/api/v1/search",
        params={"q": "login"},
        headers={"X-API-Key": "wrong"},
    )

    assert resp.status_code == 401


def test_search_accepts_valid_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "pilot-secret")
    client = _build_test_client(monkeypatch)

    resp = client.get(
        "/api/v1/search",
        params={"q": "login"},
        headers={"X-API-Key": "pilot-secret"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "login"
    assert body["total_results"] == 0
