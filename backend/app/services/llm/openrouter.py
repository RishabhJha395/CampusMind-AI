import os
import json
import logging
import httpx
from typing import AsyncGenerator, List, Dict, Any, Optional
from app.services.llm.base import BaseLLMService

logger = logging.getLogger(__name__)

class OpenRouterService(BaseLLMService):
    def __init__(
        self, 
        api_key: str = None, 
        primary_model: str = "google/gemini-2.5-flash",
        fallback_model: str = "google/gemini-2.5-flash",
        max_tokens: int = 1024,
        temperature: float = 0.3
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = httpx.AsyncClient(timeout=60.0)

    def build_system_prompt(self, context_texts: List[str], university_name: str, bot_persona: str = "") -> str:
        context_str = "\n\n".join([f"--- Context {i+1} ---\n{text}" for i, text in enumerate(context_texts)])
        
        persona = bot_persona or f"You are the official AI assistant for {university_name}."
        
        prompt = f"""{persona}
You are an AI assistant that answers questions STRICTLY AND ONLY using the information provided in the CONTEXT below.

CRITICAL RULES:
1. ABSOLUTELY NO HALLUCINATION. You must never invent, guess, or pull information from your pre-trained knowledge.
2. If the user's question cannot be explicitly answered by reading the CONTEXT, you must reply exactly with: "I don't have enough information about that right now."
3. If the context contains conflicting information (e.g., two different people listed as HOD), mention both and state where they were found.
4. Be concise, polite, and professional.

CONTEXT:
{context_str}
"""
        return prompt

    async def _make_api_call(self, messages: List[Dict[str, str]], stream: bool = False, model: str = None) -> httpx.Response:
        """Helper to make the actual HTTP call to OpenRouter with retries and fallback."""
        if not self.api_key:
            raise ValueError("OpenRouter API key is not set.")
            
        target_model = model or self.primary_model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/CampusMindAI", 
            "X-Title": "CampusMind AI",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": stream,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            # We use a stream request if stream=True, else standard post
            if stream:
                req = self.client.build_request("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response = await self.client.send(req, stream=True)
            else:
                response = await self.client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            logger.warning(f"OpenRouter API error {status} with model {target_model}: {e.response.text}")
            
            # If ANY error happens on the primary model, fall back!
            if target_model == self.primary_model and self.fallback_model:
                logger.info(f"Falling back to model {self.fallback_model}")
                return await self._make_api_call(messages, stream=stream, model=self.fallback_model)
            
            raise
        except Exception as e:
            logger.error(f"OpenRouter connection error: {str(e)}")
            if target_model == self.primary_model and self.fallback_model:
                logger.info(f"Falling back to model {self.fallback_model} due to connection error")
                return await self._make_api_call(messages, stream=stream, model=self.fallback_model)
            raise

    async def generate_response(self, query: str, context_texts: List[str], university_name: str, bot_persona: str = "") -> str:
        system_prompt = self.build_system_prompt(context_texts, university_name, bot_persona)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = await self._make_api_call(messages, stream=False)
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        return "I'm sorry, I couldn't generate a response."

    async def generate_text(self, messages: List[Dict[str, str]]) -> str:
        """Raw LLM call without RAG context wrapper, useful for query expansion/classification."""
        response = await self._make_api_call(messages, stream=False)
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        return ""

    async def generate_response_stream(self, query: str, context_texts: List[str], university_name: str, bot_persona: str = "") -> AsyncGenerator[str, None]:
        system_prompt = self.build_system_prompt(context_texts, university_name, bot_persona)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = await self._make_api_call(messages, stream=True)
        
        async for chunk in response.aiter_lines():
            if chunk.startswith("data: "):
                data_str = chunk[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                except json.JSONDecodeError:
                    continue
