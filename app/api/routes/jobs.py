from fastapi import APIRouter, HTTPException
from app.api.schemas.document import IngestionJobResponse
from app.storage.document_registry import registry

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


@router.get("/{job_id}", response_model=IngestionJobResponse)
def get_job_status(job_id: str):
    job = registry.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return IngestionJobResponse(**job)
