from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.api.v1 import universities, chat
from app.api.deps import get_vector_store
from app.services.vector_store.qdrant_store import QdrantStore
import os
from dotenv import load_dotenv

# Load .env from the root directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=env_path)

app = FastAPI(
    title="CampusMind AI API",
    description="Multi-tenant RAG Knowledge Platform",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.middleware import setup_middlewares
setup_middlewares(app)

from app.api.v1 import universities, chat, stats, reindex

app.include_router(universities.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1", tags=["Admin"])
app.include_router(reindex.router, prefix="/api/v1", tags=["Admin"])

class HealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    version: str

@app.get("/", include_in_schema=False)
async def root():
    return {"detail": "Not Found"}

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check(vector_store: QdrantStore = Depends(get_vector_store)):
    is_qdrant_healthy = vector_store.check_health()
    
    return {
        "status": "healthy" if is_qdrant_healthy else "degraded",
        "qdrant_connected": is_qdrant_healthy,
        "version": "1.0.0"
    }
