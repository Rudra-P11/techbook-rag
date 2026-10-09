from typing import Optional, Any
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    embedding_model: str
    vector_store_status: str
    total_vectors: int
    openai_configured: bool
