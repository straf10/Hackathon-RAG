"""Tests for the /ingest endpoint.

Covers: successful ingestion, skip-when-populated, concurrent lock rejection,
force re-ingest, FileNotFoundError, ValueError (no PDFs), and metadata
extraction from filenames.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.ingest import router
from app.services.indexer import _extract_metadata, enrich_metadata

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app)

_URL = "/ingest"


def _ok_result(docs=6, chunks=1200):
    return {
        "status": "ok",
        "documents_loaded": docs,
        "chunks_created": chunks,
        "existing_chunks": 0,
        "collection": "financial_10k",
    }


def _skipped_result(existing=1200):
    return {
        "status": "skipped",
        "documents_loaded": 0,
        "chunks_created": 0,
        "existing_chunks": existing,
        "collection": "financial_10k",
    }


def _already_running_result():
    return {
        "status": "already_running",
        "documents_loaded": 0,
        "chunks_created": 0,
        "existing_chunks": 0,
        "collection": "financial_10k",
    }


# ===========================================================================
# /ingest — successful ingestion
# ===========================================================================
class TestIngestSuccess:
    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value=_ok_result())
    def test_returns_200(self, _run, _persist):
        resp = _client.post(_URL, json={"force": False})
        assert resp.status_code == 200

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value=_ok_result())
    def test_response_has_correct_shape(self, _run, _persist):
        body = _client.post(_URL, json={"force": False}).json()
        assert body["status"] == "ok"
        assert body["documents_processed"] == 6
        assert body["chunks_created"] == 1200

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value=_ok_result())
    def test_no_body_accepted(self, _run, _persist):
        resp = _client.post(_URL)
        assert resp.status_code == 200

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value=_ok_result())
    def test_empty_json_accepted(self, _run, _persist):
        resp = _client.post(_URL, json={})
        assert resp.status_code == 200


# ===========================================================================
# /ingest — skipped (already populated)
# ===========================================================================
class TestIngestSkipped:
    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value=_skipped_result())
    def test_returns_skipped_status(self, _run, _persist):
        body = _client.post(_URL, json={"force": False}).json()
        assert body["status"] == "skipped"
        assert body["existing_chunks"] == 1200


# ===========================================================================
# /ingest — already running
# ===========================================================================
class TestIngestAlreadyRunning:
    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value=_already_running_result())
    def test_returns_already_running_status(self, _run, _persist):
        body = _client.post(_URL, json={"force": False}).json()
        assert body["status"] == "already_running"


# ===========================================================================
# /ingest — error paths
# ===========================================================================
class TestIngestErrors:
    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", side_effect=FileNotFoundError)
    def test_missing_data_dir_returns_404(self, _run, _persist):
        resp = _client.post(_URL, json={"force": False})
        assert resp.status_code == 404

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", side_effect=ValueError)
    def test_no_pdfs_returns_400(self, _run, _persist):
        resp = _client.post(_URL, json={"force": False})
        assert resp.status_code == 400

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", side_effect=RuntimeError("boom"))
    def test_unexpected_error_returns_500(self, _run, _persist):
        resp = _client.post(_URL, json={"force": False})
        assert resp.status_code == 500


# ===========================================================================
# _extract_metadata — filename parsing
# ===========================================================================
class TestExtractMetadata:
    def test_10k_detected_from_filename(self):
        meta = _extract_metadata("data/nvidia/10k_2024.pdf")
        assert meta["company"] == "nvidia"
        assert meta["year"] == 2024
        assert meta["doc_type"] == "10-K"
        assert meta["source_file"] == "10k_2024.pdf"

    def test_10q_detected_from_filename(self):
        meta = _extract_metadata("data/nvidia/10q_2024.pdf")
        assert meta["doc_type"] == "10-Q"

    def test_10q_hyphenated(self):
        meta = _extract_metadata("data/nvidia/10-Q_2024.pdf")
        assert meta["doc_type"] == "10-Q"

    def test_def14a_detected(self):
        meta = _extract_metadata("data/nvidia/def14a_2024.pdf")
        assert meta["doc_type"] == "DEF 14A"

    def test_def14a_with_separator(self):
        meta = _extract_metadata("data/nvidia/DEF_14A_2024.pdf")
        assert meta["doc_type"] == "DEF 14A"

    def test_unknown_doc_type_fallback(self):
        meta = _extract_metadata("data/nvidia/nvidia_2024.pdf")
        assert meta["doc_type"] == "Other"

    def test_google_2025(self):
        meta = _extract_metadata("data/google/10k_2025.pdf")
        assert meta["company"] == "google"
        assert meta["year"] == 2025

    def test_apple_2024(self):
        meta = _extract_metadata("data/apple/10k_2024.pdf")
        assert meta["company"] == "apple"
        assert meta["year"] == 2024

    def test_hyphenated_filename(self):
        meta = _extract_metadata("data/google/google-2024.pdf")
        assert meta["company"] == "google"
        assert meta["year"] == 2024

    def test_no_year_in_filename(self):
        meta = _extract_metadata("data/nvidia/quarterly_report.pdf")
        assert meta["year"] == 0

    def test_deeply_nested_path(self):
        meta = _extract_metadata("/a/b/c/apple/10k_2025.pdf")
        assert meta["company"] == "apple"
        assert meta["source_file"] == "10k_2025.pdf"


# ===========================================================================
# enrich_metadata — document enrichment
# ===========================================================================
class TestEnrichMetadata:
    def _make_doc(self, file_path: str):
        class FakeDoc:
            def __init__(self, fp):
                self.metadata = {"file_path": fp}
        return FakeDoc(file_path)

    def test_enriches_company_field(self):
        docs = [self._make_doc("data/nvidia/nvidia_2024.pdf")]
        result = enrich_metadata(docs)
        assert result[0].metadata["company"] == "nvidia"

    def test_enriches_year_field(self):
        docs = [self._make_doc("data/apple/apple_2025.pdf")]
        result = enrich_metadata(docs)
        assert result[0].metadata["year"] == 2025

    def test_enriches_multiple_docs(self):
        docs = [
            self._make_doc("data/nvidia/nvidia_2024.pdf"),
            self._make_doc("data/google/google_2025.pdf"),
        ]
        result = enrich_metadata(docs)
        assert result[0].metadata["company"] == "nvidia"
        assert result[1].metadata["company"] == "google"

    def test_empty_file_path_handled(self):
        docs = [self._make_doc("")]
        result = enrich_metadata(docs)
        assert result[0].metadata["company"] == ""
        assert result[0].metadata["year"] == 0
