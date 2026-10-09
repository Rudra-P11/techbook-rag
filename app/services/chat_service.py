import time
import logging
from typing import Optional, List
from app.api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMetrics,
    RetrievedChunk
)
from app.guardrails.prompt_injection import injection_guardrail
from app.guardrails.citation_validation import citation_validator
from app.guardrails.domain_guardrail import domain_guardrail
from app.services.retrieval_service import retrieval_service
from app.generation.client import generation_client

logger = logging.getLogger(__name__)

# Calibrated minimum cosine similarity threshold for BGE-small-en-v1.5
RELEVANCE_DENSE_THRESHOLD = 0.38


class ChatService:
    def answer_query(self, request: ChatRequest) -> ChatResponse:
        start_total = time.perf_counter()

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
                    total_latency_ms=total_latency_ms
                ),
                conversation_id=request.conversation_id
            )

        # Step 2: Input validation & Prompt injection guardrail
        sanitized_query, was_flagged = injection_guardrail.sanitize_query(request.query)
        if was_flagged:
            logger.warning(f"Query flagged by prompt injection guardrail: '{request.query}'")

        # Step 3: Hybrid Retrieval
        subjects = request.filters.subjects if request.filters else None
        document_ids = request.filters.document_ids if request.filters else None

        context_text, evidence_list, all_fused_chunks, retrieval_latency_ms = retrieval_service.retrieve(
            query=sanitized_query,
            subjects=subjects,
            document_ids=document_ids,
            top_k=request.top_k
        )

        # Step 4: Relevance Threshold Guardrail (FR-07)
        # Check if the retrieved evidence is actually relevant to the query.
        max_dense_score = max([ev.get("dense_score", 0.0) for ev in evidence_list], default=0.0)
        max_lexical_score = max([ev.get("lexical_score", 0.0) for ev in evidence_list], default=0.0)

        is_insufficient = (
            not evidence_list or 
            (max_dense_score < RELEVANCE_DENSE_THRESHOLD and max_lexical_score <= 0.0)
        )

        if is_insufficient:
            total_latency_ms = int((time.perf_counter() - start_total) * 1000)
            logger.info(f"Relevance threshold not met (dense: {max_dense_score:.3f}, lexical: {max_lexical_score:.3f}). Abstaining without LLM call.")
            return ChatResponse(
                answer="The provided technical books do not contain sufficient information to answer this question.",
                citations=[],
                retrieved_chunks=[],
                metrics=ChatMetrics(
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=0,
                    total_latency_ms=total_latency_ms
                ),
                conversation_id=request.conversation_id
            )

        # Step 5: Generation via OpenAI
        try:
            raw_answer, gen_latency_ms = generation_client.generate_answer(
                query=sanitized_query,
                context=context_text,
                model=request.model
            )
        except Exception as e:
            total_latency_ms = int((time.perf_counter() - start_total) * 1000)
            logger.error(f"Generation failure: {e}")
            return ChatResponse(
                answer=f"Unable to generate an answer at this time due to an upstream provider error: {str(e)}",
                citations=[],
                retrieved_chunks=[],
                metrics=ChatMetrics(
                    retrieval_latency_ms=retrieval_latency_ms,
                    generation_latency_ms=0,
                    total_latency_ms=total_latency_ms
                ),
                conversation_id=request.conversation_id
            )

        # Step 5: Citation Validation & Formatting
        final_answer, citations = citation_validator.process_and_validate(
            raw_answer=raw_answer,
            evidence_list=evidence_list,
            format_inline=True
        )

        # Step 6: Retrieved chunk debug metadata
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
                    final_rank=ev.get("final_rank")
                ))

        total_latency_ms = int((time.perf_counter() - start_total) * 1000)

        return ChatResponse(
            answer=final_answer,
            citations=citations,
            retrieved_chunks=retrieved_chunk_models,
            metrics=ChatMetrics(
                retrieval_latency_ms=retrieval_latency_ms,
                generation_latency_ms=gen_latency_ms,
                total_latency_ms=total_latency_ms
            ),
            conversation_id=request.conversation_id
        )


chat_service = ChatService()
