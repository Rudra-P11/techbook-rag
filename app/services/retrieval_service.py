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
        top_k: int = settings.FINAL_CONTEXT_CHUNKS,
        retrieval_mode: str = "hybrid",
        rrf_k: int = 60,
        w_dense: float = 1.0,
        w_lex: float = 1.0
    ) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], int, Dict[str, Any]]:
        """
        Flexible multi-mode retrieval workflow:
        - 'dense_only': Vector ANN alone (Qdrant HNSW)
        - 'bm25_only': Lexical search alone (BM25 Okapi inverted index)
        - 'hybrid': Standard Cormack RRF (k=60)
        - 'hybrid_tuned': Steeper rank decay (k=10 or user k, w_lex=1.5)
        - 'custom': User-configured k and weights

        Returns:
            (context_text, evidence_list, all_fused_chunks, latency_ms, telemetry_stats)
        """
        start_time = time.perf_counter()
        mode = (retrieval_mode or "hybrid").lower()

        dense_candidates: List[Dict[str, Any]] = []
        lexical_candidates: List[Dict[str, Any]] = []
        fused_candidates: List[Dict[str, Any]] = []

        # Parameter calibration
        effective_k = rrf_k
        effective_w_dense = w_dense
        effective_w_lex = w_lex

        if mode == "hybrid_tuned":
            effective_k = 10 if rrf_k == 60 else rrf_k
            effective_w_lex = 1.5 if w_lex == 1.0 else w_lex

        # 1. Branch: Dense ANN search
        if mode in ("dense_only", "hybrid", "hybrid_tuned", "custom"):
            dense_candidates = dense_search.search(
                query=query,
                top_k=settings.DENSE_TOP_K,
                subjects=subjects,
                document_ids=document_ids
            )

        # 2. Branch: Lexical BM25 search
        if mode in ("bm25_only", "hybrid", "hybrid_tuned", "custom"):
            lexical_candidates = lexical_search.search(
                query=query,
                top_k=settings.LEXICAL_TOP_K,
                subjects=subjects,
                document_ids=document_ids
            )

        # 3. Strategy combination
        if mode == "dense_only":
            fused_candidates = []
            for rank, c in enumerate(dense_candidates, 1):
                item = dict(c)
                item["dense_rank"] = rank
                item["lexical_rank"] = None
                item["dense_score"] = float(item.get("dense_score", item.get("score", 0.0)))
                item["lexical_score"] = 0.0
                item["rrf_score"] = round(item["dense_score"], 4)
                item["final_rank"] = rank
                fused_candidates.append(item)

        elif mode == "bm25_only":
            fused_candidates = []
            for rank, c in enumerate(lexical_candidates, 1):
                item = dict(c)
                item["dense_rank"] = None
                item["lexical_rank"] = rank
                item["dense_score"] = 0.0
                item["lexical_score"] = float(item.get("lexical_score", item.get("score", 0.0)))
                item["rrf_score"] = round(item["lexical_score"], 4)
                item["final_rank"] = rank
                fused_candidates.append(item)

        else:
            # Hybrid fusion (standard, tuned, or custom)
            if dense_candidates and lexical_candidates:
                fused_candidates = rank_fusion.reciprocal_rank_fusion(
                    dense_results=dense_candidates,
                    lexical_results=lexical_candidates,
                    k=effective_k,
                    top_k=settings.FUSION_TOP_K,
                    w_dense=effective_w_dense,
                    w_lex=effective_w_lex
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

        top_dense = dense_candidates[0].get("dense_score", dense_candidates[0].get("score")) if dense_candidates else None
        top_lex = lexical_candidates[0].get("lexical_score", lexical_candidates[0].get("score")) if lexical_candidates else None
        top_rrf = fused_candidates[0].get("rrf_score", fused_candidates[0].get("score")) if fused_candidates else None

        telemetry_stats = {
            "retrieval_mode": mode,
            "rrf_k": effective_k,
            "w_dense": effective_w_dense,
            "w_lex": effective_w_lex,
            "dense_count": len(dense_candidates),
            "lexical_count": len(lexical_candidates),
            "fused_count": len(fused_candidates),
            "top_dense_score": round(float(top_dense), 4) if top_dense is not None else None,
            "top_lexical_score": round(float(top_lex), 4) if top_lex is not None else None,
            "top_rrf_score": round(float(top_rrf), 5) if top_rrf is not None else None
        }

        return context_text, evidence_list, fused_candidates, latency_ms, telemetry_stats


retrieval_service = RetrievalService()
