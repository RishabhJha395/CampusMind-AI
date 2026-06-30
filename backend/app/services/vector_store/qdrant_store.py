import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.services.vector_store.base import BaseVectorStore, VectorResult

logger = logging.getLogger(__name__)

class QdrantStore(BaseVectorStore):
    def __init__(self, url: str, api_key: Optional[str] = None):
        if url == ":memory:":
            self.client = QdrantClient(location=":memory:")
            logger.info("Initialized Qdrant client in memory mode")
        elif url.startswith("path="):
            path = url.split("path=")[1]
            self.client = QdrantClient(path=path)
            logger.info(f"Initialized Qdrant client at local path {path}")
        else:
            self.client = QdrantClient(url=url, api_key=api_key)
            logger.info(f"Initialized Qdrant client at {url}")

    def check_health(self) -> bool:
        try:
            # We can use get_collections to test basic connectivity
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    def create_collection(self, collection_name: str, vector_size: int, distance_metric: str = "Cosine") -> bool:
        try:
            distance = models.Distance.COSINE
            if distance_metric.upper() == "EUCLID":
                distance = models.Distance.EUCLID
            elif distance_metric.upper() == "DOT":
                distance = models.Distance.DOT

            # Check if collection exists
            collections = self.client.get_collections().collections
            if any(c.name == collection_name for c in collections):
                logger.info(f"Collection {collection_name} already exists.")
                return True

            logger.info(f"Creating collection {collection_name}...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=distance
                ),
                # Use scalar quantization for free tier memory optimization
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                )
            )
            
            # Create essential payload indexes
            indexes = ["university_id", "category", "doc_type", "content_hash"]
            for field in indexes:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
            # Create Full-Text index for hybrid search
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="content",
                field_schema=models.TextIndexParams(
                    type="text",
                    tokenizer=models.TokenizerType.WORD,
                    min_token_len=2,
                    max_token_len=15,
                    lowercase=True
                )
            )
            
            logger.info(f"Collection {collection_name} created successfully.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """
        Expected format for each point in `points`:
        {
            "id": "uuid-string",
            "vector": [0.1, 0.2, ...],
            "payload": {"university_id": "dtu", "content": "..."}
        }
        """
        try:
            qdrant_points = [
                models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {})
                ) for p in points
            ]
            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            return False

    def search(self, collection_name: str, query_vector: List[float], limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[VectorResult]:
        try:
            # Build Qdrant filter object if filters are provided
            qdrant_filter = None
            if filters:
                must_conditions = []
                for key, value in filters.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                if must_conditions:
                    qdrant_filter = models.Filter(must=must_conditions)

            results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=limit
            ).points
            
            return [
                VectorResult(id=str(r.id), score=r.score, payload=r.payload)
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to search collection {collection_name}: {e}")
            return []

    def text_search(self, collection_name: str, query_text: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[VectorResult]:
        """Performs a full-text exact keyword search using Qdrant Scroll API with text filter."""
        try:
            # Build Qdrant filter object
            must_conditions = []
            
            # 1. Base metadata filters (university_id, etc.)
            if filters:
                for key, value in filters.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                    
            # 2. Text match condition on 'content' field
            must_conditions.append(
                models.FieldCondition(
                    key="content",
                    match=models.MatchText(text=query_text)
                )
            )

            qdrant_filter = models.Filter(must=must_conditions)

            # Scroll to find exact text matches (since it's a payload filter, not a vector search)
            records, _ = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=qdrant_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Since scroll doesn't have a semantic 'score', we assign a flat score or keyword matching score if possible.
            # Qdrant scroll doesn't return scores. We'll assign a baseline score of 1.0 for exact matches.
            return [
                VectorResult(id=str(r.id), score=1.0, payload=r.payload)
                for r in records
            ]
        except Exception as e:
            logger.error(f"Failed to perform text_search on {collection_name}: {e}")
            return []

    def delete(self, collection_name: str, point_ids: List[str]) -> bool:
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=point_ids)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete points from {collection_name}: {e}")
            return False
