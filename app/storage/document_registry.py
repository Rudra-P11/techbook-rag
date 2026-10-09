import sqlite3
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentRegistry:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            db_url = settings.REGISTRY_DB_URL.replace("sqlite:///", "")
            self.db_path = settings.get_absolute_path(db_url)
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    page_count INTEGER DEFAULT 0,
                    subject TEXT DEFAULT 'General',
                    author TEXT,
                    publication_year INTEGER,
                    language TEXT DEFAULT 'en',
                    source_uri TEXT,
                    license TEXT,
                    ingestion_status TEXT NOT NULL DEFAULT 'pending',
                    chunk_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    processing_version TEXT DEFAULT '1.0',
                    embedding_model TEXT DEFAULT 'BAAI/bge-small-en-v1.5',
                    index_version TEXT DEFAULT 'v1',
                    error_message TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_hash ON documents(file_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_status ON documents(ingestion_status)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    job_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    stage TEXT NOT NULL DEFAULT 'init',
                    progress_pct REAL DEFAULT 0.0,
                    stage_message TEXT DEFAULT '',
                    warnings TEXT DEFAULT '[]',
                    error TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_ms INTEGER DEFAULT 0,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_status ON ingestion_jobs(status)")
            conn.commit()

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE file_hash = ? AND ingestion_status != 'deleted'", (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_documents(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if include_deleted:
                cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            else:
                cursor.execute("SELECT * FROM documents WHERE ingestion_status != 'deleted' ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def create_document(self, doc_data: Dict[str, Any]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    document_id, filename, display_name, file_hash, file_size_bytes,
                    page_count, subject, author, publication_year, language,
                    source_uri, license, ingestion_status, chunk_count,
                    created_at, updated_at, processing_version, embedding_model,
                    index_version, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_data["document_id"],
                doc_data["filename"],
                doc_data.get("display_name", doc_data["filename"]),
                doc_data["file_hash"],
                doc_data["file_size_bytes"],
                doc_data.get("page_count", 0),
                doc_data.get("subject", "General"),
                doc_data.get("author"),
                doc_data.get("publication_year"),
                doc_data.get("language", "en"),
                doc_data.get("source_uri"),
                doc_data.get("license"),
                doc_data.get("ingestion_status", "pending"),
                doc_data.get("chunk_count", 0),
                doc_data.get("created_at", now),
                now,
                doc_data.get("processing_version", "1.0"),
                doc_data.get("embedding_model", settings.EMBEDDING_MODEL),
                doc_data.get("index_version", "v1"),
                doc_data.get("error_message")
            ))
            conn.commit()

    def update_document_status(
        self,
        document_id: str,
        status: str,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["ingestion_status = ?", "updated_at = ?"]
            params = [status, now]

            if page_count is not None:
                updates.append("page_count = ?")
                params.append(page_count)
            if chunk_count is not None:
                updates.append("chunk_count = ?")
                params.append(chunk_count)
            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)

            params.append(document_id)
            query = f"UPDATE documents SET {', '.join(updates)} WHERE document_id = ?"
            cursor.execute(query, params)
            conn.commit()

    def mark_document_deleted(self, document_id: str) -> None:
        self.update_document_status(document_id, "deleted")

    # Ingestion Jobs
    def create_job(self, job_id: str, document_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ingestion_jobs (
                    job_id, document_id, status, stage, progress_pct,
                    stage_message, warnings, error, started_at
                ) VALUES (?, ?, 'processing', 'upload', 0.0, 'Job started', '[]', NULL, ?)
            """, (job_id, document_id, now))
            conn.commit()

    def update_job_progress(
        self,
        job_id: str,
        stage: str,
        progress_pct: float,
        message: str = "",
        warning: Optional[str] = None
    ) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT warnings FROM ingestion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            current_warnings = json.loads(row["warnings"]) if row and row["warnings"] else []
            if warning:
                current_warnings.append(warning)

            cursor.execute("""
                UPDATE ingestion_jobs
                SET stage = ?, progress_pct = ?, stage_message = ?, warnings = ?
                WHERE job_id = ?
            """, (stage, progress_pct, message, json.dumps(current_warnings), job_id))
            conn.commit()

    def complete_job(self, job_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT started_at FROM ingestion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            duration_ms = 0
            if row and row["started_at"]:
                start_dt = datetime.fromisoformat(row["started_at"])
                duration_ms = int((datetime.now(timezone.utc) - start_dt).total_seconds() * 1000)

            cursor.execute("""
                UPDATE ingestion_jobs
                SET status = 'completed', stage = 'ready', progress_pct = 100.0,
                    stage_message = 'Ingestion completed successfully',
                    completed_at = ?, duration_ms = ?
                WHERE job_id = ?
            """, (now, duration_ms, job_id))
            conn.commit()

    def fail_job(self, job_id: str, error_message: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT started_at FROM ingestion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            duration_ms = 0
            if row and row["started_at"]:
                start_dt = datetime.fromisoformat(row["started_at"])
                duration_ms = int((datetime.now(timezone.utc) - start_dt).total_seconds() * 1000)

            cursor.execute("""
                UPDATE ingestion_jobs
                SET status = 'failed', stage = 'failed', stage_message = ?,
                    error = ?, completed_at = ?, duration_ms = ?
                WHERE job_id = ?
            """, (error_message, error_message, now, duration_ms, job_id))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ingestion_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                res = dict(row)
                res["warnings"] = json.loads(res.get("warnings") or "[]")
                return res
            return None


registry = DocumentRegistry()
