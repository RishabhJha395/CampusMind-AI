import asyncio
from app.services.rag.orchestrator import RAGService
import logging

logging.basicConfig(level=logging.INFO)

from app.services.embedding.local_embedder import LocalEmbedder
from app.services.vector_store.qdrant_store import QdrantStore
from app.services.llm.openrouter import OpenRouterService
import os

async def test_retrieval():
    embedder = LocalEmbedder()
    vector_store = QdrantStore(url=os.getenv("QDRANT_URL", "path=qdrant_data"))
    llm_service = OpenRouterService()
    rag = RAGService(vector_store, embedder, llm_service)
    
    query = "who is the HOD of Computer Science & Engineering"
    print(f"\n--- QUERY: {query} ---")
    context, sources = await rag.retrieve_context("dtu", query)
    
    print("\n--- RETRIEVED CONTEXT ---")
    for i, c in enumerate(context):
        print(f"\n[Chunk {i+1}] Source: {sources[i]['title']}")
        print(c)
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_retrieval())
