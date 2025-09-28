"""
Multimodal Worker specific pytest configuration and fixtures
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
import numpy as np
from PIL import Image
import torch
import tempfile
import os

@pytest.fixture
def mock_clip_model():
    """Mock CLIP model for image processing"""
    mock_model = Mock()
    mock_model.encode_image = Mock(return_value=torch.randn(1, 512))
    mock_model.encode_text = Mock(return_value=torch.randn(1, 512))
    return mock_model

@pytest.fixture
def mock_blip_model():
    """Mock BLIP model for image captioning"""
    mock_model = Mock()
    mock_model.generate = Mock(return_value=["A test image caption"])
    return mock_model

@pytest.fixture
def mock_whisper_model():
    """Mock Whisper model for audio transcription"""
    mock_model = Mock()
    mock_model.transcribe = Mock(return_value={"text": "Test audio transcription"})
    return mock_model

@pytest.fixture
def mock_sentence_transformer():
    """Mock sentence transformer for text embeddings"""
    mock_model = Mock()
    mock_model.encode = Mock(return_value=np.random.rand(384))
    return mock_model

@pytest.fixture
def test_image_file(tmp_path):
    """Create a test image file"""
    img = Image.new('RGB', (224, 224), color='blue')
    img_path = tmp_path / "test_image.jpg"
    img.save(img_path)
    return str(img_path)

@pytest.fixture
def test_audio_file(tmp_path):
    """Create a test audio file"""
    # Create a simple audio file (WAV format)
    audio_path = tmp_path / "test_audio.wav"
    # For testing purposes, create a dummy file
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
    return str(audio_path)

@pytest.fixture
def test_video_file(tmp_path):
    """Create a test video file"""
    video_path = tmp_path / "test_video.mp4"
    # For testing purposes, create a dummy file
    with open(video_path, 'wb') as f:
        f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp41mp42isom')
    return str(video_path)

@pytest.fixture
def mock_image_processor():
    """Mock image processor"""
    mock_processor = AsyncMock()
    mock_processor.process_image = AsyncMock(return_value={
        "embeddings": np.random.rand(512),
        "caption": "Test image caption",
        "metadata": {"width": 224, "height": 224, "format": "RGB"}
    })
    return mock_processor

@pytest.fixture
def mock_text_processor():
    """Mock text processor"""
    mock_processor = AsyncMock()
    mock_processor.process_text = AsyncMock(return_value={
        "embeddings": np.random.rand(384),
        "chunks": ["Test chunk 1", "Test chunk 2"],
        "metadata": {"word_count": 10, "language": "en"}
    })
    return mock_processor

@pytest.fixture
def mock_audio_processor():
    """Mock audio processor"""
    mock_processor = AsyncMock()
    mock_processor.process_audio = AsyncMock(return_value={
        "transcription": "Test audio transcription",
        "embeddings": np.random.rand(512),
        "metadata": {"duration": 5.0, "sample_rate": 16000}
    })
    return mock_processor

@pytest.fixture
def mock_video_processor():
    """Mock video processor"""
    mock_processor = AsyncMock()
    mock_processor.process_video = AsyncMock(return_value={
        "transcription": "Test video transcription",
        "keyframes": [np.random.rand(224, 224, 3) for _ in range(5)],
        "embeddings": np.random.rand(512),
        "metadata": {"duration": 30.0, "fps": 30, "frame_count": 900}
    })
    return mock_processor

@pytest.fixture
def test_processing_request():
    """Test processing request"""
    return {
        "content_type": "image",
        "content": "base64_encoded_image_data",
        "metadata": {
            "filename": "test.jpg",
            "size": 1024,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }

@pytest.fixture
def test_processing_response():
    """Test processing response"""
    return {
        "content_id": "test_content_id_123",
        "embeddings": np.random.rand(512).tolist(),
        "metadata": {
            "processed_at": "2024-01-01T00:00:00Z",
            "processing_time_ms": 150,
            "model_version": "v1.0"
        },
        "success": True
    }

@pytest.fixture
def mock_asyncpg_pool():
    """Mock asyncpg connection pool with proper async context manager"""
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    
    # Mock the async context manager for pool.acquire()
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    
    # Mock connection methods
    mock_conn.fetchrow.return_value = None
    mock_conn.fetch.return_value = []
    mock_conn.execute.return_value = "INSERT 0 1"
    
    return mock_pool

@pytest.fixture
def mock_asyncpg_create_pool():
    """Mock asyncpg.create_pool function"""
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    
    # Mock the async context manager for pool.acquire()
    mock_acquire = AsyncMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    mock_pool.acquire.return_value = mock_acquire
    
    # Mock connection methods
    mock_conn.fetchrow.return_value = None
    mock_conn.fetch.return_value = []
    mock_conn.execute.return_value = "INSERT 0 1"
    
    # Make the mock pool awaitable
    async def create_pool_mock(*args, **kwargs):
        return mock_pool
    
    return create_pool_mock
