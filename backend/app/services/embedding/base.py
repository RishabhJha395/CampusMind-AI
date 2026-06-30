from abc import ABC, abstractmethod
from typing import List

class BaseEmbedder(ABC):
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Convert a list of strings into a list of vector embeddings."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Convert a single query string into a vector embedding."""
        pass
