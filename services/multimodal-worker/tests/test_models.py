"""
Unit tests for model management in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import torch
import numpy as np
import os
import tempfile
from PIL import Image

from app.models import ModelManager


class TestModelManager:
    """Test cases for ModelManager"""

    @pytest.fixture
    def model_manager(self):
        """Create ModelManager instance for testing"""
        with patch('app.models.settings') as mock_settings:
            mock_settings.device = 'cpu'
            mock_settings.cache_dir = '/tmp/test_cache'
            mock_settings.model_cache_dir = '/tmp/test_models'
            mock_settings.clip_model = 'openai/clip-vit-base-patch32'
            mock_settings.blip_model = 'Salesforce/blip-image-captioning-base'
            mock_settings.whisper_model = 'openai/whisper-base'
            mock_settings.sentence_transformer_model = 'sentence-transformers/all-MiniLM-L6-v2'
            
            return ModelManager()

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        cache_dir = tempfile.mkdtemp()
        model_cache_dir = tempfile.mkdtemp()
        yield cache_dir, model_cache_dir
        # Cleanup
        import shutil
        shutil.rmtree(cache_dir, ignore_errors=True)
        shutil.rmtree(model_cache_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_load_models_success(self, model_manager):
        """Test successful model loading with real model initialization"""
        with patch('app.models.CLIPModel') as mock_clip_model, \
             patch('app.models.CLIPProcessor') as mock_clip_processor, \
             patch('app.models.BlipForConditionalGeneration') as mock_blip_model, \
             patch('app.models.BlipProcessor') as mock_blip_processor, \
             patch('app.models.whisper.load_model') as mock_whisper, \
             patch('app.models.SentenceTransformer') as mock_sentence_transformer:
            
            # Mock model instances with proper device handling
            mock_clip_instance = Mock()
            mock_clip_instance.to.return_value = mock_clip_instance
            mock_clip_instance.device = torch.device('cpu')
            mock_clip_model.from_pretrained.return_value = mock_clip_instance
            
            mock_clip_processor_instance = Mock()
            mock_clip_processor.from_pretrained.return_value = mock_clip_processor_instance
            
            mock_blip_instance = Mock()
            mock_blip_instance.to.return_value = mock_blip_instance
            mock_blip_instance.device = torch.device('cpu')
            mock_blip_model.from_pretrained.return_value = mock_blip_instance
            
            mock_blip_processor_instance = Mock()
            mock_blip_processor.from_pretrained.return_value = mock_blip_processor_instance
            
            mock_whisper_instance = Mock()
            mock_whisper.return_value = mock_whisper_instance
            
            mock_sentence_transformer_instance = Mock()
            mock_sentence_transformer_instance.device = torch.device('cpu')
            mock_sentence_transformer.return_value = mock_sentence_transformer_instance

            # Test model loading
            await model_manager.load_models()

            # Verify all models were loaded
            assert 'clip' in model_manager.models
            assert 'blip' in model_manager.models
            assert 'whisper' in model_manager.models
            assert 'sentence_transformer' in model_manager.models
            
            # Verify processors were loaded
            assert 'clip' in model_manager.processors
            assert 'blip' in model_manager.processors
            
            # Verify models were moved to correct device
            mock_clip_instance.to.assert_called_once()
            mock_blip_instance.to.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_models_failure(self, model_manager):
        """Test model loading failure with proper error handling"""
        with patch('app.models.CLIPModel') as mock_clip_model, \
             patch('os.makedirs'):
            # Mock model loading failure
            mock_clip_model.from_pretrained.side_effect = Exception("Model loading failed")

            # Test that exception is raised
            with pytest.raises(Exception, match="Model loading failed"):
                await model_manager.load_models()

    def test_get_model_success(self, model_manager):
        """Test getting a loaded model"""
        # Add a mock model
        mock_model = Mock()
        model_manager.models['test_model'] = mock_model

        # Test getting the model
        result = model_manager.get_model('test_model')
        assert result == mock_model

    def test_get_model_not_found(self, model_manager):
        """Test getting a non-existent model"""
        with pytest.raises(ValueError, match="Model 'nonexistent' not found"):
            model_manager.get_model('nonexistent')

    def test_get_processor_success(self, model_manager):
        """Test getting a loaded processor"""
        # Add a mock processor
        mock_processor = Mock()
        model_manager.processors['test_processor'] = mock_processor

        # Test getting the processor
        result = model_manager.get_processor('test_processor')
        assert result == mock_processor

    def test_get_processor_not_found(self, model_manager):
        """Test getting a non-existent processor"""
        with pytest.raises(ValueError, match="Processor 'nonexistent' not found"):
            model_manager.get_processor('nonexistent')

    @pytest.mark.asyncio
    async def test_cleanup(self, model_manager):
        """Test model cleanup with proper memory management"""
        # Add mock models with CPU method
        mock_model1 = Mock()
        mock_model1.cpu = Mock()
        mock_model1.cpu.return_value = mock_model1
        mock_model2 = Mock()
        mock_model2.cpu = Mock()
        mock_model2.cpu.return_value = mock_model2
        
        model_manager.models['model1'] = mock_model1
        model_manager.models['model2'] = mock_model2
        model_manager.processors['processor1'] = Mock()

        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.empty_cache') as mock_empty_cache:
            
            # Test cleanup
            await model_manager.cleanup()

            # Verify models were moved to CPU
            mock_model1.cpu.assert_called_once()
            mock_model2.cpu.assert_called_once()

            # Verify CUDA cache was cleared
            mock_empty_cache.assert_called_once()

            # Verify models and processors were cleared
            assert len(model_manager.models) == 0
            assert len(model_manager.processors) == 0

    def test_device_assignment(self, model_manager):
        """Test device assignment"""
        # Test that device is set correctly
        assert model_manager.device is not None
        assert isinstance(model_manager.device, torch.device)

    @pytest.mark.asyncio
    async def test_model_loading_with_cache_dir(self, model_manager):
        """Test model loading with cache directory configuration"""
        with patch('app.models.CLIPModel') as mock_clip_model, \
             patch('app.models.CLIPProcessor') as mock_clip_processor, \
             patch('app.models.BlipForConditionalGeneration') as mock_blip_model, \
             patch('app.models.BlipProcessor') as mock_blip_processor, \
             patch('app.models.whisper.load_model') as mock_whisper, \
             patch('app.models.SentenceTransformer') as mock_sentence_transformer, \
             patch('os.makedirs'):
            
            # Mock model instances
            mock_clip_instance = Mock()
            mock_clip_instance.to.return_value = mock_clip_instance
            mock_clip_model.from_pretrained.return_value = mock_clip_instance
            
            mock_clip_processor_instance = Mock()
            mock_clip_processor.from_pretrained.return_value = mock_clip_processor_instance
            
            mock_blip_instance = Mock()
            mock_blip_instance.to.return_value = mock_blip_instance
            mock_blip_model.from_pretrained.return_value = mock_blip_instance
            
            mock_blip_processor_instance = Mock()
            mock_blip_processor.from_pretrained.return_value = mock_blip_processor_instance
            
            mock_whisper_instance = Mock()
            mock_whisper.return_value = mock_whisper_instance
            
            mock_sentence_transformer_instance = Mock()
            mock_sentence_transformer_instance.device = torch.device('cpu')
            mock_sentence_transformer.return_value = mock_sentence_transformer_instance

            # Test model loading
            await model_manager.load_models()

            # Verify cache_dir was used in model loading calls
            mock_clip_model.from_pretrained.assert_called_once()
            mock_sentence_transformer.assert_called_once()
            
            # Verify the cache_dir parameter was passed
            clip_call_args = mock_clip_model.from_pretrained.call_args
            assert 'cache_dir' in clip_call_args.kwargs

    def test_model_manager_initialization(self, model_manager):
        """Test ModelManager initialization"""
        # Test that models and processors dictionaries are initialized
        assert isinstance(model_manager.models, dict)
        assert isinstance(model_manager.processors, dict)
        assert len(model_manager.models) == 0
        assert len(model_manager.processors) == 0

    @pytest.mark.asyncio
    async def test_model_loading_with_gpu_device(self, temp_dirs):
        """Test model loading with GPU device"""
        cache_dir, model_cache_dir = temp_dirs
        
        with patch('app.models.settings') as mock_settings:
            mock_settings.device = 'cuda:0'
            mock_settings.cache_dir = cache_dir
            mock_settings.model_cache_dir = model_cache_dir
            mock_settings.clip_model = 'openai/clip-vit-base-patch32'
            mock_settings.blip_model = 'Salesforce/blip-image-captioning-base'
            mock_settings.whisper_model = 'openai/whisper-base'
            mock_settings.sentence_transformer_model = 'sentence-transformers/all-MiniLM-L6-v2'
            
            model_manager = ModelManager()
            
            with patch('app.models.CLIPModel') as mock_clip_model, \
                 patch('app.models.CLIPProcessor') as mock_clip_processor, \
                 patch('app.models.BlipForConditionalGeneration') as mock_blip_model, \
                 patch('app.models.BlipProcessor') as mock_blip_processor, \
                 patch('app.models.whisper.load_model') as mock_whisper, \
                 patch('app.models.SentenceTransformer') as mock_sentence_transformer:
                
                # Mock model instances
                mock_clip_instance = Mock()
                mock_clip_instance.to.return_value = mock_clip_instance
                mock_clip_model.from_pretrained.return_value = mock_clip_instance
                
                mock_clip_processor_instance = Mock()
                mock_clip_processor.from_pretrained.return_value = mock_clip_processor_instance
                
                mock_blip_instance = Mock()
                mock_blip_instance.to.return_value = mock_blip_instance
                mock_blip_model.from_pretrained.return_value = mock_blip_instance
                
                mock_blip_processor_instance = Mock()
                mock_blip_processor.from_pretrained.return_value = mock_blip_processor_instance
                
                mock_whisper_instance = Mock()
                mock_whisper.return_value = mock_whisper_instance
                
                mock_sentence_transformer_instance = Mock()
                mock_sentence_transformer_instance.device = torch.device('cuda:0')
                mock_sentence_transformer.return_value = mock_sentence_transformer_instance

                # Test model loading
                await model_manager.load_models()

                # Verify models were moved to GPU device
                mock_clip_instance.to.assert_called_with(torch.device('cuda:0'))
                mock_blip_instance.to.assert_called_with(torch.device('cuda:0'))

    @pytest.mark.asyncio
    async def test_model_loading_partial_failure(self, model_manager):
        """Test model loading with partial failure"""
        with patch('app.models.CLIPModel') as mock_clip_model, \
             patch('app.models.CLIPProcessor') as mock_clip_processor, \
             patch('app.models.BlipForConditionalGeneration') as mock_blip_model, \
             patch('os.makedirs'):
            
            # Mock successful CLIP loading
            mock_clip_instance = Mock()
            mock_clip_instance.to.return_value = mock_clip_instance
            mock_clip_model.from_pretrained.return_value = mock_clip_instance
            
            mock_clip_processor_instance = Mock()
            mock_clip_processor.from_pretrained.return_value = mock_clip_processor_instance
            
            # Mock BLIP loading failure
            mock_blip_model.from_pretrained.side_effect = Exception("BLIP loading failed")

            # Test that exception is raised
            with pytest.raises(Exception, match="BLIP loading failed"):
                await model_manager.load_models()

    @pytest.mark.asyncio
    async def test_cleanup_without_cuda(self, model_manager):
        """Test cleanup when CUDA is not available"""
        # Add mock models
        mock_model1 = Mock()
        mock_model1.cpu = Mock()
        mock_model1.cpu.return_value = mock_model1
        
        model_manager.models['model1'] = mock_model1
        model_manager.processors['processor1'] = Mock()

        with patch('torch.cuda.is_available', return_value=False), \
             patch('torch.cuda.empty_cache') as mock_empty_cache:
            
            # Test cleanup
            await model_manager.cleanup()

            # Verify model was moved to CPU
            mock_model1.cpu.assert_called_once()

            # Verify CUDA cache was NOT cleared
            mock_empty_cache.assert_not_called()

            # Verify models and processors were cleared
            assert len(model_manager.models) == 0
            assert len(model_manager.processors) == 0

    def test_model_manager_with_custom_settings(self):
        """Test ModelManager with custom settings"""
        with patch('app.models.settings') as mock_settings, \
             patch('os.makedirs') as mock_makedirs:
            mock_settings.device = 'cpu'
            mock_settings.cache_dir = '/custom/cache'
            mock_settings.model_cache_dir = '/custom/models'
            mock_settings.clip_model = 'custom/clip-model'
            mock_settings.blip_model = 'custom/blip-model'
            mock_settings.whisper_model = 'custom/whisper-model'
            mock_settings.sentence_transformer_model = 'custom/sentence-model'
            
            model_manager = ModelManager()
            
            # Verify device is set correctly
            assert model_manager.device == torch.device('cpu')
            
            # Verify models and processors are initialized
            assert isinstance(model_manager.models, dict)
            assert isinstance(model_manager.processors, dict)

    @pytest.mark.asyncio
    async def test_model_inference_capabilities(self, model_manager):
        """Test model inference capabilities after loading"""
        with patch('app.models.CLIPModel') as mock_clip_model, \
             patch('app.models.CLIPProcessor') as mock_clip_processor, \
             patch('app.models.BlipForConditionalGeneration') as mock_blip_model, \
             patch('app.models.BlipProcessor') as mock_blip_processor, \
             patch('app.models.whisper.load_model') as mock_whisper, \
             patch('app.models.SentenceTransformer') as mock_sentence_transformer, \
             patch('os.makedirs'):
            
            # Mock model instances with inference methods
            mock_clip_instance = Mock()
            mock_clip_instance.to.return_value = mock_clip_instance
            mock_clip_instance.device = torch.device('cpu')
            mock_clip_instance.get_image_features = Mock()
            mock_clip_model.from_pretrained.return_value = mock_clip_instance
            
            mock_clip_processor_instance = Mock()
            mock_clip_processor_instance.return_value = {'pixel_values': torch.randn(1, 3, 224, 224)}
            mock_clip_processor.from_pretrained.return_value = mock_clip_processor_instance
            
            mock_blip_instance = Mock()
            mock_blip_instance.to.return_value = mock_blip_instance
            mock_blip_instance.device = torch.device('cpu')
            mock_blip_instance.generate = Mock()
            mock_blip_model.from_pretrained.return_value = mock_blip_instance
            
            mock_blip_processor_instance = Mock()
            mock_blip_processor_instance.return_value = {'pixel_values': torch.randn(1, 3, 224, 224)}
            mock_blip_processor.from_pretrained.return_value = mock_blip_processor_instance
            
            mock_whisper_instance = Mock()
            mock_whisper_instance.transcribe = Mock()
            mock_whisper.return_value = mock_whisper_instance
            
            mock_sentence_transformer_instance = Mock()
            mock_sentence_transformer_instance.device = torch.device('cpu')
            mock_sentence_transformer_instance.encode = Mock()
            mock_sentence_transformer.return_value = mock_sentence_transformer_instance

            # Test model loading
            await model_manager.load_models()

            # Test that models have inference capabilities
            clip_model = model_manager.get_model('clip')
            assert hasattr(clip_model, 'get_image_features')
            
            blip_model = model_manager.get_model('blip')
            assert hasattr(blip_model, 'generate')
            
            whisper_model = model_manager.get_model('whisper')
            assert hasattr(whisper_model, 'transcribe')
            
            sentence_transformer = model_manager.get_model('sentence_transformer')
            assert hasattr(sentence_transformer, 'encode')

    @pytest.mark.asyncio
    async def test_model_memory_management(self, model_manager):
        """Test model memory management during loading and cleanup"""
        with patch('app.models.CLIPModel') as mock_clip_model, \
             patch('app.models.CLIPProcessor') as mock_clip_processor, \
             patch('app.models.BlipForConditionalGeneration') as mock_blip_model, \
             patch('app.models.BlipProcessor') as mock_blip_processor, \
             patch('app.models.whisper.load_model') as mock_whisper, \
             patch('app.models.SentenceTransformer') as mock_sentence_transformer, \
             patch('os.makedirs'):
            
            # Mock model instances
            mock_clip_instance = Mock()
            mock_clip_instance.to.return_value = mock_clip_instance
            mock_clip_model.from_pretrained.return_value = mock_clip_instance
            
            mock_clip_processor_instance = Mock()
            mock_clip_processor.from_pretrained.return_value = mock_clip_processor_instance
            
            mock_blip_instance = Mock()
            mock_blip_instance.to.return_value = mock_blip_instance
            mock_blip_model.from_pretrained.return_value = mock_blip_instance
            
            mock_blip_processor_instance = Mock()
            mock_blip_processor.from_pretrained.return_value = mock_blip_processor_instance
            
            mock_whisper_instance = Mock()
            mock_whisper.return_value = mock_whisper_instance
            
            mock_sentence_transformer_instance = Mock()
            mock_sentence_transformer_instance.device = torch.device('cpu')
            mock_sentence_transformer.return_value = mock_sentence_transformer_instance

            # Test model loading
            await model_manager.load_models()

            # Verify models are loaded
            assert len(model_manager.models) == 4
            assert len(model_manager.processors) == 2

            # Test cleanup
            with patch('torch.cuda.is_available', return_value=True), \
                 patch('torch.cuda.empty_cache') as mock_empty_cache:
                
                await model_manager.cleanup()

                # Verify models were moved to CPU
                mock_clip_instance.to.assert_called()
                mock_blip_instance.to.assert_called()

                # Verify CUDA cache was cleared
                mock_empty_cache.assert_called_once()

                # Verify models and processors were cleared
                assert len(model_manager.models) == 0
                assert len(model_manager.processors) == 0