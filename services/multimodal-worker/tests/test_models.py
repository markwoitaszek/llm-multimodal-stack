"""
Unit tests for ModelManager in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import torch
import numpy as np
from PIL import Image

from app.models import ModelManager


class TestModelManager:
    """Test cases for ModelManager"""

    @pytest.fixture
    def model_manager(self):
        """Create ModelManager instance for testing"""
        return ModelManager()

    @pytest.mark.asyncio
    async def test_model_manager_initialization(self, model_manager):
        """Test ModelManager initialization"""
        assert model_manager is not None
        assert hasattr(model_manager, 'clip_model')
        assert hasattr(model_manager, 'blip_model')
        assert hasattr(model_manager, 'whisper_model')
        assert hasattr(model_manager, 'sentence_transformer')

    @pytest.mark.asyncio
    @patch('app.models.CLIPModel')
    @patch('app.models.BLIPModel')
    @patch('app.models.WhisperModel')
    @patch('app.models.SentenceTransformer')
    async def test_load_models_success(self, mock_sentence_transformer, mock_whisper, 
                                     mock_blip, mock_clip, model_manager):
        """Test successful model loading"""
        # Setup mocks
        mock_clip.return_value = Mock()
        mock_blip.return_value = Mock()
        mock_whisper.return_value = Mock()
        mock_sentence_transformer.return_value = Mock()

        # Test model loading
        await model_manager.load_models()

        # Verify models were loaded
        assert model_manager.clip_model is not None
        assert model_manager.blip_model is not None
        assert model_manager.whisper_model is not None
        assert model_manager.sentence_transformer is not None

    @pytest.mark.asyncio
    @patch('app.models.CLIPModel')
    async def test_load_models_clip_failure(self, mock_clip, model_manager):
        """Test model loading failure for CLIP"""
        mock_clip.side_effect = Exception("CLIP model loading failed")

        with pytest.raises(Exception, match="CLIP model loading failed"):
            await model_manager.load_models()

    @pytest.mark.asyncio
    async def test_get_model_clip(self, model_manager, mock_clip_model):
        """Test getting CLIP model"""
        model_manager.clip_model = mock_clip_model
        
        model = model_manager.get_model("clip")
        assert model == mock_clip_model

    @pytest.mark.asyncio
    async def test_get_model_blip(self, model_manager, mock_blip_model):
        """Test getting BLIP model"""
        model_manager.blip_model = mock_blip_model
        
        model = model_manager.get_model("blip")
        assert model == mock_blip_model

    @pytest.mark.asyncio
    async def test_get_model_whisper(self, model_manager, mock_whisper_model):
        """Test getting Whisper model"""
        model_manager.whisper_model = mock_whisper_model
        
        model = model_manager.get_model("whisper")
        assert model == mock_whisper_model

    @pytest.mark.asyncio
    async def test_get_model_sentence_transformer(self, model_manager, mock_sentence_transformer):
        """Test getting SentenceTransformer model"""
        model_manager.sentence_transformer = mock_sentence_transformer
        
        model = model_manager.get_model("sentence_transformer")
        assert model == mock_sentence_transformer

    @pytest.mark.asyncio
    async def test_get_model_invalid(self, model_manager):
        """Test getting invalid model"""
        with pytest.raises(ValueError, match="Unknown model type"):
            model_manager.get_model("invalid_model")

    @pytest.mark.asyncio
    async def test_get_processor_image(self, model_manager):
        """Test getting image processor"""
        processor = model_manager.get_processor("image")
        assert processor is not None
        assert hasattr(processor, 'process')

    @pytest.mark.asyncio
    async def test_get_processor_text(self, model_manager):
        """Test getting text processor"""
        processor = model_manager.get_processor("text")
        assert processor is not None
        assert hasattr(processor, 'process')

    @pytest.mark.asyncio
    async def test_get_processor_audio(self, model_manager):
        """Test getting audio processor"""
        processor = model_manager.get_processor("audio")
        assert processor is not None
        assert hasattr(processor, 'process')

    @pytest.mark.asyncio
    async def test_get_processor_video(self, model_manager):
        """Test getting video processor"""
        processor = model_manager.get_processor("video")
        assert processor is not None
        assert hasattr(processor, 'process')

    @pytest.mark.asyncio
    async def test_get_processor_invalid(self, model_manager):
        """Test getting invalid processor"""
        with pytest.raises(ValueError, match="Unknown processor type"):
            model_manager.get_processor("invalid_processor")

    @pytest.mark.asyncio
    async def test_cleanup(self, model_manager):
        """Test model cleanup"""
        # Setup models
        model_manager.clip_model = Mock()
        model_manager.blip_model = Mock()
        model_manager.whisper_model = Mock()
        model_manager.sentence_transformer = Mock()

        # Test cleanup
        await model_manager.cleanup()

        # Verify models are cleared
        assert model_manager.clip_model is None
        assert model_manager.blip_model is None
        assert model_manager.whisper_model is None
        assert model_manager.sentence_transformer is None

    @pytest.mark.asyncio
    async def test_model_health_check(self, model_manager, mock_clip_model, 
                                    mock_blip_model, mock_whisper_model, 
                                    mock_sentence_transformer):
        """Test model health check"""
        # Setup models
        model_manager.clip_model = mock_clip_model
        model_manager.blip_model = mock_blip_model
        model_manager.whisper_model = mock_whisper_model
        model_manager.sentence_transformer = mock_sentence_transformer

        # Test health check
        health_status = await model_manager.health_check()
        
        assert health_status["clip_model"] == "healthy"
        assert health_status["blip_model"] == "healthy"
        assert health_status["whisper_model"] == "healthy"
        assert health_status["sentence_transformer"] == "healthy"

    @pytest.mark.asyncio
    async def test_model_health_check_with_failed_model(self, model_manager):
        """Test model health check with failed model"""
        # Setup models with one failed
        model_manager.clip_model = None
        model_manager.blip_model = Mock()
        model_manager.whisper_model = Mock()
        model_manager.sentence_transformer = Mock()

        # Test health check
        health_status = await model_manager.health_check()
        
        assert health_status["clip_model"] == "failed"
        assert health_status["blip_model"] == "healthy"
        assert health_status["whisper_model"] == "healthy"
        assert health_status["sentence_transformer"] == "healthy"

    @pytest.mark.asyncio
    async def test_model_memory_usage(self, model_manager, mock_clip_model):
        """Test model memory usage tracking"""
        model_manager.clip_model = mock_clip_model
        
        # Mock memory usage
        mock_clip_model.get_memory_usage.return_value = {
            "gpu_memory_mb": 1024,
            "cpu_memory_mb": 512
        }

        memory_usage = await model_manager.get_memory_usage()
        
        assert "clip_model" in memory_usage
        assert memory_usage["clip_model"]["gpu_memory_mb"] == 1024
        assert memory_usage["clip_model"]["cpu_memory_mb"] == 512
