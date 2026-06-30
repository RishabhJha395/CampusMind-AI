import logging
import os
from typing import List
from app.services.embedding.base import BaseEmbedder

logger = logging.getLogger(__name__)

class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", batch_size: int = 32):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None
        self.use_local = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
        self.hf_token = os.getenv("HF_TOKEN", "")
        
        if not self.use_local:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(token=self.hf_token)
            except ImportError:
                logger.warning("huggingface_hub not installed, HF offloading disabled")
                self._hf_client = None
        
    @property
    def model(self):
        if not self.use_local:
            return None
            
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
            
            if self._hf_client:
                import numpy as np
                # The HF Inference API returns a raw list or numpy array
                raw_embeds = self._hf_client.feature_extraction(texts, model=self.model_name)
                # Ensure it's a list of lists of floats
                if hasattr(raw_embeds, "tolist"):
                    return raw_embeds.tolist()
                return list(raw_embeds)
            else:
                return []

    def embed_query(self, query: str) -> List[float]:
        res = self.embed_texts([query])
        return res[0] if res else []
