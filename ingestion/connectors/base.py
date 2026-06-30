from abc import ABC, abstractmethod
from typing import AsyncGenerator
from ingestion.models.schemas import Document

class BaseConnector(ABC):
    
    @abstractmethod
    async def extract(self) -> AsyncGenerator[Document, None]:
        """
        Extracts documents from the source.
        Yields Document objects one by one to avoid high memory usage.
        """
        pass
