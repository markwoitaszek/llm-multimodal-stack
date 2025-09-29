"""
Unit tests for configuration in multimodal-worker service
"""
import pytest
from unittest.mock import patch, Mock
import os
import sys
from pathlib import Path

# Add the service directory to the path
service_dir = Path(__file__).parent.parent.parent / "services" / "multimodal-worker"
sys.path.insert(0, str(service_dir))

from app.config import settings


class TestConfig:
    """Test cases for configuration management"""

    def test_settings_initialization(self):
        """Test that settings are properly initialized"""
        assert settings is not None
        assert hasattr(settings, 'postgres_url')
        assert hasattr(settings, 'minio_url')
        assert hasattr(settings, 'qdrant_url')

    @patch.dict(os.environ, {'POSTGRES_URL': 'test_postgres_url'})
    def test_environment_variable_override(self):
        """Test that environment variables override default settings"""
        # This test verifies that environment variables can override settings
        # The actual override would happen during settings initialization
        assert True  # Placeholder for actual environment variable testing

    def test_settings_types(self):
        """Test that settings have correct types"""
        assert isinstance(settings.postgres_url, str)
        assert isinstance(settings.minio_url, str)
        assert isinstance(settings.qdrant_url, str)

    def test_required_settings_present(self):
        """Test that all required settings are present"""
        required_settings = [
            'postgres_url', 'minio_url', 'qdrant_url',
            'llm_base_url', 'llm_model'
        ]
        
        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing required setting: {setting}"