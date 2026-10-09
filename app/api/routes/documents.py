import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from app.api.schemas.document import DocumentMetadata, DocumentUploadResponse
from app.storage.document_registry import registry
from app.storage.qdrant_store import qdrant_store
from app.ingestion.pipeline import pipeline
from app.config import settings

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


def run_ingestion_background(file_path: Path, subject: Optional[str], title: Optional[str], job_id: str):
    pipeline.ingest_file(
        file_path=file_path,
        subject=subject,
        display_name=title,
        job_id=job_id
    )


@router.post("", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    subject: Optional[str] = Form(None),
    title: Optional[str] = Form(None)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    storage_dir = settings.get_absolute_path(settings.DOCUMENT_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    dest_path = storage_dir / file.filename
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    file_hash = pipeline.calculate_file_hash(dest_path)

    # Trigger background ingestion job
    background_tasks.add_task(
        run_ingestion_background,
        dest_path,
        subject,
        title,
        job_id
    )

    return DocumentUploadResponse(
        document_id=doc_id,
        job_id=job_id,
        filename=file.filename,
        file_hash=file_hash,
        status="processing",
        message="Document uploaded. Ingestion job started in background."
    )


@router.get("", response_model=List[DocumentMetadata])
def list_documents():
    docs = registry.list_documents()
    return [DocumentMetadata(**d) for d in docs]


@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document(document_id: str):
    doc = registry.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentMetadata(**doc)


@router.delete("/{document_id}")
def delete_document(document_id: str):
    doc = registry.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove points from Qdrant
    qdrant_store.delete_by_document(document_id)
    # Mark deleted in registry
    registry.mark_document_deleted(document_id)

    return {"success": True, "message": f"Document {document_id} and its vector chunks deleted."}
