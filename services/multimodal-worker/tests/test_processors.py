"""
Unit tests for processors in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
import torch
from PIL import Image
import tempfile
import os
import cv2

from app.processors import ImageProcessor, VideoProcessor, TextProcessor


class TestImageProcessor:
    """Test cases for ImageProcessor"""

    @pytest.fixture
    def mock_managers(self):
        """Create mock managers for testing"""
        model_manager = Mock()
        db_manager = AsyncMock()
        storage_manager = Mock()
        return model_manager, db_manager, storage_manager

    @pytest.fixture
    def image_processor(self, mock_managers):
        """Create ImageProcessor instance for testing"""
        model_manager, db_manager, storage_manager = mock_managers
        return ImageProcessor(model_manager, db_manager, storage_manager)

    @pytest.fixture
    def test_image(self):
        """Create a test image"""
        return Image.new('RGB', (224, 224), color='red')

    @pytest.fixture
    def temp_image_file(self, test_image):
        """Create a temporary image file"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            yield tmp_file.name
        os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_process_image_success(self, image_processor, temp_image_file):
        """Test successful image processing"""
        # Mock dependencies
        image_processor.model_manager.get_model.return_value = Mock()
        image_processor.model_manager.get_processor.return_value = Mock()
        image_processor.storage_manager.calculate_file_hash.return_value = "test_hash"
        image_processor.storage_manager.generate_object_path.return_value = "test/path/image.jpg"
        image_processor.storage_manager.upload_file.return_value = None
        image_processor.db_manager.create_image.return_value = "test_image_id"

        # Mock embedding generation
        with patch.object(image_processor, 'generate_image_embedding') as mock_embedding, \
             patch.object(image_processor, 'generate_image_caption') as mock_caption, \
             patch.object(image_processor, 'extract_image_features') as mock_features:
            
            mock_embedding.return_value = np.random.rand(512)
            mock_caption.return_value = "A test image"
            mock_features.return_value = {"mean_brightness": 128.5}

            # Test image processing
            result = await image_processor.process_image(temp_image_file, "test_document_id")

            # Verify result structure
            assert "image_id" in result
            assert "embedding" in result
            assert "caption" in result
            assert "features" in result
            assert "storage_path" in result
            assert "dimensions" in result

            # Verify database record was created
            image_processor.db_manager.create_image.assert_called_once()
            
            # Verify storage upload was called
            image_processor.storage_manager.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_image_embedding(self, image_processor, test_image):
        """Test image embedding generation"""
        # Mock CLIP model and processor
        mock_clip_model = Mock()
        mock_clip_model.device = torch.device('cpu')
        mock_clip_model.get_image_features.return_value = torch.randn(1, 512)
        
        mock_clip_processor = Mock()
        mock_clip_processor.return_value = {
            'pixel_values': torch.randn(1, 3, 224, 224)
        }

        image_processor.model_manager.get_model.return_value = mock_clip_model
        image_processor.model_manager.get_processor.return_value = mock_clip_processor

        # Test embedding generation
        embedding = await image_processor.generate_image_embedding(test_image)

        # Verify embedding structure
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)

        # Verify model was called correctly
        image_processor.model_manager.get_model.assert_called_with('clip')
        image_processor.model_manager.get_processor.assert_called_with('clip')

    @pytest.mark.asyncio
    async def test_generate_image_caption(self, image_processor, test_image):
        """Test image caption generation"""
        # Mock BLIP model and processor
        mock_blip_model = Mock()
        mock_blip_model.device = torch.device('cpu')
        mock_blip_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
        
        mock_blip_processor = Mock()
        mock_blip_processor.return_value = {
            'pixel_values': torch.randn(1, 3, 224, 224)
        }
        mock_blip_processor.decode.return_value = "A test image caption"

        image_processor.model_manager.get_model.return_value = mock_blip_model
        image_processor.model_manager.get_processor.return_value = mock_blip_processor

        # Test caption generation
        caption = await image_processor.generate_image_caption(test_image)

        # Verify caption
        assert isinstance(caption, str)
        assert caption == "A test image caption"

        # Verify model was called correctly
        image_processor.model_manager.get_model.assert_called_with('blip')
        image_processor.model_manager.get_processor.assert_called_with('blip')

    def test_extract_image_features(self, image_processor, test_image):
        """Test image feature extraction"""
        # Test feature extraction
        features = image_processor.extract_image_features(test_image)

        # Verify features structure
        assert isinstance(features, dict)
        assert "mean_brightness" in features
        assert "std_brightness" in features
        assert "dominant_colors" in features
        assert "aspect_ratio" in features
        assert "file_size" in features

        # Verify feature values
        assert isinstance(features["mean_brightness"], float)
        assert isinstance(features["aspect_ratio"], float)
        assert features["aspect_ratio"] == 1.0  # Square image

    def test_get_dominant_colors(self, image_processor):
        """Test dominant color extraction"""
        # Create a test image array
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        with patch('sklearn.cluster.KMeans') as mock_kmeans:
            mock_kmeans_instance = Mock()
            mock_kmeans_instance.cluster_centers_ = np.array([[100, 150, 200], [50, 75, 100]])
            mock_kmeans.return_value = mock_kmeans_instance

            # Test dominant color extraction
            colors = image_processor.get_dominant_colors(img_array, k=2)

            # Verify colors structure
            assert isinstance(colors, list)
            assert len(colors) == 2
            assert all(isinstance(color, list) for color in colors)

    @pytest.mark.asyncio
    async def test_process_image_with_large_image(self, image_processor, temp_image_file):
        """Test image processing with large image that needs resizing"""
        # Create a large image
        large_image = Image.new('RGB', (2000, 2000), color='blue')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            large_image.save(tmp_file.name, 'JPEG')
            large_image_path = tmp_file.name

        try:
            # Mock dependencies
            image_processor.model_manager.get_model.return_value = Mock()
            image_processor.model_manager.get_processor.return_value = Mock()
            image_processor.storage_manager.calculate_file_hash.return_value = "test_hash"
            image_processor.storage_manager.generate_object_path.return_value = "test/path/large_image.jpg"
            image_processor.storage_manager.upload_file.return_value = None
            image_processor.db_manager.create_image.return_value = "test_image_id"

            # Mock embedding generation
            with patch.object(image_processor, 'generate_image_embedding') as mock_embedding, \
                 patch.object(image_processor, 'generate_image_caption') as mock_caption, \
                 patch.object(image_processor, 'extract_image_features') as mock_features:
                
                mock_embedding.return_value = np.random.rand(512)
                mock_caption.return_value = "A large test image"
                mock_features.return_value = {"mean_brightness": 128.5}

                # Test image processing
                result = await image_processor.process_image(large_image_path, "test_document_id")

                # Verify result
                assert "image_id" in result
                assert "dimensions" in result
                # Image should be resized
                assert result["dimensions"][0] <= 1024  # Assuming max size is 1024
                assert result["dimensions"][1] <= 1024

        finally:
            os.unlink(large_image_path)

    @pytest.mark.asyncio
    async def test_process_image_failure(self, image_processor, temp_image_file):
        """Test image processing failure"""
        # Mock model failure
        image_processor.model_manager.get_model.side_effect = Exception("Model not found")

        # Test that exception is raised
        with pytest.raises(Exception, match="Model not found"):
            await image_processor.process_image(temp_image_file, "test_document_id")


class TestVideoProcessor:
    """Test cases for VideoProcessor"""

    @pytest.fixture
    def mock_managers(self):
        """Create mock managers for testing"""
        model_manager = Mock()
        db_manager = AsyncMock()
        storage_manager = Mock()
        return model_manager, db_manager, storage_manager

    @pytest.fixture
    def video_processor(self, mock_managers):
        """Create VideoProcessor instance for testing"""
        model_manager, db_manager, storage_manager = mock_managers
        return VideoProcessor(model_manager, db_manager, storage_manager)

    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary video file"""
        # Create a simple test video file (this would be a real video in production)
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            # Write some dummy video data
            tmp_file.write(b"fake video data")
            yield tmp_file.name
        os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_process_video_success(self, video_processor, temp_video_file):
        """Test successful video processing"""
        # Mock dependencies
        video_processor.model_manager.get_model.return_value = Mock()
        video_processor.storage_manager.calculate_file_hash.return_value = "test_hash"
        video_processor.storage_manager.generate_object_path.return_value = "test/path/video.mp4"
        video_processor.storage_manager.upload_file.return_value = None
        video_processor.db_manager.create_video.return_value = "test_video_id"
        video_processor.db_manager.create_video_keyframe.return_value = "test_keyframe_id"

        # Mock video processing methods
        with patch.object(video_processor, 'transcribe_video_audio') as mock_transcribe, \
             patch.object(video_processor, 'extract_keyframes') as mock_keyframes, \
             patch.object(video_processor, 'generate_text_embedding') as mock_text_embedding, \
             patch.object(video_processor, 'process_keyframe') as mock_process_keyframe, \
             patch('app.processors.VideoFileClip') as mock_video_clip:
            
            # Mock video clip
            mock_clip = Mock()
            mock_clip.duration = 10.0
            mock_clip.fps = 30.0
            mock_clip.size = (1920, 1080)
            mock_clip.close.return_value = None
            mock_video_clip.return_value = mock_clip

            # Mock transcription and keyframes
            mock_transcribe.return_value = "Test video transcription"
            mock_keyframes.return_value = [(0.0, "keyframe1.jpg"), (5.0, "keyframe2.jpg")]
            mock_text_embedding.return_value = np.random.rand(512)
            mock_process_keyframe.return_value = {
                "keyframe_id": "test_keyframe_id",
                "timestamp": 0.0,
                "embedding": np.random.rand(512),
                "caption": "Test keyframe caption",
                "storage_path": "test/path/keyframe.jpg"
            }

            # Test video processing
            result = await video_processor.process_video(temp_video_file, "test_document_id")

            # Verify result structure
            assert "video_id" in result
            assert "transcription" in result
            assert "text_embedding" in result
            assert "keyframes" in result
            assert "storage_path" in result
            assert "duration" in result
            assert "dimensions" in result

            # Verify database record was created
            video_processor.db_manager.create_video.assert_called_once()
            
            # Verify storage upload was called
            video_processor.storage_manager.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_video_audio(self, video_processor, temp_video_file):
        """Test video audio transcription"""
        # Mock Whisper model
        mock_whisper_model = Mock()
        mock_whisper_model.transcribe.return_value = {"text": "Test transcription"}
        video_processor.model_manager.get_model.return_value = mock_whisper_model

        with patch('app.processors.VideoFileClip') as mock_video_clip, \
             patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
             patch('os.unlink') as mock_unlink:
            
            # Mock video clip with audio
            mock_clip = Mock()
            mock_audio = Mock()
            mock_audio.write_audiofile.return_value = None
            mock_clip.audio = mock_audio
            mock_clip.close.return_value = None
            mock_video_clip.return_value = mock_clip

            # Mock temporary file
            mock_temp = Mock()
            mock_temp.name = "temp_audio.wav"
            mock_temp_file.return_value.__enter__.return_value = mock_temp

            # Test transcription
            transcription = await video_processor.transcribe_video_audio(temp_video_file)

            # Verify transcription
            assert transcription == "Test transcription"

            # Verify Whisper model was called
            video_processor.model_manager.get_model.assert_called_with('whisper')

    @pytest.mark.asyncio
    async def test_extract_keyframes(self, video_processor, temp_video_file):
        """Test keyframe extraction"""
        with patch('cv2.VideoCapture') as mock_capture, \
             patch('cv2.imwrite') as mock_imwrite, \
             patch('app.processors.settings') as mock_settings:
            
            mock_settings.keyframe_interval = 5.0
            mock_settings.temp_dir = "/tmp"

            # Mock video capture
            mock_cap = Mock()
            mock_cap.get.return_value = 30.0  # FPS
            mock_cap.set.return_value = None
            mock_cap.read.return_value = (True, np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8))
            mock_cap.release.return_value = None
            mock_capture.return_value = mock_cap

            # Test keyframe extraction
            keyframes = await video_processor.extract_keyframes(temp_video_file, 10.0)

            # Verify keyframes structure
            assert isinstance(keyframes, list)
            assert len(keyframes) > 0
            assert all(isinstance(kf, tuple) and len(kf) == 2 for kf in keyframes)

    @pytest.mark.asyncio
    async def test_process_keyframe(self, video_processor):
        """Test keyframe processing"""
        # Create a temporary keyframe file
        test_image = Image.new('RGB', (224, 224), color='green')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            test_image.save(tmp_file.name, 'JPEG')
            keyframe_path = tmp_file.name

        try:
            # Mock dependencies
            video_processor.model_manager.get_model.return_value = Mock()
            video_processor.model_manager.get_processor.return_value = Mock()
            video_processor.storage_manager.calculate_file_hash.return_value = "test_hash"
            video_processor.storage_manager.generate_object_path.return_value = "test/path/keyframe.jpg"
            video_processor.storage_manager.upload_file.return_value = None
            video_processor.db_manager.create_video_keyframe.return_value = "test_keyframe_id"

            # Mock embedding and caption generation
            with patch.object(video_processor, 'generate_image_embedding') as mock_embedding, \
                 patch.object(video_processor, 'generate_image_caption') as mock_caption:
                
                mock_embedding.return_value = np.random.rand(512)
                mock_caption.return_value = "Test keyframe caption"

                # Test keyframe processing
                result = await video_processor.process_keyframe("test_video_id", keyframe_path, 5.0)

                # Verify result structure
                assert "keyframe_id" in result
                assert "timestamp" in result
                assert "embedding" in result
                assert "caption" in result
                assert "storage_path" in result

                # Verify timestamp
                assert result["timestamp"] == 5.0

        finally:
            if os.path.exists(keyframe_path):
                os.unlink(keyframe_path)

    @pytest.mark.asyncio
    async def test_generate_text_embedding(self, video_processor):
        """Test text embedding generation"""
        # Mock sentence transformer
        mock_sentence_transformer = Mock()
        mock_sentence_transformer.encode.return_value = np.random.rand(512)
        video_processor.model_manager.get_model.return_value = mock_sentence_transformer

        # Test text embedding generation
        embedding = await video_processor.generate_text_embedding("Test text")

        # Verify embedding
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)

        # Verify model was called correctly
        video_processor.model_manager.get_model.assert_called_with('sentence_transformer')


class TestTextProcessor:
    """Test cases for TextProcessor"""

    @pytest.fixture
    def mock_managers(self):
        """Create mock managers for testing"""
        model_manager = Mock()
        db_manager = AsyncMock()
        storage_manager = Mock()
        return model_manager, db_manager, storage_manager

    @pytest.fixture
    def text_processor(self, mock_managers):
        """Create TextProcessor instance for testing"""
        model_manager, db_manager, storage_manager = mock_managers
        return TextProcessor(model_manager, db_manager, storage_manager)

    @pytest.mark.asyncio
    async def test_process_text_success(self, text_processor):
        """Test successful text processing"""
        # Mock dependencies
        text_processor.db_manager.create_text_chunk.return_value = "test_chunk_id"

        # Mock embedding generation
        with patch.object(text_processor, 'generate_text_embedding') as mock_embedding, \
             patch('app.processors.settings') as mock_settings:
            
            mock_settings.chunk_size = 100
            mock_settings.chunk_overlap = 20
            mock_embedding.return_value = np.random.rand(512)

            # Test text processing
            test_text = "This is a test document with multiple sentences. " * 10  # Long text
            result = await text_processor.process_text(test_text, "test_document_id")

            # Verify result structure
            assert "chunks" in result
            assert "total_chunks" in result
            assert isinstance(result["chunks"], list)
            assert len(result["chunks"]) > 0

            # Verify chunk structure
            for chunk in result["chunks"]:
                assert "chunk_id" in chunk
                assert "chunk_index" in chunk
                assert "text" in chunk
                assert "embedding" in chunk

            # Verify database records were created
            assert text_processor.db_manager.create_text_chunk.call_count == len(result["chunks"])

    def test_chunk_text(self, text_processor):
        """Test text chunking"""
        with patch('app.processors.settings') as mock_settings:
            mock_settings.chunk_size = 5
            mock_settings.chunk_overlap = 2

            # Test text chunking
            test_text = "This is a test document with multiple words for chunking"
            chunks = text_processor.chunk_text(test_text)

            # Verify chunks
            assert isinstance(chunks, list)
            assert len(chunks) > 0
            assert all(isinstance(chunk, str) for chunk in chunks)

            # Verify chunk sizes are reasonable
            for chunk in chunks:
                words = chunk.split()
                assert len(words) <= 5  # chunk_size

    @pytest.mark.asyncio
    async def test_generate_text_embedding(self, text_processor):
        """Test text embedding generation"""
        # Mock sentence transformer
        mock_sentence_transformer = Mock()
        mock_sentence_transformer.encode.return_value = np.random.rand(512)
        text_processor.model_manager.get_model.return_value = mock_sentence_transformer

        # Test text embedding generation
        embedding = await text_processor.generate_text_embedding("Test text")

        # Verify embedding
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)

        # Verify model was called correctly
        text_processor.model_manager.get_model.assert_called_with('sentence_transformer')

    @pytest.mark.asyncio
    async def test_process_text_with_short_text(self, text_processor):
        """Test text processing with short text"""
        # Mock dependencies
        text_processor.db_manager.create_text_chunk.return_value = "test_chunk_id"

        # Mock embedding generation
        with patch.object(text_processor, 'generate_text_embedding') as mock_embedding, \
             patch('app.processors.settings') as mock_settings:
            
            mock_settings.chunk_size = 100
            mock_settings.chunk_overlap = 20
            mock_embedding.return_value = np.random.rand(512)

            # Test with short text
            short_text = "Short text"
            result = await text_processor.process_text(short_text, "test_document_id")

            # Verify result
            assert len(result["chunks"]) == 1
            assert result["total_chunks"] == 1
            assert result["chunks"][0]["text"] == short_text

    @pytest.mark.asyncio
    async def test_process_text_failure(self, text_processor):
        """Test text processing failure"""
        # Mock embedding generation failure
        with patch.object(text_processor, 'generate_text_embedding') as mock_embedding:
            mock_embedding.side_effect = Exception("Embedding generation failed")

            # Test that exception is raised
            with pytest.raises(Exception, match="Embedding generation failed"):
                await text_processor.process_text("Test text", "test_document_id")

    def test_chunk_text_with_overlap(self, text_processor):
        """Test text chunking with overlap"""
        with patch('app.processors.settings') as mock_settings:
            mock_settings.chunk_size = 3
            mock_settings.chunk_overlap = 1

            # Test text chunking
            test_text = "word1 word2 word3 word4 word5 word6"
            chunks = text_processor.chunk_text(test_text)

            # Verify chunks have overlap
            assert len(chunks) > 1
            
            # Verify first few chunks
            first_chunk_words = chunks[0].split()
            second_chunk_words = chunks[1].split()
            
            # Should have overlap (last word of first chunk should be in second chunk)
            if len(chunks) > 1:
                assert first_chunk_words[-1] in second_chunk_words