import logging
from typing import List
from app.services.llm.openrouter import OpenRouterService

logger = logging.getLogger(__name__)

class QueryExpansionService:
    def __init__(self, llm_service: OpenRouterService):
        self.llm_service = llm_service
        
    async def expand_query(self, query: str) -> List[str]:
        """
        Uses the LLM to generate 3 semantic variations of the user's query.
        Returns a list of 4 queries (original + 3 variations).
        """
        prompt = f"""You are an expert search engine query expander.
The user is searching a university knowledge base (containing rulebooks, syllabi, admission schedules, circulars, etc.).

Original Query: "{query}"

Generate 3 alternative search queries that mean the exact same thing but use different vocabulary, synonyms, or official terminology (e.g. "syllabus" -> "scheme of teaching", "schedule" -> "timeline").
Return ONLY the 3 queries separated by newlines, with no bullet points, numbers, or introductory text.
"""
        messages = [{"role": "user", "content": prompt}]
        
        try:
            # We assume LLM service has generate_text available
            # If we fall back to a smaller/faster model for expansion, we could do it here
            response = await self.llm_service.generate_text(messages)
            
            variations = [v.strip() for v in response.split('\n') if v.strip()]
            
            # Clean up potential LLM artifacts (like 1., -, etc.)
            clean_variations = []
            for v in variations:
                import re
                cleaned = re.sub(r'^[\d\.\-\*\s]+', '', v)
                if cleaned:
                    clean_variations.append(cleaned)
                    
            # Return original + top 3 variations
            return [query] + clean_variations[:3]
            
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return [query]
