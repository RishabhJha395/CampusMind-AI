import logging
from typing import List
from app.services.embedding.base import BaseEmbedder

logger = logging.getLogger(__name__)

class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        
    @property
    def model(self):
        # Lazy loading to save memory until first use
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            # Force CPU usage to optimize for free tier (Render)
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info("Model loaded successfully")
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
            
        logger.debug(f"Embedding {len(texts)} texts in batches of {self.batch_size}")
        
        # sentence-transformers encode method supports batching and normalization
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True, # L2 normalization required for Cosine similarity
            convert_to_numpy=True,
            show_progress_bar=False
        )
        
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]
