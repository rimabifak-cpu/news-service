"""
Unit tests for middleware
Test coverage: Request tracing and error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from starlette.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware import RequestTracingMiddleware, ErrorHandlingMiddleware


class TestRequestTracingMiddleware:
    """Tests for RequestTracingMiddleware"""

    @pytest.mark.asyncio
    async def test_dispatch_AddsRequestId_ToResponseHeaders(self):
        """RequestTracingMiddleware_dispatch_AddsRequestId_ToResponseHeaders"""
        # Arrange
        async def call_next(request: Request):
            return Response(content="OK")
        
        middleware = RequestTracingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Act
        with patch('uuid.uuid4', return_value='test-request-id-123'):
            response = await middleware.dispatch(mock_request, call_next)
        
        # Assert
        assert response.headers.get("X-Request-ID") == 'test-request-id-123'

    @pytest.mark.asyncio
    async def test_dispatch_LogsRequestStart_WithCorrectData(self):
        """RequestTracingMiddleware_dispatch_LogsRequestStart_WithCorrectData"""
        # Arrange
        async def call_next(request: Request):
            return Response(content="OK")
        
        middleware = RequestTracingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/posts"
        mock_request.query_params = {"limit": "10"}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"X-User-ID": "user-456"}
        mock_request.state = MagicMock()
        
        # Act & Assert
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.logger') as mock_logger:
                await middleware.dispatch(mock_request, call_next)
                
                # Verify logger.info was called for REQUEST_START
                assert mock_logger.info.called
                call_args = mock_logger.info.call_args_list[0]
                assert call_args[0][0] == "REQUEST_START"
                assert call_args[1]['extra']['request_id'] == 'test-req-id'
                assert call_args[1]['extra']['user_id'] == 'user-456'
                assert call_args[1]['extra']['method'] == 'POST'

    @pytest.mark.asyncio
    async def test_dispatch_LogsRequestEnd_WithDuration(self):
        """RequestTracingMiddleware_dispatch_LogsRequestEnd_WithDuration"""
        # Arrange
        async def call_next(request: Request):
            return Response(content="OK", status_code=200)
        
        middleware = RequestTracingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/sources"
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Act & Assert
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.logger') as mock_logger:
                await middleware.dispatch(mock_request, call_next)
                
                # Verify logger.info was called for REQUEST_END
                log_messages = [call[0][0] for call in mock_logger.info.call_args_list]
                assert "REQUEST_END" in log_messages

    @pytest.mark.asyncio
    async def test_dispatch_LogsSlowRequest_WhenDurationExceeds2Seconds(self):
        """RequestTracingMiddleware_dispatch_LogsSlowRequest_WhenDurationExceeds2Seconds"""
        # Arrange
        import time
        
        async def call_next(request: Request):
            time.sleep(0.1)  # Small delay
            return Response(content="OK")
        
        middleware = RequestTracingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/slow"
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Act & Assert
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.logger') as mock_logger:
                # Mock time.time to simulate slow request
                with patch('time.time', side_effect=[1000.0, 1003.0]):  # 3 seconds
                    await middleware.dispatch(mock_request, call_next)
                    
                    # Verify warning was logged for slow request
                    assert mock_logger.warning.called
                    warning_call = mock_logger.warning.call_args
                    assert warning_call[0][0] == "SLOW_REQUEST"
                    assert warning_call[1]['extra']['duration_ms'] > 2000

    @pytest.mark.asyncio
    async def test_dispatch_LogsError_WhenExceptionOccurs(self):
        """RequestTracingMiddleware_dispatch_LogsError_WhenExceptionOccurs"""
        # Arrange
        async def call_next(request: Request):
            raise ValueError("Test error")
        
        middleware = RequestTracingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/error"
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Act & Assert
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.logger') as mock_logger:
                with pytest.raises(ValueError):
                    await middleware.dispatch(mock_request, call_next)
                
                # Verify error was logged
                assert mock_logger.error.called
                error_call = mock_logger.error.call_args
                assert error_call[0][0] == "REQUEST_ERROR"
                assert error_call[1]['extra']['error_message'] == "Test error"

    @pytest.mark.asyncio
    async def test_dispatch_UsesAnonymousUserId_WhenHeaderMissing(self):
        """RequestTracingMiddleware_dispatch_UsesAnonymousUserId_WhenHeaderMissing"""
        # Arrange
        async def call_next(request: Request):
            return Response(content="OK")
        
        middleware = RequestTracingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}  # No X-User-ID header
        mock_request.state = MagicMock()
        
        # Act & Assert
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.logger') as mock_logger:
                await middleware.dispatch(mock_request, call_next)
                
                # Verify user_id is "anonymous"
                call_args = mock_logger.info.call_args_list[0]
                assert call_args[1]['extra']['user_id'] == 'anonymous'


class TestErrorHandlingMiddleware:
    """Tests for ErrorHandlingMiddleware"""

    @pytest.mark.asyncio
    async def test_dispatch_ReturnsJsonResponse_WhenErrorOccurs(self):
        """ErrorHandlingMiddleware_dispatch_ReturnsJsonResponse_WhenErrorOccurs"""
        # Arrange
        async def call_next(request: Request):
            raise RuntimeError("Unexpected error")
        
        middleware = ErrorHandlingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/error"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.debug = False
        
        # Act
        with patch('uuid.uuid4', return_value='test-req-id'):
            response = await middleware.dispatch(mock_request, call_next)
        
        # Assert
        assert response.status_code == 500
        assert response.headers.get("content-type") == "application/json"

    @pytest.mark.asyncio
    async def test_dispatch_LogsUnhandledError_WithDetails(self):
        """ErrorHandlingMiddleware_dispatch_LogsUnhandledError_WithDetails"""
        # Arrange
        async def call_next(request: Request):
            raise RuntimeError("Test error message")
        
        middleware = ErrorHandlingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/posts"
        mock_request.headers = {"X-User-ID": "user-789"}
        mock_request.state = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.debug = True
        
        # Act & Assert
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.logger') as mock_logger:
                await middleware.dispatch(mock_request, call_next)
                
                # Verify error was logged
                assert mock_logger.error.called
                error_call = mock_logger.error.call_args
                assert error_call[0][0] == "UNHANDLED_ERROR"
                assert error_call[1]['extra']['error_type'] == "RuntimeError"
                assert error_call[1]['extra']['error_message'] == "Test error message"
                assert error_call[1]['extra']['request_id'] == 'test-req-id'

    @pytest.mark.asyncio
    async def test_dispatch_IncludesErrorDetail_InDebugMode(self):
        """ErrorHandlingMiddleware_dispatch_IncludesErrorDetail_InDebugMode"""
        # Arrange
        async def call_next(request: Request):
            raise ValueError("Detailed error message")
        
        middleware = ErrorHandlingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.debug = True
        
        # Act
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.RequestTracingMiddleware.dispatch') as mock_call_next:
                mock_call_next.side_effect = ValueError("Detailed error message")
                
                from starlette.responses import JSONResponse
                response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert - in debug mode, detail should be included
        import json
        body = json.loads(response.body)
        assert "Detailed error message" in str(body.get("detail", ""))

    @pytest.mark.asyncio
    async def test_dispatch_HidesErrorDetail_InProduction(self):
        """ErrorHandlingMiddleware_dispatch_HidesErrorDetail_InProduction"""
        # Arrange
        async def call_next(request: Request):
            raise ValueError("Sensitive error details")
        
        middleware = ErrorHandlingMiddleware(None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.state = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.debug = False
        
        # Act
        with patch('uuid.uuid4', return_value='test-req-id'):
            with patch('app.middleware.RequestTracingMiddleware.dispatch') as mock_call_next:
                mock_call_next.side_effect = ValueError("Sensitive error details")
                
                from starlette.responses import JSONResponse
                response = await middleware.dispatch(mock_request, mock_call_next)
        
        # Assert - in production, generic message
        import json
        body = json.loads(response.body)
        assert body.get("detail") == "An unexpected error occurred"
