"""
Memory System API Tests
"""
import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.models import (
    MemoryRequest, ConversationRequest, RetrieveRequest, ContextRequest,
    ConsolidateRequest, MemoryType, MemoryImportance
)
from app.api import app


class TestMemorySystemAPI:
    """Test Memory System API endpoints"""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Memory System Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "dependencies" in data
    
    @patch('app.memory_manager.memory_manager.store_memory')
    def test_store_memory_endpoint(self, mock_store_memory, test_client, sample_memory_request):
        """Test store memory endpoint"""
        # Mock memory storage response
        mock_memory_response = {
            "memory_id": "test_memory_id",
            "content": sample_memory_request.content,
            "memory_type": sample_memory_request.memory_type.value,
            "importance": sample_memory_request.importance.value,
            "tags": sample_memory_request.tags,
            "metadata": sample_memory_request.metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "embedding": [0.1] * 384
        }
        
        mock_store_memory.return_value = AsyncMock(return_value=mock_memory_response)
        
        response = test_client.post("/api/v1/memories", json=sample_memory_request.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == sample_memory_request.content
        assert data["memory_type"] == sample_memory_request.memory_type.value
    
    def test_store_memory_endpoint_invalid_request(self, test_client):
        """Test store memory endpoint with invalid request"""
        invalid_request = {
            "content": "",  # Empty content should fail
            "memory_type": "invalid_type",  # Invalid memory type
            "importance": "invalid_importance"  # Invalid importance
        }
        
        response = test_client.post("/api/v1/memories", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @patch('app.database.db_manager.get_memory')
    def test_get_memory_endpoint(self, mock_get_memory, test_client):
        """Test get memory endpoint"""
        mock_memory = {
            "id": "test_memory_id",
            "content": "Test memory content",
            "memory_type": "knowledge",
            "importance": "medium",
            "tags": ["test"],
            "metadata": {"source": "test"},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "accessed_at": datetime.utcnow(),
            "access_count": 1,
            "consolidated": False
        }
        
        mock_get_memory.return_value = AsyncMock(return_value=mock_memory)
        
        response = test_client.get("/api/v1/memories/test_memory_id")
        assert response.status_code == 200
        data = response.json()
        assert data["memory_id"] == "test_memory_id"
        assert data["content"] == "Test memory content"
    
    def test_get_memory_endpoint_not_found(self, test_client):
        """Test get memory endpoint when memory not found"""
        response = test_client.get("/api/v1/memories/nonexistent_memory_id")
        assert response.status_code == 404
    
    @patch('app.memory_manager.memory_manager.update_memory')
    def test_update_memory_endpoint(self, mock_update_memory, test_client):
        """Test update memory endpoint"""
        update_request = {
            "content": "Updated memory content",
            "importance": "high"
        }
        
        mock_updated_memory = {
            "memory_id": "test_memory_id",
            "content": "Updated memory content",
            "memory_type": "knowledge",
            "importance": "high",
            "tags": ["test"],
            "metadata": {"source": "test"},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_update_memory.return_value = AsyncMock(return_value=mock_updated_memory)
        
        response = test_client.put("/api/v1/memories/test_memory_id", json=update_request)
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated memory content"
        assert data["importance"] == "high"
    
    @patch('app.memory_manager.memory_manager.delete_memory')
    def test_delete_memory_endpoint(self, mock_delete_memory, test_client):
        """Test delete memory endpoint"""
        mock_delete_memory.return_value = AsyncMock(return_value=True)
        
        response = test_client.delete("/api/v1/memories/test_memory_id")
        assert response.status_code == 200
        data = response.json()
        assert data["memory_id"] == "test_memory_id"
        assert data["deleted"] is True
    
    def test_delete_memory_endpoint_not_found(self, test_client):
        """Test delete memory endpoint when memory not found"""
        response = test_client.delete("/api/v1/memories/nonexistent_memory_id")
        assert response.status_code == 404
    
    @patch('app.memory_manager.memory_manager.retrieve_memories')
    def test_retrieve_memories_endpoint(self, mock_retrieve_memories, test_client, sample_retrieve_request):
        """Test retrieve memories endpoint"""
        mock_retrieve_response = {
            "query": sample_retrieve_request.query,
            "memories": [
                {
                    "memory_id": "retrieved_memory_1",
                    "content": "Retrieved memory content",
                    "memory_type": "knowledge",
                    "importance": "medium",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            ],
            "total_results": 1,
            "execution_time_ms": 50.0,
            "retrieval_id": "test_retrieval_id"
        }
        
        mock_retrieve_memories.return_value = AsyncMock(return_value=mock_retrieve_response)
        
        response = test_client.post("/api/v1/memories/retrieve", json=sample_retrieve_request.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == sample_retrieve_request.query
        assert len(data["memories"]) == 1
    
    @patch('app.memory_manager.memory_manager.store_conversation')
    def test_store_conversation_endpoint(self, mock_store_conversation, test_client, sample_conversation_request):
        """Test store conversation endpoint"""
        mock_conversation_response = {
            "conversation_id": "test_conversation_id",
            "messages": sample_conversation_request.messages,
            "user_id": sample_conversation_request.user_id,
            "session_id": sample_conversation_request.session_id,
            "context": sample_conversation_request.context,
            "summary": sample_conversation_request.summary,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        mock_store_conversation.return_value = AsyncMock(return_value=mock_conversation_response)
        
        response = test_client.post("/api/v1/conversations", json=sample_conversation_request.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test_conversation_id"
        assert len(data["messages"]) == 3
    
    @patch('app.memory_manager.memory_manager.get_conversation')
    def test_get_conversation_endpoint(self, mock_get_conversation, test_client):
        """Test get conversation endpoint"""
        mock_conversation = {
            "conversation_id": "test_conversation_id",
            "messages": [{"role": "user", "content": "Hello"}],
            "user_id": "test_user",
            "session_id": "test_session",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_get_conversation.return_value = AsyncMock(return_value=mock_conversation)
        
        response = test_client.get("/api/v1/conversations/test_conversation_id")
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test_conversation_id"
        assert len(data["messages"]) == 1
    
    def test_get_conversation_endpoint_not_found(self, test_client):
        """Test get conversation endpoint when conversation not found"""
        response = test_client.get("/api/v1/conversations/nonexistent_conversation_id")
        assert response.status_code == 404
    
    @patch('app.database.db_manager.get_conversations_by_session')
    def test_get_conversations_by_session_endpoint(self, mock_get_conversations, test_client):
        """Test get conversations by session endpoint"""
        mock_conversations = [
            {
                "id": "conv_1",
                "messages": [{"role": "user", "content": "Message 1"}],
                "user_id": "test_user",
                "session_id": "test_session",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "accessed_at": None,
                "access_count": 0
            }
        ]
        
        mock_get_conversations.return_value = AsyncMock(return_value=mock_conversations)
        
        response = test_client.get("/api/v1/conversations/session/test_session")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session"
        assert len(data["conversations"]) == 1
    
    @patch('app.memory_manager.memory_manager.get_context')
    def test_get_context_endpoint(self, mock_get_context, test_client, sample_context_request):
        """Test get context endpoint"""
        mock_context_response = {
            "query": sample_context_request.query,
            "context": [
                {
                    "type": "conversation",
                    "id": "conv_1",
                    "content": [{"role": "user", "content": "Context message"}],
                    "created_at": datetime.utcnow().isoformat(),
                    "relevance_score": 0.9
                }
            ],
            "total_context_items": 1,
            "execution_time_ms": 30.0,
            "context_id": "test_context_id"
        }
        
        mock_get_context.return_value = AsyncMock(return_value=mock_context_response)
        
        response = test_client.post("/api/v1/context", json=sample_context_request.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == sample_context_request.query
        assert len(data["context"]) == 1
    
    @patch('app.memory_manager.memory_manager.consolidate_memories')
    def test_consolidate_memories_endpoint(self, mock_consolidate_memories, test_client, sample_consolidate_request):
        """Test consolidate memories endpoint"""
        mock_consolidate_response = {
            "consolidated_count": 5,
            "new_memories_created": 2,
            "consolidation_time_ms": 100.0,
            "consolidation_id": "test_consolidation_id"
        }
        
        mock_consolidate_memories.return_value = AsyncMock(return_value=mock_consolidate_response)
        
        response = test_client.post("/api/v1/memories/consolidate", json=sample_consolidate_request.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["consolidated_count"] == 5
        assert data["new_memories_created"] == 2
    
    @patch('app.memory_manager.memory_manager.get_memory_stats')
    def test_stats_endpoint(self, mock_get_stats, test_client):
        """Test statistics endpoint"""
        mock_stats = {
            "total_memories": 100,
            "total_conversations": 50,
            "memory_types_distribution": {"knowledge": 60, "conversation": 40},
            "importance_distribution": {"high": 20, "medium": 60, "low": 20},
            "average_memory_size": 150.5,
            "cache_hit_rate": 0.8,
            "active_sessions": 5
        }
        
        mock_get_stats.return_value = AsyncMock(return_value=mock_stats)
        
        response = test_client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_memories"] == 100
        assert data["total_conversations"] == 50
        assert "memory_types_distribution" in data
    
    def test_clear_cache_endpoint(self, test_client):
        """Test clear cache endpoint"""
        response = test_client.delete("/api/v1/cache")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Cache cleared successfully"
    
    @patch('app.database.db_manager.cleanup_old_memories')
    def test_cleanup_old_memories_endpoint(self, mock_cleanup, test_client):
        """Test cleanup old memories endpoint"""
        mock_cleanup.return_value = AsyncMock(return_value=25)
        
        response = test_client.post("/api/v1/cleanup")
        assert response.status_code == 200
        data = response.json()
        assert data["cleaned_count"] == 25
        assert "message" in data


class TestMemorySystemAPIIntegration:
    """Integration tests for Memory System API"""
    
    @pytest.mark.asyncio
    async def test_full_memory_workflow(self, test_client, initialized_db_manager, mock_embedding_service):
        """Test complete memory workflow"""
        # Mock the embedding service
        with patch('app.embeddings.cached_embedding_service', mock_embedding_service):
            # Store memory
            memory_request = {
                "content": "Integration test memory",
                "memory_type": "knowledge",
                "importance": "medium",
                "tags": ["integration", "test"],
                "user_id": "integration_test_user",
                "session_id": "integration_test_session"
            }
            
            response = test_client.post("/api/v1/memories", json=memory_request)
            assert response.status_code == 200
            
            # Retrieve memory
            retrieve_request = {
                "query": "integration test",
                "memory_types": ["knowledge"],
                "user_id": "integration_test_user",
                "session_id": "integration_test_session",
                "limit": 10
            }
            
            response = test_client.post("/api/v1/memories/retrieve", json=retrieve_request)
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, test_client):
        """Test concurrent memory operations"""
        import asyncio
        
        async def store_memory(content: str):
            """Store a memory"""
            memory_request = {
                "content": content,
                "memory_type": "knowledge",
                "importance": "medium",
                "user_id": "concurrent_test_user",
                "session_id": "concurrent_test_session"
            }
            response = test_client.post("/api/v1/memories", json=memory_request)
            return response.status_code
        
        # Create multiple concurrent memory storage requests
        tasks = [
            store_memory(f"Concurrent memory {i}")
            for i in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should complete (either successfully or with expected errors)
        for result in results:
            assert isinstance(result, int)  # Should be status code, not exception


class TestMemorySystemAPIErrorHandling:
    """Test error handling in Memory System API"""
    
    def test_store_memory_with_database_error(self, test_client):
        """Test store memory when database is unavailable"""
        with patch('app.database.db_manager.create_memory', side_effect=Exception("Database error")):
            memory_request = {
                "content": "Test memory",
                "memory_type": "knowledge",
                "importance": "medium"
            }
            
            response = test_client.post("/api/v1/memories", json=memory_request)
            assert response.status_code == 500
    
    def test_retrieve_memories_with_embedding_error(self, test_client):
        """Test retrieve memories when embedding generation fails"""
        with patch('app.embeddings.cached_embedding_service.generate_embedding', 
                  side_effect=Exception("Embedding error")):
            retrieve_request = {
                "query": "test query",
                "limit": 10
            }
            
            response = test_client.post("/api/v1/memories/retrieve", json=retrieve_request)
            assert response.status_code == 500
    
    def test_invalid_memory_type(self, test_client):
        """Test store memory with invalid memory type"""
        memory_request = {
            "content": "Test memory",
            "memory_type": "invalid_type",
            "importance": "medium"
        }
        
        response = test_client.post("/api/v1/memories", json=memory_request)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_importance_level(self, test_client):
        """Test store memory with invalid importance level"""
        memory_request = {
            "content": "Test memory",
            "memory_type": "knowledge",
            "importance": "invalid_importance"
        }
        
        response = test_client.post("/api/v1/memories", json=memory_request)
        assert response.status_code == 422  # Validation error
    
    def test_retrieve_with_invalid_limit(self, test_client):
        """Test retrieve memories with invalid limit"""
        retrieve_request = {
            "query": "test query",
            "limit": -1  # Invalid limit
        }
        
        response = test_client.post("/api/v1/memories/retrieve", json=retrieve_request)
        assert response.status_code == 422  # Validation error