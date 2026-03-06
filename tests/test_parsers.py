"""
Unit tests for parsers
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime

from app.parsers.rss import RSSParser
from app.parsers.website import WebsiteParser
from app.parsers.base import ParsedItem


class TestRSSParser:
    """Tests for RSS Parser"""
    
    @pytest.mark.asyncio
    async def test_parse_returns_list_of_items(self):
        """RSSParser_parse_ReturnsListOfParsedItems"""
        # Arrange
        config = {"url": "https://example.com/rss"}
        parser = RSSParser(config)
        
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Title</title>
                    <description>Test Description</description>
                    <link>https://example.com/post1</link>
                </item>
            </channel>
        </rss>"""
        mock_response.raise_for_status = MagicMock()
        
        with patch('app.parsers.rss.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            # Act
            items = await parser.parse()
            
            # Assert
            assert isinstance(items, list)
            assert len(items) >= 1
    
    @pytest.mark.asyncio
    async def test_parse_handles_empty_feed(self):
        """RSSParser_parse_EmptyFeed_ReturnsEmptyList"""
        # Arrange
        config = {"url": "https://example.com/rss"}
        parser = RSSParser(config)
        
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
            </channel>
        </rss>"""
        mock_response.raise_for_status = MagicMock()
        
        with patch('app.parsers.rss.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            
            # Act
            items = await parser.parse()
            
            # Assert
            assert items == []
    
    def test_extract_image_from_media_content(self):
        """RSSParser_extractImage_MediaContent_ReturnsImageUrl"""
        # Arrange
        config = {"url": "https://example.com/rss"}
        parser = RSSParser(config)
        
        mock_entry = MagicMock()
        mock_entry.media_content = [{"url": "https://example.com/image.jpg", "medium": "image"}]
        mock_entry.enclosures = []
        mock_entry.content = []
        mock_entry.summary = ""
        
        # Act
        image_url = parser._extract_image(mock_entry)
        
        # Assert
        assert image_url == "https://example.com/image.jpg"
    
    def test_extract_image_from_enclosure(self):
        """RSSParser_extractImage_Enclosure_ReturnsImageUrl"""
        # Arrange
        config = {"url": "https://example.com/rss"}
        parser = RSSParser(config)
        
        mock_entry = MagicMock()
        mock_entry.media_content = []
        mock_entry.enclosures = [{"url": "https://example.com/image2.jpg", "type": "image/jpeg"}]
        mock_entry.content = []
        mock_entry.summary = ""
        
        # Act
        image_url = parser._extract_image(mock_entry)
        
        # Assert
        assert image_url == "https://example.com/image2.jpg"
    
    def test_parse_date_with_published(self):
        """RSSParser_parseDate_WithPublished_ReturnsDatetime"""
        # Arrange
        config = {"url": "https://example.com/rss"}
        parser = RSSParser(config)
        
        mock_entry = MagicMock()
        mock_entry.published_parsed = (2024, 1, 15, 10, 30, 0, 0, 0, 0)
        mock_entry.updated_parsed = None
        
        # Act
        date = parser._parse_date(mock_entry)
        
        # Assert
        assert date is not None
        assert date.year == 2024


class TestWebsiteParser:
    """Tests for Website Parser"""
    
    @pytest.mark.asyncio
    async def test_make_full_url_absolute(self):
        """WebsiteParser_makeFullUrl_AbsoluteUrl_ReturnsSame"""
        # Arrange
        config = {"url": "https://example.com"}
        parser = WebsiteParser(config)
        
        # Act
        result = parser._make_full_url("https://other.com/page")
        
        # Assert
        assert result == "https://other.com/page"
    
    @pytest.mark.asyncio
    async def test_make_full_url_relative(self):
        """WebsiteParser_makeFullUrl_RelativeUrl_ReturnsAbsolute"""
        # Arrange
        config = {"url": "https://example.com"}
        parser = WebsiteParser(config)
        
        # Act
        result = parser._make_full_url("/page")
        
        # Assert
        assert result == "https://example.com/page"
    
    @pytest.mark.asyncio
    async def test_parse_date_valid_format(self):
        """WebsiteParser_parseDate_ValidFormat_ReturnsDatetime"""
        # Arrange
        config = {"url": "https://example.com"}
        parser = WebsiteParser(config)
        
        # Act
        result = parser._parse_date("2024-01-15")
        
        # Assert
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_parse_date_empty_string(self):
        """WebsiteParser_parseDate_EmptyString_ReturnsNone"""
        # Arrange
        config = {"url": "https://example.com"}
        parser = WebsiteParser(config)
        
        # Act
        result = parser._parse_date("")
        
        # Assert
        assert result is None


class TestParsedItem:
    """Tests for ParsedItem dataclass"""
    
    def test_parsed_item_creation(self):
        """ParsedItem_creation_AllFieldsSet"""
        # Act
        item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com",
            image_url="https://example.com/img.jpg",
            published_at=datetime.utcnow()
        )
        
        # Assert
        assert item.title == "Test"
        assert item.content == "Content"
        assert item.url == "https://example.com"
        assert item.image_url == "https://example.com/img.jpg"
    
    def test_parsed_item_optional_fields(self):
        """ParsedItem_optionalFields_DefaultToNone"""
        # Act
        item = ParsedItem(title="Test", content="Content", url="https://example.com")
        
        # Assert
        assert item.image_url is None
        assert item.published_at is None
        assert item.author is None
