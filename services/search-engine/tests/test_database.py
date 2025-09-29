"""
Search Engine Database Tests
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock

from app.database import db_manager, SearchContent, SearchLog
from app.config import settings


class TestDatabaseManager:
    """Test Database Manager functionality"""
    
    @pytest.mark.asyncio
    async def test_initialize(self, test_engine):
        """Test database initialization"""
        # Test that initialization works
        db_manager.engine = test_engine
        db_manager.session_factory = None
        
        await db_manager.initialize()
        
        assert db_manager.engine is not None
        assert db_manager.session_factory is not None
    
    @pytest.mark.asyncio
    async def test_create_content(self, initialized_db_manager):
        """Test creating content"""
        content_id = "test_create_1"
        content = "Test content for creation"
        content_type = "text"
        metadata = {"source": "test", "category": "sample"}
        embedding = [0.1] * 384
        
        success = await initialized_db_manager.create_content(
            content_id=content_id,
            content=content,
            content_type=content_type,
            metadata=metadata,
            embedding=embedding
        )
        
        assert success is True
        
        # Verify content was created
        created_content = await initialized_db_manager.get_content(content_id)
        assert created_content is not None
        assert created_content["content"] == content
        assert created_content["content_type"] == content_type
        assert created_content["metadata"] == metadata
        assert created_content["embedding"] == embedding
    
    @pytest.mark.asyncio
    async def test_get_content(self, initialized_db_manager):
        """Test getting content"""
        # Create test content first
        content_id = "test_get_1"
        await initialized_db_manager.create_content(
            content_id=content_id,
            content="Test content for retrieval",
            content_type="text"
        )
        
        # Get content
        content = await initialized_db_manager.get_content(content_id)
        
        assert content is not None
        assert content["id"] == content_id
        assert content["content"] == "Test content for retrieval"
        assert content["content_type"] == "text"
    
    @pytest.mark.asyncio
    async def test_get_content_not_found(self, initialized_db_manager):
        """Test getting non-existent content"""
        content = await initialized_db_manager.get_content("nonexistent_id")
        assert content is None
    
    @pytest.mark.asyncio
    async def test_update_content(self, initialized_db_manager):
        """Test updating content"""
        # Create test content first
        content_id = "test_update_1"
        await initialized_db_manager.create_content(
            content_id=content_id,
            content="Original content",
            content_type="text",
            metadata={"original": True}
        )
        
        # Update content
        success = await initialized_db_manager.update_content(
            content_id=content_id,
            content="Updated content",
            metadata={"updated": True},
            embedding=[0.2] * 384
        )
        
        assert success is True
        
        # Verify update
        updated_content = await initialized_db_manager.get_content(content_id)
        assert updated_content["content"] == "Updated content"
        assert updated_content["metadata"]["updated"] is True
        assert updated_content["embedding"] == [0.2] * 384
    
    @pytest.mark.asyncio
    async def test_update_content_not_found(self, initialized_db_manager):
        """Test updating non-existent content"""
        success = await initialized_db_manager.update_content(
            content_id="nonexistent_id",
            content="Updated content"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_content(self, initialized_db_manager):
        """Test deleting content"""
        # Create test content first
        content_id = "test_delete_1"
        await initialized_db_manager.create_content(
            content_id=content_id,
            content="Content to delete",
            content_type="text"
        )
        
        # Delete content
        success = await initialized_db_manager.delete_content(content_id)
        
        assert success is True
        
        # Verify deletion
        deleted_content = await initialized_db_manager.get_content(content_id)
        assert deleted_content is None
    
    @pytest.mark.asyncio
    async def test_delete_content_not_found(self, initialized_db_manager):
        """Test deleting non-existent content"""
        success = await initialized_db_manager.delete_content("nonexistent_id")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_search_content(self, initialized_db_manager):
        """Test searching content"""
        # Create test content
        test_contents = [
            ("search_test_1", "Python programming tutorial"),
            ("search_test_2", "Machine learning with Python"),
            ("search_test_3", "JavaScript web development")
        ]
        
        for content_id, content in test_contents:
            await initialized_db_manager.create_content(
                content_id=content_id,
                content=content,
                content_type="text"
            )
        
        # Search for Python content
        results = await initialized_db_manager.search_content(
            query="Python",
            limit=10
        )
        
        # Should find at least 2 results
        assert len(results) >= 2
        
        # Verify results contain Python
        for result in results:
            assert "Python" in result["content"]
    
    @pytest.mark.asyncio
    async def test_search_content_with_filters(self, initialized_db_manager):
        """Test searching content with filters"""
        # Create test content with different types
        await initialized_db_manager.create_content(
            content_id="filter_test_1",
            content="Text document about AI",
            content_type="text"
        )
        
        await initialized_db_manager.create_content(
            content_id="filter_test_2",
            content="Image of AI model",
            content_type="image"
        )
        
        # Search with content type filter
        results = await initialized_db_manager.search_content(
            query="AI",
            content_types=["text"],
            limit=10
        )
        
        # Should only return text content
        assert len(results) == 1
        assert results[0]["content_type"] == "text"
    
    @pytest.mark.asyncio
    async def test_get_content_count(self, initialized_db_manager):
        """Test getting content count"""
        # Create test content
        for i in range(5):
            await initialized_db_manager.create_content(
                content_id=f"count_test_{i}",
                content=f"Test content {i}",
                content_type="text"
            )
        
        # Get total count
        total_count = await initialized_db_manager.get_content_count()
        assert total_count >= 5
        
        # Get count by type
        text_count = await initialized_db_manager.get_content_count("text")
        assert text_count >= 5
        
        image_count = await initialized_db_manager.get_content_count("image")
        assert image_count == 0
    
    @pytest.mark.asyncio
    async def test_log_search(self, initialized_db_manager):
        """Test logging search operations"""
        success = await initialized_db_manager.log_search(
            query="test query",
            search_type="semantic",
            results_count=5,
            execution_time_ms=100.0,
            cached=False
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_search_stats(self, initialized_db_manager):
        """Test getting search statistics"""
        # Log some searches
        await initialized_db_manager.log_search(
            query="query 1",
            search_type="semantic",
            results_count=3,
            execution_time_ms=50.0,
            cached=False
        )
        
        await initialized_db_manager.log_search(
            query="query 2",
            search_type="keyword",
            results_count=2,
            execution_time_ms=75.0,
            cached=True
        )
        
        # Get stats
        stats = await initialized_db_manager.get_search_stats()
        
        assert stats["total_searches"] >= 2
        assert stats["average_execution_time_ms"] > 0
        assert stats["cache_hit_rate"] >= 0


class TestDatabaseModels:
    """Test database models"""
    
    def test_search_content_model(self):
        """Test SearchContent model structure"""
        # Create a SearchContent instance
        content = SearchContent(
            id="test_model_1",
            content="Test content",
            content_type="text",
            metadata={"test": True},
            embedding=[0.1] * 384
        )
        
        assert content.id == "test_model_1"
        assert content.content == "Test content"
        assert content.content_type == "text"
        assert content.metadata == {"test": True}
        assert content.embedding == [0.1] * 384
        assert content.created_at is not None
        assert content.updated_at is not None
    
    def test_search_log_model(self):
        """Test SearchLog model structure"""
        # Create a SearchLog instance
        search_log = SearchLog(
            query="test query",
            search_type="semantic",
            results_count=5,
            execution_time_ms=100.0,
            cached=False
        )
        
        assert search_log.query == "test query"
        assert search_log.search_type == "semantic"
        assert search_log.results_count == 5
        assert search_log.execution_time_ms == 100.0
        assert search_log.cached is False
        assert search_log.created_at is not None


class TestDatabaseErrorHandling:
    """Test database error handling"""
    
    @pytest.mark.asyncio
    async def test_create_content_error(self, initialized_db_manager):
        """Test error handling in create_content"""
        # Try to create content with invalid data
        success = await initialized_db_manager.create_content(
            content_id=None,  # Invalid ID
            content="Test content",
            content_type="text"
        )
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_search_content_error(self, initialized_db_manager):
        """Test error handling in search_content"""
        # Search with invalid query
        results = await initialized_db_manager.search_content(
            query="",  # Empty query
            limit=10
        )
        
        # Should return empty list on error
        assert results == []
    
    @pytest.mark.asyncio
    async def test_get_search_stats_error(self, initialized_db_manager):
        """Test error handling in get_search_stats"""
        # This should handle database errors gracefully
        stats = await initialized_db_manager.get_search_stats()
        
        # Should return default values on error
        assert isinstance(stats, dict)
        assert "total_searches" in stats
        assert "average_execution_time_ms" in stats
        assert "cache_hit_rate" in stats


class TestDatabaseConcurrency:
    """Test database concurrency"""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, initialized_db_manager):
        """Test concurrent database operations"""
        # Create multiple content items concurrently
        tasks = []
        for i in range(10):
            task = initialized_db_manager.create_content(
                content_id=f"concurrent_test_{i}",
                content=f"Concurrent content {i}",
                content_type="text"
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # All operations should succeed
        assert all(results)
        
        # Verify all content was created
        for i in range(10):
            content = await initialized_db_manager.get_content(f"concurrent_test_{i}")
            assert content is not None
            assert content["content"] == f"Concurrent content {i}"
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self, initialized_db_manager):
        """Test concurrent search operations"""
        # Create test content first
        for i in range(5):
            await initialized_db_manager.create_content(
                content_id=f"search_concurrent_{i}",
                content=f"Search test content {i}",
                content_type="text"
            )
        
        # Perform multiple searches concurrently
        tasks = []
        for i in range(5):
            task = initialized_db_manager.search_content(
                query=f"content {i}",
                limit=5
            )
            tasks.append(task)
        
        # Execute all searches concurrently
        results = await asyncio.gather(*tasks)
        
        # All searches should complete
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)