import re
import math
import logging
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SearchStrategy(str):
    HYBRID = "hybrid"
    DENSE_ONLY = "dense_only"
    LEXICAL_ONLY = "lexical_only"
    NONE = "none"

class JEVQueryDecision(BaseModel):
    requires_retrieval: bool = Field(description="Noul boolean: whether vector/lexical retrieval is required")
    search_strategy: str = Field(default="hybrid", description="Choice: recommended search strategy")
    confidence: float = Field(default=1.0, description="Score: confidence rating (0.0 to 1.0)")
    direct_response: Optional[str] = Field(default=None, description="Direct answer if retrieval is skipped")

class JEVContextResult(BaseModel):
    selected_evidence: List[Dict[str, Any]]
    total_jev_score: float
    is_sufficient: bool
    pruned_count: int

class JEVDecisionEngine:
    """
    System 1 Probabilistic Decision Model (Joint Evidential Valuation).
    Operates as a high-speed, zero-API-cost decision gate governing:
    1. Pre-Retrieval Routing (Direct Answer vs Hybrid Search)
    2. Post-Retrieval Joint Evidential Value (JEV) Context Truncation & Redundancy Removal
    3. Evidence Sufficiency Decision Gate
    """

    def __init__(self, relevance_threshold: float = 0.38, redundancy_lambda: float = 0.40):
        self.relevance_threshold = relevance_threshold
        self.redundancy_lambda = redundancy_lambda

    def evaluate_query_intent(self, query: str) -> JEVQueryDecision:
        """
        System 1 Fast Decision Gate: Determines query intent, search routing, or direct response.
        Zero API cost — evaluates syntax, semantic length, keywords, and intent heuristics.
        """
        clean_q = query.strip().lower()
        words = clean_q.split()

        # 1. Greetings & Meta Conversational Queries (Direct Answer, Skip Retrieval)
        greetings = {"hi", "hello", "hey", "greetings", "good morning", "good evening", "who are you", "what can you do"}
        if clean_q in greetings or (len(words) <= 2 and clean_q in greetings):
            return JEVQueryDecision(
                requires_retrieval=False,
                search_strategy=SearchStrategy.NONE,
                confidence=0.99,
                direct_response="Hello! I am **TechBook RAG**, an intelligent technical knowledge assistant grounded in 11 textbooks across SQL, Deep Learning, Python, and Software Engineering. How can I assist you today?"
            )

        # 2. Non-Technical / Out-of-Domain Topic Interception (Astrology, Cooking, Sports, Pop Culture, etc.)
        non_technical_keywords = {
            "astrology", "horoscope", "zodiac", "astrological", "tarot", "sun sign", "star sign",
            "recipe", "baking", "cook", "cooking", "cuisine", "ingredient",
            "cricket", "football", "basketball", "soccer", "tennis", "olympics", "ipl",
            "movie", "film", "actor", "actress", "celebrity", "gossip", "pop culture",
            "fashion", "makeup", "skincare", "horoscopes", "superstition", "mythology"
        }
        query_terms = set(re.findall(r'\w+', clean_q))
        matched_out_of_scope = query_terms.intersection(non_technical_keywords)
        if matched_out_of_scope:
            topic = next(iter(matched_out_of_scope))
            logger.info(f"JEV Pre-Gate intercepted non-technical query (topic: '{topic}'): '{query}'")
            return JEVQueryDecision(
                requires_retrieval=False,
                search_strategy=SearchStrategy.NONE,
                confidence=0.98,
                direct_response=f"The query ('{query}') falls outside the domain of computer science, SQL, Python, machine learning, and systems engineering textbooks indexed in TechBook RAG."
            )

        # 3. Pure Code / Exact Identifier Queries (Lexical Preference)
        code_indicators = ["select ", "from ", "where ", "def ", "class ", "import ", "err ", "exception", "ora-", "syntaxerror"]
        if any(indicator in clean_q for indicator in code_indicators) and len(words) < 8:
            return JEVQueryDecision(
                requires_retrieval=True,
                search_strategy=SearchStrategy.HYBRID,
                confidence=0.90
            )

        # 4. Standard Technical Conceptual Queries (Hybrid RRF Search)
        return JEVQueryDecision(
            requires_retrieval=True,
            search_strategy=SearchStrategy.HYBRID,
            confidence=0.95
        )

    def compute_jaccard_similarity(self, text1: str, text2: str) -> float:
        """Computes word-level Jaccard similarity between two text snippets."""
        set1 = set(re.findall(r'\w+', text1.lower()))
        set2 = set(re.findall(r'\w+', text2.lower()))
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def calculate_joint_evidential_value(
        self, 
        evidence_list: List[Dict[str, Any]], 
        max_chunks: int = 6
    ) -> JEVContextResult:
        """
        Calculates Joint Evidential Value (JEV) across retrieved candidate passages.
        Optimizes Joint Utility JEV(S) = sum(Relevance) - lambda * sum(Redundancy).
        Trims low-utility/redundant context before passing to LLM.
        """
        if not evidence_list:
            return JEVContextResult(selected_evidence=[], total_jev_score=0.0, is_sufficient=False, pruned_count=0)

        selected: List[Dict[str, Any]] = []
        total_jev = 0.0
        pruned_count = 0

        for candidate in evidence_list:
            # Individual relevance score (blend of dense similarity & RRF rank)
            dense_score = candidate.get("dense_score") or 0.0
            rrf_score = candidate.get("rrf_score") or candidate.get("score") or 0.0
            
            # Base relevance utility
            rel_utility = max(dense_score, rrf_score * 30.0) # Scale RRF score to [0,1] domain

            # Calculate redundancy against already selected passages
            max_redundancy = 0.0
            for sel in selected:
                sim = self.compute_jaccard_similarity(candidate.get("text", ""), sel.get("text", ""))
                if sim > max_redundancy:
                    max_redundancy = sim

            # Joint Evidential Value (JEV) formula: Marginal Utility adjusted by information redundancy
            jev_candidate_score = rel_utility * (1.0 - (self.redundancy_lambda * max_redundancy))

            # Prune if candidate is highly redundant (similarity > 0.60) and provides low marginal novelty
            is_redundant = max_redundancy > 0.85 or (max_redundancy > 0.60 and jev_candidate_score < 0.55)
            if is_redundant:
                pruned_count += 1
                logger.debug(f"JEV pruned redundant candidate chunk {candidate.get('chunk_id')} (similarity: {max_redundancy:.2f})")
                continue

            candidate["jev_score"] = round(jev_candidate_score, 4)
            selected.append(candidate)
            total_jev += jev_candidate_score

            if len(selected) >= max_chunks:
                break

        # Calibrated evidence sufficiency decision gate:
        # Require either exact keyword match (BM25 > 0) OR strong dense semantic similarity (>= 0.52)
        max_dense = max([c.get("dense_score", 0.0) for c in selected], default=0.0)
        max_lexical = max([c.get("lexical_score", 0.0) for c in selected], default=0.0)

        is_sufficient = len(selected) > 0 and (
            (max_lexical > 0.0 and max_dense >= 0.38) or (max_dense >= 0.52)
        )

        return JEVContextResult(
            selected_evidence=selected,
            total_jev_score=round(total_jev, 4),
            is_sufficient=is_sufficient,
            pruned_count=pruned_count
        )


jev_engine = JEVDecisionEngine()

