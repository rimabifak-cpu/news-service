"""
Pytest configuration and fixtures
"""
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add app to path
sys.path.insert(0, 'app')


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_source():
    """Mock news source"""
    source = MagicMock()
    source.id = 1
    source.name = "Test Source"
    source.url = "https://example.com"
    source.source_type = "website"
    source.is_active = True
    source.ai_enabled = True
    source.ai_prompt = "Test prompt"
    source.selector_title = "h1"
    source.selector_content = "article"
    source.selector_image = "img"
    source.selector_date = "time"
    source.last_parsed = None
    source.created_at = datetime.utcnow()
    return source


@pytest.fixture
def mock_post():
    """Mock news post"""
    post = MagicMock()
    post.id = 1
    post.source_id = 1
    post.original_title = "Test Title"
    post.original_content = "Test Content"
    post.original_url = "https://example.com/post/1"
    post.original_image_url = None
    post.original_published_at = datetime.utcnow()
    post.adapted_title = "Adapted Title"
    post.adapted_content = "Adapted Content"
    post.content_hash = "abc123"
    post.status = "ready"
    post.processed_image_path = None
    post.telegram_message_id = None
    post.published_at = None
    post.created_at = datetime.utcnow()
    post.updated_at = datetime.utcnow()
    return post


@pytest.fixture
def sample_parsed_item():
    """Sample parsed item from parser"""
    from app.parsers.base import ParsedItem
    return ParsedItem(
        title="Test Title",
        content="Test Content",
        url="https://example.com/post/1",
        image_url="https://example.com/image.jpg",
        published_at=datetime.utcnow()
    )
