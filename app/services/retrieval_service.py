import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.retrieval.dense_search import dense_search
from app.retrieval.lexical_search import lexical_search
from app.retrieval.fusion import rank_fusion
from app.retrieval.context_builder import context_builder
from app.config import settings

logger = logging.getLogger(__name__)


class RetrievalService:
    def retrieve(
        self,
        query: str,
        subjects: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = settings.FINAL_CONTEXT_CHUNKS
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], int]:
        """
        Hybrid retrieval workflow:
        1. Dense ANN search
        2. Lexical BM25 search
        3. Reciprocal Rank Fusion
        4. Context formatting with Evidence IDs

        Returns:
            (context_text, evidence_list, all_fused_chunks, latency_ms)
        """
        start_time = time.perf_counter()

        # 1. Dense search
        dense_candidates = dense_search.search(
            query=query,
            top_k=settings.DENSE_TOP_K,
            subjects=subjects,
            document_ids=document_ids
        )

        # 2. Lexical search
        lexical_candidates = lexical_search.search(
            query=query,
            top_k=settings.LEXICAL_TOP_K,
            subjects=subjects,
            document_ids=document_ids
        )

        # 3. Hybrid fusion
        if dense_candidates and lexical_candidates:
            fused_candidates = rank_fusion.reciprocal_rank_fusion(
                dense_results=dense_candidates,
                lexical_results=lexical_candidates,
                top_k=settings.FUSION_TOP_K
            )
        elif dense_candidates:
            fused_candidates = dense_candidates
        else:
            fused_candidates = lexical_candidates

        # 4. Context builder
        context_text, evidence_list = context_builder.build_context(
            ranked_chunks=fused_candidates,
            max_chunks=top_k,
            max_tokens=settings.MAX_CONTEXT_TOKENS
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return context_text, evidence_list, fused_candidates, latency_ms


retrieval_service = RetrievalService()
