"""
Unit tests for retrieval engine in retrieval-proxy service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
import httpx
from datetime import datetime

from app.retrieval import RetrievalEngine


class TestRetrievalEngine:
    """Test cases for RetrievalEngine"""

    @pytest.fixture
    def mock_managers(self):
        """Create mock managers for testing"""
        db_manager = AsyncMock()
        vector_manager = Mock()
        return db_manager, vector_manager

    @pytest.fixture
    def retrieval_engine(self, mock_managers):
        """Create RetrievalEngine instance for testing"""
        db_manager, vector_manager = mock_managers
        with patch('app.retrieval.settings') as mock_settings:
            mock_settings.default_search_limit = 10
            mock_settings.max_search_limit = 100
            mock_settings.similarity_threshold = 0.7
            mock_settings.multimodal_worker_url = "http://localhost:8001"
            return RetrievalEngine(db_manager, vector_manager)

    @pytest.fixture
    def mock_vector_results(self):
        """Create mock vector search results"""
        return [
            {
                'id': 'embedding1',
                'score': 0.95,
                'payload': {'content_type': 'text', 'document_id': 'doc1'},
                'modality': 'text',
                'collection': 'test-text'
            },
            {
                'id': 'embedding2',
                'score': 0.87,
                'payload': {'content_type': 'image', 'document_id': 'doc2'},
                'modality': 'image',
                'collection': 'test-image'
            }
        ]

    @pytest.fixture
    def mock_content_info(self):
        """Create mock content information"""
        return {
            'content_type': 'text',
            'content': 'This is test content',
            'document_id': 'doc1',
            'filename': 'test.txt',
            'file_type': 'text',
            'created_at': '2024-01-01T00:00:00Z'
        }

    @pytest.mark.asyncio
    async def test_search_success(self, retrieval_engine, mock_vector_results, mock_content_info):
        """Test successful search operation"""
        # Mock dependencies
        retrieval_engine.vector_manager.search_hybrid.return_value = mock_vector_results
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = mock_content_info
        retrieval_engine.db_manager.create_search_session.return_value = "session123"

        # Mock query embedding generation
        with patch.object(retrieval_engine, 'generate_query_embedding') as mock_embedding:
            mock_embedding.return_value = np.random.rand(384)

            # Test search
            result = await retrieval_engine.search(
                query="test query",
                modalities=['text', 'image'],
                limit=10,
                filters={'content_types': ['text']},
                score_threshold=0.8
            )

            # Verify result structure
            assert "session_id" in result
            assert "query" in result
            assert "modalities" in result
            assert "results_count" in result
            assert "results" in result
            assert "context_bundle" in result
            assert "metadata" in result

            # Verify search parameters
            assert result["query"] == "test query"
            assert result["modalities"] == ['text', 'image']
            assert result["results_count"] == 1  # Only text result after filtering

            # Verify vector search was called
            retrieval_engine.vector_manager.search_hybrid.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_default_parameters(self, retrieval_engine, mock_vector_results, mock_content_info):
        """Test search with default parameters"""
        # Mock dependencies
        retrieval_engine.vector_manager.search_hybrid.return_value = mock_vector_results
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = mock_content_info
        retrieval_engine.db_manager.create_search_session.return_value = "session123"

        # Mock query embedding generation
        with patch.object(retrieval_engine, 'generate_query_embedding') as mock_embedding:
            mock_embedding.return_value = np.random.rand(384)

            # Test search with minimal parameters
            result = await retrieval_engine.search(query="test query")

            # Verify default values were used
            assert result["modalities"] == ['text', 'image', 'video']  # Default modalities
            assert result["results_count"] == 2  # All results included

    @pytest.mark.asyncio
    async def test_search_with_limit_exceeded(self, retrieval_engine, mock_vector_results, mock_content_info):
        """Test search with limit exceeding maximum"""
        # Mock dependencies
        retrieval_engine.vector_manager.search_hybrid.return_value = mock_vector_results
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = mock_content_info
        retrieval_engine.db_manager.create_search_session.return_value = "session123"

        # Mock query embedding generation
        with patch.object(retrieval_engine, 'generate_query_embedding') as mock_embedding:
            mock_embedding.return_value = np.random.rand(384)

            # Test search with limit exceeding maximum
            result = await retrieval_engine.search(query="test query", limit=200)

            # Verify limit was capped
            retrieval_engine.vector_manager.search_hybrid.assert_called_once()
            call_args = retrieval_engine.vector_manager.search_hybrid.call_args
            assert call_args[1]['limit'] == 200  # 2 * 100 (max limit)

    @pytest.mark.asyncio
    async def test_generate_query_embedding_success(self, retrieval_engine):
        """Test successful query embedding generation"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3] * 128}  # 384 dimensions
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test embedding generation
            embedding = await retrieval_engine.generate_query_embedding("test query")

            # Verify result
            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (384,)
            assert embedding[0] == 0.1

    @pytest.mark.asyncio
    async def test_generate_query_embedding_failure(self, retrieval_engine):
        """Test query embedding generation failure"""
        # Mock HTTP failure
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.RequestError("Connection failed")

            # Test embedding generation
            embedding = await retrieval_engine.generate_query_embedding("test query")

            # Verify fallback result
            assert isinstance(embedding, np.ndarray)
            assert embedding.shape == (384,)
            assert np.all(embedding == 0)  # Zero vector fallback

    @pytest.mark.asyncio
    async def test_enrich_search_results_success(self, retrieval_engine, mock_vector_results, mock_content_info):
        """Test successful search result enrichment"""
        # Mock database response
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = mock_content_info

        # Mock artifact links
        with patch.object(retrieval_engine, 'get_artifact_links') as mock_artifacts:
            mock_artifacts.return_value = {"view_url": "/api/v1/artifacts/text/doc1"}

            # Test result enrichment
            enriched_results = await retrieval_engine.enrich_search_results(mock_vector_results)

            # Verify results
            assert len(enriched_results) == 2
            assert enriched_results[0]['embedding_id'] == 'embedding1'
            assert enriched_results[0]['score'] == 0.95
            assert enriched_results[0]['content_type'] == 'text'
            assert enriched_results[0]['content'] == 'This is test content'
            assert enriched_results[0]['document_id'] == 'doc1'
            assert enriched_results[0]['filename'] == 'test.txt'

    @pytest.mark.asyncio
    async def test_enrich_search_results_with_missing_content(self, retrieval_engine, mock_vector_results):
        """Test search result enrichment with missing content"""
        # Mock database response - no content found
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = None

        # Test result enrichment
        enriched_results = await retrieval_engine.enrich_search_results(mock_vector_results)

        # Verify results - should be empty due to missing content
        assert len(enriched_results) == 0

    @pytest.mark.asyncio
    async def test_enrich_search_results_with_database_error(self, retrieval_engine, mock_vector_results):
        """Test search result enrichment with database error"""
        # Mock database error
        retrieval_engine.db_manager.get_content_by_embedding_id.side_effect = Exception("Database error")

        # Test result enrichment
        enriched_results = await retrieval_engine.enrich_search_results(mock_vector_results)

        # Verify results - should be empty due to error
        assert len(enriched_results) == 0

    def test_apply_filters_success(self, retrieval_engine):
        """Test successful filter application"""
        # Test data
        results = [
            {
                'file_type': 'text',
                'content_type': 'text',
                'score': 0.95
            },
            {
                'file_type': 'image',
                'content_type': 'image',
                'score': 0.87
            },
            {
                'file_type': 'text',
                'content_type': 'text',
                'score': 0.75
            }
        ]

        # Test filters
        filters = {
            'file_types': ['text'],
            'content_types': ['text'],
            'min_score': 0.8
        }

        # Test filter application
        filtered_results = retrieval_engine.apply_filters(results, filters)

        # Verify results
        assert len(filtered_results) == 1
        assert filtered_results[0]['file_type'] == 'text'
        assert filtered_results[0]['content_type'] == 'text'
        assert filtered_results[0]['score'] == 0.95

    def test_apply_filters_with_no_filters(self, retrieval_engine):
        """Test filter application with no filters"""
        # Test data
        results = [
            {'file_type': 'text', 'content_type': 'text', 'score': 0.95},
            {'file_type': 'image', 'content_type': 'image', 'score': 0.87}
        ]

        # Test with no filters
        filtered_results = retrieval_engine.apply_filters(results, {})

        # Verify all results are returned
        assert len(filtered_results) == 2

    def test_apply_filters_with_empty_results(self, retrieval_engine):
        """Test filter application with empty results"""
        # Test with empty results
        filtered_results = retrieval_engine.apply_filters([], {'file_types': ['text']})

        # Verify empty results
        assert len(filtered_results) == 0

    @pytest.mark.asyncio
    async def test_create_context_bundle_success(self, retrieval_engine):
        """Test successful context bundle creation"""
        # Test data
        results = [
            {
                'content_type': 'text',
                'content': 'This is test text content',
                'filename': 'test.txt',
                'chunk_index': 0,
                'score': 0.95
            },
            {
                'content_type': 'image',
                'content': 'A test image caption',
                'filename': 'test.jpg',
                'dimensions': {'width': 1920, 'height': 1080},
                'score': 0.87
            }
        ]

        # Test context bundle creation
        context_bundle = await retrieval_engine.create_context_bundle(results, "test query")

        # Verify result structure
        assert "query" in context_bundle
        assert "sections" in context_bundle
        assert "unified_context" in context_bundle
        assert "total_results" in context_bundle
        assert "context_length" in context_bundle
        assert "citations" in context_bundle

        # Verify query
        assert context_bundle["query"] == "test query"

        # Verify sections
        assert len(context_bundle["sections"]) == 2  # text and image sections
        assert context_bundle["sections"][0]["type"] == "text"
        assert context_bundle["sections"][1]["type"] == "image"

        # Verify total results
        assert context_bundle["total_results"] == 2

    @pytest.mark.asyncio
    async def test_create_context_bundle_with_empty_results(self, retrieval_engine):
        """Test context bundle creation with empty results"""
        # Test with empty results
        context_bundle = await retrieval_engine.create_context_bundle([], "test query")

        # Verify result structure
        assert context_bundle["query"] == "test query"
        assert len(context_bundle["sections"]) == 0
        assert context_bundle["total_results"] == 0

    def test_create_text_context(self, retrieval_engine):
        """Test text context creation"""
        # Test data
        text_results = [
            {
                'content': 'This is the first chunk of text content.',
                'filename': 'test.txt',
                'chunk_index': 0
            },
            {
                'content': 'This is the second chunk of text content.',
                'filename': 'test.txt',
                'chunk_index': 1
            }
        ]

        # Test text context creation
        context = retrieval_engine.create_text_context(text_results)

        # Verify result
        assert "[1]" in context
        assert "[2]" in context
        assert "This is the first chunk" in context
        assert "This is the second chunk" in context
        assert "Source: test.txt" in context

    def test_create_image_context(self, retrieval_engine):
        """Test image context creation"""
        # Test data
        image_results = [
            {
                'content': 'A test image caption',
                'filename': 'test.jpg',
                'dimensions': {'width': 1920, 'height': 1080},
                'artifacts': {'view_url': '/api/v1/artifacts/image/doc1'}
            }
        ]

        # Test image context creation
        context = retrieval_engine.create_image_context(image_results)

        # Verify result
        assert "[IMG-1]" in context
        assert "A test image caption" in context
        assert "Source: test.jpg" in context
        assert "Size: 1920x1080" in context
        assert "View: /api/v1/artifacts/image/doc1" in context

    def test_create_video_context(self, retrieval_engine):
        """Test video context creation"""
        # Test data
        video_results = [
            {
                'transcription': 'This is a test video transcription with some content.',
                'filename': 'test.mp4',
                'duration': 120.5,
                'artifacts': {'view_url': '/api/v1/artifacts/video/doc1'}
            }
        ]

        # Test video context creation
        context = retrieval_engine.create_video_context(video_results)

        # Verify result
        assert "[VID-1]" in context
        assert "This is a test video transcription" in context
        assert "Source: test.mp4" in context
        assert "Duration: 120.5 seconds" in context
        assert "Watch: /api/v1/artifacts/video/doc1" in context

    def test_create_keyframe_context(self, retrieval_engine):
        """Test keyframe context creation"""
        # Test data
        keyframe_results = [
            {
                'content': 'A test keyframe caption',
                'filename': 'test.mp4',
                'timestamp': 5.0,
                'artifacts': {'view_url': '/api/v1/artifacts/keyframe/kf1'}
            }
        ]

        # Test keyframe context creation
        context = retrieval_engine.create_keyframe_context(keyframe_results)

        # Verify result
        assert "[KF-1]" in context
        assert "A test keyframe caption" in context
        assert "Source: test.mp4" in context
        assert "Video Keyframe (5.0s)" in context
        assert "View: /api/v1/artifacts/keyframe/kf1" in context

    def test_create_unified_context(self, retrieval_engine):
        """Test unified context creation"""
        # Test data
        sections = [
            {
                'type': 'text',
                'title': 'Relevant Text Content',
                'content': 'Test text content',
                'count': 2
            },
            {
                'type': 'image',
                'title': 'Relevant Images',
                'content': 'Test image content',
                'count': 1
            }
        ]

        # Test unified context creation
        context = retrieval_engine.create_unified_context(sections, "test query")

        # Verify result
        assert "# Search Results for: test query" in context
        assert "Found 3 relevant items across 2 content types" in context
        assert "## Relevant Text Content (2 items)" in context
        assert "## Relevant Images (1 items)" in context
        assert "Test text content" in context
        assert "Test image content" in context

    def test_generate_citations(self, retrieval_engine):
        """Test citation generation"""
        # Test data
        content_info = {
            'filename': 'test.txt',
            'content_type': 'text',
            'document_id': 'doc1',
            'created_at': '2024-01-01T00:00:00Z'
        }

        # Test citation generation
        citations = retrieval_engine.generate_citations(content_info)

        # Verify result
        assert citations['source'] == 'test.txt'
        assert citations['type'] == 'text'
        assert citations['document_id'] == 'doc1'
        assert citations['created_at'] == '2024-01-01T00:00:00Z'

    @pytest.mark.asyncio
    async def test_get_artifact_links_for_image(self, retrieval_engine):
        """Test artifact link generation for image content"""
        # Test data
        content_info = {
            'content_type': 'image',
            'document_id': 'doc1',
            'image_path': 'test/path/image.jpg'
        }

        # Test artifact link generation
        artifacts = await retrieval_engine.get_artifact_links(content_info)

        # Verify result
        assert artifacts['view_url'] == "/api/v1/artifacts/image/doc1"
        assert artifacts['download_url'] == "/api/v1/artifacts/download/doc1"

    @pytest.mark.asyncio
    async def test_get_artifact_links_for_video(self, retrieval_engine):
        """Test artifact link generation for video content"""
        # Test data
        content_info = {
            'content_type': 'video',
            'document_id': 'doc1',
            'video_path': 'test/path/video.mp4'
        }

        # Test artifact link generation
        artifacts = await retrieval_engine.get_artifact_links(content_info)

        # Verify result
        assert artifacts['view_url'] == "/api/v1/artifacts/video/doc1"
        assert artifacts['download_url'] == "/api/v1/artifacts/download/doc1"

    @pytest.mark.asyncio
    async def test_get_artifact_links_for_keyframe(self, retrieval_engine):
        """Test artifact link generation for keyframe content"""
        # Test data
        content_info = {
            'content_type': 'keyframe',
            'id': 'kf1',
            'keyframe_path': 'test/path/keyframe.jpg'
        }

        # Test artifact link generation
        artifacts = await retrieval_engine.get_artifact_links(content_info)

        # Verify result
        assert artifacts['view_url'] == "/api/v1/artifacts/keyframe/kf1"

    @pytest.mark.asyncio
    async def test_get_artifact_links_for_unknown_type(self, retrieval_engine):
        """Test artifact link generation for unknown content type"""
        # Test data
        content_info = {
            'content_type': 'unknown',
            'document_id': 'doc1'
        }

        # Test artifact link generation
        artifacts = await retrieval_engine.get_artifact_links(content_info)

        # Verify result
        assert artifacts == {}

    def test_extract_all_citations(self, retrieval_engine):
        """Test citation extraction from results"""
        # Test data
        results = [
            {
                'citations': {
                    'source': 'test1.txt',
                    'type': 'text'
                }
            },
            {
                'citations': {
                    'source': 'test2.jpg',
                    'type': 'image'
                }
            },
            {
                'content': 'no citations'
            }
        ]

        # Test citation extraction
        citations = retrieval_engine.extract_all_citations(results)

        # Verify result
        assert len(citations) == 2
        assert citations[0]['source'] == 'test1.txt'
        assert citations[1]['source'] == 'test2.jpg'

    @pytest.mark.asyncio
    async def test_search_with_context_bundle_creation_failure(self, retrieval_engine, mock_vector_results, mock_content_info):
        """Test search with context bundle creation failure"""
        # Mock dependencies
        retrieval_engine.vector_manager.search_hybrid.return_value = mock_vector_results
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = mock_content_info
        retrieval_engine.db_manager.create_search_session.return_value = "session123"

        # Mock query embedding generation
        with patch.object(retrieval_engine, 'generate_query_embedding') as mock_embedding:
            mock_embedding.return_value = np.random.rand(384)

            # Mock context bundle creation failure
            with patch.object(retrieval_engine, 'create_context_bundle') as mock_context:
                mock_context.side_effect = Exception("Context creation failed")

                # Test search
                result = await retrieval_engine.search(query="test query")

                # Verify result still contains error information
                assert "context_bundle" in result
                assert "error" in result["context_bundle"]

    @pytest.mark.asyncio
    async def test_search_with_database_session_creation_failure(self, retrieval_engine, mock_vector_results, mock_content_info):
        """Test search with database session creation failure"""
        # Mock dependencies
        retrieval_engine.vector_manager.search_hybrid.return_value = mock_vector_results
        retrieval_engine.db_manager.get_content_by_embedding_id.return_value = mock_content_info
        retrieval_engine.db_manager.create_search_session.side_effect = Exception("Session creation failed")

        # Mock query embedding generation
        with patch.object(retrieval_engine, 'generate_query_embedding') as mock_embedding:
            mock_embedding.return_value = np.random.rand(384)

            # Test search - should still work but without session_id
            result = await retrieval_engine.search(query="test query")

            # Verify result structure
            assert "session_id" not in result or result["session_id"] is None
            assert "query" in result
            assert "results" in result