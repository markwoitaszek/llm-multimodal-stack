"""
Unit tests for storage operations in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import os
from io import BytesIO

from app.storage import StorageManager


class TestStorageManager:
    """Test cases for StorageManager"""

    @pytest.fixture
    def storage_manager(self):
        """Create StorageManager instance for testing"""
        return StorageManager()

    @pytest.mark.asyncio
    @patch('app.storage.Minio')
    async def test_storage_manager_initialization(self, mock_minio, storage_manager):
        """Test StorageManager initialization"""
        assert storage_manager is not None
        assert hasattr(storage_manager, 'client')
        assert hasattr(storage_manager, 'bucket_name')

    @pytest.mark.asyncio
    @patch('app.storage.Minio')
    async def test_initialize_success(self, mock_minio, storage_manager):
        """Test successful storage initialization"""
        # Mock MinIO client
        mock_client = AsyncMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Test initialization
        await storage_manager.initialize()

        # Verify client was created
        mock_minio.assert_called_once()
        assert storage_manager.client == mock_client

    @pytest.mark.asyncio
    @patch('app.storage.Minio')
    async def test_initialize_create_bucket(self, mock_minio, storage_manager):
        """Test storage initialization with bucket creation"""
        # Mock MinIO client
        mock_client = AsyncMock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = False

        # Test initialization
        await storage_manager.initialize()

        # Verify bucket was created
        mock_client.make_bucket.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.storage.Minio')
    async def test_initialize_failure(self, mock_minio, storage_manager):
        """Test storage initialization failure"""
        # Mock MinIO client failure
        mock_minio.side_effect = Exception("Connection failed")

        # Test initialization
        with pytest.raises(Exception, match="Connection failed"):
            await storage_manager.initialize()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_manager):
        """Test successful file upload"""
        # Mock client
        mock_client = AsyncMock()
        storage_manager.client = mock_client

        # Create test file
        test_content = b"test file content"
        test_file = BytesIO(test_content)

        # Test upload
        result = await storage_manager.upload_file(
            test_file,
            "test_file.jpg",
            content_type="image/jpeg"
        )

        # Verify result
        assert result == "test_file.jpg"
        mock_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_failure(self, storage_manager):
        """Test file upload failure"""
        # Mock client with failure
        mock_client = AsyncMock()
        mock_client.put_object.side_effect = Exception("Upload failed")
        storage_manager.client = mock_client

        # Create test file
        test_content = b"test file content"
        test_file = BytesIO(test_content)

        # Test upload
        with pytest.raises(Exception, match="Upload failed"):
            await storage_manager.upload_file(
                test_file,
                "test_file.jpg",
                content_type="image/jpeg"
            )

    @pytest.mark.asyncio
    async def test_download_file_success(self, storage_manager):
        """Test successful file download"""
        # Mock client
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.read.return_value = b"downloaded content"
        mock_client.get_object.return_value = mock_response
        storage_manager.client = mock_client

        # Test download
        result = await storage_manager.download_file("test_file.jpg")

        # Verify result
        assert result == b"downloaded content"
        mock_client.get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file_failure(self, storage_manager):
        """Test file download failure"""
        # Mock client with failure
        mock_client = AsyncMock()
        mock_client.get_object.side_effect = Exception("Download failed")
        storage_manager.client = mock_client

        # Test download
        with pytest.raises(Exception, match="Download failed"):
            await storage_manager.download_file("test_file.jpg")

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_manager):
        """Test successful file deletion"""
        # Mock client
        mock_client = AsyncMock()
        storage_manager.client = mock_client

        # Test deletion
        result = await storage_manager.delete_file("test_file.jpg")

        # Verify result
        assert result is True
        mock_client.remove_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_failure(self, storage_manager):
        """Test file deletion failure"""
        # Mock client with failure
        mock_client = AsyncMock()
        mock_client.remove_object.side_effect = Exception("Delete failed")
        storage_manager.client = mock_client

        # Test deletion
        with pytest.raises(Exception, match="Delete failed"):
            await storage_manager.delete_file("test_file.jpg")

    @pytest.mark.asyncio
    async def test_list_files_success(self, storage_manager):
        """Test successful file listing"""
        # Mock client
        mock_client = AsyncMock()
        mock_objects = [
            Mock(object_name="file1.jpg"),
            Mock(object_name="file2.mp4"),
            Mock(object_name="file3.txt")
        ]
        mock_client.list_objects.return_value = mock_objects
        storage_manager.client = mock_client

        # Test listing
        result = await storage_manager.list_files(prefix="file")

        # Verify result
        assert len(result) == 3
        assert "file1.jpg" in result
        assert "file2.mp4" in result
        assert "file3.txt" in result

    @pytest.mark.asyncio
    async def test_list_files_with_prefix(self, storage_manager):
        """Test file listing with prefix filter"""
        # Mock client
        mock_client = AsyncMock()
        mock_objects = [
            Mock(object_name="image1.jpg"),
            Mock(object_name="image2.png"),
            Mock(object_name="video1.mp4")
        ]
        mock_client.list_objects.return_value = mock_objects
        storage_manager.client = mock_client

        # Test listing with prefix
        result = await storage_manager.list_files(prefix="image")

        # Verify result
        assert len(result) == 2
        assert "image1.jpg" in result
        assert "image2.png" in result
        assert "video1.mp4" not in result

    @pytest.mark.asyncio
    async def test_file_exists_success(self, storage_manager):
        """Test file existence check"""
        # Mock client
        mock_client = AsyncMock()
        mock_client.stat_object.return_value = Mock(size=1024)
        storage_manager.client = mock_client

        # Test existence check
        result = await storage_manager.file_exists("test_file.jpg")

        # Verify result
        assert result is True
        mock_client.stat_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_exists_not_found(self, storage_manager):
        """Test file existence check for non-existent file"""
        # Mock client
        mock_client = AsyncMock()
        mock_client.stat_object.side_effect = Exception("File not found")
        storage_manager.client = mock_client

        # Test existence check
        result = await storage_manager.file_exists("nonexistent_file.jpg")

        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, storage_manager):
        """Test getting file information"""
        # Mock client
        mock_client = AsyncMock()
        mock_stat = Mock(
            size=1024,
            last_modified="2024-01-01T00:00:00Z",
            content_type="image/jpeg"
        )
        mock_client.stat_object.return_value = mock_stat
        storage_manager.client = mock_client

        # Test getting file info
        result = await storage_manager.get_file_info("test_file.jpg")

        # Verify result
        assert result["size"] == 1024
        assert result["last_modified"] == "2024-01-01T00:00:00Z"
        assert result["content_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_get_file_url_success(self, storage_manager):
        """Test getting file URL"""
        # Mock client
        mock_client = AsyncMock()
        mock_client.presigned_get_object.return_value = "http://test-url.com/file.jpg"
        storage_manager.client = mock_client

        # Test getting file URL
        result = await storage_manager.get_file_url("test_file.jpg", expires_in=3600)

        # Verify result
        assert result == "http://test-url.com/file.jpg"
        mock_client.presigned_get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check(self, storage_manager):
        """Test storage health check"""
        # Mock client
        mock_client = AsyncMock()
        mock_client.bucket_exists.return_value = True
        storage_manager.client = mock_client

        # Test health check
        result = await storage_manager.health_check()

        # Verify result
        assert result["status"] == "healthy"
        assert "response_time_ms" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, storage_manager):
        """Test storage health check failure"""
        # Mock client with failure
        mock_client = AsyncMock()
        mock_client.bucket_exists.side_effect = Exception("Connection failed")
        storage_manager.client = mock_client

        # Test health check
        result = await storage_manager.health_check()

        # Verify result
        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_copy_file_success(self, storage_manager):
        """Test successful file copying"""
        # Mock client
        mock_client = AsyncMock()
        storage_manager.client = mock_client

        # Test copying
        result = await storage_manager.copy_file("source_file.jpg", "dest_file.jpg")

        # Verify result
        assert result is True
        mock_client.copy_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_file_success(self, storage_manager):
        """Test successful file moving"""
        # Mock client
        mock_client = AsyncMock()
        storage_manager.client = mock_client

        # Test moving
        result = await storage_manager.move_file("source_file.jpg", "dest_file.jpg")

        # Verify result
        assert result is True
        mock_client.copy_object.assert_called_once()
        mock_client.remove_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage_manager):
        """Test getting storage statistics"""
        # Mock client
        mock_client = AsyncMock()
        mock_objects = [
            Mock(size=1024),
            Mock(size=2048),
            Mock(size=512)
        ]
        mock_client.list_objects.return_value = mock_objects
        storage_manager.client = mock_client

        # Test getting stats
        result = await storage_manager.get_storage_stats()

        # Verify result
        assert result["total_files"] == 3
        assert result["total_size_bytes"] == 3584
        assert result["avg_file_size_bytes"] == 1194
