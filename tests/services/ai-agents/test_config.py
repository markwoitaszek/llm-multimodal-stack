"""
Unit tests for configuration in ai-agents service
"""
import pytest
from unittest.mock import patch, Mock
import os
import sys
from pathlib import Path

# Add the service directory to the path
service_dir = Path(__file__).parent.parent.parent / "services" / "ai-agents"
sys.path.insert(0, str(service_dir))

from app.config import settings


class TestConfig:
    """Test cases for configuration management"""

    def test_settings_initialization(self):
        """Test that settings are properly initialized"""
        assert settings is not None
        assert hasattr(settings, 'postgres_url')
        assert hasattr(settings, 'llm_base_url')
        assert hasattr(settings, 'llm_model')

    def test_settings_types(self):
        """Test that settings have correct types"""
        assert isinstance(settings.postgres_url, str)
        assert isinstance(settings.llm_base_url, str)
        assert isinstance(settings.llm_model, str)

    def test_required_settings_present(self):
        """Test that all required settings are present"""
        required_settings = [
            'postgres_url', 'llm_base_url', 'llm_model',
            'multimodal_worker_url', 'retrieval_proxy_url'
        ]
        
        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing required setting: {setting}"