import os
from functools import lru_cache
from typing import Generator
from fastapi import Depends
from app.services.vector_store.qdrant_store import QdrantStore
from app.services.embedding.local_embedder import LocalEmbedder
from app.services.llm.openrouter import OpenRouterService
from app.services.rag.orchestrator import RAGService

@lru_cache()
def get_vector_store() -> QdrantStore:
    # In production, these should come from config/settings
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY", None)
    return QdrantStore(url=url, api_key=api_key)

@lru_cache()
def get_embedder() -> LocalEmbedder:
    model_name = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    return LocalEmbedder(model_name=model_name, batch_size=batch_size)

@lru_cache()
def get_llm_service() -> OpenRouterService:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    primary_model = os.getenv("LLM_MODEL", "google/gemini-2.5-flash:free")
    fallback_model = os.getenv("LLM_MODEL_FALLBACK", "deepseek/deepseek-r1:free")
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    return OpenRouterService(
        api_key=api_key,
        primary_model=primary_model,
        fallback_model=fallback_model,
        max_tokens=max_tokens,
        temperature=temperature
    )

@lru_cache()
def get_rag_service(
    vector_store: QdrantStore = Depends(get_vector_store),
    embedder: LocalEmbedder = Depends(get_embedder),
    llm: OpenRouterService = Depends(get_llm_service)
) -> RAGService:
    return RAGService(vector_store=vector_store, embedder=embedder, llm_service=llm)
