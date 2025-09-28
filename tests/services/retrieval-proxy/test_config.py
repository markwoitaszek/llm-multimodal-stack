"""
Unit tests for configuration in retrieval-proxy service
"""
import pytest
from unittest.mock import patch, Mock
import os

from app.config import settings


class TestConfig:
    """Test cases for configuration management"""

    def test_settings_initialization(self):
        """Test that settings are properly initialized"""
        assert settings is not None
        assert hasattr(settings, 'postgres_url')
        assert hasattr(settings, 'qdrant_url')
        assert hasattr(settings, 'multimodal_worker_url')

    def test_settings_types(self):
        """Test that settings have correct types"""
        assert isinstance(settings.postgres_url, str)
        assert isinstance(settings.qdrant_url, str)
        assert isinstance(settings.multimodal_worker_url, str)

    def test_required_settings_present(self):
        """Test that all required settings are present"""
        required_settings = [
            'postgres_url', 'qdrant_url', 'multimodal_worker_url'
        ]
        
        for setting in required_settings:
            assert hasattr(settings, setting), f"Missing required setting: {setting}"