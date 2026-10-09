import sys
import json
import time
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.services.retrieval_service import retrieval_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_retrieval")


def evaluate():
    questions_file = settings.get_absolute_path("./evaluation/questions.jsonl")
    if not questions_file.exists():
        logger.error(f"Questions file not found: {questions_file}")
        return

    questions = []
    with open(questions_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    logger.info(f"Running retrieval evaluation on {len(questions)} benchmark questions...")

    latencies = []
    term_recall_hits = 0
    total_term_evaluated = 0

    for q in questions:
        query = q["query"]
        expected_terms = q.get("expected_terms", [])

        start = time.perf_counter()
        context_text, evidence_list, all_fused, latency_ms = retrieval_service.retrieve(
            query=query,
            top_k=6
        )
        latencies.append(latency_ms)

        # Check if expected terms appeared in retrieved context
        if expected_terms:
            total_term_evaluated += 1
            context_lower = context_text.lower()
            hit_count = sum(1 for term in expected_terms if term.lower() in context_lower)
            if hit_count >= 1:
                term_recall_hits += 1

        logger.info(f"Q: '{query[:40]}...' | Latency: {latency_ms}ms | Retrieved passages: {len(evidence_list)}")

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    recall_rate = (term_recall_hits / total_term_evaluated) if total_term_evaluated else 0

    report = {
        "benchmark_questions": len(questions),
        "avg_retrieval_latency_ms": round(avg_latency, 2),
        "term_recall_rate": round(recall_rate, 2),
        "latencies_ms": latencies
    }

    report_path = settings.get_absolute_path("./evaluation/reports/retrieval_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Retrieval Evaluation Summary:")
    logger.info(f"Average Retrieval Latency: {avg_latency:.1f} ms")
    logger.info(f"Keyword/Term Recall: {recall_rate*100:.1f}%")
    logger.info(f"Report saved to: {report_path}")


if __name__ == "__main__":
    evaluate()
