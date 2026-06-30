from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.vector_store.qdrant_store import QdrantStore
from app.api.deps import get_vector_store
import time
import os

router = APIRouter()

START_TIME = time.time()

@router.get("/stats", summary="Get system statistics and database metrics")
async def get_stats(vector_store: QdrantStore = Depends(get_vector_store)):
    stats: Dict[str, Any] = {
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "database": {
            "status": "connected" if vector_store.check_health() else "disconnected",
            "collections": []
        }
    }
    
    try:
        if vector_store.check_health():
            # Get collection info
            collections = vector_store.client.get_collections().collections
            for c in collections:
                info = vector_store.client.get_collection(c.name)
                stats["database"]["collections"].append({
                    "name": c.name,
                    "vectors_count": info.points_count,
                    "status": str(info.status)
                })
    except Exception as e:
        stats["database"]["error"] = str(e)
        
    return stats
