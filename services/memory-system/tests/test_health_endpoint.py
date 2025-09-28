"""
Test suite for memory system health endpoint
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from app.models import HealthResponse, MemoryStats


class TestHealthEndpoint:
    """Test cases for the health endpoint"""
    
    def test_health_endpoint_healthy(self):
        """Test health endpoint when all systems are healthy"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock healthy database manager
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.return_value = {
                "status": "healthy",
                "pool_size": 5,
                "active_connections": 2,
                "idle_connections": 3,
                "error": None
            }
            mock_db_manager.get_memory_stats.return_value = {
                "total_conversations": 10,
                "total_messages": 50,
                "total_knowledge_items": 5,
                "total_summaries": 2,
                "active_conversations": 3
            }
            
            # Mock healthy cache manager
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.return_value = {
                "status": "healthy",
                "connected_clients": 1,
                "used_memory": 1024000,
                "error": None
            }
            mock_cache_manager.get_cache_stats.return_value = {
                "status": "connected",
                "hit_rate": 85.5,
                "used_memory": 1024000
            }
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["service"] == "memory-system"
            assert data["version"] == "1.0.0"
            assert data["database_status"] == "healthy"
            assert data["redis_status"] == "healthy"
            assert data["memory_stats"] is not None
            assert data["memory_stats"]["total_conversations"] == 10
            assert data["memory_stats"]["cache_hit_rate"] == 85.5
            assert data["memory_stats"]["memory_usage_mb"] == 1.0  # 1024000 / (1024 * 1024)
    
    def test_health_endpoint_degraded_database(self):
        """Test health endpoint when database is unhealthy"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock unhealthy database manager
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.return_value = {
                "status": "unhealthy",
                "pool_size": 0,
                "active_connections": 0,
                "idle_connections": 0,
                "error": "Connection timeout"
            }
            
            # Mock healthy cache manager
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.return_value = {
                "status": "healthy",
                "connected_clients": 1,
                "used_memory": 1024000,
                "error": None
            }
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["database_status"] == "unhealthy"
            assert data["redis_status"] == "healthy"
            assert data["memory_stats"] is None
    
    def test_health_endpoint_degraded_redis(self):
        """Test health endpoint when Redis is unhealthy"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock healthy database manager
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.return_value = {
                "status": "healthy",
                "pool_size": 5,
                "active_connections": 2,
                "idle_connections": 3,
                "error": None
            }
            mock_db_manager.get_memory_stats.return_value = {
                "total_conversations": 10,
                "total_messages": 50,
                "total_knowledge_items": 5,
                "total_summaries": 2,
                "active_conversations": 3
            }
            
            # Mock unhealthy cache manager
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.return_value = {
                "status": "unhealthy",
                "connected_clients": 0,
                "used_memory": 0,
                "error": "Connection refused"
            }
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "degraded"
            assert data["database_status"] == "healthy"
            assert data["redis_status"] == "unhealthy"
            assert data["memory_stats"] is not None
            assert data["memory_stats"]["cache_hit_rate"] == 0.0
            assert data["memory_stats"]["memory_usage_mb"] == 0.0
    
    def test_health_endpoint_unhealthy_both(self):
        """Test health endpoint when both systems are unhealthy"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock unhealthy database manager
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.return_value = {
                "status": "unhealthy",
                "pool_size": 0,
                "active_connections": 0,
                "idle_connections": 0,
                "error": "Connection timeout"
            }
            
            # Mock unhealthy cache manager
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.return_value = {
                "status": "unhealthy",
                "connected_clients": 0,
                "used_memory": 0,
                "error": "Connection refused"
            }
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert data["database_status"] == "unhealthy"
            assert data["redis_status"] == "unhealthy"
            assert data["memory_stats"] is None
    
    def test_health_endpoint_memory_stats_failure(self):
        """Test health endpoint when memory stats calculation fails"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock healthy database manager with failing stats
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.return_value = {
                "status": "healthy",
                "pool_size": 5,
                "active_connections": 2,
                "idle_connections": 3,
                "error": None
            }
            mock_db_manager.get_memory_stats.side_effect = Exception("Stats calculation failed")
            
            # Mock healthy cache manager
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.return_value = {
                "status": "healthy",
                "connected_clients": 1,
                "used_memory": 1024000,
                "error": None
            }
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["database_status"] == "healthy"
            assert data["redis_status"] == "healthy"
            assert data["memory_stats"] is None
    
    def test_health_endpoint_cache_stats_failure(self):
        """Test health endpoint when cache stats calculation fails"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock healthy database manager
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.return_value = {
                "status": "healthy",
                "pool_size": 5,
                "active_connections": 2,
                "idle_connections": 3,
                "error": None
            }
            mock_db_manager.get_memory_stats.return_value = {
                "total_conversations": 10,
                "total_messages": 50,
                "total_knowledge_items": 5,
                "total_summaries": 2,
                "active_conversations": 3
            }
            
            # Mock healthy cache manager with failing stats
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.return_value = {
                "status": "healthy",
                "connected_clients": 1,
                "used_memory": 1024000,
                "error": None
            }
            mock_cache_manager.get_cache_stats.side_effect = Exception("Cache stats failed")
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert data["database_status"] == "healthy"
            assert data["redis_status"] == "healthy"
            assert data["memory_stats"] is not None
            assert data["memory_stats"]["cache_hit_rate"] == 0.0
            assert data["memory_stats"]["memory_usage_mb"] == 0.0
    
    def test_health_endpoint_exception_handling(self):
        """Test health endpoint exception handling"""
        with patch('app.api.get_db_manager') as mock_db_dep, \
             patch('app.api.get_cache_manager') as mock_cache_dep:
            
            # Mock managers that raise exceptions
            mock_db_manager = AsyncMock()
            mock_db_manager.health_check.side_effect = Exception("Database health check failed")
            
            mock_cache_manager = AsyncMock()
            mock_cache_manager.health_check.side_effect = Exception("Cache health check failed")
            
            mock_db_dep.return_value = mock_db_manager
            mock_cache_dep.return_value = mock_cache_manager
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert data["database_status"] == "unknown"
            assert data["redis_status"] == "unknown"
            assert data["memory_stats"] is None


if __name__ == "__main__":
    pytest.main([__file__])