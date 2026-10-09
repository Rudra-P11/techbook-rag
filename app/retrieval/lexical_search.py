import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from app.config import settings

logger = logging.getLogger(__name__)


class LexicalSearch:
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self._indexed_count = 0

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Lowercase, retain alphanumeric words and code symbols (e.g. underscores)
        return re.findall(r'[a-zA-Z0-9_]+', text.lower())

    def refresh_index(self) -> int:
        """
        Loads all chunk JSON files from extracted data directory and builds BM25 index.
        """
        extracted_dir = settings.get_absolute_path(settings.EXTRACTED_TEXT_DIR)
        all_chunks = []

        for chunk_file in extracted_dir.glob("*_chunks.json"):
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunks = json.load(f)
                    if isinstance(chunks, list):
                        all_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Error loading {chunk_file} for BM25: {e}")

        if not all_chunks:
            self.bm25 = None
            self.corpus_chunks = []
            return 0

        tokenized_corpus = [self.tokenize(c.get("chunk_text", "")) for c in all_chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus_chunks = all_chunks
        self._indexed_count = len(all_chunks)
        logger.info(f"BM25 index built with {self._indexed_count} chunks.")
        return self._indexed_count

    def search(
        self,
        query: str,
        top_k: int = settings.LEXICAL_TOP_K,
        subjects: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes BM25 search over corpus chunks.
        """
        if not self.bm25 or not self.corpus_chunks:
            self.refresh_index()

        if not self.bm25 or not self.corpus_chunks:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        
        # Pair with chunks and filter
        scored_candidates = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue
            chunk = self.corpus_chunks[idx]

            # Filter by subjects
            if subjects and chunk.get("subject") not in subjects:
                continue
            # Filter by document_ids
            if document_ids and chunk.get("document_id") not in document_ids:
                continue

            candidate = dict(chunk)
            candidate["score"] = float(score)
            candidate["search_type"] = "lexical"
            scored_candidates.append(candidate)

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates[:top_k]


lexical_search = LexicalSearch()
