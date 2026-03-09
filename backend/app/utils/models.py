"""
Centralized OpenAI / embedding model logic.
Used by rag_engine and indexer to avoid duplication.
"""

import logging

from ..config import settings

logger = logging.getLogger(__name__)

_EMBED_DIM = 1536  # text-embedding-3-small output dimensionality


def has_valid_openai_key() -> bool:
    """Return True only when the configured key looks like a real OpenAI key
    (starts with ``sk-``).  Rejects empty strings and placeholder values."""
    key = settings.OPENAI_API_KEY
    return bool(key and key.startswith("sk-"))


def get_embed_model():
    """Return OpenAI embedding model when key is valid, else MockEmbedding."""
    if has_valid_openai_key():
        try:
            from llama_index.embeddings.openai import OpenAIEmbedding

            return OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )
        except ImportError:
            logger.warning(
                "llama-index-embeddings-openai not installed — falling back to MockEmbedding"
            )
    else:
        logger.warning("Valid OPENAI_API_KEY not found — falling back to MockEmbedding")

    try:
        from llama_index.core.embeddings.mock_embed_model import MockEmbedding
    except ImportError:
        from llama_index.core import MockEmbedding  # type: ignore[attr-defined]

    return MockEmbedding(embed_dim=_EMBED_DIM)


def get_llm():
    """Return OpenAI LLM when key is valid, else MockLLM."""
    if has_valid_openai_key():
        try:
            from llama_index.llms.openai import OpenAI

            return OpenAI(
                model="gpt-4.1",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1,
            )
        except ImportError:
            logger.warning(
                "llama-index-llms-openai not installed — falling back to MockLLM"
            )
    else:
        logger.warning("Valid OPENAI_API_KEY not found — falling back to MockLLM")

    try:
        from llama_index.core.llms.mock import MockLLM
    except ImportError:
        from llama_index.core.llms import MockLLM  # type: ignore[attr-defined]

    return MockLLM(max_tokens=512)
