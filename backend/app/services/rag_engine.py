"""
RAG Engine — LlamaIndex retrieval-augmented generation pipeline for
financial 10-K filings stored in ChromaDB.

Falls back to MockLLM / MockEmbedding when no OPENAI_API_KEY is set so the
module remains importable and runnable without credentials.
"""

import logging

import chromadb.errors
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.question_gen import LLMQuestionGenerator
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.vector_stores import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)
from llama_index.vector_stores.chroma import ChromaVectorStore

from ..config import settings
from ..utils.chroma import COLLECTION_NAME, connect_chroma
from ..utils.models import get_embed_model, get_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------


class RAGEngine:
    """High-level interface for querying the financial 10-K vector store."""

    def __init__(
        self,
        chroma_host: str = settings.CHROMA_HOST,
        chroma_port: int = settings.CHROMA_PORT,
        collection_name: str = COLLECTION_NAME,
    ):
        self.llm = get_llm()
        self.embed_model = get_embed_model()
        self.collection_name = collection_name
        self._chroma_host = chroma_host
        self._chroma_port = chroma_port
        self._index = self._connect(chroma_host, chroma_port)
        logger.info("RAGEngine initialised (collection=%s)", collection_name)

    # -- ChromaDB connection ------------------------------------------------

    def _connect(self, host: str, port: int) -> VectorStoreIndex:
        """Connect to ChromaDB and wrap the collection in a
        ``VectorStoreIndex``."""
        collection, _client = connect_chroma(host, port, self.collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        return VectorStoreIndex.from_vector_store(
            vector_store,
            embed_model=self.embed_model,
        )

    def _reconnect(self) -> None:
        """Re-establish the ChromaDB connection (e.g. after force re-ingest
        deleted and recreated the collection)."""
        logger.info("Reconnecting to ChromaDB (collection may have been recreated)")
        self._index = self._connect(self._chroma_host, self._chroma_port)

    # -- metadata filtering -------------------------------------------------

    @staticmethod
    def _build_filters(
        companies: list[str] | None = None,
        years: list[int] | None = None,
    ) -> MetadataFilters | None:
        """Construct metadata filters.

        When both ``companies`` and ``years`` are provided the resulting
        filter is: ``company IN [...]  AND  year IN [...]``.
        """
        conditions: list[MetadataFilter] = []

        if companies:
            conditions.append(
                MetadataFilter(
                    key="company",
                    value=[c.lower() for c in companies],
                    operator=FilterOperator.IN,
                )
            )
        if years:
            conditions.append(
                MetadataFilter(
                    key="year",
                    value=years,
                    operator=FilterOperator.IN,
                )
            )

        if not conditions:
            return None

        return MetadataFilters(
            filters=conditions,
            condition=FilterCondition.AND,
        )

    # -- query engines ------------------------------------------------------

    def _get_query_engine(
        self,
        filters: MetadataFilters | None = None,
        similarity_top_k: int = 5,
    ):
        """Build a standard single-step query engine with optional
        metadata pre-filtering."""
        kwargs: dict = {
            "llm": self.llm,
            "similarity_top_k": similarity_top_k,
        }
        if filters is not None:
            kwargs["filters"] = filters
        return self._index.as_query_engine(**kwargs)

    def _get_sub_question_engine(
        self,
        filters: MetadataFilters | None = None,
        similarity_top_k: int = 5,
    ):
        """``SubQuestionQueryEngine`` decomposes a complex question into
        simpler sub-questions, runs each against the base engine, and merges
        the answers.  Best for comparison queries such as
        *"Compare NVIDIA revenue 2024 vs 2025"*."""
        base_engine = self._get_query_engine(
            filters=filters,
            similarity_top_k=similarity_top_k,
        )
        tool = QueryEngineTool(
            query_engine=base_engine,
            metadata=ToolMetadata(
                name="financial_10k_filings",
                description=(
                    "10-K annual report data for NVIDIA, Google/Alphabet, "
                    "and Apple for fiscal years 2024–2025.  Covers revenue, "
                    "expenses, net income, risk factors, and other financial "
                    "metrics."
                ),
            ),
        )
        question_gen = LLMQuestionGenerator.from_defaults(llm=self.llm)
        return SubQuestionQueryEngine.from_defaults(
            query_engine_tools=[tool],
            llm=self.llm,
            question_gen=question_gen,
        )

    # -- public API ---------------------------------------------------------

    def query(
        self,
        question: str,
        companies: list[str] | None = None,
        years: list[int] | None = None,
        use_sub_questions: bool = True,
        similarity_top_k: int = 5,
    ) -> dict:
        """Run a RAG query against the financial 10-K vector store.

        Parameters
        ----------
        question:
            Natural-language question.
        companies:
            Optional filter — e.g. ``["nvidia", "apple"]``.
        years:
            Optional filter — e.g. ``[2024, 2025]``.
        use_sub_questions:
            Use ``SubQuestionQueryEngine`` for multi-step reasoning.
        similarity_top_k:
            Number of chunks to retrieve.

        Returns
        -------
        dict
            ``{"answer": str, "source_nodes": [{"filename", "page_label",
            "score", "text_snippet"}, ...]}``
        """
        logger.info(
            "Query: %r | companies=%s years=%s sub_q=%s top_k=%d",
            question,
            companies,
            years,
            use_sub_questions,
            similarity_top_k,
        )

        metadata_filters = self._build_filters(companies, years)

        try:
            return self._execute_query(
                question, metadata_filters, use_sub_questions, similarity_top_k,
            )
        except chromadb.errors.NotFoundError:
            self._reconnect()
            return self._execute_query(
                question, metadata_filters, use_sub_questions, similarity_top_k,
            )

    def _execute_query(
        self,
        question: str,
        metadata_filters: MetadataFilters | None,
        use_sub_questions: bool,
        similarity_top_k: int,
    ) -> dict:
        """Run the query against the current index, with optional
        sub-question decomposition and fallback to standard engine."""
        if use_sub_questions:
            try:
                engine = self._get_sub_question_engine(
                    filters=metadata_filters,
                    similarity_top_k=similarity_top_k,
                )
                response = engine.query(question)
                return self._format_response(response)
            except chromadb.errors.NotFoundError:
                raise
            except Exception:
                logger.warning(
                    "SubQuestionQueryEngine failed (MockLLM cannot produce "
                    "structured output) — falling back to standard engine",
                    exc_info=True,
                )

        engine = self._get_query_engine(
            filters=metadata_filters,
            similarity_top_k=similarity_top_k,
        )
        response = engine.query(question)
        return self._format_response(response)

    # -- response formatting ------------------------------------------------

    @staticmethod
    def _format_response(response) -> dict:
        """Extract the answer string and source-node metadata into a
        serialisable dict suitable for API responses."""
        source_nodes: list[dict] = []
        for node in getattr(response, "source_nodes", []):
            meta = node.metadata or {}
            has_file = bool(
                meta.get("source_file") or meta.get("file_name")
            )
            text = (node.text or "")[:500]
            is_sub_q = (
                not has_file
                and text.lower().startswith("sub question:")
            )

            source_nodes.append(
                {
                    "filename": meta.get(
                        "source_file", meta.get("file_name", "unknown")
                    ),
                    "page_label": meta.get(
                        "page_label", str(meta.get("page", "N/A"))
                    ),
                    "score": (
                        round(node.score, 4) if node.score is not None else None
                    ),
                    "text_snippet": text,
                    "source_type": "sub_question" if is_sub_q else "document",
                }
            )

        return {
            "answer": str(response),
            "source_nodes": source_nodes,
        }
