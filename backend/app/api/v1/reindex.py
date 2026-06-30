from fastapi import APIRouter, Depends, HTTPException, Security, BackgroundTasks
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import subprocess
import os
import logging
from app.api.middleware import limiter
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# In production, this should come from .env
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "super-secret-admin-key-123")

class ReindexRequest(BaseModel):
    university: str = "dtu"

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == ADMIN_API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=403, detail="Could not validate credentials"
    )

def run_ingestion_pipeline(university: str):
    """Runs the ingestion pipeline as a background task."""
    try:
        logger.info(f"Starting ingestion pipeline for {university}...")
        # Path to python executable in the virtual environment
        python_exec = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_exec):
            python_exec = "python" # fallback
            
        subprocess.run(
            [python_exec, "-m", "ingestion.main", "--university", university],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Ingestion pipeline for {university} completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ingestion pipeline failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Error starting pipeline: {e}")

@router.post("/reindex", summary="Trigger the background ingestion pipeline")
@limiter.limit("5/minute")
async def trigger_reindex(
    request: Request,
    reindex_req: ReindexRequest, 
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    background_tasks.add_task(run_ingestion_pipeline, reindex_req.university)
    return {"status": "accepted", "message": f"Reindexing started for {reindex_req.university} in the background."}
