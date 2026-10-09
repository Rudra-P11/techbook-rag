import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT_SECONDS: int = 30
    OPENAI_MAX_RETRIES: int = 2
    OPENAI_MAX_OUTPUT_TOKENS: int = 1200

    # Embeddings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DEVICE: str = "cpu"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Vector Database (Qdrant)
    # If QDRANT_URL is provided and reachable, connect to remote/docker instance.
    # Otherwise fallback to local embedded Qdrant at QDRANT_PATH.
    QDRANT_URL: Optional[str] = None
    QDRANT_PATH: Optional[str] = "./data/qdrant_storage"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "techbook_chunks"

    # Storage Paths
    DOCUMENT_STORAGE_DIR: str = "./data/documents"
    EXTRACTED_TEXT_DIR: str = "./data/extracted"
    REGISTRY_DB_URL: str = "sqlite:///./data/registry.db"

    # Chunking
    CHUNK_SIZE_TOKENS: int = 700
    CHUNK_OVERLAP_TOKENS: int = 105
    MIN_CHUNK_SIZE_TOKENS: int = 150
    MAX_CHUNK_SIZE_TOKENS: int = 1000

    # Retrieval
    DENSE_TOP_K: int = 20
    LEXICAL_TOP_K: int = 20
    FUSION_TOP_K: int = 30
    RERANKER_ENABLED: bool = False
    FINAL_CONTEXT_CHUNKS: int = 6
    MAX_CONTEXT_TOKENS: int = 5000

    # Security & Guardrails
    ADMIN_API_KEY: Optional[str] = None
    MAX_UPLOAD_SIZE_MB: int = 150
    MAX_QUERY_LENGTH: int = 4000

    # Observability
    METRICS_ENABLED: bool = True
    TRACE_RETRIEVAL: bool = True

    def get_absolute_path(self, relative_path: str) -> Path:
        p = Path(relative_path)
        if p.is_absolute():
            return p
        return BASE_DIR / relative_path

    def ensure_directories(self) -> None:
        """Ensure necessary runtime directories exist."""
        for path_str in [
            self.DOCUMENT_STORAGE_DIR,
            self.EXTRACTED_TEXT_DIR,
            "./data/indexes",
            "./data/qdrant_storage",
            "./evaluation/reports"
        ]:
            target = self.get_absolute_path(path_str)
            target.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
