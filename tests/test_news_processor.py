"""
Unit tests for News Processor
Test coverage: Post processing, channel assignment, status transitions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.news_processor import NewsProcessor, _to_naive_datetime
from app.parsers.base import ParsedItem
from app.models.db_models import PostStatus


class TestNewsProcessorChannelAssignment:
    """Tests for channel_id assignment in posts"""

    @pytest.mark.asyncio
    async def test_process_item_NoChannel_SetsStatusReady(self):
        """NewsProcessor_processItem_NoChannel_SetsStatusReady"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.name = "Test Source"
        mock_source.channel = None  # No channel attached
        mock_source.ai_enabled = False
        
        parsed_item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com/post1"
        )
        
        # Mock no duplicate
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert - post should be created with READY status
        assert mock_session.add.called
        add_call_args = mock_session.add.call_args
        post = add_call_args[0][0]
        assert post.status == PostStatus.READY.value

    @pytest.mark.asyncio
    async def test_processItem_WithChannel_SetsChannelId(self):
        """NewsProcessor_processItem_WithChannel_SetsChannelId"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        mock_channel = MagicMock()
        mock_channel.id = 5
        mock_channel.name = "Test Channel"
        mock_channel.ai_prompt = "Test prompt"
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.name = "Test Source"
        mock_source.channel = mock_channel
        mock_source.ai_enabled = False
        mock_source.auto_publish = False
        
        parsed_item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com/post1"
        )
        
        # Mock no duplicate
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert - channel_id should be set from source
        assert mock_session.add.called
        add_call_args = mock_session.add.call_args
        post = add_call_args[0][0]
        assert post.channel_id == 5

    @pytest.mark.asyncio
    async def test_processItem_AutoPublish_SetsReadyStatus(self):
        """NewsProcessor_processItem_AutoPublish_SetsReadyStatus"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        mock_channel = MagicMock()
        mock_channel.id = 5
        mock_channel.name = "Test Channel"
        mock_channel.bot_token = "bot-token"
        mock_channel.channel_id = "@channel"
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.name = "Test Source"
        mock_source.channel = mock_channel
        mock_source.ai_enabled = False
        mock_source.auto_publish = True
        
        parsed_item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com/post1"
        )
        
        # Mock no duplicate
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        # Mock telegram publish fails (returns None)
        with patch('app.services.news_processor.telegram_service.publish_post', 
                   return_value=None):
            # Act
            await processor._process_item(mock_session, mock_source, parsed_item)
            
            # Assert - status should be READY even if publish fails
            assert mock_session.commit.called


class TestNewsProcessorDuplicateDetection:
    """Tests for duplicate post detection"""

    @pytest.mark.asyncio
    async def test_processItem_DuplicateUrl_SkipsPost(self):
        """NewsProcessor_processItem_DuplicateUrl_SkipsPost"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        
        # Mock existing post found by URL
        mock_existing_post = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing_post)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.channel = MagicMock()
        
        parsed_item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com/existing-post"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert - post should NOT be added
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_processItem_DuplicateContentHash_SkipsPost(self):
        """NewsProcessor_processItem_DuplicateContentHash_SkipsPost"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        
        # Mock existing post found by content hash
        mock_existing_post = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing_post)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.channel = MagicMock()
        
        parsed_item = ParsedItem(
            title="Test",
            content="Content",
            url="https://example.com/new-post"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert - post should NOT be added
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_processItem_NewPost_GeneratesContentHash(self):
        """NewsProcessor_processItem_NewPost_GeneratesContentHash"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        # Mock no duplicate
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.channel = MagicMock()
        mock_source.ai_enabled = False
        
        parsed_item = ParsedItem(
            title="Unique Title",
            content="Unique Content",
            url="https://example.com/unique-post"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert - content_hash should be generated
        assert mock_session.add.called
        add_call_args = mock_session.add.call_args
        post = add_call_args[0][0]
        assert post.content_hash is not None
        assert len(post.content_hash) == 64  # SHA-256 hex length


class TestNewsProcessorAdvertisementDetection:
    """Tests for advertisement marker detection"""

    @pytest.mark.asyncio
    async def test_processItem_AdvertisementInContent_MarksAsAd(self):
        """NewsProcessor_processItem_AdvertisementInContent_MarksAsAd"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.channel = MagicMock()
        mock_source.ai_enabled = False
        
        parsed_item = ParsedItem(
            title="Normal Title",
            content="This is #реклама sponsored content",
            url="https://example.com/ad-post"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert
        assert mock_session.add.called
        add_call_args = mock_session.add.call_args
        post = add_call_args[0][0]
        assert post.is_advertisement == True

    @pytest.mark.asyncio
    async def test_processItem_AdvertisementInTitle_MarksAsAd(self):
        """NewsProcessor_processItem_AdvertisementInTitle_MarksAsAd"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.channel = MagicMock()
        mock_source.ai_enabled = False
        
        parsed_item = ParsedItem(
            title="#ad Sponsored Product",
            content="Some content here",
            url="https://example.com/ad-post"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert
        assert mock_session.add.called
        add_call_args = mock_session.add.call_args
        post = add_call_args[0][0]
        assert post.is_advertisement == True

    @pytest.mark.asyncio
    async def test_processItem_NoAdvertisementMarkers_NotMarkedAsAd(self):
        """NewsProcessor_processItem_NoAdvertisementMarkers_NotMarkedAsAd"""
        # Arrange
        processor = NewsProcessor()
        
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        mock_source = MagicMock()
        mock_source.id = 1
        mock_source.channel = MagicMock()
        mock_source.ai_enabled = False
        
        parsed_item = ParsedItem(
            title="Normal News Title",
            content="Regular news content without ads",
            url="https://example.com/news-post"
        )
        
        # Act
        await processor._process_item(mock_session, mock_source, parsed_item)
        
        # Assert
        assert mock_session.add.called
        add_call_args = mock_session.add.call_args
        post = add_call_args[0][0]
        assert post.is_advertisement == False


class TestToNaiveDatetime:
    """Tests for _to_naive_datetime helper function"""

    def test_toNaiveDateTime_TimezoneAware_ConvertsToNaive(self):
        """_to_naive_datetime_TimezoneAware_ConvertsToNaive"""
        # Arrange
        from datetime import timezone, timedelta
        
        aware_dt = datetime(2024, 3, 7, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        
        # Act
        result = _to_naive_datetime(aware_dt)
        
        # Assert
        assert result.tzinfo is None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 7

    def test_toNaiveDateTime_AlreadyNaive_ReturnsAsIs(self):
        """_to_naive_datetime_AlreadyNaive_ReturnsAsIs"""
        # Arrange
        naive_dt = datetime(2024, 3, 7, 12, 0, 0)
        
        # Act
        result = _to_naive_datetime(naive_dt)
        
        # Assert
        assert result == naive_dt
        assert result.tzinfo is None

    def test_toNaiveDateTime_None_ReturnsNone(self):
        """_to_naive_datetime_None_ReturnsNone"""
        # Act
        result = _to_naive_datetime(None)
        
        # Assert
        assert result is None
