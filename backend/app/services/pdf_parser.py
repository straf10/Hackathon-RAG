import logging
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PyMuPDFReader

from ..config import settings

logger = logging.getLogger(__name__)

_FILE_EXTRACTOR = {".pdf": PyMuPDFReader()}


def load_pdf_documents(data_dir: Path = settings.DATA_DIR) -> list:
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    pdf_files = sorted(data_dir.glob("**/*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in {data_dir}")

    logger.info("Found %d PDF file(s) in %s", len(pdf_files), data_dir)
    for f in pdf_files:
        logger.info("  -> %s", f.name)

    all_documents = []
    success_count = 0
    failed_files = []

    for pdf_path in pdf_files:
        try:
            reader = SimpleDirectoryReader(
                input_files=[str(pdf_path)],
                file_extractor=_FILE_EXTRACTOR,
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
