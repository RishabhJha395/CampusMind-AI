import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.services.vector_store.base import BaseVectorStore, VectorResult
from app.services.embedding.base import BaseEmbedder
from app.services.llm.base import BaseLLMService
from app.config.universities.registry import registry
from app.services.retrieval.query_expansion import QueryExpansionService
from app.services.retrieval.reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: BaseEmbedder,
        llm_service: BaseLLMService
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_service = llm_service
        
        # Initialize Advanced RAG components
        self.query_expander = QueryExpansionService(llm_service)
        self.reranker = CrossEncoderReranker()

    def _reciprocal_rank_fusion(self, search_results_lists: List[List[VectorResult]], k: int = 60) -> List[VectorResult]:
        """Merges multiple lists of VectorResults using Reciprocal Rank Fusion."""
        fused_scores = {}
        payload_map = {}
        
        for results in search_results_lists:
            for rank, doc in enumerate(results):
                doc_id = doc.id
                if doc_id not in fused_scores:
                    fused_scores[doc_id] = 0.0
                    payload_map[doc_id] = doc.payload
                
                # RRF Formula: 1 / (k + rank)
                fused_scores[doc_id] += 1.0 / (k + rank)
                
        # Sort by fused score
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        # Reconstruct VectorResult list
        fused_results = []
        for doc_id in sorted_ids:
            fused_results.append(
                VectorResult(
                    id=doc_id,
                    score=fused_scores[doc_id],
                    payload=payload_map[doc_id]
                )
            )
            
        return fused_results

    async def retrieve_context(self, university_id: str, query: str, top_k: int = 20, retrieve_k: int = 40) -> tuple[List[str], List[Dict[str, Any]]]:
        """
        Retrieves relevant context using Query Expansion -> Hybrid Search -> RRF -> Cross-Encoder Reranking.
        """
        try:
            uni_config = registry.get_university(university_id)
            collection_name = uni_config.vector_store.collection_name
        except KeyError:
            logger.error(f"University {university_id} not found in registry.")
            return [], []

        filters = {"university_id": university_id}
        all_search_results = []
        
        # 1. Expand Query
        expanded_queries = await self.query_expander.expand_query(query)
        logger.info(f"Expanded queries: {expanded_queries}")
        
        # 2. Dense Search for all query variations
        for eq in expanded_queries:
            query_vector = self.embedder.embed_query(eq)
            dense_res = self.vector_store.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=retrieve_k,
                filters=filters
            )
            all_search_results.append(dense_res)
            
        # 3. Text Search (Exact Keyword) on original query
        if hasattr(self.vector_store, 'text_search'):
            text_res = self.vector_store.text_search(
                collection_name=collection_name,
                query_text=query,
                limit=retrieve_k,
                filters=filters
            )
            if text_res:
                all_search_results.append(text_res)
                
        # 4. Reciprocal Rank Fusion
        fused_results = self._reciprocal_rank_fusion(all_search_results)
        
        # Take top 20 candidates for reranking
        candidates = fused_results[:retrieve_k]
        
        # 5. Cross-Encoder Reranking
        reranked_results = self.reranker.rerank(query, candidates, top_k=top_k)
        
        # 6. Build final context
        context_texts = []
        sources = []
        
        for res in reranked_results:
            payload = res.payload
            content = payload.get("content", "")
            if content:
                context_texts.append(content)
                
            source_info = {
                "url": payload.get("source_url", ""),
                "title": payload.get("title", "Untitled Document"),
                "score": res.score
            }
            sources.append(source_info)
            
        return context_texts, sources

    async def chat(self, university_id: str, query: str, stream: bool = False) -> Dict[str, Any]:
        """Generate a single non-streaming response."""
        try:
            uni_config = registry.get_university(university_id)
        except KeyError:
            return {"error": "Invalid university ID"}

        context_texts, sources = await self.retrieve_context(university_id, query)
        
        response = await self.llm_service.generate_response(
            query=query,
            context_texts=context_texts,
            university_name=uni_config.university_name,
            bot_persona=uni_config.branding.welcome_message
        )
        
        return {
            "answer": response,
            "sources": sources
        }

    async def chat_stream(self, university_id: str, query: str) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        try:
            uni_config = registry.get_university(university_id)
        except KeyError:
            yield "Error: Invalid university ID"
            return

        context_texts, sources = await self.retrieve_context(university_id, query)
        
        import json
        sources_meta = json.dumps({"type": "sources", "data": sources})
        yield f"data: {sources_meta}\n\n"
        
        async for chunk in self.llm_service.generate_response_stream(
            query=query,
            context_texts=context_texts,
            university_name=uni_config.university_name,
            bot_persona=uni_config.branding.welcome_message
        ):
            chunk_data = json.dumps({"type": "chunk", "content": chunk})
            yield f"data: {chunk_data}\n\n"
            
        yield "data: [DONE]\n\n"
