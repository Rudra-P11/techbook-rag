import logging
from typing import List, Dict, Any, Optional
from app.ingestion.embedder import embedder
from app.storage.qdrant_store import qdrant_store
from app.config import settings

logger = logging.getLogger(__name__)


class DenseSearch:
    def search(
        self,
        query: str,
        top_k: int = settings.DENSE_TOP_K,
        subjects: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Embeds the query using the local SentenceTransformer model and
        performs Cosine ANN search in Qdrant.
        """
        try:
            query_vector = embedder.embed_query(query)
            results = qdrant_store.search(
                query_vector=query_vector,
                top_k=top_k,
                subjects=subjects,
                document_ids=document_ids
            )
            for r in results:
                r["search_type"] = "dense"
                r["dense_score"] = float(r.get("score", 0.0))
            return results
        except Exception as e:
            logger.error(f"Dense search error: {e}")
            return []


dense_search = DenseSearch()
