from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class VectorResult(BaseModel):
    id: str
    score: float
    payload: Dict[str, Any]

class BaseVectorStore(ABC):
    
    @abstractmethod
    def create_collection(self, collection_name: str, vector_size: int, distance_metric: str) -> bool:
        """Create a new collection if it doesn't exist."""
        pass
        
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete an existing collection."""
        pass
        
    @abstractmethod
    def upsert(self, collection_name: str, points: List[Dict[str, Any]]) -> bool:
        """Insert or update vectors with payloads."""
        pass
        
    @abstractmethod
    def search(self, collection_name: str, query_vector: List[float], limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[VectorResult]:
        """Search for similar vectors."""
        pass
        
    @abstractmethod
    def delete(self, collection_name: str, point_ids: List[str]) -> bool:
        """Delete specific points by ID."""
        pass
        
    @abstractmethod
    def check_health(self) -> bool:
        """Check if the vector store is reachable and healthy."""
        pass
