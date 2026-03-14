"""Tests for RAGEngine internals: response formatting.

These tests exercise static/class methods that do not require a live
ChromaDB or OpenAI connection.
"""

from unittest.mock import MagicMock

from app.services.rag_engine import RAGEngine


# ===========================================================================
# _format_response
# ===========================================================================
class TestFormatResponse:
    def _make_node(self, metadata=None, text="Sample text", score=0.85):
        node = MagicMock()
        node.metadata = metadata or {}
        node.text = text
        node.score = score
        return node

    def test_empty_response(self):
        resp = MagicMock()
        resp.source_nodes = []
        resp.__str__ = lambda self: "No info"
        result = RAGEngine._format_response(resp)
        assert result["answer"] == "No info"
        assert result["source_nodes"] == []

    def test_single_document_source(self):
        node = self._make_node(
            metadata={"source_file": "nvidia_2024.pdf", "page_label": "42"},
        )
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Revenue was $26.9B"
        result = RAGEngine._format_response(resp)
        assert len(result["source_nodes"]) == 1
        assert result["source_nodes"][0]["filename"] == "nvidia_2024.pdf"
        assert result["source_nodes"][0]["source_type"] == "document"

    def test_sub_question_detected(self):
        node = self._make_node(
            metadata={},
            text="Sub question: What was revenue? Revenue was $26.9B",
        )
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["source_type"] == "sub_question"

    def test_text_truncated_at_500_chars(self):
        node = self._make_node(
            metadata={"source_file": "f.pdf"},
            text="x" * 1000,
        )
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert len(result["source_nodes"][0]["text_snippet"]) == 500

    def test_none_score_preserved(self):
        node = self._make_node(score=None)
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["score"] is None

    def test_score_rounded_to_4_decimals(self):
        node = self._make_node(score=0.123456789)
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["score"] == 0.1235

    def test_fallback_to_file_name_key(self):
        node = self._make_node(metadata={"file_name": "apple_2024.pdf"})
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["filename"] == "apple_2024.pdf"

    def test_unknown_filename_when_no_metadata(self):
        node = self._make_node(metadata={})
        node.text = "Regular document text"
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["filename"] == "unknown"

    def test_page_label_from_page_key(self):
        node = self._make_node(metadata={"source_file": "f.pdf", "page": 7})
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["page_label"] == "7"

    def test_page_label_from_source_key(self):
        """PyMuPDFReader stores page number in 'source'; ensure we use it."""
        node = self._make_node(
            metadata={"source_file": "nvidia_2024.pdf", "source": "42"},
        )
        resp = MagicMock()
        resp.source_nodes = [node]
        resp.__str__ = lambda self: "Answer"
        result = RAGEngine._format_response(resp)
        assert result["source_nodes"][0]["page_label"] == "42"

    def test_no_source_nodes_attribute(self):
        class BareResponse:
            def __str__(self):
                return "Answer"
        result = RAGEngine._format_response(BareResponse())
        assert result["source_nodes"] == []
