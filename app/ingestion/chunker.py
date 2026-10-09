import hashlib
import re
from typing import List, Dict, Any
from app.config import settings


class StructureAwareChunker:
    """
    Deterministic, token-aware chunker that respects paragraphs, code blocks,
    and page provenance.
    """

    def __init__(
        self,
        target_tokens: int = settings.CHUNK_SIZE_TOKENS,
        overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS,
        min_tokens: int = settings.MIN_CHUNK_SIZE_TOKENS,
        max_tokens: int = settings.MAX_CHUNK_SIZE_TOKENS,
    ):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count using whitespace and sub-word heuristic (~0.75 words per token).
        """
        if not text:
            return 0
        words = len(text.split())
        chars = len(text)
        # Standard heuristic: 1 token ≈ 4 characters or ~0.75 words
        return max(int(chars / 4.0), int(words * 1.3), 1)

    def chunk_document(
        self,
        document_id: str,
        filename: str,
        title: str,
        subject: str,
        file_hash: str,
        pages_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunk extracted pages into passages with page provenance.
        """
        # Step 1: Collect structural units (paragraphs / sections) tagged with their page numbers
        units = []
        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]
            if not text:
                continue

            # Split by double newline (paragraphs / code blocks)
            paras = [p.strip() for p in text.split("\n\n") if p.strip()]
            for p in paras:
                units.append({
                    "text": p,
                    "page_number": page_num,
                    "token_count": self.estimate_tokens(p)
                })

        if not units:
            return []

        chunks = []
        current_paras = []
        current_tokens = 0
        current_pages = set()
        chunk_idx = 0

        for unit in units:
            unit_tokens = unit["token_count"]

            # If adding this unit exceeds target_tokens and current_tokens is already >= min_tokens
            if current_tokens + unit_tokens > self.target_tokens and current_tokens >= self.min_tokens:
                # Emit current chunk
                chunk_text = "\n\n".join([u["text"] for u in current_paras])
                page_list = sorted(list(current_pages))
                cid = self._create_chunk_id(document_id, chunk_idx, chunk_text)

                chunks.append({
                    "chunk_id": cid,
                    "document_id": document_id,
                    "filename": filename,
                    "title": title,
                    "subject": subject,
                    "start_page": page_list[0] if page_list else 1,
                    "end_page": page_list[-1] if page_list else 1,
                    "page_numbers": page_list,
                    "chunk_index": chunk_idx,
                    "chunk_text": chunk_text,
                    "token_count": current_tokens,
                    "file_hash": file_hash,
                    "chunker_version": "1.0",
                    "embedding_model": settings.EMBEDDING_MODEL
                })
                chunk_idx += 1

                # Calculate overlap units
                overlap_paras = []
                overlap_token_count = 0
                for u in reversed(current_paras):
                    if overlap_token_count + u["token_count"] <= self.overlap_tokens:
                        overlap_paras.insert(0, u)
                        overlap_token_count += u["token_count"]
                    else:
                        break

                current_paras = overlap_paras + [unit]
                current_tokens = overlap_token_count + unit_tokens
                current_pages = {u["page_number"] for u in current_paras}
            else:
                current_paras.append(unit)
                current_tokens += unit_tokens
                current_pages.add(unit["page_number"])

        # Emit remaining units
        if current_paras:
            chunk_text = "\n\n".join([u["text"] for u in current_paras])
            page_list = sorted(list(current_pages))
            cid = self._create_chunk_id(document_id, chunk_idx, chunk_text)
            chunks.append({
                "chunk_id": cid,
                "document_id": document_id,
                "filename": filename,
                "title": title,
                "subject": subject,
                "start_page": page_list[0] if page_list else 1,
                "end_page": page_list[-1] if page_list else 1,
                "page_numbers": page_list,
                "chunk_index": chunk_idx,
                "chunk_text": chunk_text,
                "token_count": current_tokens,
                "file_hash": file_hash,
                "chunker_version": "1.0",
                "embedding_model": settings.EMBEDDING_MODEL
            })

        return chunks

    def _create_chunk_id(self, document_id: str, chunk_index: int, text: str) -> str:
        h = hashlib.sha256(f"{document_id}:{chunk_index}:{text[:100]}".encode("utf-8")).hexdigest()[:16]
        return f"{document_id}_c{chunk_index:04d}_{h}"


chunker = StructureAwareChunker()
