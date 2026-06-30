import logging
import os
import httpx
from typing import List, Dict, Any
from app.services.vector_store.base import VectorResult

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self.use_local = os.getenv("USE_LOCAL_MODELS", "false").lower() == "true"
        self.hf_token = os.getenv("HF_TOKEN", "")
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
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
            self.is_loaded = True # HTTP API is always "loaded"

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
                
                headers = {"Authorization": f"Bearer {self.hf_token}"} if self.hf_token else {}
                inputs = [{"text": query, "text_pair": res.payload.get("content", "")} for res in results]
                
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(self.api_url, headers=headers, json={"inputs": inputs, "options": {"wait_for_model": True}})
                    response.raise_for_status()
                    scores_data = response.json()
                    
                    # HF Inference API for cross-encoder returns a list of lists of dicts or list of floats
                    # If it's a classification model, it might return [{"label": "LABEL_0", "score": 0.9}, ...]
                    for i, res in enumerate(results):
                        s = scores_data[i]
                        # Handle both single float and dict format
                        if isinstance(s, dict) and "score" in s:
                            res.score = float(s["score"])
                        elif isinstance(s, list) and len(s) > 0 and "score" in s[0]:
                            # Sometimes returns list of dicts for each pair
                            res.score = float(s[0]["score"])
                        else:
                            res.score = float(s)
                            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:top_k]
