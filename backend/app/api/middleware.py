import time
import uuid
import logging
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# Rate limiter setup (30 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # Attach request_id to state
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            logger.info(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"status={response.status_code} duration={process_time:.2f}ms"
            )
            return response
            
        except Exception as e:
            # If an exception makes it all the way here and wasn't caught by the global handler
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"req_id={request_id} method={request.method} path={request.url.path} "
                f"status=500 duration={process_time:.2f}ms error={str(e)}"
            )
            raise e

def setup_middlewares(app: FastAPI):
    """Wires up all middlewares and global exception handlers to the FastAPI app."""
    
    # Add Request Logging Middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Configure Rate Limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", "unknown")
        logger.error(f"Unhandled Exception [req_id={req_id}]: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal Server Error", "request_id": req_id}
        )
