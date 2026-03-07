"""
Middleware для детального логирования и трассировки запросов
"""
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware для трассировки запросов с request_id"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Генерируем request_id для каждого запроса
        request_id = str(uuid.uuid4())
        
        # Добавляем request_id в контекст логов
        request.state.request_id = request_id
        
        # Извлекаем user_id из заголовков (если есть)
        user_id = request.headers.get("X-User-ID", "anonymous")
        
        # Логируем начало запроса
        start_time = time.time()
        logger.info(
            "REQUEST_START",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
            }
        )
        
        try:
            # Выполняем запрос
            response = await call_next(request)
            
            # Логируем завершение запроса
            duration = time.time() - start_time
            logger.info(
                "REQUEST_END",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            # Добавляем request_id в заголовки ответа
            response.headers["X-Request-ID"] = request_id
            
            # Логирование медленных запросов
            if duration > 2.0:
                logger.warning(
                    "SLOW_REQUEST",
                    extra={
                        "request_id": request_id,
                        "user_id": user_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration * 1000, 2),
                        "threshold_ms": 2000,
                    }
                )
            
            return response
            
        except Exception as e:
            # Логируем ошибку
            duration = time.time() - start_time
            logger.error(
                "REQUEST_ERROR",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": round(duration * 1000, 2),
                },
                exc_info=True
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Глобальный обработчик ошибок"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            user_id = request.headers.get("X-User-ID", "anonymous")
            
            logger.error(
                "UNHANDLED_ERROR",
                extra={
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True
            )
            
            # Возвращаем стандартный ответ об ошибке
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "request_id": request_id,
                    "detail": str(e) if request.app.debug else "An unexpected error occurred"
                }
            )
