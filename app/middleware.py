"""
Middleware for request tracking and error handling
"""
import uuid
import json
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from loguru import logger


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request ID tracking"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request_id
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Log request start
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "module": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "message": "Request started"
        }
        logger.info(json.dumps(log_data))
        
        # Process request
        response = await call_next(request)
        
        # Log request end
        log_data.update({
            "level": "INFO",
            "status_code": response.status_code,
            "message": "Request completed"
        })
        logger.info(json.dumps(log_data))
        
        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            # Generate request_id if not present
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            
            # Log error with full context
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "ERROR",
                "module": "error_handler",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "message": "Unhandled exception"
            }
            logger.error(json.dumps(error_data))
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                    "error_type": type(e).__name__
                }
            )
