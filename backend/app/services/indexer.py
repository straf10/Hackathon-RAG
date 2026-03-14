import hashlib
import json
import logging
import re
import threading
from pathlib import Path

import tiktoken
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.schema import TextNode
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import PrivateAttr

from ..config import settings
from ..utils.chroma import COLLECTION_NAME, connect_chroma
from ..utils.models import get_embed_model
from .pdf_parser import load_pdf_documents

logger = logging.getLogger(__name__)

_FINGERPRINT_FILE = settings.APP_DATA_DIR / "corpus_fingerprint.json"

_ingest_lock = threading.Lock()


class ProgressReportingEmbedding(BaseEmbedding):
    """Transparent wrapper that reports embedding progress to a shared dict.

    Delegates every embedding call to the wrapped model while updating
    ``status["progress_pct"]`` after each batch.  Progress is capped at
    ``max_pct`` (default 95%) so the caller can reserve the last slice
    for post-embedding work (index save, fingerprint write, etc.).
    """

    _inner: BaseEmbedding = PrivateAttr()
    _status: dict = PrivateAttr()
    _total: int = PrivateAttr()
    _processed: int = PrivateAttr(default=0)
    _max_pct: float = PrivateAttr(default=95.0)

    def __init__(
        self,
        inner: BaseEmbedding,
        status: dict,
        total_chunks: int,
        max_pct: float = 95.0,
        **kwargs,
    ):
        super().__init__(
            model_name=getattr(inner, "model_name", "progress-wrapper"),
            embed_batch_size=inner.embed_batch_size,
            callback_manager=inner.callback_manager,
            **kwargs,
        )
        self._inner = inner
        self._status = status
        self._total = max(total_chunks, 1)
        self._processed = 0
        self._max_pct = max_pct

    def _update_progress(self, n: int = 1) -> None:
        self._processed += n
        raw = (self._processed / self._total) * self._max_pct
        self._status["progress_pct"] = min(round(raw, 1), self._max_pct)

    def _get_text_embedding(self, text: str) -> list[float]:
        result = self._inner._get_text_embedding(text)
        self._update_progress(1)
        return result

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        results = self._inner._get_text_embeddings(texts)
        self._update_progress(len(texts))
        return results

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._inner._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        result = await self._inner._aget_text_embedding(text)
        self._update_progress(1)
        return result

    async def _aget_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        results = await self._inner._aget_text_embeddings(texts)
        self._update_progress(len(texts))
        return results

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return await self._inner._aget_query_embedding(query)


def _compute_corpus_fingerprint(data_dir: Path) -> str:
    """MD5 of the sorted (relative-path, size) list of PDFs in *data_dir*."""
    files = sorted(data_dir.glob("**/*.pdf"))
    entries = [(str(f.relative_to(data_dir)), f.stat().st_size) for f in files]
    return hashlib.md5(json.dumps(entries).encode()).hexdigest()


def _load_stored_fingerprint() -> str | None:
    try:
        return json.loads(_FINGERPRINT_FILE.read_text()).get("fingerprint")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _save_fingerprint(fingerprint: str) -> None:
    _FINGERPRINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    _FINGERPRINT_FILE.write_text(json.dumps({"fingerprint": fingerprint}))


_DOC_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"10[\-_]?k", re.IGNORECASE), "10-K"),
    (re.compile(r"10[\-_]?q", re.IGNORECASE), "10-Q"),
    (re.compile(r"def[\-_\s]?14[\-_\s]?a", re.IGNORECASE), "DEF 14A"),
]


def _detect_doc_type(file_path: str) -> str:
    """Infer SEC filing type from the file path via regex.

    Falls back to ``"Other"`` when no known pattern matches.
    """
    for pattern, label in _DOC_TYPE_PATTERNS:
        if pattern.search(file_path):
            return label
    return "Other"


def _extract_metadata(file_path: str) -> dict:
    p = Path(file_path)
    company = p.parent.name
    year_match = re.search(r"(\d{4})", p.stem)
    return {
        "company": company,
        "year": int(year_match.group(1)) if year_match else 0,
        "doc_type": _detect_doc_type(file_path),
        "source_file": p.name,
    }


def enrich_metadata(documents: list) -> list:
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        doc.metadata.update(_extract_metadata(file_path))
    return documents


_MAX_EMBED_TOKENS = 8191

try:
    _enc = tiktoken.encoding_for_model("text-embedding-3-small")
except KeyError:
    _enc = tiktoken.get_encoding("cl100k_base")


def _truncate_to_token_limit(text: str, max_tokens: int = _MAX_EMBED_TOKENS) -> str:
    """Return *text* truncated so it fits within *max_tokens*."""
    tokens = _enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return _enc.decode(tokens[:max_tokens])


def _documents_to_page_nodes(documents: list) -> list[TextNode]:
    """Convert each Document (one per PDF page) into a single TextNode.

    Preserves all metadata and truncates text that exceeds the
    embedding model's token limit (8 191 tokens for text-embedding-3-small).
    """
    nodes: list[TextNode] = []
    for doc in documents:
        text = _truncate_to_token_limit(doc.text)
        node = TextNode(text=text, metadata=dict(doc.metadata))
        nodes.append(node)
    return nodes


def run_ingestion(force: bool = False, status: dict | None = None) -> dict:
    if status is None:
        status = {}
    if not _ingest_lock.acquire(blocking=False):
        logger.warning("Ingestion already in progress — skipping concurrent request")
        return {
            "status": "already_running",
            "documents_loaded": 0,
            "chunks_created": 0,
            "existing_chunks": 0,
            "collection": COLLECTION_NAME,
        }
    try:
        return _run_ingestion_locked(force, status)
    finally:
        _ingest_lock.release()


def _run_ingestion_locked(force: bool, status: dict) -> dict:
    chroma_collection, client = connect_chroma(
        settings.CHROMA_HOST, settings.CHROMA_PORT, COLLECTION_NAME,
    )
    existing_count = chroma_collection.count()

    current_fp = _compute_corpus_fingerprint(settings.DATA_DIR)
    stored_fp = _load_stored_fingerprint()
    if existing_count > 0 and not force and current_fp != stored_fp:
        logger.info(
            "Corpus fingerprint changed (%s → %s) — auto-forcing re-ingestion",
            stored_fp, current_fp,
        )
        force = True

    if existing_count > 0 and not force:
        logger.info(
            "Collection '%s' already contains %d chunks — skipping ingestion "
            "(use force=True to re-ingest)",
            COLLECTION_NAME, existing_count,
        )
        return {
            "status": "skipped",
            "documents_loaded": 0,
            "chunks_created": 0,
            "existing_chunks": existing_count,
            "collection": COLLECTION_NAME,
        }

    if existing_count > 0 and force:
        logger.info("Force re-ingest: deleting existing collection '%s'", COLLECTION_NAME)
        client.delete_collection(COLLECTION_NAME)
        chroma_collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    logger.info("Loading PDF documents from %s", settings.DATA_DIR)
    documents = load_pdf_documents(settings.DATA_DIR)

    documents = enrich_metadata(documents)
    logger.info("Metadata enriched for %d documents", len(documents))

    nodes = _documents_to_page_nodes(documents)
    logger.info("Created %d page nodes from %d documents", len(nodes), len(documents))

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    embed_model = get_embed_model()

    progress_model = ProgressReportingEmbedding(
        inner=embed_model,
        status=status,
        total_chunks=len(nodes),
    )

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=progress_model,
    )

    _save_fingerprint(current_fp)
    status["progress_pct"] = 100

    result = {
        "status": "ok",
        "documents_loaded": len(documents),
        "chunks_created": len(nodes),
        "collection": COLLECTION_NAME,
    }
    logger.info("Ingestion complete: %s", result)
    return result
