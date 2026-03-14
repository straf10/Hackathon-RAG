"""Smoke tests for health, root, usage, and shutdown endpoints.

These lightweight tests verify that the core application skeleton boots
and responds correctly without any external dependencies (ChromaDB,
OpenAI, filesystem).
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

_client = TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# GET /
# ===========================================================================
class TestRoot:
    def test_returns_200(self):
        resp = _client.get("/")
        assert resp.status_code == 200

    def test_body_has_nonempty_message(self):
        body = _client.get("/").json()
        assert "message" in body and isinstance(body["message"], str) and len(body["message"]) > 0


# ===========================================================================
# GET /health
# ===========================================================================
class TestHealth:
    def test_returns_200(self):
        resp = _client.get("/health")
        assert resp.status_code == 200

    def test_status_is_ok(self):
        body = _client.get("/health").json()
        assert body == {"status": "ok"}

    def test_response_content_type_is_json(self):
        resp = _client.get("/health")
        assert "application/json" in resp.headers["content-type"]


# ===========================================================================
# GET /usage
# ===========================================================================
class TestUsage:
    def test_returns_200(self):
        resp = _client.get("/usage")
        assert resp.status_code == 200

    def test_contains_required_keys(self):
        body = _client.get("/usage").json()
        expected_keys = {
            "llm_prompt_tokens",
            "llm_completion_tokens",
            "llm_total_tokens",
            "embedding_tokens",
            "estimated_cost_usd",
            "budget_total_usd",
            "budget_remaining_usd",
        }
        assert expected_keys.issubset(body.keys())

    def test_budget_remaining_is_non_negative(self):
        body = _client.get("/usage").json()
        assert body["budget_remaining_usd"] >= 0

    def test_token_counts_are_integers(self):
        body = _client.get("/usage").json()
        for key in ("llm_prompt_tokens", "llm_completion_tokens", "embedding_tokens"):
            assert isinstance(body[key], int)

    def test_cost_is_numeric(self):
        body = _client.get("/usage").json()
        assert isinstance(body["estimated_cost_usd"], (int, float))


# ===========================================================================
# POST /shutdown
# ===========================================================================
class TestShutdown:
    @patch("app.routers.usage.persist")
    def test_returns_200_with_ok_status(self, mock_persist):
        resp = _client.post("/shutdown")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @patch("app.routers.usage.persist")
    def test_calls_persist(self, mock_persist):
        _client.post("/shutdown")
        mock_persist.assert_called_once()


# ===========================================================================
# Nonexistent routes
# ===========================================================================
class TestNotFound:
    def test_get_unknown_path_returns_404(self):
        resp = _client.get("/nonexistent")
        assert resp.status_code == 404

    def test_post_unknown_path_returns_404_or_405(self):
        resp = _client.post("/nonexistent")
        assert resp.status_code in (404, 405)
