from typing import List, Dict, Any


class RankFusion:
    @staticmethod
    def reciprocal_rank_fusion(
        dense_results: List[Dict[str, Any]],
        lexical_results: List[Dict[str, Any]],
        k: int = 60,
        top_k: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Combines dense and lexical candidates using Reciprocal Rank Fusion (RRF).
        RRF_score(d) = sum(1 / (k + rank_i))
        """
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}
        ranks_dense: Dict[str, int] = {}
        ranks_lexical: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}
        lexical_scores: Dict[str, float] = {}

        # Process dense rankings
        for rank, item in enumerate(dense_results, start=1):
            cid = item["chunk_id"]
            ranks_dense[cid] = rank
            dense_scores[cid] = float(item.get("dense_score", item.get("score", 0.0)))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item

        # Process lexical rankings
        for rank, item in enumerate(lexical_results, start=1):
            cid = item["chunk_id"]
            ranks_lexical[cid] = rank
            lexical_scores[cid] = float(item.get("lexical_score", item.get("score", 0.0)))
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (k + rank))
            if cid not in chunk_map:
                chunk_map[cid] = item

        # Sort by RRF score descending
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused = []
        for cid in sorted_cids[:top_k]:
            c = dict(chunk_map[cid])
            c["rrf_score"] = rrf_scores[cid]
            c["dense_rank"] = ranks_dense.get(cid)
            c["lexical_rank"] = ranks_lexical.get(cid)
            c["dense_score"] = dense_scores.get(cid, 0.0)
            c["lexical_score"] = lexical_scores.get(cid, 0.0)
            fused.append(c)

        return fused


rank_fusion = RankFusion()
