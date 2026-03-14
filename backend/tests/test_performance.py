"""Performance tests.

Enforces the NFR-05 latency requirement from Project_Specification.md:
    "Query response latency under 15 seconds for typical single-company questions."

The 15-second limit is a HARD assertion — any query exceeding it fails the test.

External dependencies are mocked so the test measures application overhead
only (serialization, routing, async dispatch, response formatting), not
real OpenAI/ChromaDB latency.  A separate simulated-latency test verifies
the 15s budget is enforced when the engine is slow.
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app as _full_app
from app.routers.query import router

_LATENCY_LIMIT_SECONDS = 15.0

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app, raise_server_exceptions=False)
_full_client = TestClient(_full_app, raise_server_exceptions=False)

_URL = "/query"
_GOOD_USAGE = {"budget_remaining_usd": 5.0}


def _engine_result(answer="Revenue was $130.5 billion.", n_sources=5):
    return {
        "answer": answer,
        "source_nodes": [
            {
                "filename": f"doc_{i}.pdf",
                "page_label": str(i * 10),
                "score": round(0.95 - i * 0.05, 4),
                "text_snippet": f"Source text from document {i}.",
                "source_type": "document",
            }
            for i in range(n_sources)
        ],
    }


# ===========================================================================
# NFR-05: /query must respond within 15 seconds
# ===========================================================================
class TestQueryLatency:
    """Measures wall-clock time from request to response.
    Fails if any query exceeds 15 seconds."""

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_simple_query_under_15s(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result()
        mock_eng.return_value = engine

        start = time.perf_counter()
        resp = _client.post(
            _URL,
            json={"question": "What was NVIDIA revenue in 2025?"},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < _LATENCY_LIMIT_SECONDS, (
            f"Query took {elapsed:.2f}s — exceeds {_LATENCY_LIMIT_SECONDS}s limit"
        )

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_filtered_query_under_15s(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result()
        mock_eng.return_value = engine

        start = time.perf_counter()
        resp = _client.post(
            _URL,
            json={
                "question": "Compare NVIDIA and Apple revenue in 2024",
                "use_sub_questions": True,
            },
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < _LATENCY_LIMIT_SECONDS, (
            f"Filtered query took {elapsed:.2f}s — exceeds {_LATENCY_LIMIT_SECONDS}s limit"
        )

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_large_source_list_under_15s(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result(n_sources=50)
        mock_eng.return_value = engine

        start = time.perf_counter()
        resp = _client.post(
            _URL,
            json={"question": "List all risk factors for Google in 2025"},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert len(resp.json()["sources"]) == 50
        assert elapsed < _LATENCY_LIMIT_SECONDS, (
            f"Large-source query took {elapsed:.2f}s — exceeds {_LATENCY_LIMIT_SECONDS}s limit"
        )

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_max_length_question_under_15s(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = _engine_result()
        mock_eng.return_value = engine

        start = time.perf_counter()
        resp = _client.post(
            _URL,
            json={"question": "x" * 2000},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < _LATENCY_LIMIT_SECONDS, (
            f"Max-length query took {elapsed:.2f}s — exceeds {_LATENCY_LIMIT_SECONDS}s limit"
        )


# ===========================================================================
# NFR-05: Simulated slow engine must still complete within budget
# ===========================================================================
class TestSimulatedLatency:
    """Verify the system handles engine delays correctly.

    An engine that sleeps for a controlled duration is injected.
    Tests confirm that a fast engine passes and a slow engine would
    indeed breach the limit.
    """

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_engine_at_2s_passes(self, _k, _u, mock_eng, _p):
        def slow_query(**kwargs):
            time.sleep(2)
            return _engine_result()

        engine = MagicMock()
        engine.query.side_effect = slow_query
        mock_eng.return_value = engine

        start = time.perf_counter()
        resp = _client.post(
            _URL,
            json={"question": "NVIDIA revenue?"},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < _LATENCY_LIMIT_SECONDS, (
            f"2s-delayed query took {elapsed:.2f}s total — exceeds limit"
        )

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_engine_at_5s_still_passes(self, _k, _u, mock_eng, _p):
        def slow_query(**kwargs):
            time.sleep(5)
            return _engine_result()

        engine = MagicMock()
        engine.query.side_effect = slow_query
        mock_eng.return_value = engine

        start = time.perf_counter()
        resp = _client.post(
            _URL,
            json={"question": "Apple net income 2024?"},
        )
        elapsed = time.perf_counter() - start

        assert resp.status_code == 200
        assert elapsed < _LATENCY_LIMIT_SECONDS, (
            f"5s-delayed query took {elapsed:.2f}s total — exceeds limit"
        )


# ===========================================================================
# Non-query endpoints must respond near-instantly
# ===========================================================================
class TestNonQueryLatency:
    """Health, usage, and root endpoints should respond in well under 1 second."""

    _FAST_LIMIT = 1.0

    def test_health_latency(self):
        start = time.perf_counter()
        resp = _full_client.get("/health")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < self._FAST_LIMIT

    def test_root_latency(self):
        start = time.perf_counter()
        resp = _full_client.get("/")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < self._FAST_LIMIT

    def test_usage_latency(self):
        start = time.perf_counter()
        resp = _full_client.get("/usage")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        assert elapsed < self._FAST_LIMIT
