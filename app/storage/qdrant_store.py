import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings

logger = logging.getLogger(__name__)


class QdrantStore:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self.client = self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        # Check if remote QDRANT_URL is configured
        if settings.QDRANT_URL:
            try:
                logger.info(f"Connecting to Qdrant server at {settings.QDRANT_URL}")
                client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=10.0
                )
                # Test connectivity
                client.get_collections()
                return client
            except Exception as e:
                logger.warning(f"Failed to connect to Qdrant URL {settings.QDRANT_URL}: {e}. Falling back to embedded local storage.")
        
        # Embedded local storage
        storage_path = settings.get_absolute_path(settings.QDRANT_PATH or "./data/qdrant_storage")
        storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing embedded Qdrant with persistent storage at {storage_path}")
        return QdrantClient(path=str(storage_path))

    def _ensure_collection(self, vector_dim: int = 384) -> None:
        """
        Ensure the collection exists with the required vector dimension (384 for bge-small-en-v1.5).
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(f"Creating collection '{self.collection_name}' with vector dim {vector_dim} (Cosine)")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
                # Create payload indexes for efficient filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="subject",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD
                )
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")
            raise

    def upsert_chunks(
        self,
        chunk_ids: List[str],
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        batch_size: int = 64
    ) -> None:
        """Upsert embedded chunks into Qdrant in batches."""
        total = len(chunk_ids)
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            batch_ids = chunk_ids[i:end_idx]
            batch_vectors = vectors[i:end_idx]
            batch_payloads = payloads[i:end_idx]

            points = []
            for cid, vec, payload in zip(batch_ids, batch_vectors, batch_payloads):
                # Ensure point ID is a valid UUID or uint
                # Generate deterministic UUID from chunk_id string
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, cid))
                payload["chunk_id"] = cid
                points.append(qmodels.PointStruct(
                    id=point_id,
                    vector=vec,
                    payload=payload
                ))

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            logger.info(f"Upserted batch {i} to {end_idx} of {total} chunks into Qdrant")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 20,
        subjects: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Dense similarity search with optional metadata filters."""
        filter_conditions = []
        if subjects:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="subject",
                    match=qmodels.MatchAny(any=subjects)
                )
            )
        if document_ids:
            filter_conditions.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchAny(any=document_ids)
                )
            )

        query_filter = None
        if filter_conditions:
            query_filter = qmodels.Filter(must=filter_conditions)

        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True
            )
            search_results = response.points
        else:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True
            )

        results = []
        for r in search_results:
            item = dict(r.payload or {})
            item["score"] = float(r.score)
            results.append(item)
        return results

    def delete_by_document(self, document_id: str) -> None:
        """Remove all points belonging to a specific document."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=document_id)
                        )
                    ]
                )
            ),
            wait=True
        )
        logger.info(f"Deleted points for document_id {document_id} from Qdrant")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return collection info and vector count."""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vectors_count": getattr(info, "vectors_count", getattr(info, "points_count", 0)),
                "points_count": getattr(info, "points_count", 0),
                "status": getattr(info, "status", "ready")
            }
        except Exception as e:
            return {"error": str(e), "collection_name": self.collection_name}


qdrant_store = QdrantStore()
