from fastapi import APIRouter
from app.api.schemas.common import HealthResponse
from app.config import settings
from app.storage.qdrant_store import qdrant_store

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    qdrant_stats = qdrant_store.get_collection_stats()
    return HealthResponse(
        status="ok",
        version="1.0.0",
        embedding_model=settings.EMBEDDING_MODEL,
        vector_store_status=qdrant_stats.get("status", "ready"),
        total_vectors=qdrant_stats.get("vectors_count", 0),
        openai_configured=bool(settings.OPENAI_API_KEY)
    )


@router.get("/ready")
def get_readiness():
    return {"ready": True}
