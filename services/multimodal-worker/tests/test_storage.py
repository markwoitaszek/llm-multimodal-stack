"""
Unit tests for storage operations in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import os
import hashlib
from io import BytesIO

from app.storage import StorageManager


class TestStorageManager:
    """Test cases for StorageManager"""

    @pytest.fixture
    def storage_manager(self):
        """Create StorageManager instance for testing"""
        with patch('app.storage.settings') as mock_settings:
            mock_settings.minio_endpoint = 'localhost:9000'
            mock_settings.minio_access_key = 'test_access_key'
            mock_settings.minio_secret_key = 'test_secret_key'
            mock_settings.minio_secure = False
            mock_settings.minio_bucket_images = 'test-images'
            mock_settings.minio_bucket_videos = 'test-videos'
            mock_settings.minio_bucket_documents = 'test-documents'
            return StorageManager()

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client"""
        client = Mock()
        client.bucket_exists.return_value = False
        client.make_bucket.return_value = None
        client.fput_object.return_value = None
        client.put_object.return_value = None
        client.fget_object.return_value = None
        client.presigned_get_object.return_value = "https://test-url.com"
        client.remove_object.return_value = None
        client.stat_object.return_value = Mock()
        client.list_objects.return_value = [Mock(object_name="test1.jpg"), Mock(object_name="test2.jpg")]
        return client

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            tmp_file.write("Test file content")
            yield tmp_file.name
        os.unlink(tmp_file.name)

    @pytest.mark.asyncio
    async def test_initialize_success(self, storage_manager, mock_minio_client):
        """Test successful storage initialization"""
        with patch('app.storage.Minio', return_value=mock_minio_client) as mock_minio:
            # Test initialization
            await storage_manager.initialize()

            # Verify MinIO client was created with actual settings values
            mock_minio.assert_called_once_with(
                'localhost:9000',
                access_key='minioadmin',
                secret_key='minioadmin',
                secure=False
            )

            # Verify buckets were checked and created
            assert mock_minio_client.bucket_exists.call_count == 3
            assert mock_minio_client.make_bucket.call_count == 3

            # Verify client was stored
            assert storage_manager.client == mock_minio_client

    @pytest.mark.asyncio
    async def test_initialize_with_existing_buckets(self, storage_manager, mock_minio_client):
        """Test initialization when buckets already exist"""
        # Mock existing buckets
        mock_minio_client.bucket_exists.return_value = True

        with patch('app.storage.Minio', return_value=mock_minio_client) as mock_minio:
            # Test initialization
            await storage_manager.initialize()

            # Verify buckets were checked but not created
            assert mock_minio_client.bucket_exists.call_count == 3
            assert mock_minio_client.make_bucket.call_count == 0

    @pytest.mark.asyncio
    async def test_initialize_failure(self, storage_manager):
        """Test storage initialization failure"""
        with patch('app.storage.Minio', side_effect=Exception("Connection failed")):
            # Test that exception is raised
            with pytest.raises(Exception, match="Connection failed"):
                await storage_manager.initialize()

    @pytest.mark.asyncio
    async def test_close(self, storage_manager, mock_minio_client):
        """Test storage manager closure"""
        storage_manager.client = mock_minio_client

        # Test close
        await storage_manager.close()

        # Should not raise exception (MinIO doesn't need explicit closing)

    def test_upload_file_success(self, storage_manager, mock_minio_client, temp_file):
        """Test successful file upload"""
        storage_manager.client = mock_minio_client

        # Test file upload
        result = storage_manager.upload_file(
            bucket_name="test-bucket",
            object_name="test-object.jpg",
            file_path=temp_file,
            content_type="image/jpeg"
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called
        mock_minio_client.fput_object.assert_called_once_with(
            "test-bucket",
            "test-object.jpg",
            temp_file,
            content_type="image/jpeg"
        )

    def test_upload_file_failure(self, storage_manager, mock_minio_client, temp_file):
        """Test file upload failure"""
        storage_manager.client = mock_minio_client

        # Mock upload failure
        from minio.error import S3Error
        mock_minio_client.fput_object.side_effect = S3Error("Upload failed", "UploadError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test file upload
        result = storage_manager.upload_file(
            bucket_name="test-bucket",
            object_name="test-object.jpg",
            file_path=temp_file
        )

        # Verify result
        assert result is False

    def test_upload_data_success(self, storage_manager, mock_minio_client):
        """Test successful data upload"""
        storage_manager.client = mock_minio_client

        # Test data upload
        test_data = b"Test binary data"
        result = storage_manager.upload_data(
            bucket_name="test-bucket",
            object_name="test-object.bin",
            data=test_data,
            content_type="application/octet-stream"
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called
        mock_minio_client.put_object.assert_called_once()
        call_args = mock_minio_client.put_object.call_args
        assert call_args[0][0] == "test-bucket"  # bucket_name
        assert call_args[0][1] == "test-object.bin"  # object_name
        assert call_args[1]['length'] == len(test_data)
        assert call_args[1]['content_type'] == "application/octet-stream"

    def test_upload_data_failure(self, storage_manager, mock_minio_client):
        """Test data upload failure"""
        storage_manager.client = mock_minio_client

        # Mock upload failure
        from minio.error import S3Error
        mock_minio_client.put_object.side_effect = S3Error("Upload failed", "UploadError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test data upload
        test_data = b"Test binary data"
        result = storage_manager.upload_data(
            bucket_name="test-bucket",
            object_name="test-object.bin",
            data=test_data
        )

        # Verify result
        assert result is False

    def test_download_file_success(self, storage_manager, mock_minio_client, temp_file):
        """Test successful file download"""
        storage_manager.client = mock_minio_client

        # Test file download
        result = storage_manager.download_file(
            bucket_name="test-bucket",
            object_name="test-object.jpg",
            file_path=temp_file
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called
        mock_minio_client.fget_object.assert_called_once_with(
            "test-bucket",
            "test-object.jpg",
            temp_file
        )

    def test_download_file_failure(self, storage_manager, mock_minio_client, temp_file):
        """Test file download failure"""
        storage_manager.client = mock_minio_client

        # Mock download failure
        from minio.error import S3Error
        mock_minio_client.fget_object.side_effect = S3Error("Download failed", "DownloadError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test file download
        result = storage_manager.download_file(
            bucket_name="test-bucket",
            object_name="test-object.jpg",
            file_path=temp_file
        )

        # Verify result
        assert result is False

    def test_get_object_url_success(self, storage_manager, mock_minio_client):
        """Test successful object URL generation"""
        storage_manager.client = mock_minio_client

        # Test URL generation
        url = storage_manager.get_object_url(
            bucket_name="test-bucket",
            object_name="test-object.jpg"
        )

        # Verify result
        assert url == "https://test-url.com"

        # Verify MinIO client was called
        mock_minio_client.presigned_get_object.assert_called_once()
        call_args = mock_minio_client.presigned_get_object.call_args
        assert call_args[0][0] == "test-bucket"  # bucket_name
        assert call_args[0][1] == "test-object.jpg"  # object_name

    def test_get_object_url_failure(self, storage_manager, mock_minio_client):
        """Test object URL generation failure"""
        storage_manager.client = mock_minio_client

        # Mock URL generation failure
        from minio.error import S3Error
        mock_minio_client.presigned_get_object.side_effect = S3Error("URL generation failed", "URLError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test URL generation
        url = storage_manager.get_object_url(
            bucket_name="test-bucket",
            object_name="test-object.jpg"
        )

        # Verify result
        assert url == ""

    def test_delete_object_success(self, storage_manager, mock_minio_client):
        """Test successful object deletion"""
        storage_manager.client = mock_minio_client

        # Test object deletion
        result = storage_manager.delete_object(
            bucket_name="test-bucket",
            object_name="test-object.jpg"
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called
        mock_minio_client.remove_object.assert_called_once_with(
            "test-bucket",
            "test-object.jpg"
        )

    def test_delete_object_failure(self, storage_manager, mock_minio_client):
        """Test object deletion failure"""
        storage_manager.client = mock_minio_client

        # Mock deletion failure
        from minio.error import S3Error
        mock_minio_client.remove_object.side_effect = S3Error("Deletion failed", "DeleteError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test object deletion
        result = storage_manager.delete_object(
            bucket_name="test-bucket",
            object_name="test-object.jpg"
        )

        # Verify result
        assert result is False

    def test_object_exists_true(self, storage_manager, mock_minio_client):
        """Test object exists check when object exists"""
        storage_manager.client = mock_minio_client

        # Test object exists check
        result = storage_manager.object_exists(
            bucket_name="test-bucket",
            object_name="test-object.jpg"
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called
        mock_minio_client.stat_object.assert_called_once_with(
            "test-bucket",
            "test-object.jpg"
        )

    def test_object_exists_false(self, storage_manager, mock_minio_client):
        """Test object exists check when object doesn't exist"""
        storage_manager.client = mock_minio_client

        # Mock object doesn't exist
        from minio.error import S3Error
        mock_minio_client.stat_object.side_effect = S3Error("Object not found", "NotFoundError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test object exists check
        result = storage_manager.object_exists(
            bucket_name="test-bucket",
            object_name="test-object.jpg"
        )

        # Verify result
        assert result is False

    def test_list_objects_success(self, storage_manager, mock_minio_client):
        """Test successful object listing"""
        storage_manager.client = mock_minio_client

        # Test object listing
        result = storage_manager.list_objects(
            bucket_name="test-bucket",
            prefix="test/"
        )

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert "test1.jpg" in result
        assert "test2.jpg" in result

        # Verify MinIO client was called
        mock_minio_client.list_objects.assert_called_once_with(
            "test-bucket",
            prefix="test/"
        )

    def test_list_objects_failure(self, storage_manager, mock_minio_client):
        """Test object listing failure"""
        storage_manager.client = mock_minio_client

        # Mock listing failure
        from minio.error import S3Error
        mock_minio_client.list_objects.side_effect = S3Error("Listing failed", "ListError", "test-bucket", "test-object", "test-request-id", "test-host-id")

        # Test object listing
        result = storage_manager.list_objects(
            bucket_name="test-bucket",
            prefix="test/"
        )

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 0

    def test_calculate_file_hash(self, temp_file):
        """Test file hash calculation"""
        # Test hash calculation
        hash_result = StorageManager.calculate_file_hash(temp_file)

        # Verify result
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hex length

        # Verify hash is consistent
        hash_result2 = StorageManager.calculate_file_hash(temp_file)
        assert hash_result == hash_result2

        # Verify hash changes with content
        with open(temp_file, 'w') as f:
            f.write("Different content")
        hash_result3 = StorageManager.calculate_file_hash(temp_file)
        assert hash_result != hash_result3

    def test_calculate_data_hash(self):
        """Test data hash calculation"""
        # Test hash calculation
        test_data = b"Test binary data"
        hash_result = StorageManager.calculate_data_hash(test_data)

        # Verify result
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hex length

        # Verify hash is consistent
        hash_result2 = StorageManager.calculate_data_hash(test_data)
        assert hash_result == hash_result2

        # Verify hash changes with different data
        test_data2 = b"Different binary data"
        hash_result3 = StorageManager.calculate_data_hash(test_data2)
        assert hash_result != hash_result3

    def test_generate_object_path(self):
        """Test object path generation"""
        storage_manager = StorageManager()
        
        # Test path generation
        file_hash = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        filename = "test.jpg"
        prefix = "images"

        path = storage_manager.generate_object_path(file_hash, filename, prefix)

        # Verify result
        expected_path = f"images/ab/{file_hash}_{filename}"
        assert path == expected_path

        # Test without prefix
        path_no_prefix = storage_manager.generate_object_path(file_hash, filename)
        expected_path_no_prefix = f"ab/{file_hash}_{filename}"
        assert path_no_prefix == expected_path_no_prefix

    def test_generate_object_path_with_short_hash(self):
        """Test object path generation with short hash"""
        storage_manager = StorageManager()
        
        # Test with very short hash
        file_hash = "ab"
        filename = "test.jpg"
        prefix = "images"

        path = storage_manager.generate_object_path(file_hash, filename, prefix)

        # Verify result uses first 2 characters
        expected_path = f"images/ab/{file_hash}_{filename}"
        assert path == expected_path

    def test_storage_manager_initialization(self, storage_manager):
        """Test StorageManager initialization"""
        # Verify initial state
        assert storage_manager.client is None
        assert isinstance(storage_manager.buckets, list)
        assert len(storage_manager.buckets) == 3
        assert "test-images" in storage_manager.buckets
        assert "test-videos" in storage_manager.buckets
        assert "test-documents" in storage_manager.buckets

    def test_upload_file_without_content_type(self, storage_manager, mock_minio_client, temp_file):
        """Test file upload without content type"""
        storage_manager.client = mock_minio_client

        # Test file upload without content type
        result = storage_manager.upload_file(
            bucket_name="test-bucket",
            object_name="test-object.jpg",
            file_path=temp_file
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called without content_type
        mock_minio_client.fput_object.assert_called_once_with(
            "test-bucket",
            "test-object.jpg",
            temp_file,
            content_type=None
        )

    def test_upload_data_without_content_type(self, storage_manager, mock_minio_client):
        """Test data upload without content type"""
        storage_manager.client = mock_minio_client

        # Test data upload without content type
        test_data = b"Test binary data"
        result = storage_manager.upload_data(
            bucket_name="test-bucket",
            object_name="test-object.bin",
            data=test_data
        )

        # Verify result
        assert result is True

        # Verify MinIO client was called without content_type
        call_args = mock_minio_client.put_object.call_args
        assert call_args[1]['content_type'] is None

    def test_list_objects_without_prefix(self, storage_manager, mock_minio_client):
        """Test object listing without prefix"""
        storage_manager.client = mock_minio_client

        # Test object listing without prefix
        result = storage_manager.list_objects("test-bucket")

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2

        # Verify MinIO client was called with empty prefix
        mock_minio_client.list_objects.assert_called_once_with(
            "test-bucket",
            prefix=""
        )

    @pytest.mark.asyncio
    async def test_initialize_with_mixed_bucket_states(self, storage_manager, mock_minio_client):
        """Test initialization with some buckets existing and some not"""
        # Mock mixed bucket states
        def bucket_exists_side_effect(bucket_name):
            return bucket_name == "test-images"  # Only images bucket exists

        mock_minio_client.bucket_exists.side_effect = bucket_exists_side_effect

        with patch('app.storage.Minio', return_value=mock_minio_client) as mock_minio:
            # Test initialization
            await storage_manager.initialize()

            # Verify buckets were checked
            assert mock_minio_client.bucket_exists.call_count == 3

            # Verify only non-existing buckets were created
            assert mock_minio_client.make_bucket.call_count == 2  # videos and documents

            # Verify correct buckets were created
            make_bucket_calls = mock_minio_client.make_bucket.call_args_list
            created_buckets = [call[0][0] for call in make_bucket_calls]
            assert "test-videos" in created_buckets
            assert "test-documents" in created_buckets
            assert "test-images" not in created_buckets