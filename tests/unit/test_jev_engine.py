import pytest
from app.decision.jev_engine import jev_engine, SearchStrategy

def test_jev_fast_gate_greetings():
    decision = jev_engine.evaluate_query_intent("Hello")
    assert decision.requires_retrieval is False
    assert decision.search_strategy == SearchStrategy.NONE
    assert "TechBook RAG" in decision.direct_response

def test_jev_fast_gate_technical_query():
    decision = jev_engine.evaluate_query_intent("What is a forward pass in a neural network?")
    assert decision.requires_retrieval is True
    assert decision.search_strategy == SearchStrategy.HYBRID

def test_jev_joint_evidential_value_redundancy_pruning():
    evidence_list = [
        {
            "chunk_id": "c1",
            "dense_score": 0.82,
            "rrf_score": 0.032,
            "title": "Deep Learning Seth Weidman",
            "pages": "176-177",
            "text": "A forward pass in a neural network passes input features through layers to compute outputs."
        },
        {
            "chunk_id": "c2",
            "dense_score": 0.81,
            "rrf_score": 0.031,
            "title": "Deep Learning Seth Weidman Duplicate",
            "pages": "178",
            "text": "A forward pass in a neural network passes input features through layers to compute outputs."
        },
        {
            "chunk_id": "c3",
            "dense_score": 0.75,
            "rrf_score": 0.028,
            "title": "Deep Learning Math",
            "pages": "50",
            "text": "Backpropagation calculates gradients of loss function with respect to weights using chain rule."
        }
    ]
    
    result = jev_engine.calculate_joint_evidential_value(evidence_list, max_chunks=3)
    assert result.is_sufficient is True
    assert result.pruned_count >= 1
    assert len(result.selected_evidence) == 2
    assert "jev_score" in result.selected_evidence[0]
