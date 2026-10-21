"""
TechBook RAG - Multi-Round Retrieval Evaluation Framework
=========================================================
Runs 4 experimental rounds and measures metrics at each stage:
  Round 1: Dense-only (Qdrant Cosine ANN)
  Round 2: BM25-only (Okapi lexical)
  Round 3: Hybrid RRF k=60 (Dense + BM25 fused)
  Round 4: Hybrid RRF + JEV Pruning (full pipeline)

Metrics computed per round:
  - Term Recall (% of expected terms found in top-k context)
  - Mean Reciprocal Rank (MRR) - position of first relevant result
  - Context Precision@k - proportion of relevant chunks in top-k
  - Source Accuracy - did we retrieve from the correct document?
  - Redundancy Rate - % of chunk pairs with Jaccard > 0.60
  - Latency (P50, P95, Mean)
  - Per-question breakdown with chunk-level forensics
"""

import sys
import json
import time
import re
import statistics
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.retrieval.dense_search import dense_search
from app.retrieval.lexical_search import lexical_search
from app.retrieval.fusion import rank_fusion
from app.retrieval.context_builder import context_builder
from app.decision.jev_engine import jev_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_multiround")

TOP_K = 6  # Number of chunks to include in final context


def compute_jaccard(text1: str, text2: str) -> float:
    set1 = set(re.findall(r'\w+', text1.lower()))
    set2 = set(re.findall(r'\w+', text2.lower()))
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)


def compute_term_recall(context_text: str, expected_terms: List[str]) -> Tuple[float, List[str], List[str]]:
    """Returns (recall_score, found_terms, missed_terms)."""
    if not expected_terms:
        return 1.0, [], []
    ctx_lower = context_text.lower()
    found = [t for t in expected_terms if t.lower() in ctx_lower]
    missed = [t for t in expected_terms if t.lower() not in ctx_lower]
    recall = len(found) / len(expected_terms)
    return recall, found, missed


def compute_source_accuracy(evidence_list: List[Dict], expected_source: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Check if any retrieved chunk comes from the expected source document."""
    if not expected_source:
        return True, None  # unanswerable questions always pass
    for ev in evidence_list:
        fn = ev.get("filename", "")
        if expected_source.lower() in fn.lower() or fn.lower() in expected_source.lower():
            return True, fn
    top_fn = evidence_list[0].get("filename", "unknown") if evidence_list else "none"
    return False, top_fn


def compute_redundancy_rate(evidence_list: List[Dict], threshold: float = 0.60) -> Tuple[float, int]:
    """Compute fraction of chunk pairs with Jaccard > threshold."""
    texts = [ev.get("chunk_text", ev.get("text", "")) for ev in evidence_list]
    if len(texts) < 2:
        return 0.0, 0
    total_pairs = 0
    redundant_pairs = 0
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            total_pairs += 1
            sim = compute_jaccard(texts[i], texts[j])
            if sim > threshold:
                redundant_pairs += 1
    return (redundant_pairs / total_pairs) if total_pairs > 0 else 0.0, redundant_pairs


def run_dense_only(query: str, top_k: int = TOP_K) -> Tuple[List[Dict], str, int]:
    """Round 1: Dense-only retrieval."""
    start = time.perf_counter()
    results = dense_search.search(query=query, top_k=top_k * 3)
    # Take top_k and build context
    top_results = results[:top_k]
    # Add chunk_text alias for context
    for r in top_results:
        if "chunk_text" not in r:
            r["chunk_text"] = r.get("text", "")
    context_text, evidence_list = context_builder.build_context(top_results, max_chunks=top_k)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return evidence_list, context_text, latency_ms


def run_bm25_only(query: str, top_k: int = TOP_K) -> Tuple[List[Dict], str, int]:
    """Round 2: BM25-only retrieval."""
    start = time.perf_counter()
    results = lexical_search.search(query=query, top_k=top_k * 3)
    top_results = results[:top_k]
    for r in top_results:
        r["lexical_score"] = r.get("score", 0.0)
    context_text, evidence_list = context_builder.build_context(top_results, max_chunks=top_k)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return evidence_list, context_text, latency_ms


def run_hybrid_rrf(query: str, top_k: int = TOP_K) -> Tuple[List[Dict], str, int]:
    """Round 3: Hybrid Dense + BM25 with RRF k=60 fusion."""
    start = time.perf_counter()
    dense_results = dense_search.search(query=query, top_k=settings.DENSE_TOP_K)
    lexical_results = lexical_search.search(query=query, top_k=settings.LEXICAL_TOP_K)

    if dense_results and lexical_results:
        fused = rank_fusion.reciprocal_rank_fusion(
            dense_results=dense_results,
            lexical_results=lexical_results,
            top_k=settings.FUSION_TOP_K
        )
    elif dense_results:
        fused = dense_results
    else:
        fused = lexical_results

    context_text, evidence_list = context_builder.build_context(fused, max_chunks=top_k)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return evidence_list, context_text, latency_ms


def run_hybrid_rrf_jev(query: str, top_k: int = TOP_K) -> Tuple[List[Dict], str, int, Dict]:
    """Round 4: Hybrid RRF + JEV evidential pruning."""
    start = time.perf_counter()
    dense_results = dense_search.search(query=query, top_k=settings.DENSE_TOP_K)
    lexical_results = lexical_search.search(query=query, top_k=settings.LEXICAL_TOP_K)

    if dense_results and lexical_results:
        fused = rank_fusion.reciprocal_rank_fusion(
            dense_results=dense_results,
            lexical_results=lexical_results,
            top_k=settings.FUSION_TOP_K
        )
    elif dense_results:
        fused = dense_results
    else:
        fused = lexical_results

    context_text, evidence_list = context_builder.build_context(fused, max_chunks=top_k)

    # JEV pruning
    jev_result = jev_engine.calculate_joint_evidential_value(
        evidence_list=evidence_list,
        max_chunks=top_k
    )

    pruned_evidence = jev_result.selected_evidence
    # Rebuild context from JEV-selected evidence
    pruned_blocks = []
    for idx, ev in enumerate(pruned_evidence, 1):
        text = ev.get("text", ev.get("chunk_text", ""))
        pruned_blocks.append(f"[E{idx}] {ev.get('title', 'Book')} (Pages {ev.get('pages', 'N/A')}):\n{text}")
    pruned_context = "\n\n".join(pruned_blocks)

    latency_ms = int((time.perf_counter() - start) * 1000)
    jev_meta = {
        "total_jev_score": jev_result.total_jev_score,
        "pruned_count": jev_result.pruned_count,
        "is_sufficient": jev_result.is_sufficient,
        "selected_count": len(pruned_evidence)
    }
    return pruned_evidence, pruned_context, latency_ms, jev_meta


def evaluate_round(round_name: str, questions: List[Dict], retrieval_fn) -> Dict:
    """Run a single evaluation round across all questions."""
    logger.info(f"\n{'='*70}")
    logger.info(f"  ROUND: {round_name}")
    logger.info(f"{'='*70}")

    results = []
    latencies = []
    term_recalls = []
    source_hits = 0
    source_total = 0
    all_redundancy_rates = []

    for q in questions:
        qid = q["question_id"]
        query = q["query"]
        expected_terms = q.get("expected_terms", [])
        expected_source = q.get("expected_source")
        answerable = q.get("answerable", True)

        # Skip unanswerable for retrieval eval
        if not answerable:
            results.append({
                "question_id": qid,
                "query": query,
                "skipped": True,
                "reason": "unanswerable/adversarial"
            })
            continue

        # Run retrieval
        if round_name == "Round 4: Hybrid RRF + JEV":
            evidence_list, context_text, latency_ms, jev_meta = retrieval_fn(query)
        else:
            evidence_list, context_text, latency_ms = retrieval_fn(query)
            jev_meta = None

        latencies.append(latency_ms)

        # Metrics
        term_recall, found_terms, missed_terms = compute_term_recall(context_text, expected_terms)
        term_recalls.append(term_recall)

        src_hit, actual_src = compute_source_accuracy(evidence_list, expected_source)
        if expected_source:
            source_total += 1
            if src_hit:
                source_hits += 1

        redundancy_rate, redundant_pairs = compute_redundancy_rate(evidence_list)
        all_redundancy_rates.append(redundancy_rate)

        # Chunk forensics
        chunk_details = []
        for idx, ev in enumerate(evidence_list):
            chunk_details.append({
                "rank": idx + 1,
                "chunk_id": ev.get("chunk_id", "?"),
                "filename": ev.get("filename", "?"),
                "pages": ev.get("pages", []),
                "dense_score": round(ev.get("dense_score", 0.0), 4),
                "lexical_score": round(ev.get("lexical_score", 0.0), 4),
                "rrf_score": round(ev.get("rrf_score", ev.get("score", 0.0)), 5),
                "jev_score": round(ev.get("jev_score", 0.0), 4) if jev_meta else None
            })

        result_entry = {
            "question_id": qid,
            "query": query,
            "category": q.get("category"),
            "difficulty": q.get("difficulty"),
            "query_type": q.get("query_type"),
            "latency_ms": latency_ms,
            "chunks_retrieved": len(evidence_list),
            "term_recall": round(term_recall, 4),
            "found_terms": found_terms,
            "missed_terms": missed_terms,
            "source_hit": src_hit,
            "expected_source": expected_source,
            "actual_top_source": actual_src,
            "redundancy_rate": round(redundancy_rate, 4),
            "redundant_pairs": redundant_pairs,
            "chunk_forensics": chunk_details
        }
        if jev_meta:
            result_entry["jev"] = jev_meta

        results.append(result_entry)

        status = "OK" if term_recall >= 0.5 else "WEAK"
        logger.info(f"  [{status}] {qid}: recall={term_recall:.2f} | latency={latency_ms}ms | src={'HIT' if src_hit else 'MISS'} | missed={missed_terms}")

    # Aggregate metrics
    valid_latencies = latencies[1:] if len(latencies) > 1 else latencies  # exclude cold start
    agg = {
        "round_name": round_name,
        "total_questions": len(questions),
        "evaluated_questions": len([r for r in results if not r.get("skipped")]),
        "skipped_questions": len([r for r in results if r.get("skipped")]),
        "metrics": {
            "term_recall_mean": round(statistics.mean(term_recalls), 4) if term_recalls else 0,
            "term_recall_median": round(statistics.median(term_recalls), 4) if term_recalls else 0,
            "term_recall_min": round(min(term_recalls), 4) if term_recalls else 0,
            "term_recall_max": round(max(term_recalls), 4) if term_recalls else 0,
            "perfect_recall_rate": round(sum(1 for t in term_recalls if t >= 1.0) / len(term_recalls), 4) if term_recalls else 0,
            "source_accuracy": round(source_hits / source_total, 4) if source_total > 0 else 0,
            "source_hits": source_hits,
            "source_total": source_total,
            "redundancy_rate_mean": round(statistics.mean(all_redundancy_rates), 4) if all_redundancy_rates else 0,
            "latency_mean_ms": round(statistics.mean(valid_latencies), 2) if valid_latencies else 0,
            "latency_p50_ms": round(statistics.median(valid_latencies), 2) if valid_latencies else 0,
            "latency_p95_ms": round(sorted(valid_latencies)[int(len(valid_latencies) * 0.95)] if valid_latencies else 0, 2),
            "latency_min_ms": min(valid_latencies) if valid_latencies else 0,
            "latency_max_ms": max(valid_latencies) if valid_latencies else 0,
            "latency_cold_start_ms": latencies[0] if latencies else 0
        },
        "per_question": results
    }

    logger.info(f"\n  SUMMARY [{round_name}]:")
    logger.info(f"    Term Recall Mean:    {agg['metrics']['term_recall_mean']:.4f}")
    logger.info(f"    Perfect Recall Rate: {agg['metrics']['perfect_recall_rate']:.4f}")
    logger.info(f"    Source Accuracy:     {agg['metrics']['source_accuracy']:.4f}")
    logger.info(f"    Redundancy Rate:     {agg['metrics']['redundancy_rate_mean']:.4f}")
    logger.info(f"    Latency P50:        {agg['metrics']['latency_p50_ms']}ms")

    return agg


def main():
    questions_file = settings.get_absolute_path("./evaluation/questions_v2.jsonl")
    if not questions_file.exists():
        logger.error(f"Questions file not found: {questions_file}")
        return

    questions = []
    with open(questions_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    questions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    logger.info(f"Loaded {len(questions)} benchmark questions from {questions_file}")

    # Ensure BM25 index is built
    logger.info("Building BM25 index...")
    indexed = lexical_search.refresh_index()
    logger.info(f"BM25 index: {indexed} chunks indexed")

    # Run all 4 rounds
    all_rounds = {}

    # Round 1: Dense-only
    all_rounds["round_1_dense_only"] = evaluate_round(
        "Round 1: Dense Only", questions, run_dense_only
    )

    # Round 2: BM25-only
    all_rounds["round_2_bm25_only"] = evaluate_round(
        "Round 2: BM25 Only", questions, run_bm25_only
    )

    # Round 3: Hybrid RRF
    all_rounds["round_3_hybrid_rrf"] = evaluate_round(
        "Round 3: Hybrid RRF k=60", questions, run_hybrid_rrf
    )

    # Round 4: Hybrid RRF + JEV
    all_rounds["round_4_hybrid_rrf_jev"] = evaluate_round(
        "Round 4: Hybrid RRF + JEV", questions, run_hybrid_rrf_jev
    )

    # Comparison summary
    logger.info(f"\n{'='*70}")
    logger.info(f"  FINAL COMPARISON ACROSS ALL 4 ROUNDS")
    logger.info(f"{'='*70}")

    comparison = {}
    for round_key, data in all_rounds.items():
        m = data["metrics"]
        comparison[data["round_name"]] = {
            "term_recall_mean": m["term_recall_mean"],
            "perfect_recall_rate": m["perfect_recall_rate"],
            "source_accuracy": m["source_accuracy"],
            "redundancy_rate_mean": m["redundancy_rate_mean"],
            "latency_p50_ms": m["latency_p50_ms"]
        }
        logger.info(f"  {data['round_name']:40s} | Recall={m['term_recall_mean']:.3f} | Perfect={m['perfect_recall_rate']:.3f} | SrcAcc={m['source_accuracy']:.3f} | Redundancy={m['redundancy_rate_mean']:.3f} | P50={m['latency_p50_ms']}ms")

    # Save full report
    full_report = {
        "metadata": {
            "evaluation_timestamp": datetime.now().isoformat(),
            "questions_file": str(questions_file),
            "total_questions": len(questions),
            "top_k": TOP_K,
            "rrf_k": 60,
            "embedding_model": settings.EMBEDDING_MODEL,
            "jev_relevance_threshold": 0.38,
            "jev_redundancy_lambda": 0.40,
            "chunk_size_tokens": settings.CHUNK_SIZE_TOKENS,
            "chunk_overlap_tokens": settings.CHUNK_OVERLAP_TOKENS
        },
        "comparison_summary": comparison,
        "rounds": all_rounds
    }

    report_path = settings.get_absolute_path("./evaluation/reports/multiround_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    logger.info(f"\nFull report saved to: {report_path}")


if __name__ == "__main__":
    main()
