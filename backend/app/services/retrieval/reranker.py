import logging
import os
from typing import List, Dict, Any
from app.services.vector_store.base import VectorResult

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.use_local = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
        self.hf_token = os.getenv("HF_TOKEN", "")
        self.model = None
        self.is_loaded = False
        
        if self.use_local:
            logger.info(f"Loading local CrossEncoder model: {model_name}...")
            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(model_name, max_length=512)
                self.is_loaded = True
                logger.info("Local CrossEncoder model loaded successfully.")
            except ImportError:
                logger.error("sentence-transformers not installed. Reranker disabled.")
            except Exception as e:
                logger.error(f"Failed to load CrossEncoder model: {e}")
        else:
            try:
                from huggingface_hub import InferenceClient
                self._hf_client = InferenceClient(token=self.hf_token)
                self.is_loaded = True
            except ImportError:
                logger.error("huggingface_hub not installed. Reranker disabled.")
                self.is_loaded = False
                self._hf_client = None

    def rerank(self, query: str, results: List[VectorResult], top_k: int = 5) -> List[VectorResult]:
        if not self.is_loaded or not results:
            return results[:top_k]
            
        try:
            if self.use_local:
                pairs = [(query, res.payload.get("content", "")) for res in results]
                scores = self.model.predict(pairs)
                for i, res in enumerate(results):
                    res.score = float(scores[i])
            else:
                if not self.hf_token:
                    logger.warning("HF_TOKEN is missing!")
                
                if self._hf_client:
                    # HF API expects [{"text": q, "text_pair": c}] format for sentence-transformers payload?
                    # Wait, InferenceClient doesn't have a direct "cross_encoder" method. It has text_classification or custom post.
                    # We can use _hf_client.post()
                    api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
                    inputs = [{"text": query, "text_pair": res.payload.get("content", "")} for res in results]
                    
                    import json
                    response_bytes = self._hf_client.post(json={"inputs": inputs, "options": {"wait_for_model": True}}, model=self.model_name)
                    scores_data = json.loads(response_bytes.decode("utf-8"))
                    
                    for i, res in enumerate(results):
                        s = scores_data[i]
                        if isinstance(s, dict) and "score" in s:
                            res.score = float(s["score"])
                        elif isinstance(s, list) and len(s) > 0 and "score" in s[0]:
                            res.score = float(s[0]["score"])
                        else:
                            res.score = float(s)
                            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:top_k]
