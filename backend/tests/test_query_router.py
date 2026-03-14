"""Tests for the /query endpoint and its helper functions.

Covers: API-key guard, budget guard, mock-output detection,
OpenAI error classification, sub-question passthrough, and response
formatting.
"""

import inspect
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.query import (
    _AUTH_FAILED_MSG,
    _BUDGET_EXHAUSTED_MSG,
    _NO_API_KEY_MSG,
    _RATE_LIMIT_MSG,
    _classify_openai_error,
    _is_mock_output,
    router,
)
from app.services.rag_engine import RAGEngine

# ---------------------------------------------------------------------------
# Test client — lightweight FastAPI app with only the query router
# ---------------------------------------------------------------------------
_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app)

_URL = "/query"
_PAYLOAD = {"question": "What is NVIDIA revenue in 2024?"}

_GOOD_USAGE = {"budget_remaining_usd": 5.0}
_ZERO_USAGE = {"budget_remaining_usd": 0}
_NEGATIVE_USAGE = {"budget_remaining_usd": -0.50}


def _engine_result(answer="NVIDIA revenue was $26.9 billion.", source_nodes=None):
    return {
        "answer": answer,
        "source_nodes": source_nodes
        or [
            {
                "filename": "nvidia_10k_2024.pdf",
                "page_label": "42",
                "score": 0.92,
                "text_snippet": "Total revenue was $26.9 billion.",
                "source_type": "document",
            }
        ],
    }


# ===========================================================================
# Unit tests — _is_mock_output
# ===========================================================================
class TestIsMockOutput:
    @pytest.mark.parametrize(
        "text",
        [
            "text text text",
            "text text text text text",
            " ".join(["text"] * 100),
            "TEXT TEXT TEXT",
            "Text text Text",
            "  text text text  ",
            "text, text, text",
            "text  text  text",
        ],
    )
    def test_detects_mock_output(self, text):
        assert _is_mock_output(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "text",
            "text text",
            "NVIDIA revenue was $26.9 billion in 2024.",
            "The text shows that revenue grew significantly.",
            "text analysis of financial data shows growth",
        ],
    )
    def test_rejects_normal_text(self, text):
        assert _is_mock_output(text) is False


# ===========================================================================
# Unit tests — _classify_openai_error
# ===========================================================================
class TestClassifyOpenaiError:
    @pytest.mark.parametrize(
        "msg",
        [
            "AuthenticationError: Incorrect API key provided",
            "Error code 401: invalid api key",
            "openai.AuthenticationError: Invalid API key",
        ],
    )
    def test_detects_auth_errors(self, msg):
        assert _classify_openai_error(Exception(msg)) == _AUTH_FAILED_MSG

    @pytest.mark.parametrize(
        "msg",
        [
            "RateLimitError: Rate limit exceeded",
            "Error 429: Too Many Requests",
            "Your quota has been exceeded",
            "billing hard limit reached",
        ],
    )
    def test_detects_rate_limit_errors(self, msg):
        assert _classify_openai_error(Exception(msg)) == _RATE_LIMIT_MSG

    @pytest.mark.parametrize(
        "msg",
        [
            "Connection refused",
            "Unexpected server error",
            "ChromaDB timeout",
        ],
    )
    def test_returns_none_for_unknown_errors(self, msg):
        assert _classify_openai_error(Exception(msg)) is None


# ===========================================================================
# Unit test — RAGEngine.query default parameter
# ===========================================================================
class TestRagEngineQueryDefault:
    def test_use_sub_questions_defaults_true(self):
        sig = inspect.signature(RAGEngine.query)
        assert sig.parameters["use_sub_questions"].default is True


# ===========================================================================
# Integration — /query: no API key
# ===========================================================================
class TestQueryNoApiKey:
    @patch("app.routers.query.has_valid_openai_key", return_value=False)
    def test_returns_friendly_message(self, _mock_key):
        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == _NO_API_KEY_MSG
        assert body["sources"] == []
        assert body["query_id"]

    @patch("app.routers.query.has_valid_openai_key", return_value=False)
    def test_engine_not_called(self, _mock_key):
        with patch("app.routers.query.get_engine") as mock_eng:
            _client.post(_URL, json=_PAYLOAD)
            mock_eng.assert_not_called()


# ===========================================================================
# Integration — /query: budget exhausted
# ===========================================================================
class TestQueryBudgetExhausted:
    @pytest.mark.parametrize("usage", [_ZERO_USAGE, _NEGATIVE_USAGE])
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    @patch("app.routers.query.get_usage")
    def test_exhausted_budget_returns_message(self, mock_usage, _k, usage):
        mock_usage.return_value = usage
        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json()["answer"] == _BUDGET_EXHAUSTED_MSG


# ===========================================================================
# Integration — /query: mock-output safety net
# ===========================================================================
class TestQueryMockOutputSafetyNet:
    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_mock_output_replaced(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result(
            answer=" ".join(["text"] * 50)
        )
        mock_eng.return_value = engine

        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json()["answer"] == _NO_API_KEY_MSG


# ===========================================================================
# Integration — /query: OpenAI API errors
# ===========================================================================
class TestQueryOpenaiErrors:
    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_auth_error_returns_message(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.side_effect = Exception(
            "AuthenticationError: Invalid API key"
        )
        mock_eng.return_value = engine

        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json()["answer"] == _AUTH_FAILED_MSG

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_rate_limit_error_returns_message(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.side_effect = Exception(
            "RateLimitError: quota exceeded"
        )
        mock_eng.return_value = engine

        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json()["answer"] == _RATE_LIMIT_MSG

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_unknown_error_returns_500(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.side_effect = RuntimeError("Unexpected failure")
        mock_eng.return_value = engine

        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 500


# ===========================================================================
# Integration — /query: successful query
# ===========================================================================
class TestQuerySuccess:
    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_returns_answer_and_sources(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result()
        mock_eng.return_value = engine

        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        body = resp.json()
        assert "NVIDIA" in body["answer"]
        assert len(body["sources"]) == 1
        assert body["sources"][0]["filename"] == "nvidia_10k_2024.pdf"

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_empty_answer_replaced(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result(answer="", source_nodes=[])
        mock_eng.return_value = engine

        resp = _client.post(_URL, json=_PAYLOAD)
        assert resp.status_code == 200
        assert "don't have enough information" in resp.json()["answer"]

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_sub_questions_default_true_passed_to_engine(
        self, _k, _u, mock_eng, _p
    ):
        engine = MagicMock()
        engine.query.return_value = _engine_result()
        mock_eng.return_value = engine

        _client.post(_URL, json={"question": "Test?"})

        engine.query.assert_called_once()
        kwargs = engine.query.call_args.kwargs
        assert kwargs["use_sub_questions"] is True

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_explicit_false_passed_to_engine(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result()
        mock_eng.return_value = engine

        _client.post(
            _URL, json={"question": "Test?", "use_sub_questions": False}
        )

        kwargs = engine.query.call_args.kwargs
        assert kwargs["use_sub_questions"] is False
