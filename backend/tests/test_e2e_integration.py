"""End-to-end integration tests.

Flow: load real PDFs from data/ -> enrich metadata -> chunk -> mock-embed ->
hit /ingest (mocked) -> hit /query (mocked engine) -> validate full response
structure against the API contract in Project_Specification.md.

Also exercises the real PDF parser + metadata pipeline against the actual
10-K corpus on disk.

Requires: the ``data/`` directory with at least one PDF present.
"""

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.indexer import (
    _documents_to_page_nodes,
    _extract_metadata,
    enrich_metadata,
)
from app.services.pdf_parser import load_pdf_documents

_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_HAS_PDFS = _DATA_DIR.exists() and any(_DATA_DIR.glob("**/*.pdf"))

_client = TestClient(app, raise_server_exceptions=False)

_GOOD_USAGE = {"budget_remaining_usd": 5.0}


def _full_engine_result():
    return {
        "answer": "NVIDIA reported total revenue of $130.5 billion for fiscal year 2025.",
        "source_nodes": [
            {
                "filename": "nvidia_2025.pdf",
                "page_label": "45",
                "score": 0.9321,
                "text_snippet": "Total revenue for the fiscal year ended January 26, 2025 was $130.5 billion.",
                "source_type": "document",
            },
            {
                "filename": "nvidia_2025.pdf",
                "page_label": "46",
                "score": 0.8712,
                "text_snippet": "Revenue increased 114% compared to fiscal 2024.",
                "source_type": "document",
            },
        ],
    }


# ===========================================================================
# E2E: Real PDF loading from data/
# ===========================================================================
@pytest.mark.skipif(not _HAS_PDFS, reason="data/ directory with PDFs not found")
class TestRealPdfLoading:
    """Verify load_pdf_documents works against the actual 10-K corpus."""

    def test_loads_at_least_one_document(self):
        docs = load_pdf_documents(_DATA_DIR)
        assert len(docs) > 0

    def test_each_doc_has_text(self):
        docs = load_pdf_documents(_DATA_DIR)
        for doc in docs[:10]:
            assert hasattr(doc, "text")
            assert len(doc.text) > 0

    def test_each_doc_has_metadata(self):
        docs = load_pdf_documents(_DATA_DIR)
        for doc in docs[:10]:
            assert hasattr(doc, "metadata")
            assert isinstance(doc.metadata, dict)

    def test_file_path_in_metadata(self):
        docs = load_pdf_documents(_DATA_DIR)
        for doc in docs[:10]:
            fp = doc.metadata.get("file_path", "")
            assert fp.endswith(".pdf") or doc.metadata.get("file_name", "").endswith(".pdf")


# ===========================================================================
# E2E: Metadata enrichment on real documents
# ===========================================================================
@pytest.mark.skipif(not _HAS_PDFS, reason="data/ directory with PDFs not found")
class TestRealMetadataEnrichment:
    """Load real docs, enrich, and verify extracted metadata fields."""

    @pytest.fixture(scope="class")
    def enriched_docs(self):
        docs = load_pdf_documents(_DATA_DIR)
        return enrich_metadata(docs)

    def test_company_extracted(self, enriched_docs):
        companies_found = {d.metadata["company"] for d in enriched_docs}
        assert len(companies_found) >= 1
        for c in companies_found:
            assert c in ("nvidia", "google", "apple", "microsoft", "tesla")

    def test_year_extracted(self, enriched_docs):
        years_found = {d.metadata["year"] for d in enriched_docs}
        assert years_found.issubset({2023, 2024, 2025})

    def test_doc_type_is_10k(self, enriched_docs):
        for doc in enriched_docs[:20]:
            assert doc.metadata["doc_type"] == "10-K"

    def test_source_file_populated(self, enriched_docs):
        for doc in enriched_docs[:20]:
            assert doc.metadata["source_file"].endswith(".pdf")


# ===========================================================================
# E2E: Chunking pipeline
# ===========================================================================
@pytest.mark.skipif(not _HAS_PDFS, reason="data/ directory with PDFs not found")
class TestRealPageIndexing:
    """Verify one-node-per-page indexing from real documents."""

    @pytest.fixture(scope="class")
    def docs_and_nodes(self):
        docs = load_pdf_documents(_DATA_DIR)
        docs = enrich_metadata(docs)
        nodes = _documents_to_page_nodes(docs)
        return docs, nodes

    def test_one_node_per_page(self, docs_and_nodes):
        docs, nodes = docs_and_nodes
        assert len(nodes) == len(docs)

    def test_nodes_have_text(self, docs_and_nodes):
        _docs, nodes = docs_and_nodes
        for node in nodes[:20]:
            assert len(node.text) > 0

    def test_nodes_inherit_metadata(self, docs_and_nodes):
        _docs, nodes = docs_and_nodes
        for node in nodes[:20]:
            assert "company" in node.metadata
            assert "year" in node.metadata


# ===========================================================================
# E2E: Full /ingest -> /query flow (mocked externals)
# ===========================================================================
class TestFullApiFlow:
    """Simulate the complete user journey through the API.

    External dependencies (ChromaDB, OpenAI) are mocked.  The test validates
    that every response conforms to the API contract from the spec.
    """

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion")
    def test_ingest_then_query(self, mock_ingest, _persist):
        mock_ingest.return_value = {
            "status": "ok",
            "documents_loaded": 6,
            "chunks_created": 796,
            "existing_chunks": 0,
            "collection": "financial_10k",
        }

        # Step 1: Ingest
        resp = _client.post("/ingest", json={"force": True})
        assert resp.status_code == 200
        ingest_body = resp.json()
        assert ingest_body["status"] == "ok"
        assert ingest_body["documents_processed"] == 6
        assert ingest_body["chunks_created"] == 796
        assert "existing_chunks" in ingest_body

        # Step 2: Query
        with (
            patch("app.routers.query.has_valid_openai_key", return_value=True),
            patch("app.routers.query.get_usage", return_value=_GOOD_USAGE),
            patch("app.routers.query.get_engine") as mock_eng,
            patch("app.routers.query.persist_usage"),
        ):
            engine = MagicMock()
            engine.query.return_value = _full_engine_result()
            mock_eng.return_value = engine

            resp = _client.post(
                "/query",
                json={
                    "question": "What was NVIDIA total revenue in 2025?",
                    "use_sub_questions": True,
                },
            )
        assert resp.status_code == 200
        query_body = resp.json()

        # Validate QueryResponse contract
        assert isinstance(query_body["answer"], str)
        assert len(query_body["answer"]) > 0
        assert isinstance(query_body["sources"], list)
        assert len(query_body["sources"]) == 2
        assert isinstance(query_body["query_id"], str)
        uuid.UUID(query_body["query_id"])

        # Validate each SourceDocument
        for src in query_body["sources"]:
            assert isinstance(src["filename"], str)
            assert isinstance(src["page"], int)
            assert isinstance(src["score"], float)
            assert isinstance(src["text_snippet"], str)
            assert src["source_type"] in ("document", "sub_question")


# ===========================================================================
# E2E: Response structure matches API contract
# ===========================================================================
class TestResponseContractCompliance:
    """Verify every endpoint returns exactly the fields defined in the
    Project_Specification.md API contract (section 6.1)."""

    def test_health_contract(self):
        body = _client.get("/health").json()
        assert set(body.keys()) == {"status"}

    def test_root_contract(self):
        body = _client.get("/").json()
        assert "message" in body

    @patch("app.routers.query.has_valid_openai_key", return_value=False)
    def test_query_response_contract(self, _k):
        body = _client.post("/query", json={"question": "Q"}).json()
        assert set(body.keys()) == {"answer", "sources", "query_id"}
        assert isinstance(body["answer"], str)
        assert isinstance(body["sources"], list)
        assert isinstance(body["query_id"], str)

    @patch("app.routers.ingest.persist_usage")
    @patch("app.routers.ingest.run_ingestion", return_value={
        "status": "ok", "documents_loaded": 0, "chunks_created": 0,
        "existing_chunks": 0, "collection": "financial_10k",
    })
    def test_ingest_response_contract(self, _run, _persist):
        body = _client.post("/ingest").json()
        required = {"status", "documents_processed", "chunks_created", "existing_chunks"}
        assert required.issubset(set(body.keys()))

    def test_usage_contract(self):
        body = _client.get("/usage").json()
        required = {
            "llm_prompt_tokens", "llm_completion_tokens", "llm_total_tokens",
            "embedding_tokens", "estimated_cost_usd",
            "budget_total_usd", "budget_remaining_usd",
        }
        assert required.issubset(set(body.keys()))


# ===========================================================================
# E2E: Metadata extraction covers all 6 corpus files
# ===========================================================================
class TestCorpusMetadataExtraction:
    """Verify _extract_metadata handles every filename pattern in data/."""

    _CORPUS = [
        ("data/nvidia/10k_2023.pdf", "nvidia", 2023, "10-K"),
        ("data/nvidia/10k_2024.pdf", "nvidia", 2024, "10-K"),
        ("data/nvidia/10k_2025.pdf", "nvidia", 2025, "10-K"),
        ("data/google/10k_2023.pdf", "google", 2023, "10-K"),
        ("data/google/10k_2024.pdf", "google", 2024, "10-K"),
        ("data/google/10k_2025.pdf", "google", 2025, "10-K"),
        ("data/apple/10k_2023.pdf", "apple", 2023, "10-K"),
        ("data/apple/10k_2024.pdf", "apple", 2024, "10-K"),
        ("data/apple/10k_2025.pdf", "apple", 2025, "10-K"),
        ("data/microsoft/10k_2023.pdf", "microsoft", 2023, "10-K"),
        ("data/microsoft/10k_2024.pdf", "microsoft", 2024, "10-K"),
        ("data/microsoft/10k_2025.pdf", "microsoft", 2025, "10-K"),
        ("data/tesla/10k_2023.pdf", "tesla", 2023, "10-K"),
        ("data/tesla/10k_2024.pdf", "tesla", 2024, "10-K"),
        ("data/tesla/10k_2025.pdf", "tesla", 2025, "10-K"),
    ]

    @pytest.mark.parametrize("path,company,year,doc_type", _CORPUS)
    def test_extracts_correct_metadata(self, path, company, year, doc_type):
        meta = _extract_metadata(path)
        assert meta["company"] == company
        assert meta["year"] == year
        assert meta["doc_type"] == doc_type
        assert meta["source_file"].endswith(".pdf")
