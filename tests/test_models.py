"""
Unit tests for database models
"""
import pytest
from datetime import datetime

from app.models.db_models import Source, Post, SourceType, PostStatus


class TestSourceModel:
    """Tests for Source model"""
    
    def test_source_creation(self):
        """Source_creation_AllFieldsSet"""
        # Act
        source = Source(
            id=1,
            name="Test Source",
            url="https://example.com",
            source_type="website",
            is_active=True
        )
        
        # Assert
        assert source.id == 1
        assert source.name == "Test Source"
        assert source.url == "https://example.com"
        assert source.source_type == "website"
        assert source.is_active is True
    
    def test_source_default_values(self):
        """Source_defaultValues_AreCorrect"""
        # Act
        source = Source(name="Test", url="https://example.com")
        
        # Assert
        assert source.source_type == "website"
        assert source.is_active is True
        assert source.ai_enabled is True
        assert source.created_at is not None
    
    def test_source_repr(self):
        """Source_repr_ContainsNameAndType"""
        # Arrange
        source = Source(name="Test", url="https://example.com", source_type="rss")
        
        # Act
        result = repr(source)
        
        # Assert
        assert "Test" in result
        assert "rss" in result


class TestPostModel:
    """Tests for Post model"""
    
    def test_post_creation(self):
        """Post_creation_AllFieldsSet"""
        # Act
        post = Post(
            id=1,
            source_id=1,
            original_title="Original Title",
            original_content="Original Content",
            original_url="https://example.com/post/1",
            status="pending"
        )
        
        # Assert
        assert post.id == 1
        assert post.source_id == 1
        assert post.original_title == "Original Title"
        assert post.original_content == "Original Content"
        assert post.original_url == "https://example.com/post/1"
        assert post.status == "pending"
    
    def test_post_default_status(self):
        """Post_defaultStatus_IsPending"""
        # Act
        post = Post(
            source_id=1,
            original_title="Test",
            original_content="Content",
            original_url="https://example.com"
        )
        
        # Assert
        assert post.status == "pending"
    
    def test_post_with_content_hash(self):
        """Post_contentHash_StoredCorrectly"""
        # Act
        post = Post(
            source_id=1,
            original_title="Test",
            original_content="Content",
            original_url="https://example.com",
            content_hash="abc123def456"
        )
        
        # Assert
        assert post.content_hash == "abc123def456"
    
    def test_post_repr(self):
        """Post_repr_ContainsTitle"""
        # Act
        post = Post(
            source_id=1,
            original_title="Very Long Title That Should Be Truncated",
            original_content="Content",
            original_url="https://example.com"
        )
        
        # Assert
        assert "Very Long Title" in repr(post)


class TestEnums:
    """Tests for enum values"""
    
    def test_source_type_values(self):
        """SourceType_ContainsAllExpectedValues"""
        assert SourceType.WEBSITE.value == "website"
        assert SourceType.TELEGRAM.value == "telegram"
        assert SourceType.VK.value == "vk"
        assert SourceType.RSS.value == "rss"
    
    def test_post_status_values(self):
        """PostStatus_ContainsAllExpectedValues"""
        assert PostStatus.PENDING.value == "pending"
        assert PostStatus.PROCESSING.value == "processing"
        assert PostStatus.READY.value == "ready"
        assert PostStatus.PUBLISHED.value == "published"
        assert PostStatus.REJECTED.value == "rejected"
