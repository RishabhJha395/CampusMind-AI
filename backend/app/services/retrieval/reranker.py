import logging
from typing import List, Dict, Any
from app.services.vector_store.base import VectorResult

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        logger.info(f"Loading CrossEncoder model: {model_name}...")
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(model_name, max_length=512)
            self.is_loaded = True
            logger.info("CrossEncoder model loaded successfully.")
        except ImportError:
            logger.error("sentence-transformers not installed. Reranker disabled.")
            self.is_loaded = False
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder model: {e}")
            self.is_loaded = False

    def rerank(self, query: str, results: List[VectorResult], top_k: int = 5) -> List[VectorResult]:
        """
        Reranks a list of VectorResults based on their semantic relevance to the query.
        """
        if not self.is_loaded or not results:
            return results[:top_k]
            
        try:
            # Prepare pairs of (query, document_text)
            pairs = []
            for res in results:
                content = res.payload.get("content", "")
                pairs.append((query, content))
                
            # Score pairs
            scores = self.model.predict(pairs)
            
            # Attach scores and sort
            for i, res in enumerate(results):
                res.score = float(scores[i])  # Override vector/RRF score with CrossEncoder score
                
            # Sort descending by new score
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return results[:top_k]
