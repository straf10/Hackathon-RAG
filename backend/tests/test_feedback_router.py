"""Tests for the /feedback, /feedback/stats, and /feedback/recent endpoints.

All SQLite operations are mocked so tests run without filesystem side effects.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.feedback import router

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app)


# ===========================================================================
# POST /feedback — success
# ===========================================================================
class TestFeedbackPost:
    @patch("app.routers.feedback.save_feedback")
    def test_returns_200(self, mock_save):
        resp = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "up"},
        )
        assert resp.status_code == 200

    @patch("app.routers.feedback.save_feedback")
    def test_response_contains_feedback_id(self, mock_save):
        body = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "up"},
        ).json()
        assert "feedback_id" in body
        assert len(body["feedback_id"]) > 0

    @patch("app.routers.feedback.save_feedback")
    def test_status_is_ok(self, mock_save):
        body = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "down"},
        ).json()
        assert body["status"] == "ok"

    @patch("app.routers.feedback.save_feedback")
    def test_with_comment(self, mock_save):
        resp = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "up", "comment": "Helpful!"},
        )
        assert resp.status_code == 200
        mock_save.assert_called_once()
        call_kwargs = mock_save.call_args.kwargs
        assert call_kwargs["comment"] == "Helpful!"

    @patch("app.routers.feedback.save_feedback")
    def test_save_receives_correct_rating(self, mock_save):
        _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "down"},
        )
        call_kwargs = mock_save.call_args.kwargs
        assert call_kwargs["rating"] == "down"
        assert call_kwargs["query_id"] == "q-1"


# ===========================================================================
# POST /feedback — validation errors
# ===========================================================================
class TestFeedbackValidation:
    def test_missing_query_id_returns_422(self):
        resp = _client.post("/feedback", json={"rating": "up"})
        assert resp.status_code == 422

    def test_missing_rating_returns_422(self):
        resp = _client.post("/feedback", json={"query_id": "q-1"})
        assert resp.status_code == 422

    def test_invalid_rating_returns_422(self):
        resp = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "neutral"},
        )
        assert resp.status_code == 422

    def test_numeric_rating_returns_422(self):
        resp = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": 5},
        )
        assert resp.status_code == 422

    def test_empty_body_returns_422(self):
        resp = _client.post("/feedback", json={})
        assert resp.status_code == 422

    def test_null_body_returns_422(self):
        resp = _client.post("/feedback", content=b"null", headers={"content-type": "application/json"})
        assert resp.status_code == 422


# ===========================================================================
# POST /feedback — persistence failure
# ===========================================================================
class TestFeedbackPersistenceFailure:
    @patch("app.routers.feedback.save_feedback", side_effect=RuntimeError("DB locked"))
    def test_returns_500_on_save_error(self, _mock):
        resp = _client.post(
            "/feedback",
            json={"query_id": "q-1", "rating": "up"},
        )
        assert resp.status_code == 500


# ===========================================================================
# GET /feedback/stats
# ===========================================================================
class TestFeedbackStats:
    @patch(
        "app.routers.feedback.get_feedback_stats",
        return_value={
            "total_queries": 50,
            "positive_percentage": 80.0,
            "negative_percentage": 20.0,
        },
    )
    def test_returns_200(self, _mock):
        resp = _client.get("/feedback/stats")
        assert resp.status_code == 200

    @patch(
        "app.routers.feedback.get_feedback_stats",
        return_value={
            "total_queries": 50,
            "positive_percentage": 80.0,
            "negative_percentage": 20.0,
        },
    )
    def test_response_shape(self, _mock):
        body = _client.get("/feedback/stats").json()
        assert body["total_queries"] == 50
        assert body["positive_percentage"] == 80.0
        assert body["negative_percentage"] == 20.0

    @patch(
        "app.routers.feedback.get_feedback_stats",
        return_value={
            "total_queries": 0,
            "positive_percentage": 0.0,
            "negative_percentage": 0.0,
        },
    )
    def test_zero_stats(self, _mock):
        body = _client.get("/feedback/stats").json()
        assert body["total_queries"] == 0

    @patch("app.routers.feedback.get_feedback_stats", side_effect=RuntimeError("fail"))
    def test_error_returns_500(self, _mock):
        resp = _client.get("/feedback/stats")
        assert resp.status_code == 500


# ===========================================================================
# GET /feedback/recent
# ===========================================================================
class TestFeedbackRecent:
    @patch(
        "app.routers.feedback.get_recent_feedback",
        return_value=[
            {
                "feedback_id": "fb-1",
                "query_id": "q-1",
                "rating": "up",
                "comment": None,
                "created_at": "2026-03-10T12:00:00Z",
            }
        ],
    )
    def test_returns_200(self, _mock):
        resp = _client.get("/feedback/recent")
        assert resp.status_code == 200

    @patch(
        "app.routers.feedback.get_recent_feedback",
        return_value=[],
    )
    def test_empty_list_when_no_feedback(self, _mock):
        body = _client.get("/feedback/recent").json()
        assert body == []

    @patch(
        "app.routers.feedback.get_recent_feedback",
        return_value=[
            {
                "feedback_id": "fb-1",
                "query_id": "q-1",
                "rating": "up",
                "comment": None,
                "created_at": "2026-03-10T12:00:00Z",
            },
            {
                "feedback_id": "fb-2",
                "query_id": "q-2",
                "rating": "down",
                "comment": "Wrong",
                "created_at": "2026-03-10T12:01:00Z",
            },
        ],
    )
    def test_returns_multiple_records(self, _mock):
        body = _client.get("/feedback/recent").json()
        assert len(body) == 2

    def test_limit_below_min_returns_422(self):
        resp = _client.get("/feedback/recent?limit=0")
        assert resp.status_code == 422

    def test_limit_above_max_returns_422(self):
        resp = _client.get("/feedback/recent?limit=101")
        assert resp.status_code == 422

    @patch("app.routers.feedback.get_recent_feedback", side_effect=RuntimeError("fail"))
    def test_error_returns_500(self, _mock):
        resp = _client.get("/feedback/recent")
        assert resp.status_code == 500
