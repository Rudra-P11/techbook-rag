import time
import logging
import re
from typing import Optional, List, Dict, Any
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMetrics,
    RetrievedChunk
)
from app.guardrails.prompt_injection import injection_guardrail
from app.guardrails.citation_validation import citation_validator
from app.guardrails.domain_guardrail import domain_guardrail
from app.decision.jev_engine import jev_engine
from app.services.retrieval_service import retrieval_service
from app.generation.client import generation_client
from app.generation.local_synthesizer import local_synthesizer

logger = logging.getLogger(__name__)

# Calibrated minimum cosine similarity threshold for BGE-small-en-v1.5
RELEVANCE_DENSE_THRESHOLD = 0.38


def compute_pairwise_redundancy(evidence_list: List[Dict[str, Any]], threshold: float = 0.60) -> float:
    """Computes fraction of pairs exceeding Jaccard threshold."""
    if len(evidence_list) < 2:
        return 0.0
    texts = [e.get("text", "") for e in evidence_list]
    word_sets = [set(re.findall(r'\w+', t.lower())) for t in texts]
    redundant_pairs = 0
    total_pairs = 0
    for i in range(len(word_sets)):
        for j in range(i + 1, len(word_sets)):
            total_pairs += 1
            s1, s2 = word_sets[i], word_sets[j]
            if s1 and s2:
                jaccard = len(s1 & s2) / len(s1 | s2)
                if jaccard >= threshold:
                    redundant_pairs += 1
    return round((redundant_pairs / total_pairs) * 100.0, 1) if total_pairs > 0 else 0.0


class ChatService:
    def answer_query(self, request: ChatRequest) -> ChatResponse:
        start_total = time.perf_counter()
        jev_enabled = request.jev_enabled if request.jev_enabled is not None else True
        retrieval_mode = request.retrieval_mode or "hybrid"
        rrf_k = request.rrf_k or 60
        w_lex = request.w_lex if request.w_lex is not None else 1.0
        w_dense = request.w_dense if request.w_dense is not None else 1.0

        # Step 1: Domain & Safety Guardrails (Medical, Dangerous, Out-of-Scope)
        is_allowed, category, guardrail_msg = domain_guardrail.check_query_safety(request.query)
        if not is_allowed:
            total_latency_ms = int((time.perf_counter() - start_total) * 1000)
            logger.info(f"Query blocked by domain guardrail ({category}): '{request.query}'")
            return ChatResponse(
                answer=guardrail_msg,
                citations=[],
                retrieved_chunks=[],
                metrics=ChatMetrics(
                    retrieval_latency_ms=0,
                    generation_latency_ms=0,
                    total_latency_ms=total_latency_ms,
                    retrieval_mode=retrieval_mode,
                    rrf_k=rrf_k,
                    w_lex=w_lex,
                    jev_status="BLOCKED"
                ),
                conversation_id=request.conversation_id
            )

        # Step 2: Input validation & Prompt injection guardrail
        sanitized_query, was_flagged = injection_guardrail.sanitize_query(request.query)
        if was_flagged:
            logger.warning(f"Query flagged by prompt injection guardrail: '{request.query}'")

        # Step 3: JEV System-1 Pre-Retrieval Fast Gate (if enabled)
        jev_query_dec = None
        if jev_enabled:
            jev_query_dec = jev_engine.evaluate_query_intent(sanitized_query)
            if not jev_query_dec.requires_retrieval and jev_query_dec.direct_response:
                total_latency_ms = int((time.perf_counter() - start_total) * 1000)
                logger.info(f"JEV System-1 Fast Gate answered directly without retrieval (confidence: {jev_query_dec.confidence:.2f})")
                return ChatResponse(
                    answer=jev_query_dec.direct_response,
                    citations=[],
                    retrieved_chunks=[],
                    metrics=ChatMetrics(
                        retrieval_latency_ms=0,
                        generation_latency_ms=0,
                        total_latency_ms=total_latency_ms,
                        retrieval_mode=retrieval_mode,
                        rrf_k=rrf_k,
                        w_lex=w_lex,
                        jev_status="PRE_ROUTED"
                    ),
                    conversation_id=request.conversation_id
                )

        # Step 4: Multi-Mode Retrieval (Dense-Only, BM25-Only, Hybrid RRF, Tuned RRF, Custom)
        subjects = request.filters.subjects if request.filters else None
        document_ids = request.filters.document_ids if request.filters else None

        context_text, evidence_list, all_fused_chunks, retrieval_latency_ms, telemetry_stats = retrieval_service.retrieve(
            query=sanitized_query,
            subjects=subjects,
            document_ids=document_ids,
            top_k=request.top_k,
            retrieval_mode=retrieval_mode,
            rrf_k=rrf_k,
            w_dense=w_dense,
            w_lex=w_lex
        )

        # Step 5: JEV Joint Evidential Valuation & Redundancy Pruning
        pruned_count = 0
        total_jev_score = 0.0
        is_sufficient = True

        if jev_enabled and evidence_list:
            jev_context_res = jev_engine.calculate_joint_evidential_value(
                evidence_list=evidence_list,
                max_chunks=request.top_k or 6
            )
            pruned_count = jev_context_res.pruned_count
            total_jev_score = jev_context_res.total_jev_score
            is_sufficient = jev_context_res.is_sufficient

            if not is_sufficient:
                total_latency_ms = int((time.perf_counter() - start_total) * 1000)
                logger.info(f"JEV Relevance threshold not met (JEV score: {total_jev_score:.3f}). Abstaining without LLM call.")
                return ChatResponse(
                    answer="The provided technical books do not contain sufficient information to answer this question.",
                    citations=[],
                    retrieved_chunks=[],
                    metrics=ChatMetrics(
                        retrieval_latency_ms=retrieval_latency_ms,
                        generation_latency_ms=0,
                        total_latency_ms=total_latency_ms,
                        retrieval_mode=retrieval_mode,
                        rrf_k=rrf_k,
                        w_lex=w_lex,
                        jev_status="ABSTAIN",
                        jev_pruned=pruned_count,
                        jev_total_score=round(total_jev_score, 3)
                    ),
                    conversation_id=request.conversation_id
                )

            evidence_list = jev_context_res.selected_evidence

        # Format optimal context text
        context_blocks = []
        for idx, ev in enumerate(evidence_list, 1):
            context_blocks.append(f"[E{idx}] {ev.get('title', 'Textbook')} (Pages {ev.get('pages', 'N/A')}):\n{ev.get('text', '')}")
        context_text = "\n\n".join(context_blocks)

        redundancy_rate = compute_pairwise_redundancy(evidence_list)

        # Step 6: Grounded Generation (OpenAI or Local Deterministic Extractor Fallback)
        raw_answer = ""
        gen_latency_ms = 0
        synthesis_mode = "openai"

        if request.force_local_synthesis:
            synthesis_mode = "local_neural_extractor"
            raw_answer, gen_latency_ms = local_synthesizer.synthesize(sanitized_query, evidence_list)
        else:
            try:
                raw_answer, gen_latency_ms = generation_client.generate_answer(
                    query=sanitized_query,
                    context=context_text,
                    model=request.model,
                    history=request.history
                )
            except Exception as e:
                logger.warning(f"OpenAI generation unavailable ({e}). Falling back to local deterministic extractor.")
                synthesis_mode = "local_fallback"
                raw_answer, gen_latency_ms = local_synthesizer.synthesize(sanitized_query, evidence_list)

        # Step 7: Citation Validation & Normalization
        final_answer, citations = citation_validator.process_and_validate(
            raw_answer=raw_answer,
            evidence_list=evidence_list,
            format_inline=True
        )

        # Step 8: Retrieved chunk debug metadata
        retrieved_chunk_models = []
        if request.include_retrieval_debug:
            for ev in evidence_list:
                retrieved_chunk_models.append(RetrievedChunk(
                    chunk_id=ev["chunk_id"],
                    document_id=ev["document_id"],
                    page_numbers=ev["pages"],
                    score=round(ev["score"], 4),
                    text_preview=ev["text"][:250] + ("..." if len(ev["text"]) > 250 else ""),
                    filename=ev.get("filename"),
                    title=ev.get("title"),
                    subject=ev.get("subject"),
                    dense_rank=ev.get("dense_rank"),
                    lexical_rank=ev.get("lexical_rank"),
                    dense_score=round(ev["dense_score"], 4) if ev.get("dense_score") is not None else None,
                    lexical_score=round(ev["lexical_score"], 4) if ev.get("lexical_score") is not None else None,
                    rrf_score=round(ev.get("rrf_score", ev["score"]), 5),
                    jev_score=round(ev.get("jev_score", ev.get("dense_score", 0.0)), 4),
                    final_rank=ev.get("final_rank")
                ))

        total_latency_ms = int((time.perf_counter() - start_total) * 1000)

        jev_summary = {
            "enabled": jev_enabled,
            "requires_retrieval": jev_query_dec.requires_retrieval if jev_query_dec else True,
            "search_strategy": jev_query_dec.search_strategy if jev_query_dec else "HYBRID",
            "confidence": jev_query_dec.confidence if jev_query_dec else 1.0,
            "total_jev_score": round(total_jev_score, 3),
            "pruned_count": pruned_count,
            "is_sufficient": is_sufficient
        }

        metrics = ChatMetrics(
            retrieval_latency_ms=retrieval_latency_ms,
            generation_latency_ms=gen_latency_ms,
            total_latency_ms=total_latency_ms,
            retrieval_mode=telemetry_stats.get("retrieval_mode", retrieval_mode),
            rrf_k=telemetry_stats.get("rrf_k", rrf_k),
            w_lex=telemetry_stats.get("w_lex", w_lex),
            dense_count=telemetry_stats.get("dense_count", 0),
            lexical_count=telemetry_stats.get("lexical_count", 0),
            fused_count=telemetry_stats.get("fused_count", len(evidence_list)),
            top_dense_score=telemetry_stats.get("top_dense_score"),
            top_lexical_score=telemetry_stats.get("top_lexical_score"),
            top_rrf_score=telemetry_stats.get("top_rrf_score"),
            jev_status="PASS" if is_sufficient else "ABSTAIN",
            jev_pruned=pruned_count,
            jev_total_score=round(total_jev_score, 3),
            redundancy_rate=redundancy_rate,
            synthesis_mode=synthesis_mode
        )

        return ChatResponse(
            answer=final_answer,
            citations=citations,
            retrieved_chunks=retrieved_chunk_models,
            metrics=metrics,
            jev_decision=jev_summary,
            conversation_id=request.conversation_id
        )


chat_service = ChatService()
