#!/usr/bin/env python3
"""
Basic functionality test for user management service
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from app.config import settings
        print("✓ Config module imported successfully")
        
        from app.models import UserCreate, UserResponse, TenantCreate
        print("✓ Models module imported successfully")
        
        from app.database import db_manager
        print("✓ Database module imported successfully")
        
        from app.auth import auth_manager
        print("✓ Auth module imported successfully")
        
        from app.user_manager import user_manager
        print("✓ User manager module imported successfully")
        
        from app.tenant_manager import tenant_manager
        print("✓ Tenant manager module imported successfully")
        
        from app.cache import cache_manager
        print("✓ Cache module imported successfully")
        
        from app.api import router
        print("✓ API module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from app.config import settings
        
        # Test basic settings
        assert settings.service_name == "user-management"
        assert settings.port == 8006
        assert settings.host == "0.0.0.0"
        
        print("✓ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_models():
    """Test Pydantic models"""
    try:
        from app.models import UserCreate, UserResponse, TenantCreate, UserRole, UserStatus
        
        # Test UserCreate model
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        user = UserCreate(**user_data)
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
        assert user.status == UserStatus.ACTIVE
        
        print("✓ Models validation working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False

def test_auth():
    """Test authentication utilities"""
    try:
        from app.auth import auth_manager
        
        # Test password hashing
        password = "TestPassword123"
        hashed = auth_manager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        
        # Test password verification
        assert auth_manager.verify_password(password, hashed) == True
        assert auth_manager.verify_password("wrong", hashed) == False
        
        print("✓ Authentication utilities working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running basic functionality tests for User Management Service...")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_config,
        test_models,
        test_auth
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed! Service is ready for deployment.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())