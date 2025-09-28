"""
Memory Manager Core Logic Tests
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from app.models import (
    MemoryRequest, RetrieveRequest, ConversationRequest, ContextRequest,
    ConsolidateRequest, MemoryType, MemoryImportance
)
from app.memory_manager import MemoryManager
from app.database import db_manager
from app.embeddings import cached_embedding_service


class TestMemoryManager:
    """Test Memory Manager core functionality"""
    
    @pytest.fixture
    def memory_manager_instance(self):
        """Create memory manager instance for testing"""
        return MemoryManager()
    
    @pytest.fixture
    def mock_memory_request(self):
        """Mock memory request"""
        return MemoryRequest(
            content="Test memory content",
            memory_type=MemoryType.KNOWLEDGE,
            importance=MemoryImportance.MEDIUM,
            tags=["test", "memory"],
            metadata={"source": "test"},
            user_id="test_user",
            session_id="test_session"
        )
    
    @pytest.fixture
    def mock_retrieve_request(self):
        """Mock retrieve request"""
        return RetrieveRequest(
            query="test query",
            memory_types=[MemoryType.KNOWLEDGE],
            importance_levels=[MemoryImportance.MEDIUM],
            user_id="test_user",
            session_id="test_session",
            limit=10
        )
    
    @pytest.fixture
    def mock_conversation_request(self):
        """Mock conversation request"""
        return ConversationRequest(
            messages=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ],
            user_id="test_user",
            session_id="test_session",
            context={"topic": "greeting"},
            summary="Greeting conversation"
        )
    
    @pytest.mark.asyncio
    async def test_store_memory(self, memory_manager_instance, mock_memory_request):
        """Test storing memory"""
        with patch.object(cached_embedding_service, 'generate_embedding') as mock_embedding, \
             patch.object(db_manager, 'create_memory') as mock_create_memory:
            
            # Setup mocks
            mock_embedding.return_value = [0.1] * 384
            mock_create_memory.return_value = True
            
            # Store memory
            result = await memory_manager_instance.store_memory(mock_memory_request)
            
            # Verify result
            assert result.content == mock_memory_request.content
            assert result.memory_type == mock_memory_request.memory_type
            assert result.importance == mock_memory_request.importance
            assert result.tags == mock_memory_request.tags
            assert result.metadata == mock_memory_request.metadata
            assert result.embedding == [0.1] * 384
            
            # Verify mocks were called
            mock_embedding.assert_called_once()
            mock_create_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_memory_database_error(self, memory_manager_instance, mock_memory_request):
        """Test storing memory with database error"""
        with patch.object(cached_embedding_service, 'generate_embedding') as mock_embedding, \
             patch.object(db_manager, 'create_memory') as mock_create_memory:
            
            # Setup mocks
            mock_embedding.return_value = [0.1] * 384
            mock_create_memory.return_value = False  # Database error
            
            # Should raise exception
            with pytest.raises(Exception, match="Failed to store memory"):
                await memory_manager_instance.store_memory(mock_memory_request)
    
    @pytest.mark.asyncio
    async def test_retrieve_memories(self, memory_manager_instance, mock_retrieve_request):
        """Test retrieving memories"""
        with patch.object(memory_manager_instance, '_perform_memory_retrieval') as mock_retrieval:
            # Setup mock
            mock_memory_responses = [
                {
                    "memory_id": "memory_1",
                    "content": "Retrieved memory 1",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            mock_retrieval.return_value = mock_memory_responses
            
            # Retrieve memories
            result = await memory_manager_instance.retrieve_memories(mock_retrieve_request)
            
            # Verify result
            assert result.query == mock_retrieve_request.query
            assert len(result.memories) == 1
            assert result.total_results == 1
            assert result.execution_time_ms > 0
            assert result.retrieval_id is not None
            
            # Verify mock was called
            mock_retrieval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_memory_retrieval(self, memory_manager_instance, mock_retrieve_request):
        """Test performing memory retrieval"""
        with patch.object(db_manager, 'search_memories') as mock_search:
            # Setup mock
            mock_db_results = [
                {
                    "id": "memory_1",
                    "content": "Test memory content",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "tags": ["test"],
                    "metadata": {"source": "test"},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "score": 0.8
                }
            ]
            mock_search.return_value = mock_db_results
            
            # Perform retrieval
            results = await memory_manager_instance._perform_memory_retrieval(mock_retrieve_request)
            
            # Verify results
            assert len(results) == 1
            assert results[0].memory_id == "memory_1"
            assert results[0].content == "Test memory content"
            assert results[0].memory_type == MemoryType.KNOWLEDGE
            assert results[0].importance == MemoryImportance.MEDIUM
            
            # Verify mock was called
            mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_memory_retrieval_with_similarity_threshold(self, memory_manager_instance):
        """Test memory retrieval with similarity threshold filtering"""
        retrieve_request = RetrieveRequest(
            query="test query",
            similarity_threshold=0.7,  # Higher threshold
            limit=10
        )
        
        with patch.object(db_manager, 'search_memories') as mock_search:
            # Setup mock with low-scoring result
            mock_db_results = [
                {
                    "id": "memory_1",
                    "content": "Test memory content",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "tags": ["test"],
                    "metadata": {"source": "test"},
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "score": 0.5  # Below threshold
                }
            ]
            mock_search.return_value = mock_db_results
            
            # Perform retrieval
            results = await memory_manager_instance._perform_memory_retrieval(retrieve_request)
            
            # Should filter out low-scoring result
            assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_store_conversation(self, memory_manager_instance, mock_conversation_request):
        """Test storing conversation"""
        with patch.object(db_manager, 'create_conversation') as mock_create_conversation:
            # Setup mock
            mock_create_conversation.return_value = True
            
            # Store conversation
            result = await memory_manager_instance.store_conversation(mock_conversation_request)
            
            # Verify result
            assert result.messages == mock_conversation_request.messages
            assert result.user_id == mock_conversation_request.user_id
            assert result.session_id == mock_conversation_request.session_id
            assert result.context == mock_conversation_request.context
            assert result.summary == mock_conversation_request.summary
            
            # Verify mock was called
            mock_create_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_conversation(self, memory_manager_instance):
        """Test getting conversation"""
        with patch.object(db_manager, 'get_conversation') as mock_get_conversation:
            # Setup mock
            mock_conversation = {
                "id": "conv_1",
                "messages": [{"role": "user", "content": "Hello"}],
                "user_id": "test_user",
                "session_id": "test_session",
                "context": {"topic": "greeting"},
                "summary": "Greeting",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            mock_get_conversation.return_value = mock_conversation
            
            # Get conversation
            result = await memory_manager_instance.get_conversation("conv_1")
            
            # Verify result
            assert result.conversation_id == "conv_1"
            assert len(result.messages) == 1
            assert result.user_id == "test_user"
            assert result.session_id == "test_session"
            
            # Verify mock was called
            mock_get_conversation.assert_called_once_with("conv_1")
    
    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, memory_manager_instance):
        """Test getting non-existent conversation"""
        with patch.object(db_manager, 'get_conversation') as mock_get_conversation:
            # Setup mock
            mock_get_conversation.return_value = None
            
            # Get conversation
            result = await memory_manager_instance.get_conversation("nonexistent")
            
            # Should return None
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_context(self, memory_manager_instance):
        """Test getting context"""
        context_request = ContextRequest(
            query="What did we discuss?",
            user_id="test_user",
            session_id="test_session",
            context_window=20,
            include_conversations=True,
            include_memories=True
        )
        
        with patch.object(db_manager, 'get_conversations_by_session') as mock_get_conversations, \
             patch.object(memory_manager_instance, '_perform_memory_retrieval') as mock_memory_retrieval:
            
            # Setup mocks
            mock_conversations = [
                {
                    "id": "conv_1",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "summary": "Greeting",
                    "created_at": datetime.utcnow()
                }
            ]
            mock_get_conversations.return_value = mock_conversations
            
            mock_memory_responses = [
                {
                    "memory_id": "memory_1",
                    "content": "Context memory",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "tags": ["context"],
                    "created_at": datetime.utcnow()
                }
            ]
            mock_memory_retrieval.return_value = mock_memory_responses
            
            # Get context
            result = await memory_manager_instance.get_context(context_request)
            
            # Verify result
            assert result.query == context_request.query
            assert len(result.context) == 2  # 1 conversation + 1 memory
            assert result.total_context_items == 2
            assert result.execution_time_ms > 0
            assert result.context_id is not None
            
            # Verify mocks were called
            mock_get_conversations.assert_called_once()
            mock_memory_retrieval.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consolidate_memories(self, memory_manager_instance):
        """Test consolidating memories"""
        consolidate_request = ConsolidateRequest(
            user_id="test_user",
            session_id="test_session",
            memory_types=[MemoryType.KNOWLEDGE],
            force=False
        )
        
        with patch.object(db_manager, 'get_memories_for_consolidation') as mock_get_memories, \
             patch.object(memory_manager_instance, '_perform_consolidation') as mock_consolidation, \
             patch.object(db_manager, 'mark_memories_consolidated') as mock_mark_consolidated:
            
            # Setup mocks
            mock_memories = [
                {
                    "id": "memory_1",
                    "content": "Memory 1",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "tags": ["test"],
                    "user_id": "test_user",
                    "session_id": "test_session",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": "memory_2",
                    "content": "Memory 2",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "tags": ["test"],
                    "user_id": "test_user",
                    "session_id": "test_session",
                    "created_at": datetime.utcnow()
                }
            ]
            mock_get_memories.return_value = mock_memories
            mock_consolidation.return_value = 1  # 1 new memory created
            mock_mark_consolidated.return_value = True
            
            # Consolidate memories
            result = await memory_manager_instance.consolidate_memories(consolidate_request)
            
            # Verify result
            assert result.consolidated_count == 2
            assert result.new_memories_created == 1
            assert result.consolidation_time_ms > 0
            assert result.consolidation_id is not None
            
            # Verify mocks were called
            mock_get_memories.assert_called_once()
            mock_consolidation.assert_called_once()
            mock_mark_consolidated.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consolidate_memories_insufficient_threshold(self, memory_manager_instance):
        """Test consolidating memories when threshold not met"""
        consolidate_request = ConsolidateRequest(
            user_id="test_user",
            force=False  # Don't force
        )
        
        with patch.object(db_manager, 'get_memories_for_consolidation') as mock_get_memories:
            # Setup mock with insufficient memories
            mock_get_memories.return_value = []  # No memories to consolidate
            
            # Consolidate memories
            result = await memory_manager_instance.consolidate_memories(consolidate_request)
            
            # Should return zero counts
            assert result.consolidated_count == 0
            assert result.new_memories_created == 0
    
    @pytest.mark.asyncio
    async def test_perform_consolidation(self, memory_manager_instance):
        """Test performing consolidation"""
        memories = [
            {
                "id": "memory_1",
                "content": "Memory 1 content",
                "memory_type": "knowledge",
                "importance": "medium",
                "tags": ["test"],
                "user_id": "test_user",
                "session_id": "test_session",
                "created_at": datetime.utcnow()
            },
            {
                "id": "memory_2",
                "content": "Memory 2 content",
                "memory_type": "knowledge",
                "importance": "medium",
                "tags": ["test"],
                "user_id": "test_user",
                "session_id": "test_session",
                "created_at": datetime.utcnow()
            },
            {
                "id": "memory_3",
                "content": "Memory 3 content",
                "memory_type": "knowledge",
                "importance": "medium",
                "tags": ["test"],
                "user_id": "test_user",
                "session_id": "test_session",
                "created_at": datetime.utcnow()
            }
        ]
        
        with patch.object(db_manager, 'create_memory') as mock_create_memory:
            # Setup mock
            mock_create_memory.return_value = True
            
            # Perform consolidation
            new_memories_created = await memory_manager_instance._perform_consolidation(memories)
            
            # Should create 1 consolidated memory
            assert new_memories_created == 1
            
            # Verify mock was called
            mock_create_memory.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_consolidated_content(self, memory_manager_instance):
        """Test creating consolidated content"""
        memories = [
            {
                "content": "First memory content",
                "id": "memory_1"
            },
            {
                "content": "Second memory content",
                "id": "memory_2"
            }
        ]
        
        # Create consolidated content
        consolidated = await memory_manager_instance._create_consolidated_content(memories)
        
        # Verify content
        assert "Consolidated memories:" in consolidated
        assert "First memory content" in consolidated
        assert "Second memory content" in consolidated
    
    @pytest.mark.asyncio
    async def test_update_memory(self, memory_manager_instance):
        """Test updating memory"""
        update_request = type('UpdateRequest', (), {
            'content': 'Updated content',
            'importance': MemoryImportance.HIGH,
            'tags': ['updated'],
            'metadata': {'updated': True}
        })()
        
        with patch.object(db_manager, 'update_memory') as mock_update, \
             patch.object(db_manager, 'get_memory') as mock_get:
            
            # Setup mocks
            mock_update.return_value = True
            mock_get.return_value = {
                "id": "memory_1",
                "content": "Updated content",
                "memory_type": "knowledge",
                "importance": "high",
                "tags": ["updated"],
                "metadata": {"updated": True},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Update memory
            result = await memory_manager_instance.update_memory("memory_1", update_request)
            
            # Verify result
            assert result.memory_id == "memory_1"
            assert result.content == "Updated content"
            assert result.importance == MemoryImportance.HIGH
            assert result.tags == ["updated"]
            assert result.metadata == {"updated": True}
            
            # Verify mocks were called
            mock_update.assert_called_once()
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_memory_not_found(self, memory_manager_instance):
        """Test updating non-existent memory"""
        update_request = type('UpdateRequest', (), {
            'content': 'Updated content'
        })()
        
        with patch.object(db_manager, 'update_memory') as mock_update:
            # Setup mock
            mock_update.return_value = False  # Memory not found
            
            # Update memory
            result = await memory_manager_instance.update_memory("nonexistent", update_request)
            
            # Should return None
            assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_manager_instance):
        """Test deleting memory"""
        with patch.object(db_manager, 'delete_memory') as mock_delete:
            # Setup mock
            mock_delete.return_value = True
            
            # Delete memory
            result = await memory_manager_instance.delete_memory("memory_1")
            
            # Should return True
            assert result is True
            
            # Verify mock was called
            mock_delete.assert_called_once_with("memory_1")
    
    @pytest.mark.asyncio
    async def test_get_memory_stats(self, memory_manager_instance):
        """Test getting memory statistics"""
        with patch.object(db_manager, 'get_memory_stats') as mock_get_stats:
            # Setup mock
            mock_stats = {
                "total_memories": 100,
                "total_conversations": 50,
                "memory_types_distribution": {"knowledge": 60, "conversation": 40},
                "importance_distribution": {"high": 20, "medium": 60, "low": 20},
                "average_memory_size": 150.5
            }
            mock_get_stats.return_value = mock_stats
            
            # Get stats
            stats = await memory_manager_instance.get_memory_stats()
            
            # Verify stats
            assert stats["total_memories"] == 100
            assert stats["total_conversations"] == 50
            assert "memory_types_distribution" in stats
            assert "cache_size" in stats
            assert "cache_ttl" in stats
            
            # Verify mock was called
            mock_get_stats.assert_called_once()
    
    def test_generate_cache_key(self, memory_manager_instance):
        """Test generating cache key"""
        retrieve_request = RetrieveRequest(
            query="test query",
            memory_types=[MemoryType.KNOWLEDGE],
            importance_levels=[MemoryImportance.MEDIUM],
            tags=["test"],
            user_id="test_user",
            session_id="test_session",
            limit=10,
            similarity_threshold=0.5,
            include_metadata=True
        )
        
        # Generate cache key
        cache_key = memory_manager_instance._generate_cache_key(retrieve_request)
        
        # Should be a string
        assert isinstance(cache_key, str)
        assert len(cache_key) > 0
    
    def test_clear_cache(self, memory_manager_instance):
        """Test clearing cache"""
        # Add items to cache
        memory_manager_instance.cache["test_key"] = {
            "response": "test_response",
            "timestamp": 1234567890
        }
        
        assert len(memory_manager_instance.cache) == 1
        
        # Clear cache
        memory_manager_instance.clear_cache()
        
        assert len(memory_manager_instance.cache) == 0


class TestMemoryManagerConcurrency:
    """Test memory manager concurrency and performance"""
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test multiple concurrent memory operations"""
        memory_manager = MemoryManager()
        
        # Create multiple memory requests
        requests = [
            MemoryRequest(
                content=f"Concurrent memory {i}",
                memory_type=MemoryType.KNOWLEDGE,
                importance=MemoryImportance.MEDIUM,
                user_id="concurrent_test_user",
                session_id="concurrent_test_session"
            )
            for i in range(10)
        ]
        
        # Mock the store_memory method to avoid actual dependencies
        with patch.object(memory_manager, 'store_memory') as mock_store:
            mock_store.return_value = {
                "memory_id": "test_id",
                "content": "test content",
                "memory_type": "knowledge",
                "importance": "medium",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Execute operations concurrently
            tasks = [memory_manager.store_memory(request) for request in requests]
            results = await asyncio.gather(*tasks)
            
            # All operations should complete
            assert len(results) == 10
            for result in results:
                assert result["memory_id"] == "test_id"
    
    @pytest.mark.asyncio
    async def test_semaphore_limit(self):
        """Test semaphore limits concurrent operations"""
        memory_manager = MemoryManager()
        
        # Create more requests than the semaphore limit
        requests = [
            MemoryRequest(
                content=f"Semaphore test memory {i}",
                memory_type=MemoryType.KNOWLEDGE,
                importance=MemoryImportance.MEDIUM
            )
            for i in range(20)  # More than max_concurrent_operations
        ]
        
        with patch.object(memory_manager, 'store_memory') as mock_store:
            mock_store.return_value = {
                "memory_id": "test_id",
                "content": "test content",
                "memory_type": "knowledge",
                "importance": "medium",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Execute operations
            tasks = [memory_manager.store_memory(request) for request in requests]
            results = await asyncio.gather(*tasks)
            
            # All should complete despite semaphore limit
            assert len(results) == 20