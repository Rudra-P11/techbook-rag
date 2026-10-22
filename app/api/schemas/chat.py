from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatFilters(BaseModel):
    subjects: Optional[List[str]] = Field(default_factory=list)
    document_ids: Optional[List[str]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    query: str = Field(..., max_length=4000)
    conversation_id: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Prior conversation messages [{'role': 'user'|'assistant', 'content': '...'}]")
    filters: Optional[ChatFilters] = Field(default_factory=ChatFilters)
    top_k: int = Field(default=6, ge=1, le=20)
    model: Optional[str] = Field(default=None, description="Generation model name (e.g. gpt-4o-mini, gpt-4o)")
    include_retrieval_debug: bool = True
    retrieval_mode: Optional[str] = Field(default="hybrid", description="dense_only | bm25_only | hybrid | hybrid_tuned | custom")
    rrf_k: Optional[int] = Field(default=60, ge=1, le=200, description="RRF smoothing constant")
    w_lex: Optional[float] = Field(default=1.0, ge=0.0, le=5.0, description="BM25 lexical weight factor")
    w_dense: Optional[float] = Field(default=1.0, ge=0.0, le=5.0, description="Dense vector weight factor")
    jev_enabled: Optional[bool] = Field(default=True, description="Enable JEV redundancy pruning and sufficiency gate")


class Citation(BaseModel):
    evidence_id: str
    document_id: str
    filename: str
    title: str
    pages: List[int]
    subject: Optional[str] = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    page_numbers: List[int]
    score: float
    text_preview: str
    filename: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    dense_rank: Optional[int] = None
    lexical_rank: Optional[int] = None
    dense_score: Optional[float] = None
    lexical_score: Optional[float] = None
    rrf_score: Optional[float] = None
    jev_score: Optional[float] = None
    final_rank: Optional[int] = None


class ChatMetrics(BaseModel):
    retrieval_latency_ms: int
    generation_latency_ms: int
    total_latency_ms: int
    retrieval_mode: Optional[str] = "hybrid"
    rrf_k: Optional[int] = 60
    w_lex: Optional[float] = 1.0
    dense_count: Optional[int] = 0
    lexical_count: Optional[int] = 0
    fused_count: Optional[int] = 0
    top_dense_score: Optional[float] = None
    top_lexical_score: Optional[float] = None
    top_rrf_score: Optional[float] = None
    jev_status: Optional[str] = "PASS"
    jev_pruned: Optional[int] = 0
    jev_total_score: Optional[float] = None
    redundancy_rate: Optional[float] = 0.0


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    metrics: ChatMetrics
    jev_decision: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None

