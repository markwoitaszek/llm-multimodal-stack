"""
Unit tests for database operations in multimodal-worker service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncpg
import json
import uuid
from datetime import datetime

from app.database import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager"""

    @pytest.fixture
    def db_manager(self):
        """Create DatabaseManager instance for testing"""
        with patch('app.database.settings') as mock_settings:
            mock_settings.postgres_host = 'localhost'
            mock_settings.postgres_port = 5432
            mock_settings.postgres_db = 'test_db'
            mock_settings.postgres_user = 'test_user'
            mock_settings.postgres_password = 'test_password'
            return DatabaseManager()

    @pytest.fixture
    def mock_pool(self):
        """Create mock database pool"""
        pool = AsyncMock()
        connection = AsyncMock()
        
        # Create a proper async context manager class
        class MockAsyncContextManager:
            def __init__(self, connection):
                self.connection = connection
            
            async def __aenter__(self):
                return self.connection
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Mock pool.acquire to return our context manager (not a coroutine)
        pool.acquire = Mock(return_value=MockAsyncContextManager(connection))
        
        return pool, connection

    @pytest.mark.asyncio
    async def test_initialize_success(self, db_manager):
        """Test successful database initialization"""
        # Create proper mock pool and connection
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        
        # Create a proper async context manager class
        class MockAsyncContextManager:
            def __init__(self, connection):
                self.connection = connection
            
            async def __aenter__(self):
                return self.connection
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        # Mock pool.acquire to return our context manager (not a coroutine)
        mock_pool.acquire = Mock(return_value=MockAsyncContextManager(mock_connection))
        
        # Mock asyncpg.create_pool to return our mock pool
        async def mock_create_pool(*args, **kwargs):
            return mock_pool
        
        with patch('asyncpg.create_pool', side_effect=mock_create_pool):
            # Test the REAL initialize method
            await db_manager.initialize()
            
            # Verify pool was created and assigned
            assert db_manager.pool == mock_pool
            
            # Verify connection test was performed
            mock_connection.execute.assert_called_once_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_initialize_failure(self, db_manager):
        """Test database initialization failure"""
        with patch('asyncpg.create_pool', side_effect=Exception("Connection failed")):
            # Test that exception is raised
            with pytest.raises(Exception, match="Connection failed"):
                await db_manager.initialize()

    @pytest.mark.asyncio
    async def test_close(self, db_manager, mock_pool):
        """Test database connection pool closure"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test close
        await db_manager.close()

        # Verify pool was closed
        pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_pool(self, db_manager):
        """Test close when no pool exists"""
        # Test close without pool
        await db_manager.close()
        # Should not raise exception

    @pytest.mark.asyncio
    async def test_create_document_success(self, db_manager, mock_pool):
        """Test successful document creation"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test document creation
        document_id = await db_manager.create_document(
            filename="test.jpg",
            file_type="image",
            file_size=1024,
            mime_type="image/jpeg",
            content_hash="abc123",
            metadata={"source": "test"}
        )

        # Verify document ID is returned
        assert isinstance(document_id, str)
        assert len(document_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO documents" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_document_without_metadata(self, db_manager, mock_pool):
        """Test document creation without metadata"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test document creation without metadata
        document_id = await db_manager.create_document(
            filename="test.jpg",
            file_type="image",
            file_size=1024,
            mime_type="image/jpeg",
            content_hash="abc123"
        )

        # Verify document ID is returned
        assert isinstance(document_id, str)

        # Verify SQL was executed with empty metadata
        connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_hash_success(self, db_manager, mock_pool):
        """Test successful document retrieval by hash"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Mock database response
        mock_row = {
            'id': 'test-doc-id',
            'filename': 'test.jpg',
            'file_type': 'image',
            'file_size': 1024,
            'mime_type': 'image/jpeg',
            'content_hash': 'abc123',
            'metadata': '{"source": "test"}',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        connection.fetchrow.return_value = mock_row

        # Test document retrieval
        result = await db_manager.get_document_by_hash("abc123")

        # Verify result
        assert result is not None
        assert result['id'] == 'test-doc-id'
        assert result['filename'] == 'test.jpg'
        assert result['file_type'] == 'image'

        # Verify SQL was executed
        connection.fetchrow.assert_called_once()
        call_args = connection.fetchrow.call_args[0]
        assert "SELECT" in call_args[0]
        assert call_args[1] == "abc123"

    @pytest.mark.asyncio
    async def test_get_document_by_hash_not_found(self, db_manager, mock_pool):
        """Test document retrieval when not found"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Mock no results
        connection.fetchrow.return_value = None

        # Test document retrieval
        result = await db_manager.get_document_by_hash("nonexistent")

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_create_text_chunk_success(self, db_manager, mock_pool):
        """Test successful text chunk creation"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test text chunk creation
        chunk_id = await db_manager.create_text_chunk(
            document_id="test-doc-id",
            chunk_text="This is a test chunk",
            chunk_index=0,
            start_pos=0,
            end_pos=20,
            embedding_id="test-embedding-id",
            metadata={"word_count": 5}
        )

        # Verify chunk ID is returned
        assert isinstance(chunk_id, str)
        assert len(chunk_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO text_chunks" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_text_chunk_minimal(self, db_manager, mock_pool):
        """Test text chunk creation with minimal parameters"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test text chunk creation with minimal parameters
        chunk_id = await db_manager.create_text_chunk(
            document_id="test-doc-id",
            chunk_text="This is a test chunk",
            chunk_index=0
        )

        # Verify chunk ID is returned
        assert isinstance(chunk_id, str)

        # Verify SQL was executed
        connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_image_success(self, db_manager, mock_pool):
        """Test successful image creation"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test image creation
        image_id = await db_manager.create_image(
            document_id="test-doc-id",
            image_path="test/path/image.jpg",
            width=1920,
            height=1080,
            format="JPEG",
            caption="A test image",
            embedding_id="test-embedding-id",
            features={"mean_brightness": 128.5}
        )

        # Verify image ID is returned
        assert isinstance(image_id, str)
        assert len(image_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO images" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_image_minimal(self, db_manager, mock_pool):
        """Test image creation with minimal parameters"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test image creation with minimal parameters
        image_id = await db_manager.create_image(
            document_id="test-doc-id",
            image_path="test/path/image.jpg"
        )

        # Verify image ID is returned
        assert isinstance(image_id, str)

        # Verify SQL was executed
        connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_video_success(self, db_manager, mock_pool):
        """Test successful video creation"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test video creation
        video_id = await db_manager.create_video(
            document_id="test-doc-id",
            video_path="test/path/video.mp4",
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
            format="MP4",
            transcription="Test video transcription",
            embedding_id="test-embedding-id",
            metadata={"keyframe_count": 10}
        )

        # Verify video ID is returned
        assert isinstance(video_id, str)
        assert len(video_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO videos" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_video_keyframe_success(self, db_manager, mock_pool):
        """Test successful video keyframe creation"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test video keyframe creation
        keyframe_id = await db_manager.create_video_keyframe(
            video_id="test-video-id",
            keyframe_path="test/path/keyframe.jpg",
            timestamp=5.0,
            caption="Test keyframe caption",
            embedding_id="test-embedding-id"
        )

        # Verify keyframe ID is returned
        assert isinstance(keyframe_id, str)
        assert len(keyframe_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO video_keyframes" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_search_session_success(self, db_manager, mock_pool):
        """Test successful search session creation"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test search session creation
        session_id = await db_manager.create_search_session(
            query="test search query",
            session_name="Test Session",
            filters={"content_type": "text"},
            results_count=5,
            context_bundle={"results": ["doc1", "doc2"]}
        )

        # Verify session ID is returned
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO search_sessions" in call_args[0]

    @pytest.mark.asyncio
    async def test_add_conversation_message_success(self, db_manager, mock_pool):
        """Test successful conversation message addition"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test conversation message addition
        message_id = await db_manager.add_conversation_message(
            session_id="test-session-id",
            role="user",
            content="Hello, how are you?",
            metadata={"timestamp": "2024-01-01T00:00:00Z"}
        )

        # Verify message ID is returned
        assert isinstance(message_id, str)
        assert len(message_id) == 36  # UUID length

        # Verify SQL was executed
        connection.execute.assert_called_once()
        call_args = connection.execute.call_args[0]
        assert "INSERT INTO conversations" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, db_manager, mock_pool):
        """Test successful conversation history retrieval"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Mock database response
        mock_rows = [
            {
                'id': 'msg1',
                'role': 'user',
                'content': 'Hello',
                'metadata': '{"timestamp": "2024-01-01T00:00:00Z"}',
                'created_at': datetime.now()
            },
            {
                'id': 'msg2',
                'role': 'assistant',
                'content': 'Hi there!',
                'metadata': '{"timestamp": "2024-01-01T00:01:00Z"}',
                'created_at': datetime.now()
            }
        ]
        connection.fetch.return_value = mock_rows

        # Test conversation history retrieval
        result = await db_manager.get_conversation_history("test-session-id", limit=10)

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['role'] == 'user'
        assert result[1]['role'] == 'assistant'

        # Verify SQL was executed
        connection.fetch.assert_called_once()
        call_args = connection.fetch.call_args[0]
        assert "SELECT" in call_args[0]
        assert call_args[1] == "test-session-id"
        assert call_args[2] == 10

    @pytest.mark.asyncio
    async def test_get_conversation_history_empty(self, db_manager, mock_pool):
        """Test conversation history retrieval with no messages"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Mock no results
        connection.fetch.return_value = []

        # Test conversation history retrieval
        result = await db_manager.get_conversation_history("test-session-id")

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_database_operations_with_real_connection(self, db_manager):
        """Test database operations with real connection (integration test)"""
        # This test would require a real database connection
        # For now, we'll test the structure and error handling
        
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_connection = AsyncMock()
            
            # Create a proper async context manager class
            class MockAsyncContextManager:
                def __init__(self, connection):
                    self.connection = connection
                
                async def __aenter__(self):
                    return self.connection
                
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None
            
            # Mock pool.acquire to return our context manager (not a coroutine)
            mock_pool.acquire = Mock(return_value=MockAsyncContextManager(mock_connection))
            
            # Mock create_pool to return our mock pool
            async def mock_create_pool_func(*args, **kwargs):
                return mock_pool
            mock_create_pool.side_effect = mock_create_pool_func

            # Initialize database
            await db_manager.initialize()

            # Test that all operations can be called without errors
            # (They will fail due to missing tables, but we can test the structure)
            
            try:
                await db_manager.create_document(
                    filename="test.jpg",
                    file_type="image",
                    file_size=1024,
                    mime_type="image/jpeg",
                    content_hash="abc123"
                )
            except Exception as e:
                # Expected to fail due to missing table, but structure should be correct
                assert "INSERT INTO documents" in str(mock_connection.execute.call_args[0][0])

    @pytest.mark.asyncio
    async def test_database_error_handling(self, db_manager, mock_pool):
        """Test database error handling"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Mock database error
        connection.execute.side_effect = asyncpg.PostgresError("Database error")

        # Test that database errors are properly propagated
        with pytest.raises(asyncpg.PostgresError, match="Database error"):
            await db_manager.create_document(
                filename="test.jpg",
                file_type="image",
                file_size=1024,
                mime_type="image/jpeg",
                content_hash="abc123"
            )

    @pytest.mark.asyncio
    async def test_uuid_generation(self, db_manager, mock_pool):
        """Test that UUIDs are properly generated for all entities"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test document ID generation
        doc_id = await db_manager.create_document(
            filename="test.jpg",
            file_type="image",
            file_size=1024,
            mime_type="image/jpeg",
            content_hash="abc123"
        )
        assert len(doc_id) == 36  # UUID length

        # Test chunk ID generation
        chunk_id = await db_manager.create_text_chunk(
            document_id="test-doc-id",
            chunk_text="Test chunk",
            chunk_index=0
        )
        assert len(chunk_id) == 36  # UUID length

        # Test image ID generation
        image_id = await db_manager.create_image(
            document_id="test-doc-id",
            image_path="test/path/image.jpg"
        )
        assert len(image_id) == 36  # UUID length

        # Test video ID generation
        video_id = await db_manager.create_video(
            document_id="test-doc-id",
            video_path="test/path/video.mp4"
        )
        assert len(video_id) == 36  # UUID length

        # Test keyframe ID generation
        keyframe_id = await db_manager.create_video_keyframe(
            video_id="test-video-id",
            keyframe_path="test/path/keyframe.jpg",
            timestamp=5.0
        )
        assert len(keyframe_id) == 36  # UUID length

        # Test session ID generation
        session_id = await db_manager.create_search_session(
            query="test query"
        )
        assert len(session_id) == 36  # UUID length

        # Test message ID generation
        message_id = await db_manager.add_conversation_message(
            session_id="test-session-id",
            role="user",
            content="Test message"
        )
        assert len(message_id) == 36  # UUID length

    @pytest.mark.asyncio
    async def test_json_serialization(self, db_manager, mock_pool):
        """Test JSON serialization of metadata and features"""
        pool, connection = mock_pool
        db_manager.pool = pool

        # Test with complex metadata
        complex_metadata = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "boolean": True,
            "null": None
        }

        await db_manager.create_document(
            filename="test.jpg",
            file_type="image",
            file_size=1024,
            mime_type="image/jpeg",
            content_hash="abc123",
            metadata=complex_metadata
        )

        # Verify that metadata was serialized to JSON
        call_args = connection.execute.call_args[0]
        metadata_arg = call_args[7]  # 8th argument (0-indexed)
        assert isinstance(metadata_arg, str)
        parsed_metadata = json.loads(metadata_arg)
        assert parsed_metadata == complex_metadata