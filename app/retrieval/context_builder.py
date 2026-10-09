import re
from typing import List, Dict, Any, Tuple
from app.config import settings


class ContextBuilder:
    @staticmethod
    def estimate_tokens(text: str) -> int:
        return max(int(len(text) / 4.0), 1)

    def build_context(
        self,
        ranked_chunks: List[Dict[str, Any]],
        max_chunks: int = settings.FINAL_CONTEXT_CHUNKS,
        max_tokens: int = settings.MAX_CONTEXT_TOKENS
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Takes top ranked chunks and formats them with stable Evidence IDs (E1, E2, ...),
        subject, filename, and page numbers.
        Returns:
            (formatted_prompt_context_string, list_of_evidence_metadata)
        """
        evidence_list = []
        context_blocks = []
        accumulated_tokens = 0

        for idx, chunk in enumerate(ranked_chunks[:max_chunks], start=1):
            evidence_id = f"E{idx}"
            chunk_text = chunk.get("chunk_text", "").strip()
            pages = chunk.get("page_numbers", [chunk.get("start_page", 1)])
            pages_str = ", ".join(map(str, pages)) if pages else str(chunk.get("start_page", 1))
            title = chunk.get("title", chunk.get("filename", "Unknown Document"))
            filename = chunk.get("filename", "unknown.pdf")
            subject = chunk.get("subject", "General")

            block_str = (
                f"--- EVIDENCE [{evidence_id}] ---\n"
                f"Source: \"{title}\" (File: {filename}, Subject: {subject}, Pages: {pages_str})\n"
                f"Content:\n{chunk_text}\n"
                f"--- END EVIDENCE [{evidence_id}] ---"
            )

            block_tokens = self.estimate_tokens(block_str)
            if accumulated_tokens + block_tokens > max_tokens and evidence_list:
                break

            context_blocks.append(block_str)
            accumulated_tokens += block_tokens

            evidence_list.append({
                "evidence_id": evidence_id,
                "chunk_id": chunk.get("chunk_id", ""),
                "document_id": chunk.get("document_id", ""),
                "filename": filename,
                "title": title,
                "pages": pages,
                "subject": subject,
                "score": chunk.get("rrf_score", chunk.get("score", 0.0)),
                "dense_score": chunk.get("dense_score", 0.0),
                "lexical_score": chunk.get("lexical_score", 0.0),
                "text": chunk_text
            })

        formatted_context = "\n\n".join(context_blocks)
        return formatted_context, evidence_list


context_builder = ContextBuilder()
