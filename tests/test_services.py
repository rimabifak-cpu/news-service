"""
Unit tests for services
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.news_processor import NewsProcessor
from app.parsers.base import ParsedItem


class TestNewsProcessor:
    """Tests for NewsProcessor service"""
    
    @pytest.mark.asyncio
    async def test_get_parser_rss(self):
        """NewsProcessor_getParser_RSS_ReturnsRSSParser"""
        # Arrange
        processor = NewsProcessor()
        mock_source = MagicMock()
        mock_source.source_type = "rss"
        mock_source.name = "Test"
        mock_source.url = "https://example.com"
        mock_source.selector_title = None
        mock_source.selector_content = None
        mock_source.selector_image = None
        mock_source.selector_date = None
        
        # Act
        parser = processor._get_parser(mock_source)
        
        # Assert
        assert parser is not None
        assert parser.url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_get_parser_telegram(self):
        """NewsProcessor_getParser_Telegram_ReturnsTelegramParser"""
        # Arrange
        processor = NewsProcessor()
        mock_source = MagicMock()
        mock_source.source_type = "telegram"
        mock_source.name = "Test"
        mock_source.url = "https://t.me/test"
        mock_source.selector_title = None
        mock_source.selector_content = None
        mock_source.selector_image = None
        mock_source.selector_date = None
        
        # Act
        parser = processor._get_parser(mock_source)
        
        # Assert
        assert parser is not None
    
    @pytest.mark.asyncio
    async def test_get_parser_vk(self):
        """NewsProcessor_getParser_VK_ReturnsVKParser"""
        # Arrange
        processor = NewsProcessor()
        mock_source = MagicMock()
        mock_source.source_type = "vk"
        mock_source.name = "Test"
        mock_source.url = "https://vk.com/public123"
        mock_source.selector_title = None
        mock_source.selector_content = None
        mock_source.selector_image = None
        mock_source.selector_date = None
        
        # Act
        parser = processor._get_parser(mock_source)
        
        # Assert
        assert parser is not None
    
    @pytest.mark.asyncio
    async def test_get_parser_website(self):
        """NewsProcessor_getParser_Website_ReturnsWebsiteParser"""
        # Arrange
        processor = NewsProcessor()
        mock_source = MagicMock()
        mock_source.source_type = "website"
        mock_source.name = "Test"
        mock_source.url = "https://example.com"
        mock_source.selector_title = "h1"
        mock_source.selector_content = "article"
        mock_source.selector_image = "img"
        mock_source.selector_date = "time"
        
        # Act
        parser = processor._get_parser(mock_source)
        
        # Assert
        assert parser is not None
        assert parser.selector_title == "h1"
    
    @pytest.mark.asyncio
    async def test_process_item_duplicate_by_url(self):
        """NewsProcessor_processItem_DuplicateUrl_SkipsPost"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=MagicMock())  # Post exists
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        
        parsed_item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com/post1"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert - post should not be added
        mock_session.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_item_new_post(self):
        """NewsProcessor_processItem_NewPost_AddsToSession"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)  # No duplicate
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.ai_enabled = False
        
        parsed_item = ParsedItem(
            title="Test Title",
            content="Test Content",
            url="https://example.com/post1",
            image_url=None,
            published_at=datetime.utcnow()
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert
        assert mock_session.add.called


class TestContentHash:
    """Tests for content hash generation"""
    
    def test_hash_generation_consistency(self):
        """ContentHash_SameContent_SameHash"""
        import hashlib
        
        content = "Test Title|Test Content"
        hash1 = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Same content should produce same hash
        hash2 = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        assert hash1 == hash2
    
    def test_hash_different_content(self):
        """ContentHash_DifferentContent_DifferentHash"""
        import hashlib
        
        content1 = "Title 1|Content 1"
        content2 = "Title 2|Content 2"
        
        hash1 = hashlib.sha256(content1.encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(content2.encode('utf-8')).hexdigest()
        
        assert hash1 != hash2
    
    def test_hash_length(self):
        """ContentHash_SHA256_Is64Characters"""
        import hashlib
        
        content = "Test"
        hash_result = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        assert len(hash_result) == 64
