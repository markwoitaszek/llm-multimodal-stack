"""
Enhanced integration tests for real service communication and data flow
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx
import asyncio
import json
import numpy as np
from typing import Dict, Any, List
import tempfile
import os
from PIL import Image
import io

from tests.conftest import test_services, performance_thresholds


class TestEnhancedServiceCommunication:
    """Enhanced test cases for real inter-service communication"""

    @pytest.fixture
    def real_test_data(self):
        """Create real test data for integration tests"""
        # Create real image data
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        image_data = img_buffer.getvalue()
        
        # Create real text data
        text_data = "This is a comprehensive test document about machine learning, artificial intelligence, and deep learning technologies. It contains multiple paragraphs with detailed information about neural networks, algorithms, and applications."
        
        # Create real audio data (simulated)
        audio_data = b"fake_audio_data_for_testing"
        
        return {
            "image_data": image_data,
            "text_data": text_data,
            "audio_data": audio_data,
            "image_filename": "test_image.jpg",
            "text_filename": "test_document.txt",
            "audio_filename": "test_audio.wav"
        }

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_multimodal_processing_workflow(self, test_services, real_test_data):
        """Test real multimodal processing with actual data flow"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write test files
            image_path = os.path.join(temp_dir, real_test_data["image_filename"])
            with open(image_path, 'wb') as f:
                f.write(real_test_data["image_data"])
            
            text_path = os.path.join(temp_dir, real_test_data["text_filename"])
            with open(text_path, 'w') as f:
                f.write(real_test_data["text_data"])
            
            audio_path = os.path.join(temp_dir, real_test_data["audio_filename"])
            with open(audio_path, 'wb') as f:
                f.write(real_test_data["audio_data"])
            
            # Test real data processing workflow
            async with httpx.AsyncClient(timeout=30.0) as client:
                content_ids = []
                
                # Step 1: Process image with real file
                with open(image_path, 'rb') as f:
                    files = {'file': (real_test_data["image_filename"], f, 'image/jpeg')}
                    data = {'document_name': 'integration_test_image'}
                    
                    response = await client.post(
                        f"{multimodal_worker['url']}/api/v1/process/image",
                        files=files,
                        data=data
                    )
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["success"] is True
                    assert "content_id" in result
                    content_ids.append(result["content_id"])
                
                # Step 2: Process text with real content
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": real_test_data["text_data"],
                        "document_name": real_test_data["text_filename"],
                        "metadata": {"source": "integration_test"}
                    }
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                assert "content_id" in result
                content_ids.append(result["content_id"])
                
                # Step 3: Process audio with real file
                with open(audio_path, 'rb') as f:
                    files = {'file': (real_test_data["audio_filename"], f, 'audio/wav')}
                    data = {'document_name': 'integration_test_audio'}
                    
                    response = await client.post(
                        f"{multimodal_worker['url']}/api/v1/process/audio",
                        files=files,
                        data=data
                    )
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["success"] is True
                    assert "content_id" in result
                    content_ids.append(result["content_id"])
                
                # Step 4: Search across all processed content
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": "machine learning artificial intelligence",
                        "modalities": ["text", "image", "video"],
                        "limit": 10,
                        "score_threshold": 0.5
                    }
                )
                
                assert search_response.status_code == 200
                search_result = search_response.json()
                assert search_result["success"] is True
                assert "results" in search_result
                assert len(search_result["results"]) > 0
                
                # Verify search results contain our processed content
                found_content_ids = {result["document_id"] for result in search_result["results"]}
                assert any(cid in found_content_ids for cid in content_ids)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_agent_tool_integration(self, test_services, real_test_data):
        """Test real agent tool integration with actual service calls"""
        ai_agents = test_services["ai_agents"]
        retrieval_proxy = test_services["retrieval_proxy"]
        multimodal_worker = test_services["multimodal_worker"]
        
        # First, process some content for the agent to search
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Process text content
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": real_test_data["text_data"],
                    "document_name": "agent_test_document.txt",
                    "metadata": {"source": "agent_integration_test"}
                }
            )
            
            assert response.status_code == 200
            process_result = response.json()
            assert process_result["success"] is True
            
            # Create an agent with search capabilities
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Integration Test Agent",
                    "goal": "Search and analyze content using available tools",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 5,
                    "user_id": "integration_test_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            # Execute agent task that uses search tool
            execution_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                json={
                    "task": "Search for information about machine learning and provide a summary",
                    "user_id": "integration_test_user"
                }
            )
            
            assert execution_response.status_code == 200
            execution_result = execution_response.json()
            assert execution_result["success"] is True
            assert "result" in execution_result
            assert len(execution_result["result"]) > 0
            
            # Verify agent used tools (intermediate steps should show tool usage)
            if "intermediate_steps" in execution_result:
                tool_used = any(
                    "search_content" in str(step) for step in execution_result["intermediate_steps"]
                )
                assert tool_used, "Agent should have used search_content tool"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_data_consistency_workflow(self, test_services, real_test_data):
        """Test real data consistency across services with actual data"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        # Test data consistency with real content
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Process content with specific metadata
            test_metadata = {
                "source": "consistency_test",
                "category": "test_document",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0"
            }
            
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": real_test_data["text_data"],
                    "document_name": "consistency_test_document.txt",
                    "metadata": test_metadata
                }
            )
            
            assert response.status_code == 200
            process_result = response.json()
            assert process_result["success"] is True
            content_id = process_result["content_id"]
            
            # Step 2: Search for the content
            search_response = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "machine learning artificial intelligence",
                    "modalities": ["text"],
                    "limit": 10,
                    "filters": {"metadata": {"source": "consistency_test"}}
                }
            )
            
            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["success"] is True
            
            # Step 3: Verify data consistency
            found_content = None
            for result in search_result["results"]:
                if result["document_id"] == content_id:
                    found_content = result
                    break
            
            assert found_content is not None, "Processed content should be found in search results"
            assert found_content["content_type"] == "text"
            
            # Verify metadata consistency
            if "metadata" in found_content:
                assert found_content["metadata"]["source"] == "consistency_test"
                assert found_content["metadata"]["category"] == "test_document"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_performance_benchmarks(self, test_services, real_test_data, performance_thresholds):
        """Test real performance benchmarks with actual data processing"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test multimodal worker performance
            start_time = asyncio.get_event_loop().time()
            
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": real_test_data["text_data"],
                    "document_name": "performance_test.txt",
                    "metadata": {"source": "performance_test"}
                }
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            
            # Verify processing time meets performance thresholds
            assert processing_time < performance_thresholds["text_processing_time"], \
                f"Text processing took {processing_time:.2f}s, expected < {performance_thresholds['text_processing_time']}s"
            
            # Test retrieval proxy performance
            start_time = asyncio.get_event_loop().time()
            
            search_response = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "machine learning",
                    "modalities": ["text"],
                    "limit": 10
                }
            )
            
            search_time = asyncio.get_event_loop().time() - start_time
            
            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["success"] is True
            
            # Verify search time meets performance thresholds
            assert search_time < performance_thresholds["search_response_time"], \
                f"Search took {search_time:.2f}s, expected < {performance_thresholds['search_response_time']}s"
            
            # Test AI agents performance
            start_time = asyncio.get_event_loop().time()
            
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Performance Test Agent",
                    "goal": "Quick response test",
                    "tools": ["generate_text"],
                    "user_id": "performance_test_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            execution_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                json={
                    "task": "Provide a brief summary of machine learning",
                    "user_id": "performance_test_user"
                }
            )
            
            agent_time = asyncio.get_event_loop().time() - start_time
            
            assert execution_response.status_code == 200
            execution_result = execution_response.json()
            assert execution_result["success"] is True
            
            # Verify agent execution time meets performance thresholds
            assert agent_time < performance_thresholds["agent_execution_time"], \
                f"Agent execution took {agent_time:.2f}s, expected < {performance_thresholds['agent_execution_time']}s"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_concurrent_processing(self, test_services, real_test_data):
        """Test real concurrent processing across services"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Create multiple concurrent processing tasks
            tasks = []
            
            # Concurrent text processing
            for i in range(5):
                task = client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": f"{real_test_data['text_data']} - Concurrent test {i}",
                        "document_name": f"concurrent_test_{i}.txt",
                        "metadata": {"source": "concurrent_test", "index": i}
                    }
                )
                tasks.append(task)
            
            # Concurrent search requests
            for i in range(3):
                task = client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": f"machine learning concurrent test {i}",
                        "modalities": ["text"],
                        "limit": 5
                    }
                )
                tasks.append(task)
            
            # Execute all tasks concurrently
            start_time = asyncio.get_event_loop().time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = asyncio.get_event_loop().time() - start_time
            
            # Verify all requests succeeded
            successful_responses = 0
            for response in responses:
                if not isinstance(response, Exception):
                    if hasattr(response, 'status_code') and response.status_code == 200:
                        successful_responses += 1
            
            # At least 80% of requests should succeed
            success_rate = successful_responses / len(tasks)
            assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80% threshold"
            
            # Total time should be reasonable for concurrent processing
            assert total_time < 30.0, f"Concurrent processing took {total_time:.2f}s, expected < 30s"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_error_handling_and_recovery(self, test_services):
        """Test real error handling and recovery scenarios"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Invalid input handling
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": "",  # Empty text should be handled gracefully
                    "document_name": "empty_test.txt"
                }
            )
            
            # Should either succeed with empty content or fail gracefully
            assert response.status_code in [200, 400, 422]
            
            # Test 2: Invalid search parameters
            response = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "",  # Empty query
                    "modalities": ["invalid_modality"],
                    "limit": -1  # Invalid limit
                }
            )
            
            # Should handle invalid parameters gracefully
            assert response.status_code in [200, 400, 422]
            
            # Test 3: Agent with invalid task
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Error Test Agent",
                    "goal": "Test error handling",
                    "tools": ["generate_text"],
                    "user_id": "error_test_user"
                }
            )
            
            if agent_response.status_code == 200:
                agent_result = agent_response.json()
                agent_id = agent_result["agent_id"]
                
                # Test agent with empty task
                execution_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                    json={
                        "task": "",  # Empty task
                        "user_id": "error_test_user"
                    }
                )
                
                # Should handle empty task gracefully
                assert execution_response.status_code in [200, 400, 422]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_data_persistence_and_retrieval(self, test_services, real_test_data):
        """Test real data persistence and retrieval across services"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Process and store content
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": real_test_data["text_data"],
                    "document_name": "persistence_test_document.txt",
                    "metadata": {
                        "source": "persistence_test",
                        "created_at": "2024-01-01T00:00:00Z",
                        "tags": ["test", "persistence", "integration"]
                    }
                }
            )
            
            assert response.status_code == 200
            process_result = response.json()
            assert process_result["success"] is True
            content_id = process_result["content_id"]
            
            # Step 2: Verify content is searchable immediately
            search_response = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "machine learning artificial intelligence",
                    "modalities": ["text"],
                    "limit": 10
                }
            )
            
            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["success"] is True
            
            # Verify our content is found
            found_content = None
            for result in search_result["results"]:
                if result["document_id"] == content_id:
                    found_content = result
                    break
            
            assert found_content is not None, "Stored content should be immediately searchable"
            
            # Step 3: Test content retrieval with specific filters
            filtered_search = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "machine learning",
                    "modalities": ["text"],
                    "limit": 10,
                    "filters": {
                        "metadata": {
                            "source": "persistence_test"
                        }
                    }
                }
            )
            
            assert filtered_search.status_code == 200
            filtered_result = filtered_search.json()
            assert filtered_result["success"] is True
            
            # Verify filtered results contain our content
            found_in_filtered = any(
                result["document_id"] == content_id 
                for result in filtered_result["results"]
            )
            assert found_in_filtered, "Content should be found with metadata filters"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_service_health_and_monitoring(self, test_services):
        """Test real service health monitoring and status checks"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health endpoints for all services
            services_to_test = [
                ("multimodal_worker", multimodal_worker["url"]),
                ("retrieval_proxy", retrieval_proxy["url"]),
                ("ai_agents", ai_agents["url"])
            ]
            
            for service_name, service_url in services_to_test:
                # Test basic health endpoint
                health_response = await client.get(f"{service_url}/health")
                assert health_response.status_code == 200
                health_data = health_response.json()
                assert health_data["status"] == "healthy"
                assert "timestamp" in health_data
                
                # Test service status endpoint (if available)
                try:
                    status_response = await client.get(f"{service_url}/api/v1/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        assert "service" in status_data
                        assert "status" in status_data
                except:
                    # Status endpoint might not be available for all services
                    pass
                
                # Test root endpoint
                root_response = await client.get(f"{service_url}/")
                assert root_response.status_code == 200
                root_data = root_response.json()
                assert "message" in root_data or "service" in root_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_workflow_with_actual_embeddings(self, test_services, real_test_data):
        """Test workflow with actual embedding generation and similarity search"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Process multiple related documents
            documents = [
                "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                "Deep learning uses neural networks with multiple layers to process data.",
                "Natural language processing enables computers to understand human language.",
                "Computer vision allows machines to interpret and analyze visual information."
            ]
            
            content_ids = []
            for i, doc in enumerate(documents):
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": doc,
                        "document_name": f"embedding_test_{i}.txt",
                        "metadata": {"source": "embedding_test", "index": i}
                    }
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                content_ids.append(result["content_id"])
            
            # Step 2: Test similarity search with related queries
            similar_queries = [
                "artificial intelligence algorithms",
                "neural networks deep learning",
                "language understanding computers",
                "visual analysis machines"
            ]
            
            for query in similar_queries:
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": query,
                        "modalities": ["text"],
                        "limit": 5,
                        "score_threshold": 0.3
                    }
                )
                
                assert search_response.status_code == 200
                search_result = search_response.json()
                assert search_result["success"] is True
                assert len(search_result["results"]) > 0
                
                # Verify similarity scores are reasonable
                for result in search_result["results"]:
                    assert 0.0 <= result["score"] <= 1.0, f"Invalid similarity score: {result['score']}"
            
            # Step 3: Test cross-modal similarity (if supported)
            # This would test if image embeddings can be compared with text embeddings
            # For now, we'll test that the system handles different modalities
            cross_modal_response = await client.post(
                f"{retrieval_proxy['url']}/api/v1/search",
                json={
                    "query": "machine learning artificial intelligence",
                    "modalities": ["text", "image", "video"],
                    "limit": 10
                }
            )
            
            assert cross_modal_response.status_code == 200
            cross_modal_result = cross_modal_response.json()
            assert cross_modal_result["success"] is True