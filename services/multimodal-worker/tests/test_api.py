"""
Unit tests for API endpoints in multimodal-worker service
"""
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

# Mock moviepy import before importing main
import sys
from unittest.mock import patch, Mock
with patch.dict('sys.modules', {'moviepy.editor': Mock()}):
    from main import app


class TestMultimodalWorkerAPI:
    """Test cases for Multimodal Worker API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_image_data(self):
        """Create mock image data"""
        img = Image.new('RGB', (224, 224), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()

    @pytest.fixture
    def mock_audio_data(self):
        """Create mock audio data"""
        return base64.b64encode(b"fake audio data").decode()

    @pytest.fixture
    def mock_video_data(self):
        """Create mock video data"""
        return base64.b64encode(b"fake video data").decode()

    @pytest.fixture
    def temp_image_file(self):
        """Create a temporary image file"""
        img = Image.new('RGB', (224, 224), color='blue')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            img.save(tmp_file.name, 'JPEG')
            yield tmp_file.name
        os.unlink(tmp_file.name)

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "service" in data

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_image_success(self, mock_model_manager, mock_storage_manager, 
                                       mock_db_manager, client, temp_image_file):
        """Test successful image processing with real file upload"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_instance.get_document_by_hash.return_value = None
        mock_db_instance.create_document.return_value = "test_document_id"
        mock_db_instance.create_image.return_value = "test_image_id"
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_instance.calculate_file_hash.return_value = "test_hash"
        mock_storage_instance.generate_object_path.return_value = "test/path/image.jpg"
        mock_storage_instance.upload_file.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_instance.get_model.return_value = Mock()
        mock_model_instance.get_processor.return_value = Mock()
        mock_model_manager.return_value = mock_model_instance

        # Mock image processing
        with patch('main.ImageProcessor') as mock_image_processor:
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
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_image_invalid_file_type(self, mock_model_manager, mock_storage_manager, 
                                                 mock_db_manager, client):
        """Test image processing with invalid file type"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_manager.return_value = mock_model_instance

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
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_image_file_too_large(self, mock_model_manager, mock_storage_manager, 
                                              mock_db_manager, client, temp_image_file):
        """Test image processing with file too large"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_manager.return_value = mock_model_instance

        # Mock file size check
        with patch('main.settings') as mock_settings:
            mock_settings.max_file_size = 100  # Very small limit

            # Test with large file
            with open(temp_image_file, 'rb') as f:
                response = client.post(
                    "/process/image",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"document_name": "Test Image"}
                )

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "error" in data

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_video_success(self, mock_model_manager, mock_storage_manager, 
                                       mock_db_manager, client):
        """Test successful video processing"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_instance.get_document_by_hash.return_value = None
        mock_db_instance.create_document.return_value = "test_document_id"
        mock_db_instance.create_video.return_value = "test_video_id"
        mock_db_instance.create_video_keyframe.return_value = "test_keyframe_id"
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_instance.calculate_file_hash.return_value = "test_hash"
        mock_storage_instance.generate_object_path.return_value = "test/path/video.mp4"
        mock_storage_instance.upload_file.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_instance.get_model.return_value = Mock()
        mock_model_manager.return_value = mock_model_instance

        # Mock video processing
        with patch('main.VideoProcessor') as mock_video_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_video.return_value = {
                "video_id": "test_video_id",
                "transcription": "Test video transcription",
                "text_embedding": [0.1, 0.2, 0.3] * 170,
                "keyframes": [
                    {
                        "keyframe_id": "test_keyframe_id",
                        "timestamp": 5.0,
                        "embedding": [0.4, 0.5, 0.6] * 170,
                        "caption": "Test keyframe caption",
                        "storage_path": "test/path/keyframe.jpg"
                    }
                ],
                "storage_path": "test/path/video.mp4",
                "duration": 120.5,
                "dimensions": (1920, 1080)
            }
            mock_video_processor.return_value = mock_processor_instance

            # Test video processing
            response = client.post(
                "/process/video",
                files={"file": ("test.mp4", b"fake video data", "video/mp4")},
                data={"document_name": "Test Video", "metadata": '{"source": "test"}'}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert "video_id" in data["data"]
            assert "transcription" in data["data"]
            assert "keyframes_count" in data["data"]
            assert "duration" in data["data"]

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_text_success(self, mock_model_manager, mock_storage_manager, 
                                      mock_db_manager, client):
        """Test successful text processing"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_instance.get_document_by_hash.return_value = None
        mock_db_instance.create_document.return_value = "test_document_id"
        mock_db_instance.create_text_chunk.return_value = "test_chunk_id"
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_instance.get_model.return_value = Mock()
        mock_model_manager.return_value = mock_model_instance

        # Mock text processing
        with patch('main.TextProcessor') as mock_text_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_text.return_value = {
                "chunks": [
                    {
                        "chunk_id": "test_chunk_id",
                        "chunk_index": 0,
                        "text": "This is a test document for processing.",
                        "embedding": [0.1, 0.2, 0.3] * 170
                    }
                ],
                "total_chunks": 1
            }
            mock_text_processor.return_value = mock_processor_instance

            # Test text processing
            response = client.post(
                "/process/text",
                json={
                    "text": "This is a test document for processing.",
                    "document_name": "Test Document",
                    "metadata": {"source": "test"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert "chunks_count" in data["data"]

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_text_empty_text(self, mock_model_manager, mock_storage_manager, 
                                         mock_db_manager, client):
        """Test text processing with empty text"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_manager.return_value = mock_model_instance

        # Test with empty text
        response = client.post(
            "/process/text",
            json={
                "text": "",
                "document_name": "Empty Document"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_image_duplicate_document(self, mock_model_manager, mock_storage_manager, 
                                                  mock_db_manager, client, temp_image_file):
        """Test image processing with duplicate document"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_instance.get_document_by_hash.return_value = {
            "id": "existing_document_id",
            "filename": "existing.jpg",
            "file_type": "image"
        }
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_instance.calculate_file_hash.return_value = "existing_hash"
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_manager.return_value = mock_model_instance

        # Test with duplicate document
        with open(temp_image_file, 'rb') as f:
            response = client.post(
                "/process/image",
                files={"file": ("test.jpg", f, "image/jpeg")},
                data={"document_name": "Test Image"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Document already processed"
        assert data["data"]["document_id"] == "existing_document_id"

    def test_models_status_endpoint(self, client):
        """Test models status endpoint"""
        response = client.get("/models/status")
        assert response.status_code == 200
        data = response.json()
        assert "clip" in data
        assert "blip" in data
        assert "whisper" in data
        assert "sentence_transformer" in data

    def test_storage_status_endpoint(self, client):
        """Test storage status endpoint"""
        response = client.get("/storage/status")
        assert response.status_code == 200
        data = response.json()
        assert "minio" in data
        assert "postgres" in data
        assert "qdrant" in data

    @pytest.mark.asyncio
    async def test_cache_stats_endpoint(self, client):
        """Test cache stats endpoint"""
        with patch('main.cache_manager') as mock_cache_manager:
            mock_cache_manager.get_cache_stats.return_value = {
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
        with patch('main.cache_manager') as mock_cache_manager:
            mock_cache_manager.clear_all_cache.return_value = True

            response = client.delete("/cache/clear")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "cleared successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_invalidate_file_cache_endpoint(self, client):
        """Test invalidate file cache endpoint"""
        with patch('main.cache_manager') as mock_cache_manager:
            mock_cache_manager.invalidate_file_cache.return_value = 5

            response = client.delete("/cache/file/test_hash")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "Invalidated 5 cache entries" in data["message"]
            assert data["file_hash"] == "test_hash"

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/health")
        assert response.status_code == 405

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_image_processing_failure(self, mock_model_manager, mock_storage_manager, 
                                                  mock_db_manager, client, temp_image_file):
        """Test image processing failure during processing"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_instance.get_document_by_hash.return_value = None
        mock_db_instance.create_document.return_value = "test_document_id"
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_instance.calculate_file_hash.return_value = "test_hash"
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_manager.return_value = mock_model_instance

        # Mock image processing failure
        with patch('main.ImageProcessor') as mock_image_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_image.side_effect = Exception("Processing failed")
            mock_image_processor.return_value = mock_processor_instance

            # Test image processing failure
            with open(temp_image_file, 'rb') as f:
                response = client.post(
                    "/process/image",
                    files={"file": ("test.jpg", f, "image/jpeg")},
                    data={"document_name": "Test Image"}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data
            assert "Processing failed" in data["error"]

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_text_with_long_text(self, mock_model_manager, mock_storage_manager, 
                                             mock_db_manager, client):
        """Test text processing with long text that gets chunked"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_instance.get_document_by_hash.return_value = None
        mock_db_instance.create_document.return_value = "test_document_id"
        mock_db_instance.create_text_chunk.return_value = "test_chunk_id"
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_instance.get_model.return_value = Mock()
        mock_model_manager.return_value = mock_model_instance

        # Mock text processing with multiple chunks
        with patch('main.TextProcessor') as mock_text_processor:
            mock_processor_instance = AsyncMock()
            mock_processor_instance.process_text.return_value = {
                "chunks": [
                    {
                        "chunk_id": "test_chunk_id_1",
                        "chunk_index": 0,
                        "text": "This is the first chunk of a long document.",
                        "embedding": [0.1, 0.2, 0.3] * 170
                    },
                    {
                        "chunk_id": "test_chunk_id_2",
                        "chunk_index": 1,
                        "text": "This is the second chunk of the same document.",
                        "embedding": [0.4, 0.5, 0.6] * 170
                    }
                ],
                "total_chunks": 2
            }
            mock_text_processor.return_value = mock_processor_instance

            # Test text processing with long text
            long_text = "This is a very long document that should be split into multiple chunks. " * 20
            response = client.post(
                "/process/text",
                json={
                    "text": long_text,
                    "document_name": "Long Document",
                    "metadata": {"source": "test"}
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document_id" in data["data"]
            assert data["data"]["chunks_count"] == 2

    @pytest.mark.asyncio
    @patch('main.DatabaseManager')
    @patch('main.StorageManager')
    @patch('main.ModelManager')
    async def test_process_video_invalid_file_type(self, mock_model_manager, mock_storage_manager, 
                                                 mock_db_manager, client):
        """Test video processing with invalid file type"""
        # Mock managers
        mock_db_instance = AsyncMock()
        mock_db_instance.initialize.return_value = None
        mock_db_instance.close.return_value = None
        mock_db_manager.return_value = mock_db_instance

        mock_storage_instance = Mock()
        mock_storage_instance.initialize.return_value = None
        mock_storage_instance.close.return_value = None
        mock_storage_manager.return_value = mock_storage_instance

        mock_model_instance = Mock()
        mock_model_instance.load_models.return_value = None
        mock_model_instance.cleanup.return_value = None
        mock_model_manager.return_value = mock_model_instance

        # Test with invalid file type
        response = client.post(
            "/process/video",
            files={"file": ("test.txt", b"not a video", "text/plain")},
            data={"document_name": "Test File"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_api_error_handling(self, client):
        """Test API error handling for malformed requests"""
        # Test with invalid JSON
        response = client.post(
            "/process/text",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

        # Test with missing required fields
        response = client.post(
            "/process/text",
            json={"document_name": "Test"}  # Missing 'text' field
        )
        assert response.status_code == 422