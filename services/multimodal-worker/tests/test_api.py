"""
Unit tests for API endpoints in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import json
import base64
from io import BytesIO
from PIL import Image

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
    @patch('main.model_manager')
    @patch('main.db_manager')
    @patch('main.storage_manager')
    async def test_process_image_success(self, mock_storage, mock_db, mock_models, 
                                       client, mock_image_data):
        """Test successful image processing"""
        # Mock managers
        mock_models.get_model.return_value = Mock()
        mock_db.insert_record.return_value = "test_content_id"
        mock_storage.upload_file.return_value = "test_file_url"

        # Test image processing
        response = client.post(
            "/process/image",
            json={
                "image_data": mock_image_data,
                "metadata": {
                    "filename": "test.jpg",
                    "source": "test"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content_id" in data
        assert "embeddings" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    @patch('main.model_manager')
    async def test_process_image_invalid_data(self, mock_models, client):
        """Test image processing with invalid data"""
        # Test with invalid base64 data
        response = client.post(
            "/process/image",
            json={
                "image_data": "invalid_base64_data",
                "metadata": {"filename": "test.jpg"}
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.model_manager')
    @patch('main.db_manager')
    async def test_process_text_success(self, mock_db, mock_models, client):
        """Test successful text processing"""
        # Mock models
        mock_transformer = Mock()
        mock_transformer.encode.return_value = [0.1, 0.2, 0.3] * 128  # 384 dimensions
        mock_models.get_model.return_value = mock_transformer
        mock_db.insert_record.return_value = "test_content_id"

        # Test text processing
        response = client.post(
            "/process/text",
            json={
                "text": "This is a test document for processing.",
                "metadata": {
                    "source": "test",
                    "language": "en"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content_id" in data
        assert "embeddings" in data
        assert "chunks" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    @patch('main.model_manager')
    @patch('main.db_manager')
    async def test_process_audio_success(self, mock_db, mock_models, client, mock_audio_data):
        """Test successful audio processing"""
        # Mock models
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = {"text": "Test transcription"}
        mock_clip = Mock()
        mock_clip.encode_text.return_value = Mock()
        mock_models.get_model.side_effect = lambda model_type: {
            "whisper": mock_whisper,
            "clip": mock_clip
        }[model_type]
        mock_db.insert_record.return_value = "test_content_id"

        # Test audio processing
        response = client.post(
            "/process/audio",
            json={
                "audio_data": mock_audio_data,
                "metadata": {
                    "filename": "test.wav",
                    "duration": 5.0
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content_id" in data
        assert "transcription" in data
        assert "embeddings" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    @patch('main.model_manager')
    @patch('main.db_manager')
    async def test_process_video_success(self, mock_db, mock_models, client, mock_video_data):
        """Test successful video processing"""
        # Mock models
        mock_whisper = Mock()
        mock_whisper.transcribe.return_value = {"text": "Test video transcription"}
        mock_clip = Mock()
        mock_clip.encode_text.return_value = Mock()
        mock_models.get_model.side_effect = lambda model_type: {
            "whisper": mock_whisper,
            "clip": mock_clip
        }[model_type]
        mock_db.insert_record.return_value = "test_content_id"

        # Test video processing
        response = client.post(
            "/process/video",
            json={
                "video_data": mock_video_data,
                "metadata": {
                    "filename": "test.mp4",
                    "duration": 30.0
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "content_id" in data
        assert "transcription" in data
        assert "keyframes" in data
        assert "embeddings" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    @patch('main.db_manager')
    async def test_get_content_success(self, mock_db, client):
        """Test getting content by ID"""
        # Mock database response
        mock_db.get_content_by_id.return_value = {
            "id": "test_content_id",
            "content_type": "image",
            "filename": "test.jpg",
            "status": "processed",
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Test getting content
        response = client.get("/content/test_content_id")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_content_id"
        assert data["content_type"] == "image"
        assert data["filename"] == "test.jpg"

    @pytest.mark.asyncio
    @patch('main.db_manager')
    async def test_get_content_not_found(self, mock_db, client):
        """Test getting non-existent content"""
        # Mock database response
        mock_db.get_content_by_id.return_value = None

        # Test getting content
        response = client.get("/content/nonexistent_id")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.db_manager')
    async def test_list_content_success(self, mock_db, client):
        """Test listing content"""
        # Mock database response
        mock_db.get_content_by_type.return_value = [
            {"id": "content_1", "content_type": "image"},
            {"id": "content_2", "content_type": "image"}
        ]

        # Test listing content
        response = client.get("/content?content_type=image&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["content"]) == 2
        assert data["total"] == 2

    @pytest.mark.asyncio
    @patch('main.db_manager')
    async def test_get_processing_stats(self, mock_db, client):
        """Test getting processing statistics"""
        # Mock database response
        mock_db.get_processing_stats.return_value = {
            "total_content": 100,
            "processed_content": 95,
            "failed_content": 5,
            "avg_processing_time_ms": 150
        }

        # Test getting stats
        response = client.get("/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_content"] == 100
        assert data["processed_content"] == 95
        assert data["failed_content"] == 5
        assert data["avg_processing_time_ms"] == 150

    @pytest.mark.asyncio
    @patch('main.model_manager')
    async def test_model_health_check(self, mock_models, client):
        """Test model health check"""
        # Mock model health check
        mock_models.health_check.return_value = {
            "clip_model": "healthy",
            "blip_model": "healthy",
            "whisper_model": "healthy",
            "sentence_transformer": "healthy"
        }

        # Test model health check
        response = client.get("/models/health")

        assert response.status_code == 200
        data = response.json()
        assert data["clip_model"] == "healthy"
        assert data["blip_model"] == "healthy"
        assert data["whisper_model"] == "healthy"
        assert data["sentence_transformer"] == "healthy"

    @pytest.mark.asyncio
    @patch('main.storage_manager')
    async def test_storage_health_check(self, mock_storage, client):
        """Test storage health check"""
        # Mock storage health check
        mock_storage.health_check.return_value = {
            "status": "healthy",
            "response_time_ms": 50
        }

        # Test storage health check
        response = client.get("/storage/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "response_time_ms" in data

    def test_invalid_endpoint(self, client):
        """Test invalid endpoint"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test method not allowed"""
        response = client.put("/health")
        assert response.status_code == 405

    @pytest.mark.asyncio
    @patch('main.model_manager')
    async def test_process_with_missing_metadata(self, mock_models, client):
        """Test processing with missing metadata"""
        # Test image processing without metadata
        response = client.post(
            "/process/image",
            json={
                "image_data": "dummy_base64_data"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.model_manager')
    async def test_process_with_empty_content(self, mock_models, client):
        """Test processing with empty content"""
        # Test text processing with empty text
        response = client.post(
            "/process/text",
            json={
                "text": "",
                "metadata": {"source": "test"}
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    @patch('main.model_manager')
    async def test_process_with_model_failure(self, mock_models, client):
        """Test processing with model failure"""
        # Mock model failure
        mock_models.get_model.side_effect = Exception("Model loading failed")

        # Test text processing
        response = client.post(
            "/process/text",
            json={
                "text": "Test text",
                "metadata": {"source": "test"}
            }
        )

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data
