import logging
import re
import time
from pathlib import Path

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore

from ..config import settings
from ..utils.models import get_embed_model
from .pdf_parser import load_pdf_documents

logger = logging.getLogger(__name__)

COLLECTION_NAME = "financial_10k"
_CHROMA_MAX_RETRIES = 5
_CHROMA_RETRY_DELAY = 3


def _connect_chroma(
    host: str, port: int, collection_name: str
) -> tuple[chromadb.Collection, chromadb.ClientAPI]:
    """Connect to ChromaDB with retry logic for startup race conditions."""
    last_exc: Exception | None = None
    for attempt in range(1, _CHROMA_MAX_RETRIES + 1):
        try:
            client = chromadb.HttpClient(host=host, port=port)
            collection = client.get_or_create_collection(collection_name)
            logger.info(
                "ChromaDB connected at %s:%s (attempt %d, collection=%s, count=%d)",
                host, port, attempt, collection_name, collection.count(),
            )
            return collection, client
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "ChromaDB connection attempt %d/%d failed (%s:%s): %s — retrying in %ds",
                attempt, _CHROMA_MAX_RETRIES, host, port, exc, _CHROMA_RETRY_DELAY,
            )
            if attempt < _CHROMA_MAX_RETRIES:
                time.sleep(_CHROMA_RETRY_DELAY)

    raise ConnectionError(
        f"ChromaDB at {host}:{port} unreachable after {_CHROMA_MAX_RETRIES} attempts"
    ) from last_exc


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
    chroma_collection, _ = _connect_chroma(
        settings.CHROMA_HOST, settings.CHROMA_PORT, COLLECTION_NAME,
    )
    existing_count = chroma_collection.count()

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
        client = chromadb.HttpClient(
            host=settings.CHROMA_HOST, port=settings.CHROMA_PORT,
        )
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
