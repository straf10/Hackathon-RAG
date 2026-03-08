import logging
import os
import sys
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PyMuPDFReader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Local: resolve relative to project root; Docker: /app/data via env var
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parents[3] / "data"))


def load_pdf_documents(data_dir: Path = DATA_DIR) -> list:
    if not data_dir.exists():
        logger.error("Data directory not found: %s", data_dir)
        sys.exit(1)

    pdf_files = sorted(data_dir.glob("**/*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in %s", data_dir)
        sys.exit(1)

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


if __name__ == "__main__":
    documents = load_pdf_documents()
