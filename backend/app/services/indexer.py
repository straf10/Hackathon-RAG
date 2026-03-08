import logging
import re
from pathlib import Path

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from ..config import settings
from .pdf_parser import load_pdf_documents

logger = logging.getLogger(__name__)

COLLECTION_NAME = "financial_10k"


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


def run_ingestion() -> dict:
    logger.info("Loading PDF documents from %s", settings.DATA_DIR)
    documents = load_pdf_documents(settings.DATA_DIR)

    documents = enrich_metadata(documents)
    logger.info("Metadata enriched for %d documents", len(documents))

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
    nodes = splitter.get_nodes_from_documents(documents)
    logger.info("Created %d chunks from %d documents", len(nodes), len(documents))

    chroma_client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )
    chroma_collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY,
    )

    index = VectorStoreIndex(
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
