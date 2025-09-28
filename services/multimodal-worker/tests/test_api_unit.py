import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json
import base64
import tempfile
import os
from io import BytesIO
from PIL import Image

# Set test environment variables before importing main
os.environ['TEST_CACHE_DIR'] = tempfile.mkdtemp(prefix="test_cache_")
os.environ['TEST_MODEL_CACHE_DIR'] = os.path.join(os.environ['TEST_CACHE_DIR'], "models")
os.environ['TEST_TEMP_DIR'] = tempfile.mkdtemp(prefix="test_temp_")

# Create the model cache directory
os.makedirs(os.environ['TEST_MODEL_CACHE_DIR'], exist_ok=True)

# Import FastAPI app directly without lifespan
from fastapi import FastAPI
from app.api import router

# Create a test app without lifespan
app = FastAPI()
app.include_router(router)

# Mock the managers in app state
app.state.model_manager = Mock()
app.state.db_manager = AsyncMock()
app.state.storage_manager = Mock()
app.state.cache_manager = Mock()


class TestMultimodalWorkerAPIUnit:
    """Unit tests for Multimodal Worker API endpoints with proper mocking"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def temp_image_file(self):
        """Create temporary image file for testing"""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file.name, 'JPEG')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)

    @pytest.fixture
    def temp_video_file(self):
        """Create temporary video file for testing"""
        # Create a simple test video file (just a placeholder)
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.write(b'fake video content')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    @pytest.mark.asyncio
    async def test_process_image_success(self, client, temp_image_file):
        """Test successful image processing with mocked dependencies"""
        # Mock database operations
        client.app.state.db_manager.get_document_by_hash.return_value = None
        client.app.state.db_manager.create_document.return_value = "test_document_id"
        client.app.state.db_manager.create_image.return_value = "test_image_id"
        
        # Mock storage operations
        client.app.state.storage_manager.calculate_file_hash.return_value = "test_hash"
        client.app.state.storage_manager.generate_object_path.return_value = "test/path/image.jpg"
        client.app.state.storage_manager.upload_file.return_value = None
        
        # Mock model operations
        client.app.state.model_manager.get_model.return_value = Mock()
        client.app.state.model_manager.get_processor.return_value = Mock()
        
        # Mock image processing
        with patch('app.api.ImageProcessor') as mock_image_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_image.return_value = {
                "image_id": "test_image_id",
                "embedding": [0.1, 0.2, 0.3] * 170,  # 512 dimensions
                "caption": "A test image",
                "features": {"mean_brightness": 128.5},
                "storage_path": "test/path/image.jpg",
                "dimensions": (224, 224)
            }
            mock_image_processor.return_value = mock_processor_instance

            # Test image processing with file upload
            with open(temp_image_file, 'rb') as f:
                response = client.post(
                    "/process/image",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"document_name": "Test Image", "metadata": '{"source": "test"}'}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert "image_id" in data["data"]
            assert "caption" in data["data"]
            assert "dimensions" in data["data"]

    @pytest.mark.asyncio
    async def test_process_image_invalid_file_type(self, client):
        """Test image processing with invalid file type"""
        # Mock database operations
        client.app.state.db_manager.get_document_by_hash.return_value = None
        client.app.state.db_manager.create_document.return_value = "test_document_id"
        
        # Mock storage operations
        client.app.state.storage_manager.calculate_file_hash.return_value = "test_hash"
        client.app.state.storage_manager.generate_object_path.return_value = "test/path/image.jpg"
        
        # Mock model operations
        client.app.state.model_manager.get_model.return_value = Mock()
        client.app.state.model_manager.get_processor.return_value = Mock()

        # Test with invalid file type
        response = client.post(
            "/process/image",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"document_name": "Test File"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_process_video_success(self, client, temp_video_file):
        """Test successful video processing with mocked dependencies"""
        # Mock database operations
        client.app.state.db_manager.get_document_by_hash.return_value = None
        client.app.state.db_manager.create_document.return_value = "test_document_id"
        client.app.state.db_manager.create_video.return_value = "test_video_id"
        
        # Mock storage operations
        client.app.state.storage_manager.calculate_file_hash.return_value = "test_hash"
        client.app.state.storage_manager.generate_object_path.return_value = "test/path/video.mp4"
        client.app.state.storage_manager.upload_file.return_value = None
        
        # Mock model operations
        client.app.state.model_manager.get_model.return_value = Mock()
        client.app.state.model_manager.get_processor.return_value = Mock()

        # Mock video processing
        with patch('app.api.VideoProcessor') as mock_video_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_video.return_value = {
                "video_id": "test_video_id",
                "duration": 10.5,
                "transcription": "Test transcription",
                "keyframes": [{"timestamp": 0.0, "image_id": "keyframe_1"}],
                "storage_path": "test/path/video.mp4"
            }
            mock_video_processor.return_value = mock_processor_instance

            # Test video processing
            with open(temp_video_file, 'rb') as f:
                response = client.post(
                    "/process/video",
                    files={"file": ("test.mp4", f, "video/mp4")},
                    data={"document_name": "Test Video", "metadata": '{"source": "test"}'}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert "video_id" in data["data"]
            assert "duration" in data["data"]
            assert "transcription" in data["data"]

    @pytest.mark.asyncio
    async def test_process_text_success(self, client):
        """Test successful text processing with mocked dependencies"""
        # Mock database operations
        client.app.state.db_manager.get_document_by_hash.return_value = None
        client.app.state.db_manager.create_document.return_value = "test_document_id"
        client.app.state.db_manager.create_text_chunk.return_value = "test_chunk_id"
        
        # Mock model operations
        client.app.state.model_manager.get_model.return_value = Mock()
        client.app.state.model_manager.get_processor.return_value = Mock()

        # Mock text processing
        with patch('app.api.TextProcessor') as mock_text_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_text.return_value = {
                "chunks": [
                    {
                        "chunk_id": "test_chunk_id",
                        "text": "Test text content",
                        "embedding": [0.1, 0.2, 0.3] * 170,  # 512 dimensions
                        "metadata": {"chunk_index": 0}
                    }
                ]
            }
            mock_text_processor.return_value = mock_processor_instance

            # Test text processing
            response = client.post(
                "/process/text",
                json={
                    "text": "Test text content",
                    "document_name": "Test Document",
                    "metadata": {"source": "test"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert "chunks" in data["data"]

    def test_models_status_endpoint(self, client):
        """Test models status endpoint"""
        # Mock model manager
        client.app.state.model_manager.get_model_status.return_value = {
            "clip_model": "loaded",
            "blip_model": "loaded",
            "whisper_model": "loaded"
        }

        response = client.get("/models/status")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_storage_status_endpoint(self, client):
        """Test storage status endpoint"""
        # Mock storage manager
        client.app.state.storage_manager.get_status.return_value = {
            "minio": "connected",
            "postgres": "connected",
            "qdrant": "connected"
        }

        response = client.get("/storage/status")
        assert response.status_code == 200
        data = response.json()
        assert "minio" in data
        assert "postgres" in data
        assert "qdrant" in data

    @pytest.mark.asyncio
    async def test_cache_stats_endpoint(self, client):
        """Test cache stats endpoint"""
        # Mock cache manager
        client.app.state.cache_manager.get_cache_stats.return_value = {
            "total_entries": 100,
            "hit_rate": 0.85,
            "memory_usage_mb": 50
        }

        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_entries" in data
        assert "hit_rate" in data
        assert "memory_usage_mb" in data

    @pytest.mark.asyncio
    async def test_clear_cache_endpoint(self, client):
        """Test clear cache endpoint"""
        # Mock cache manager
        client.app.state.cache_manager.clear_all_cache.return_value = True

        response = client.delete("/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_invalidate_file_cache_endpoint(self, client):
        """Test invalidate file cache endpoint"""
        # Mock cache manager
        client.app.state.cache_manager.invalidate_file_cache.return_value = 5

        response = client.delete("/cache/file/test_hash")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "invalidated" in data["message"]

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.get("/process/image")
        assert response.status_code == 405
