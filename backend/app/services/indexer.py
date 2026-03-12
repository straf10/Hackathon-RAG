import hashlib
import json
import logging
import re
import threading
from pathlib import Path

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore

from ..config import settings
from ..utils.chroma import COLLECTION_NAME, connect_chroma
from ..utils.models import get_embed_model
from .pdf_parser import load_pdf_documents

logger = logging.getLogger(__name__)

_FINGERPRINT_FILE = settings.FEEDBACK_DB_DIR / "corpus_fingerprint.json"

_ingest_lock = threading.Lock()


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


def _extract_metadata(file_path: str) -> dict:
    p = Path(file_path)
    company = p.parent.name
    year_match = re.search(r"(\d{4})", p.stem)
    return {
        "company": company,
        "year": int(year_match.group(1)) if year_match else 0,
        "doc_type": "10-K",
        "source_file": p.name,
    }


def enrich_metadata(documents: list) -> list:
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        doc.metadata.update(_extract_metadata(file_path))
    return documents


def run_ingestion(force: bool = False) -> dict:
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
        return _run_ingestion_locked(force)
    finally:
        _ingest_lock.release()


def _run_ingestion_locked(force: bool) -> dict:
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
        chroma_collection = client.get_or_create_collection(COLLECTION_NAME)

    logger.info("Loading PDF documents from %s", settings.DATA_DIR)
    documents = load_pdf_documents(settings.DATA_DIR)

    documents = enrich_metadata(documents)
    logger.info("Metadata enriched for %d documents", len(documents))

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
    nodes = splitter.get_nodes_from_documents(documents)
    logger.info("Created %d chunks from %d documents", len(nodes), len(documents))

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    embed_model = get_embed_model()

    VectorStoreIndex(
        nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    _save_fingerprint(current_fp)

    result = {
        "status": "ok",
        "documents_loaded": len(documents),
        "chunks_created": len(nodes),
        "collection": COLLECTION_NAME,
    }
    logger.info("Ingestion complete: %s", result)
    return result


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    run_ingestion()
