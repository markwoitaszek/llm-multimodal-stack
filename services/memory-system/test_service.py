#!/usr/bin/env python3
"""
Simple test script for Memory System Service
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from app.config import settings
        print("✓ Config imported successfully")
        
        from app.models import ConversationCreate, MessageCreate, KnowledgeCreate
        print("✓ Models imported successfully")
        
        from app.database import DatabaseManager
        print("✓ Database manager imported successfully")
        
        from app.cache import CacheManager
        print("✓ Cache manager imported successfully")
        
        from app.conversation import ConversationManager
        print("✓ Conversation manager imported successfully")
        
        from app.knowledge_base import KnowledgeManager
        print("✓ Knowledge manager imported successfully")
        
        from app.memory_manager import MemoryManager
        print("✓ Memory manager imported successfully")
        
        from app.api import router
        print("✓ API router imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_models():
    """Test Pydantic models"""
    try:
        from app.models import ConversationCreate, MessageCreate, KnowledgeCreate, MessageRole, KnowledgeCategory
        
        # Test conversation creation
        conv_data = ConversationCreate(
            agent_id="test-agent-123",
            title="Test Conversation",
            metadata={"test": True}
        )
        print("✓ ConversationCreate model works")
        
        # Test message creation
        msg_data = MessageCreate(
            conversation_id="test-conv-123",
            role=MessageRole.USER,
            content="Hello, world!",
            metadata={"test": True}
        )
        print("✓ MessageCreate model works")
        
        # Test knowledge creation
        kb_data = KnowledgeCreate(
            agent_id="test-agent-123",
            category=KnowledgeCategory.FACT,
            title="Test Knowledge",
            content="This is a test knowledge entry",
            tags=["test", "example"],
            metadata={"test": True}
        )
        print("✓ KnowledgeCreate model works")
        
        return True
        
    except Exception as e:
        print(f"✗ Model test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from app.config import settings
        
        # Test that settings are loaded
        assert settings.service_name == "memory-system"
        assert settings.port == 8005
        assert settings.host == "0.0.0.0"
        
        print("✓ Configuration loaded successfully")
        print(f"  Service: {settings.service_name}")
        print(f"  Host: {settings.host}")
        print(f"  Port: {settings.port}")
        print(f"  Redis DB: {settings.redis_db}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint models and structure"""
    try:
        from app.models import HealthResponse, MemoryStats
        from datetime import datetime
        
        # Test MemoryStats model
        stats = MemoryStats(
            total_conversations=10,
            total_messages=50,
            total_knowledge_items=5,
            total_summaries=2,
            active_conversations=3,
            cache_hit_rate=85.5,
            memory_usage_mb=1.0
        )
        print("✓ MemoryStats model works")
        
        # Test HealthResponse model
        health = HealthResponse(
            status="healthy",
            service="memory-system",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            database_status="healthy",
            redis_status="healthy",
            memory_stats=stats
        )
        print("✓ HealthResponse model works")
        
        # Test health response without stats
        health_no_stats = HealthResponse(
            status="degraded",
            service="memory-system",
            version="1.0.0",
            timestamp=datetime.utcnow(),
            database_status="healthy",
            redis_status="unhealthy"
        )
        print("✓ HealthResponse model works without stats")
        
        return True
        
    except Exception as e:
        print(f"✗ Health endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Memory System Service...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Model Test", test_models),
        ("Config Test", test_config),
        ("Health Endpoint Test", test_health_endpoint)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"  {test_name} failed!")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Memory System Service is ready.")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())