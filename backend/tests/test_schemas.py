"""Comprehensive tests for all Pydantic request/response schemas.

Covers: field defaults, validation boundaries, type coercion, null handling,
and malformed input rejection for every model in schemas.py.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)


# ===========================================================================
# QueryRequest
# ===========================================================================
class TestQueryRequest:
    # -- defaults --
    def test_default_use_sub_questions_true(self):
        req = QueryRequest(question="Revenue?")
        assert req.use_sub_questions is True

    def test_default_companies_none(self):
        req = QueryRequest(question="Revenue?")
        assert req.companies is None

    def test_default_years_none(self):
        req = QueryRequest(question="Revenue?")
        assert req.years is None

    # -- question length boundaries --
    def test_min_length_question(self):
        req = QueryRequest(question="Q")
        assert req.question == "Q"

    def test_max_length_question(self):
        q = "x" * 2000
        req = QueryRequest(question=q)
        assert len(req.question) == 2000

    def test_empty_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="")

    def test_question_too_long_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="x" * 2001)

    def test_missing_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest()

    # -- question type mismatches --
    def test_none_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question=None)

    def test_numeric_question_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question=12345)

    # -- companies / years filters --
    def test_companies_list_accepted(self):
        req = QueryRequest(question="Q", companies=["nvidia", "apple"])
        assert req.companies == ["nvidia", "apple"]

    def test_years_list_accepted(self):
        req = QueryRequest(question="Q", years=[2024, 2025])
        assert req.years == [2024, 2025]

    def test_empty_companies_list_accepted(self):
        req = QueryRequest(question="Q", companies=[])
        assert req.companies == []

    def test_empty_years_list_accepted(self):
        req = QueryRequest(question="Q", years=[])
        assert req.years == []

    def test_companies_max_length_boundary(self):
        req = QueryRequest(question="Q", companies=["c"] * 10)
        assert len(req.companies) == 10

    def test_companies_over_max_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="Q", companies=["c"] * 11)

    def test_years_max_length_boundary(self):
        req = QueryRequest(question="Q", years=list(range(10)))
        assert len(req.years) == 10

    def test_years_over_max_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(question="Q", years=list(range(11)))

    # -- use_sub_questions --
    def test_explicit_false_honored(self):
        req = QueryRequest(question="Q", use_sub_questions=False)
        assert req.use_sub_questions is False

    # -- JSON round-trip --
    def test_json_round_trip(self):
        req = QueryRequest(question="Test?", companies=["nvidia"], years=[2024])
        data = req.model_dump()
        restored = QueryRequest.model_validate(data)
        assert restored == req

    def test_model_validate_missing_question(self):
        with pytest.raises(ValidationError):
            QueryRequest.model_validate({})

    def test_model_validate_null_question(self):
        with pytest.raises(ValidationError):
            QueryRequest.model_validate({"question": None})


# ===========================================================================
# SourceDocument
# ===========================================================================
class TestSourceDocument:
    def test_minimal_construction(self):
        sd = SourceDocument(filename="f.pdf", page=1, score=0.9, text_snippet="text")
        assert sd.source_type == "document"

    def test_custom_source_type(self):
        sd = SourceDocument(
            filename="f.pdf", page=1, score=0.5, text_snippet="t",
            source_type="sub_question",
        )
        assert sd.source_type == "sub_question"

    def test_zero_score(self):
        sd = SourceDocument(filename="f.pdf", page=0, score=0.0, text_snippet="")
        assert sd.score == 0.0

    def test_negative_page_accepted(self):
        sd = SourceDocument(filename="f.pdf", page=-1, score=0.5, text_snippet="t")
        assert sd.page == -1

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            SourceDocument(filename="f.pdf", page=1, score=0.9)


# ===========================================================================
# QueryResponse
# ===========================================================================
class TestQueryResponse:
    def test_minimal_construction(self):
        qr = QueryResponse(answer="Answer", sources=[])
        assert qr.query_id == ""

    def test_with_query_id(self):
        qr = QueryResponse(answer="A", sources=[], query_id="abc-123")
        assert qr.query_id == "abc-123"

    def test_with_sources(self):
        src = SourceDocument(filename="f.pdf", page=1, score=0.8, text_snippet="t")
        qr = QueryResponse(answer="A", sources=[src])
        assert len(qr.sources) == 1

    def test_missing_answer_rejected(self):
        with pytest.raises(ValidationError):
            QueryResponse(sources=[])


# ===========================================================================
# IngestRequest
# ===========================================================================
class TestIngestRequest:
    def test_default_force_false(self):
        req = IngestRequest()
        assert req.force is False

    def test_explicit_force_true(self):
        req = IngestRequest(force=True)
        assert req.force is True

    def test_from_json_empty(self):
        req = IngestRequest.model_validate({})
        assert req.force is False


# ===========================================================================
# IngestResponse
# ===========================================================================
class TestIngestResponse:
    def test_minimal(self):
        resp = IngestResponse(status="ok", documents_processed=6, chunks_created=796)
        assert resp.existing_chunks == 0

    def test_skipped_status(self):
        resp = IngestResponse(
            status="skipped", documents_processed=0, chunks_created=0,
            existing_chunks=796,
        )
        assert resp.status == "skipped"
        assert resp.existing_chunks == 796

    def test_missing_required_field_rejected(self):
        with pytest.raises(ValidationError):
            IngestResponse(status="ok", documents_processed=6)


