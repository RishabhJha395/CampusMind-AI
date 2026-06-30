from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from app.services.rag.orchestrator import RAGService
from app.api.deps import get_rag_service
from app.api.middleware import limiter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    university_id: str
    query: str
    stream: Optional[bool] = False

@router.post("/chat", summary="Query the RAG system for a specific university")
@limiter.limit("30/minute")
async def chat(request: Request, chat_request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    if not chat_request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        if chat_request.stream:
            # Return SSE stream
            return StreamingResponse(
                rag_service.chat_stream(chat_request.university_id, chat_request.query),
                media_type="text/event-stream"
            )
        else:
            # Return standard JSON response
            return await rag_service.chat(chat_request.university_id, chat_request.query)
            
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while processing the chat.")
