from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    display_name: str
    file_hash: str
    file_size_bytes: int
    page_count: int
    subject: str = "General"
    author: Optional[str] = None
    publication_year: Optional[int] = None
    language: str = "en"
    source_uri: Optional[str] = None
    license: Optional[str] = None
    ingestion_status: str
    chunk_count: int = 0
    created_at: str
    updated_at: str
    processing_version: str = "1.0"
    embedding_model: str
    index_version: str = "v1"
    error_message: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    filename: str
    file_hash: str
    status: str
    message: str


class IngestionJobResponse(BaseModel):
    job_id: str
    document_id: str
    status: str
    stage: str
    progress_pct: float
    stage_message: str
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: int = 0
