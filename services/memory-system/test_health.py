#!/usr/bin/env python3
"""
Simple test script for memory system health endpoint
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import DatabaseManager
from app.cache import CacheManager
from app.api import health_check
from fastapi import Request
from unittest.mock import AsyncMock


async def test_health_endpoint():
    """Test the health endpoint functionality"""
    print("Testing Memory System Health Endpoint...")
    
    # Mock the dependencies
    mock_db_manager = AsyncMock()
    mock_cache_manager = AsyncMock()
    
    # Test case 1: All systems healthy
    print("\n1. Testing healthy state...")
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
    
    try:
        response = await health_check(mock_db_manager, mock_cache_manager)
        print(f"✅ Healthy state: {response.status}")
        print(f"   Database: {response.database_status}")
        print(f"   Redis: {response.redis_status}")
        print(f"   Memory stats: {response.memory_stats is not None}")
    except Exception as e:
        print(f"❌ Healthy state failed: {e}")
    
    # Test case 2: Database unhealthy
    print("\n2. Testing degraded state (DB unhealthy)...")
    mock_db_manager.health_check.return_value = {
        "status": "unhealthy",
        "pool_size": 0,
        "active_connections": 0,
        "idle_connections": 0,
        "error": "Connection timeout"
    }
    
    try:
        response = await health_check(mock_db_manager, mock_cache_manager)
        print(f"✅ Degraded state: {response.status}")
        print(f"   Database: {response.database_status}")
        print(f"   Redis: {response.redis_status}")
    except Exception as e:
        print(f"❌ Degraded state failed: {e}")
    
    # Test case 3: Both systems unhealthy
    print("\n3. Testing unhealthy state...")
    mock_cache_manager.health_check.return_value = {
        "status": "unhealthy",
        "connected_clients": 0,
        "used_memory": 0,
        "error": "Connection refused"
    }
    
    try:
        response = await health_check(mock_db_manager, mock_cache_manager)
        print(f"✅ Unhealthy state: {response.status}")
        print(f"   Database: {response.database_status}")
        print(f"   Redis: {response.redis_status}")
    except Exception as e:
        print(f"❌ Unhealthy state failed: {e}")
    
    print("\n✅ Health endpoint tests completed!")


if __name__ == "__main__":
    asyncio.run(test_health_endpoint())