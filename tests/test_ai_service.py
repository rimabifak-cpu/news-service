"""
Unit tests for AI Service
Test coverage: AI text adaptation and title generation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.ai_service import AIService


class TestAIServiceAdaptText:
    """Tests for AIService.adapt_text method"""

    @pytest.mark.asyncio
    async def test_adapt_text_SuccessfulAdaptation_ReturnsAdaptedText(self):
        """AIService_adapt_text_SuccessfulAdaptation_ReturnsAdaptedText"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Adapted text with emojis 🎉"}
            }]
        }
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await service.adapt_text("Original text", "Test prompt")
            
            # Assert
            assert result == "Adapted text with emojis 🎉"
            assert service.request_count == 1
            assert service.error_count == 0

    @pytest.mark.asyncio
    async def test_adapt_text_NoApiKey_ReturnsOriginalText(self):
        """AIService_adapt_text_NoApiKey_ReturnsOriginalText"""
        # Arrange
        service = AIService()
        service.api_key = None
        
        # Act
        result = await service.adapt_text("Original text")
        
        # Assert
        assert result == "Original text"

    @pytest.mark.asyncio
    async def test_adapt_text_EmptyText_ReturnsEmptyString(self):
        """AIService_adapt_text_EmptyText_ReturnsEmptyString"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        # Act
        result = await service.adapt_text("")
        
        # Assert
        assert result == ""

    @pytest.mark.asyncio
    async def test_adapt_text_WhitespaceOnlyText_ReturnsEmptyString(self):
        """AIService_adapt_text_WhitespaceOnlyText_ReturnsEmptyString"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        # Act
        result = await service.adapt_text("   \n\t  ")
        
        # Assert
        assert result == "   \n\t  "

    @pytest.mark.asyncio
    async def test_adapt_text_ApiError_ReturnsOriginalText(self):
        """AIService_adapt_text_ApiError_ReturnsOriginalText"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await service.adapt_text("Original text")
            
            # Assert
            assert result == "Original text"
            assert service.error_count == 1

    @pytest.mark.asyncio
    async def test_adapt_text_Timeout_ReturnsOriginalText(self):
        """AIService_adapt_text_Timeout_ReturnsOriginalText"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client_class.return_value = mock_client
            
            # Act
            result = await service.adapt_text("Original text")
            
            # Assert
            assert result == "Original text"
            assert service.error_count == 1

    @pytest.mark.asyncio
    async def test_adapt_text_ConnectionError_ReturnsOriginalText(self):
        """AIService_adapt_text_ConnectionError_ReturnsOriginalText"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_client_class.return_value = mock_client
            
            # Act
            result = await service.adapt_text("Original text")
            
            # Assert
            assert result == "Original text"
            assert service.error_count == 1

    @pytest.mark.asyncio
    async def test_adapt_text_UsesDefaultPrompt_WhenNoPromptProvided(self):
        """AIService_adapt_text_UsesDefaultPrompt_WhenNoPromptProvided"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Adapted"}}]
        }
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            await service.adapt_text("Text", None)
            
            # Assert - verify post was called (prompt should be in request)
            assert mock_client.post.called
            call_args = mock_client.post.call_args
            request_json = call_args[1]['json']
            assert "Адаптируй этот текст" in request_json['messages'][1]['content']

    @pytest.mark.asyncio
    async def test_adapt_text_UsesCustomPrompt_WhenProvided(self):
        """AIService_adapt_text_UsesCustomPrompt_WhenProvided"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Adapted"}}]
        }
        
        custom_prompt = "Make it funny"
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            await service.adapt_text("Text", custom_prompt)
            
            # Assert
            call_args = mock_client.post.call_args
            request_json = call_args[1]['json']
            assert custom_prompt in request_json['messages'][1]['content']

    @pytest.mark.asyncio
    async def test_adapt_text_TrimsLongText_To5000Characters(self):
        """AIService_adapt_text_TrimsLongText_To5000Characters"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        long_text = "A" * 10000
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            await service.adapt_text(long_text)
            
            # Assert
            call_args = mock_client.post.call_args
            request_json = call_args[1]['json']
            message_content = request_json['messages'][1]['content']
            assert len(message_content) <= 5000 + 500  # prompt + text

    @pytest.mark.asyncio
    async def test_adapt_text_IncrementsRequestCount_OnEachCall(self):
        """AIService_adapt_text_IncrementsRequestCount_OnEachCall"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "OK"}}]
        }
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            await service.adapt_text("Text 1")
            await service.adapt_text("Text 2")
            await service.adapt_text("Text 3")
            
            # Assert
            assert service.request_count == 3


class TestAIServiceGenerateTitle:
    """Tests for AIService.generate_title method"""

    @pytest.mark.asyncio
    async def test_generate_title_SuccessfulGeneration_ReturnsTitle(self):
        """AIService_generate_title_SuccessfulGeneration_ReturnsTitle"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "🔥 Breaking News Title!"}
            }]
        }
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await service.generate_title("Some content here")
            
            # Assert
            assert result == "🔥 Breaking News Title!"

    @pytest.mark.asyncio
    async def test_generate_title_NoApiKey_ReturnsFirstLine(self):
        """AIService_generate_title_NoApiKey_ReturnsFirstLine"""
        # Arrange
        service = AIService()
        service.api_key = None
        
        content = "First line\nSecond line\nThird line"
        
        # Act
        result = await service.generate_title(content)
        
        # Assert
        assert result == "First line"

    @pytest.mark.asyncio
    async def test_generate_title_ApiError_ReturnsFirstLine(self):
        """AIService_generate_title_ApiError_ReturnsFirstLine"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            content = "First line\nSecond line"
            
            # Act
            result = await service.generate_title(content)
            
            # Assert
            assert result == "First line"

    @pytest.mark.asyncio
    async def test_generate_title_TrimsTitle_ToMaxLength(self):
        """AIService_generate_title_TrimsTitle_ToMaxLength"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "A" * 200}  # Very long title
            }]
        }
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            result = await service.generate_title("Content", max_length=100)
            
            # Assert
            assert len(result) <= 100

    @pytest.mark.asyncio
    async def test_generate_title_TrimsContent_To1000Characters(self):
        """AIService_generate_title_TrimsContent_To1000Characters"""
        # Arrange
        service = AIService()
        service.api_key = "test-key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        long_content = "A" * 2000
        
        with patch.object(httpx, 'AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Act
            await service.generate_title(long_content)
            
            # Assert
            call_args = mock_client.post.call_args
            request_json = call_args[1]['json']
            message_content = request_json['messages'][1]['content']
            assert len(message_content) <= 1000 + 200  # prompt + content
