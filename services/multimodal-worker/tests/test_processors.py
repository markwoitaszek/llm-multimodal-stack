"""
Unit tests for processors in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
from PIL import Image
import torch

from app.processors import ImageProcessor, TextProcessor, AudioProcessor, VideoProcessor


class TestImageProcessor:
    """Test cases for ImageProcessor"""

    @pytest.fixture
    def image_processor(self, mock_model_manager, mock_database_manager, mock_storage_manager):
        """Create ImageProcessor instance for testing"""
        return ImageProcessor(mock_model_manager, mock_database_manager, mock_storage_manager)

    @pytest.mark.asyncio
    async def test_image_processor_initialization(self, image_processor):
        """Test ImageProcessor initialization"""
        assert image_processor is not None
        assert hasattr(image_processor, 'model_manager')
        assert hasattr(image_processor, 'db_manager')
        assert hasattr(image_processor, 'storage_manager')

    @pytest.mark.asyncio
    async def test_generate_image_embedding(self, image_processor, mock_image, mock_embedding):
        """Test image embedding generation"""
        # Mock CLIP model
        mock_clip = Mock()
        mock_clip.encode_image.return_value = torch.tensor([mock_embedding])
        image_processor.model_manager.get_model.return_value = mock_clip

        # Test embedding generation
        result = await image_processor.generate_image_embedding(mock_image)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (512,)
        assert np.allclose(result, mock_embedding)

    @pytest.mark.asyncio
    async def test_generate_image_caption(self, image_processor, mock_image):
        """Test image caption generation"""
        # Mock BLIP model
        mock_blip = Mock()
        mock_blip.generate.return_value = ["A test image caption"]
        image_processor.model_manager.get_model.return_value = mock_blip

        # Test caption generation
        result = await image_processor.generate_image_caption(mock_image)
        
        assert isinstance(result, str)
        assert result == "A test image caption"

    @pytest.mark.asyncio
    async def test_process_image_success(self, image_processor, mock_image, mock_embedding):
        """Test complete image processing"""
        # Mock models
        mock_clip = Mock()
        mock_clip.encode_image.return_value = torch.tensor([mock_embedding])
        mock_blip = Mock()
        mock_blip.generate.return_value = ["Test caption"]
        
        image_processor.model_manager.get_model.side_effect = lambda model_type: {
            "clip": mock_clip,
            "blip": mock_blip
        }[model_type]

        # Mock database operations
        image_processor.db_manager.insert_record.return_value = "test_content_id"

        # Test processing
        result = await image_processor.process_image(mock_image, {"filename": "test.jpg"})
        
        assert result["success"] is True
        assert "content_id" in result
        assert "embeddings" in result
        assert "caption" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_process_image_failure(self, image_processor, mock_image):
        """Test image processing failure"""
        # Mock model failure
        image_processor.model_manager.get_model.side_effect = Exception("Model error")

        # Test processing
        result = await image_processor.process_image(mock_image, {"filename": "test.jpg"})
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_extract_image_metadata(self, image_processor, mock_image):
        """Test image metadata extraction"""
        result = await image_processor.extract_metadata(mock_image)
        
        assert "width" in result
        assert "height" in result
        assert "format" in result
        assert "mode" in result
        assert result["width"] == 224
        assert result["height"] == 224


class TestTextProcessor:
    """Test cases for TextProcessor"""

    @pytest.fixture
    def text_processor(self, mock_model_manager, mock_database_manager, mock_storage_manager):
        """Create TextProcessor instance for testing"""
        return TextProcessor(mock_model_manager, mock_database_manager, mock_storage_manager)

    @pytest.mark.asyncio
    async def test_text_processor_initialization(self, text_processor):
        """Test TextProcessor initialization"""
        assert text_processor is not None
        assert hasattr(text_processor, 'model_manager')
        assert hasattr(text_processor, 'db_manager')
        assert hasattr(text_processor, 'storage_manager')

    @pytest.mark.asyncio
    async def test_generate_text_embedding(self, text_processor, mock_text, mock_embedding):
        """Test text embedding generation"""
        # Mock sentence transformer
        mock_transformer = Mock()
        mock_transformer.encode.return_value = mock_embedding
        text_processor.model_manager.get_model.return_value = mock_transformer

        # Test embedding generation
        result = await text_processor.generate_text_embedding(mock_text)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (384,)
        assert np.allclose(result, mock_embedding)

    @pytest.mark.asyncio
    async def test_chunk_text(self, text_processor):
        """Test text chunking"""
        long_text = "This is a long text that should be chunked into smaller pieces. " * 10
        
        chunks = await text_processor.chunk_text(long_text, chunk_size=100, overlap=20)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)

    @pytest.mark.asyncio
    async def test_process_text_success(self, text_processor, mock_text, mock_embedding):
        """Test complete text processing"""
        # Mock sentence transformer
        mock_transformer = Mock()
        mock_transformer.encode.return_value = mock_embedding
        text_processor.model_manager.get_model.return_value = mock_transformer

        # Mock database operations
        text_processor.db_manager.insert_record.return_value = "test_content_id"

        # Test processing
        result = await text_processor.process_text(mock_text, {"source": "test"})
        
        assert result["success"] is True
        assert "content_id" in result
        assert "embeddings" in result
        assert "chunks" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_extract_text_metadata(self, text_processor):
        """Test text metadata extraction"""
        text = "This is a test document with some content."
        
        result = await text_processor.extract_metadata(text)
        
        assert "word_count" in result
        assert "character_count" in result
        assert "language" in result
        assert result["word_count"] == 9
        assert result["character_count"] == 42


class TestAudioProcessor:
    """Test cases for AudioProcessor"""

    @pytest.fixture
    def audio_processor(self, mock_model_manager, mock_database_manager, mock_storage_manager):
        """Create AudioProcessor instance for testing"""
        return AudioProcessor(mock_model_manager, mock_database_manager, mock_storage_manager)

    @pytest.mark.asyncio
    async def test_audio_processor_initialization(self, audio_processor):
        """Test AudioProcessor initialization"""
        assert audio_processor is not None
        assert hasattr(audio_processor, 'model_manager')
        assert hasattr(audio_processor, 'db_manager')
        assert hasattr(audio_processor, 'storage_manager')

    @pytest.mark.asyncio
    async def test_transcribe_audio(self, audio_processor, mock_audio_data):
        """Test audio transcription"""
        # Mock Whisper model
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = {"text": "Test audio transcription"}
        audio_processor.model_manager.get_model.return_value = mock_whisper

        # Test transcription
        result = await audio_processor.transcribe_audio(mock_audio_data)
        
        assert isinstance(result, str)
        assert result == "Test audio transcription"

    @pytest.mark.asyncio
    async def test_process_audio_success(self, audio_processor, mock_audio_data, mock_embedding):
        """Test complete audio processing"""
        # Mock models
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = {"text": "Test transcription"}
        mock_clip = Mock()
        mock_clip.encode_text.return_value = torch.tensor([mock_embedding])
        
        audio_processor.model_manager.get_model.side_effect = lambda model_type: {
            "whisper": mock_whisper,
            "clip": mock_clip
        }[model_type]

        # Mock database operations
        audio_processor.db_manager.insert_record.return_value = "test_content_id"

        # Test processing
        result = await audio_processor.process_audio(mock_audio_data, {"filename": "test.wav"})
        
        assert result["success"] is True
        assert "content_id" in result
        assert "transcription" in result
        assert "embeddings" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_extract_audio_metadata(self, audio_processor, mock_audio_data):
        """Test audio metadata extraction"""
        result = await audio_processor.extract_metadata(mock_audio_data)
        
        assert "duration" in result
        assert "sample_rate" in result
        assert "channels" in result
        assert result["sample_rate"] == 16000


class TestVideoProcessor:
    """Test cases for VideoProcessor"""

    @pytest.fixture
    def video_processor(self, mock_model_manager, mock_database_manager, mock_storage_manager):
        """Create VideoProcessor instance for testing"""
        return VideoProcessor(mock_model_manager, mock_database_manager, mock_storage_manager)

    @pytest.mark.asyncio
    async def test_video_processor_initialization(self, video_processor):
        """Test VideoProcessor initialization"""
        assert video_processor is not None
        assert hasattr(video_processor, 'model_manager')
        assert hasattr(video_processor, 'db_manager')
        assert hasattr(video_processor, 'storage_manager')

    @pytest.mark.asyncio
    async def test_extract_keyframes(self, video_processor, mock_video_data):
        """Test video keyframe extraction"""
        keyframes = await video_processor.extract_keyframes(mock_video_data, max_frames=5)
        
        assert isinstance(keyframes, list)
        assert len(keyframes) <= 5
        assert all(isinstance(frame, np.ndarray) for frame in keyframes)

    @pytest.mark.asyncio
    async def test_process_video_success(self, video_processor, mock_video_data, mock_embedding):
        """Test complete video processing"""
        # Mock models
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = {"text": "Test video transcription"}
        mock_clip = Mock()
        mock_clip.encode_text.return_value = torch.tensor([mock_embedding])
        
        video_processor.model_manager.get_model.side_effect = lambda model_type: {
            "whisper": mock_whisper,
            "clip": mock_clip
        }[model_type]

        # Mock database operations
        video_processor.db_manager.insert_record.return_value = "test_content_id"

        # Test processing
        result = await video_processor.process_video(mock_video_data, {"filename": "test.mp4"})
        
        assert result["success"] is True
        assert "content_id" in result
        assert "transcription" in result
        assert "keyframes" in result
        assert "embeddings" in result
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_extract_video_metadata(self, video_processor, mock_video_data):
        """Test video metadata extraction"""
        result = await video_processor.extract_metadata(mock_video_data)
        
        assert "duration" in result
        assert "fps" in result
        assert "frame_count" in result
        assert "width" in result
        assert "height" in result
        assert result["fps"] == 30
        assert result["frame_count"] == 900
