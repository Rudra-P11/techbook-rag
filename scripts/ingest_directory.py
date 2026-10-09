import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_cli")


def main():
    import requests

    parser = argparse.ArgumentParser(description="Batch ingest technical PDF books into TechBook RAG.")
    parser.add_argument(
        "--dir",
        type=str,
        default="./Corpus",
        help="Directory containing PDF books to ingest (default: ./Corpus)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-indexing of already indexed files"
    )
    args = parser.parse_args()

    target_dir = settings.get_absolute_path(args.dir)
    if not target_dir.exists():
        logger.error(f"Target directory does not exist: {target_dir}")
        return

    pdf_files = list(target_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {target_dir}")
        return

    # Check if API server is running
    api_available = False
    api_base_url = f"http://127.0.0.1:{settings.APP_PORT}"
    try:
        r = requests.get(f"{api_base_url}/health", timeout=2)
        if r.status_code == 200:
            api_available = True
            logger.info(f"Detected running FastAPI server at {api_base_url}. Routing uploads through API.")
    except Exception:
        api_available = False

    logger.info(f"Found {len(pdf_files)} PDF files in {target_dir}. Starting batch ingestion...")

    total = len(pdf_files)
    successful = 0
    for idx, pdf in enumerate(pdf_files, start=1):
        logger.info(f"[{idx}/{total}] Ingesting: {pdf.name}")
        try:
            if api_available:
                with open(pdf, "rb") as f:
                    resp = requests.post(
                        f"{api_base_url}/api/v1/documents",
                        files={"file": (pdf.name, f, "application/pdf")},
                        timeout=120
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info(f"[{idx}/{total}] API Job Created: {data.get('job_id')} | Doc: {data.get('document_id')}")
                    successful += 1
                else:
                    logger.error(f"[{idx}/{total}] API Error {resp.status_code}: {resp.text}")
            else:
                from app.ingestion.pipeline import pipeline
                result = pipeline.ingest_file(pdf, force_reindex=args.force)
                status = result.get("status")
                page_count = result.get("page_count", 0)
                chunk_count = result.get("chunk_count", 0)
                logger.info(f"[{idx}/{total}] Status: {status} | Pages: {page_count} | Chunks: {chunk_count}")
                successful += 1
        except Exception as e:
            logger.error(f"[{idx}/{total}] Failed to ingest {pdf.name}: {e}", exc_info=True)

    logger.info(f"Batch ingestion completed. Successfully processed {successful}/{total} documents.")


if __name__ == "__main__":
    main()
