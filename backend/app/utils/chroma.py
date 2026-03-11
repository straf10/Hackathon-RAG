"""Shared ChromaDB connection logic with retry handling."""

import logging
import time

import chromadb

logger = logging.getLogger(__name__)

COLLECTION_NAME = "financial_10k"
_CHROMA_MAX_RETRIES = 5
_CHROMA_RETRY_DELAY = 3


def connect_chroma(
    host: str, port: int, collection_name: str = COLLECTION_NAME,
) -> tuple[chromadb.Collection, chromadb.ClientAPI]:
    """Connect to ChromaDB over HTTP with retry logic.

    Returns the ``(collection, client)`` tuple.  Raises ``ConnectionError``
    when the server is unreachable after all retries.
    """
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
