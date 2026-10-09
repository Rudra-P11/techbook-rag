import logging
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self._model = None

    def _load_model(self):
        if self._model is None:
            logger.info(f"Loading embedding model '{self.model_name}' on device '{self.device}'...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Embedding model successfully loaded.")
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of text strings into normalized float vectors.
        """
        if not texts:
            return []
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single search query.
        """
        model = self._load_model()
        vec = model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        return vec.tolist()


embedder = EmbeddingService()
