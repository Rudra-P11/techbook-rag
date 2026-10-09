import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.config import settings
from app.storage.document_registry import registry
from app.storage.qdrant_store import qdrant_store
from app.ingestion.pdf_loader import pdf_loader
from app.ingestion.chunker import chunker
from app.ingestion.embedder import embedder

logger = logging.getLogger(__name__)


class IngestionPipeline:
    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def ingest_file(
        self,
        file_path: Path,
        subject: Optional[str] = None,
        display_name: Optional[str] = None,
        job_id: Optional[str] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        End-to-end ingestion pipeline:
        PDF Validation -> Text & OCR Extraction -> Structure Chunking ->
        Local Embeddings -> Qdrant Persistent Storage.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_hash = self.calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        filename = file_path.name
        title = display_name or file_path.stem.replace("_", " ").replace(".", " ").strip()

        # Deduce subject if not provided
        if not subject:
            lower_name = filename.lower()
            if "sql" in lower_name:
                subject = "SQL"
            elif "python" in lower_name:
                subject = "Python"
            elif "deep learning" in lower_name or "neural" in lower_name:
                subject = "Deep Learning"
            elif "machine learning" in lower_name or "ml" in lower_name:
                subject = "Machine Learning"
            elif "linear algebra" in lower_name or "math" in lower_name:
                subject = "Mathematics & Data Science"
            elif "finance" in lower_name:
                subject = "Financial Engineering"
            elif "crypto" in lower_name or "security" in lower_name:
                subject = "Security & Cryptography"
            elif "c++" in lower_name or "asio" in lower_name:
                subject = "Systems & C++"
            else:
                subject = "Computer Science"

        # Check existing document by hash
        existing_doc = registry.get_document_by_hash(file_hash)
        if existing_doc and not force_reindex and existing_doc["ingestion_status"] == "indexed":
            logger.info(f"File {filename} is already indexed (doc_id={existing_doc['document_id']}). Skipping duplicate.")
            return {
                "document_id": existing_doc["document_id"],
                "status": "already_indexed",
                "message": "Document already ingested and indexed."
            }

        doc_id = existing_doc["document_id"] if existing_doc else f"doc_{uuid.uuid4().hex[:12]}"
        if not job_id:
            job_id = f"job_{uuid.uuid4().hex[:12]}"

        # Initialize record & job
        registry.create_document({
            "document_id": doc_id,
            "filename": filename,
            "display_name": title,
            "file_hash": file_hash,
            "file_size_bytes": file_size,
            "subject": subject,
            "ingestion_status": "processing"
        })
        registry.create_job(job_id, doc_id)

        try:
            # Stage 1: Extraction & OCR
            registry.update_job_progress(job_id, "extract", 20.0, "Extracting text and running OCR where needed")
            pages_data, summary = pdf_loader.load_pdf(file_path)
            page_count = summary["page_count"]

            # Save extracted text backup for BM25 and inspection
            extracted_dir = settings.get_absolute_path(settings.EXTRACTED_TEXT_DIR)
            extracted_file = extracted_dir / f"{doc_id}_extracted.json"
            with open(extracted_file, "w", encoding="utf-8") as f:
                json.dump({"pages": pages_data, "summary": summary}, f, indent=2)

            # Stage 2: Chunking
            registry.update_job_progress(job_id, "chunk", 50.0, f"Chunking {page_count} pages with token boundary preservation")
            chunks = chunker.chunk_document(
                document_id=doc_id,
                filename=filename,
                title=title,
                subject=subject,
                file_hash=file_hash,
                pages_data=pages_data
            )
            chunk_count = len(chunks)

            # Save chunks to JSON file
            chunks_file = extracted_dir / f"{doc_id}_chunks.json"
            with open(chunks_file, "w", encoding="utf-8") as f:
                json.dump(chunks, f, indent=2)

            # Stage 3: Embedding & Vector Indexing
            registry.update_job_progress(job_id, "embed", 75.0, f"Generating local embeddings for {chunk_count} chunks")
            chunk_texts = [c["chunk_text"] for c in chunks]
            vectors = embedder.embed_texts(chunk_texts)

            registry.update_job_progress(job_id, "index", 90.0, f"Indexing vectors into Qdrant collection")
            chunk_ids = [c["chunk_id"] for c in chunks]
            qdrant_store.upsert_chunks(
                chunk_ids=chunk_ids,
                vectors=vectors,
                payloads=chunks
            )

            # Complete
            registry.update_document_status(
                document_id=doc_id,
                status="indexed",
                page_count=page_count,
                chunk_count=chunk_count
            )
            registry.complete_job(job_id)

            logger.info(f"Successfully ingested {filename}: {page_count} pages, {chunk_count} chunks.")
            return {
                "document_id": doc_id,
                "job_id": job_id,
                "page_count": page_count,
                "chunk_count": chunk_count,
                "status": "indexed",
                "message": "Ingestion successful"
            }

        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}", exc_info=True)
            registry.update_document_status(doc_id, "failed", error_message=str(e))
            registry.fail_job(job_id, str(e))
            raise


pipeline = IngestionPipeline()
