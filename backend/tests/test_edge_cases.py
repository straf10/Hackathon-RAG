"""Edge-case and malformed-input tests.

Validates that the API and schemas handle boundary conditions, null inputs,
type mismatches, and malformed data gracefully.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.models.schemas import QueryRequest, FeedbackRequest
from app.routers.query import _is_mock_output, _safe_int, router as query_router

_app = FastAPI()
_app.include_router(query_router)
_client = TestClient(_app, raise_server_exceptions=False)

_URL = "/query"
_GOOD_USAGE = {"budget_remaining_usd": 5.0}


# ===========================================================================
# _safe_int — type coercion helper
# ===========================================================================
class TestSafeInt:
    def test_normal_int(self):
        assert _safe_int(42) == 42

    def test_string_int(self):
        assert _safe_int("42") == 42

    def test_float_truncated(self):
        assert _safe_int(3.9) == 3

    def test_none_returns_zero(self):
        assert _safe_int(None) == 0

    def test_empty_string_returns_zero(self):
        assert _safe_int("") == 0

    def test_non_numeric_string_returns_zero(self):
        assert _safe_int("abc") == 0

    def test_list_returns_zero(self):
        assert _safe_int([1, 2]) == 0

    def test_dict_returns_zero(self):
        assert _safe_int({"a": 1}) == 0

    def test_bool_true_returns_one(self):
        assert _safe_int(True) == 1

    def test_negative_int(self):
        assert _safe_int(-5) == -5

    def test_string_negative(self):
        assert _safe_int("-10") == -10


# ===========================================================================
# Malformed JSON to /query
# ===========================================================================
class TestQueryMalformedInput:
    def test_empty_json_body_returns_422(self):
        resp = _client.post(_URL, json={})
        assert resp.status_code == 422

    def test_null_body_returns_422(self):
        resp = _client.post(
            _URL,
            content=b"null",
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 422

    def test_string_body_returns_422(self):
        resp = _client.post(
            _URL,
            content=b'"just a string"',
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 422

    def test_array_body_returns_422(self):
        resp = _client.post(
            _URL,
            content=b'[1, 2, 3]',
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 422

    def test_invalid_json_returns_422(self):
        resp = _client.post(
            _URL,
            content=b'{bad json}',
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 422

    def test_question_null_returns_422(self):
        resp = _client.post(_URL, json={"question": None})
        assert resp.status_code == 422

    def test_question_empty_string_returns_422(self):
        resp = _client.post(_URL, json={"question": ""})
        assert resp.status_code == 422

    def test_question_too_long_returns_422(self):
        resp = _client.post(_URL, json={"question": "x" * 2001})
        assert resp.status_code == 422

    def test_companies_wrong_type_returns_422(self):
        resp = _client.post(
            _URL,
            json={"question": "Q", "companies": "nvidia"},
        )
        assert resp.status_code == 422

    def test_years_wrong_type_returns_422(self):
        resp = _client.post(
            _URL,
            json={"question": "Q", "years": "2024"},
        )
        assert resp.status_code == 422

    def test_companies_too_many_returns_422(self):
        resp = _client.post(
            _URL,
            json={"question": "Q", "companies": ["c"] * 11},
        )
        assert resp.status_code == 422

    def test_years_too_many_returns_422(self):
        resp = _client.post(
            _URL,
            json={"question": "Q", "years": list(range(11))},
        )
        assert resp.status_code == 422


# ===========================================================================
# Query with companies/years passthrough
# ===========================================================================
class TestQueryFilterPassthrough:
    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_companies_passed_to_engine(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {"answer": "A", "source_nodes": []}
        mock_eng.return_value = engine
        _client.post(
            _URL,
            json={"question": "Q", "companies": ["nvidia", "apple"]},
        )
        kwargs = engine.query.call_args.kwargs
        assert kwargs["companies"] == ["nvidia", "apple"]

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_years_passed_to_engine(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {"answer": "A", "source_nodes": []}
        mock_eng.return_value = engine
        _client.post(
            _URL,
            json={"question": "Q", "years": [2024, 2025]},
        )
        kwargs = engine.query.call_args.kwargs
        assert kwargs["years"] == [2024, 2025]

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_none_filters_passed_when_omitted(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {"answer": "A", "source_nodes": []}
        mock_eng.return_value = engine
        _client.post(_URL, json={"question": "Q"})
        kwargs = engine.query.call_args.kwargs
        assert kwargs["companies"] is None
        assert kwargs["years"] is None


# ===========================================================================
# Query ID is always returned
# ===========================================================================
class TestQueryIdPresence:
    @patch("app.routers.query.has_valid_openai_key", return_value=False)
    def test_query_id_present_on_no_key(self, _k):
        body = _client.post(_URL, json={"question": "Q"}).json()
        assert "query_id" in body
        assert len(body["query_id"]) > 0

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_query_id_is_uuid_format(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {"answer": "A", "source_nodes": []}
        mock_eng.return_value = engine
        body = _client.post(_URL, json={"question": "Q"}).json()
        import uuid
        uuid.UUID(body["query_id"])


# ===========================================================================
# _is_mock_output — edge cases
# ===========================================================================
class TestMockOutputEdgeCases:
    def test_whitespace_only(self):
        assert _is_mock_output("   ") is False

    def test_newlines_in_text_still_detected(self):
        assert _is_mock_output("text\ntext\ntext") is True

    def test_single_word_text(self):
        assert _is_mock_output("text") is False

    def test_two_words_text(self):
        assert _is_mock_output("text text") is False

    def test_mixed_case_three_text(self):
        assert _is_mock_output("Text TEXT text") is True


# ===========================================================================
# Source nodes with missing/null fields
# ===========================================================================
class TestSourceNodeEdgeCases:
    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_source_with_missing_score(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {
            "answer": "A",
            "source_nodes": [
                {
                    "filename": "f.pdf",
                    "page_label": "1",
                    "text_snippet": "text",
                    "source_type": "document",
                }
            ],
        }
        mock_eng.return_value = engine
        resp = _client.post(_URL, json={"question": "Q"})
        assert resp.status_code == 200
        assert resp.json()["sources"][0]["score"] == 0.0

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_source_with_none_page_label(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {
            "answer": "A",
            "source_nodes": [
                {
                    "filename": "f.pdf",
                    "score": 0.9,
                    "text_snippet": "text",
                    "source_type": "document",
                }
            ],
        }
        mock_eng.return_value = engine
        resp = _client.post(_URL, json={"question": "Q"})
        assert resp.status_code == 200
        assert resp.json()["sources"][0]["page"] == 0

    @patch("app.routers.query.persist_usage")
    @patch("app.routers.query.get_engine")
    @patch("app.routers.query.get_usage", return_value=_GOOD_USAGE)
    @patch("app.routers.query.has_valid_openai_key", return_value=True)
    def test_empty_source_nodes_list(self, _k, _u, mock_eng, _p):
        engine = MagicMock()
        engine.query.return_value = {"answer": "A", "source_nodes": []}
        mock_eng.return_value = engine
        resp = _client.post(_URL, json={"question": "Q"})
        assert resp.status_code == 200
        assert resp.json()["sources"] == []


# ===========================================================================
# QueryRequest — additional edge-case validation
# ===========================================================================
class TestQueryRequestEdgeCases:
    def test_whitespace_only_question_accepted_if_nonzero_length(self):
        req = QueryRequest(question=" ")
        assert req.question == " "

    def test_unicode_question(self):
        req = QueryRequest(question="Ποιά είναι τα έσοδα;")
        assert "έσοδα" in req.question

    def test_special_characters_in_question(self):
        req = QueryRequest(question="Revenue > $10B? (2024)")
        assert req.question == "Revenue > $10B? (2024)"

    def test_years_with_float_coerced(self):
        req = QueryRequest(question="Q", years=[2024.0])
        assert req.years == [2024]

    def test_extra_fields_ignored(self):
        req = QueryRequest.model_validate(
            {"question": "Q", "unknown_field": "value"}
        )
        assert not hasattr(req, "unknown_field")


# ===========================================================================
# FeedbackRequest — edge-case validation
# ===========================================================================
class TestFeedbackRequestEdgeCases:
    def test_very_long_comment_accepted(self):
        req = FeedbackRequest(
            query_id="q-1", rating="up", comment="x" * 10000
        )
        assert len(req.comment) == 10000

    def test_empty_comment_accepted(self):
        req = FeedbackRequest(query_id="q-1", rating="up", comment="")
        assert req.comment == ""

    def test_unicode_comment(self):
        req = FeedbackRequest(
            query_id="q-1", rating="down", comment="Κακή απάντηση"
        )
        assert "Κακή" in req.comment
