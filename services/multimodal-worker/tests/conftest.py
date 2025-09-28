"""
Test configuration and fixtures
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment with proper directories and configuration"""
    # Create temporary directories for testing
    test_cache_dir = tempfile.mkdtemp(prefix="test_cache_")
    test_model_cache_dir = os.path.join(test_cache_dir, "models")
    test_temp_dir = tempfile.mkdtemp(prefix="test_temp_")
    
    os.makedirs(test_model_cache_dir, exist_ok=True)
    
    # Set environment variables to override settings
    os.environ['TEST_CACHE_DIR'] = test_cache_dir
    os.environ['TEST_MODEL_CACHE_DIR'] = test_model_cache_dir
    os.environ['TEST_TEMP_DIR'] = test_temp_dir
    
    yield
    
    # Cleanup
    import shutil
    try:
        shutil.rmtree(test_cache_dir)
        shutil.rmtree(test_temp_dir)
    except:
        pass

@pytest.fixture
def mock_managers():
    """Create mock managers for testing"""
    model_manager = Mock()
    db_manager = AsyncMock()
    storage_manager = Mock()
    return model_manager, db_manager, storage_manager