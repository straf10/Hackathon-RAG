import logging
import os
from collections import defaultdict
from pathlib import Path

import tiktoken
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PyMuPDFReader

logger = logging.getLogger(__name__)

# Local: resolve relative to project root; Docker: /app/data via env var
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[3] / "data"))


def load_pdf_documents(data_dir: Path = DATA_DIR) -> list:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    pdf_files = sorted(data_dir.glob("**/*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in {data_dir}")

    logger.info("Found %d PDF file(s) in %s", len(pdf_files), data_dir)
    for f in pdf_files:
        logger.info("  -> %s", f.name)

    file_extractor = {".pdf": PyMuPDFReader()}

    all_documents = []
    success_count = 0
    failed_files = []

    for pdf_path in pdf_files:
        try:
            reader = SimpleDirectoryReader(
                input_files=[str(pdf_path)],
                file_extractor=file_extractor,
            )
            docs = reader.load_data()
            all_documents.extend(docs)
            success_count += 1
            logger.info(
                "OK  | %-30s | %d document(s)", pdf_path.name, len(docs)
            )
        except Exception:
            failed_files.append(pdf_path.name)
            logger.exception("FAIL | %s", pdf_path.name)

    logger.info("=" * 60)
    logger.info("Files processed : %d / %d", success_count, len(pdf_files))
    logger.info("Total documents : %d", len(all_documents))
    if failed_files:
        logger.warning("Failed files    : %s", ", ".join(failed_files))

    return all_documents


def count_tokens(documents: list, model: str = "text-embedding-3-small") -> dict:
    encoding = tiktoken.encoding_for_model(model)
    per_file: dict[str, int] = defaultdict(int)

    for doc in documents:
        filename = doc.metadata.get("file_name", "unknown")
        per_file[filename] += len(encoding.encode(doc.text))

    total = sum(per_file.values())
    cost_estimate = total / 1_000_000 * 0.02

    logger.info("=" * 60)
    logger.info("Token count (model: %s)", model)
    for filename, count in sorted(per_file.items()):
        logger.info("  %-30s %8d tokens", filename, count)
    logger.info("-" * 60)
    logger.info("  %-30s %8d tokens", "TOTAL", total)
    logger.info("  Estimated embedding cost: $%.4f", cost_estimate)

    return {"per_file": dict(per_file), "total": total, "cost_estimate": cost_estimate}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )
    documents = load_pdf_documents()
    count_tokens(documents)
