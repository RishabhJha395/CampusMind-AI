from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any, Optional

class BaseLLMService(ABC):
    
    @abstractmethod
    def build_system_prompt(self, context_texts: List[str], university_name: str, bot_persona: str = "") -> str:
        """Assembles the system prompt using retrieved context and university identity."""
        pass
        
    @abstractmethod
    async def generate_response(self, query: str, context_texts: List[str], university_name: str, bot_persona: str = "") -> str:
        """Generate a complete text response based on query and context."""
        pass
        
    @abstractmethod
    async def generate_response_stream(self, query: str, context_texts: List[str], university_name: str, bot_persona: str = "") -> AsyncGenerator[str, None]:
        """Generate a streaming text response based on query and context."""
        pass
