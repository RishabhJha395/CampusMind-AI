import logging
import os
import httpx
from typing import List
from app.services.embedding.base import BaseEmbedder

logger = logging.getLogger(__name__)

class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        self.use_local = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
        self.hf_token = os.getenv("HF_TOKEN", "")
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/{self.model_name}"
        
    @property
    def model(self):
        if not self.use_local:
            return None
            
        # Lazy loading to save memory until first use
        if self._model is None:
            logger.info(f"Loading local embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name, device="cpu")
            logger.info("Local model loaded successfully")
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
            
        logger.debug(f"Embedding {len(texts)} texts in batches of {self.batch_size}")
        
        if self.use_local:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embeddings.tolist()
        else:
            if not self.hf_token:
                logger.warning("HF_TOKEN is missing! Using unauthenticated requests which may be heavily rate-limited.")
            
            headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
            
            # Use sync httpx since this is called synchronously in many places, or we can use a basic requests-like approach
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
                response.raise_for_status()
                return response.json()

    def embed_query(self, query: str) -> List[float]:
        return self.embed_texts([query])[0]
