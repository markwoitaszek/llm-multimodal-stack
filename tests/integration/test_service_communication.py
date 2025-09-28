"""
Integration tests for service communication
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
import asyncio
from typing import Dict, Any

from tests.conftest import test_services


class TestServiceCommunication:
    """Test cases for inter-service communication"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multimodal_worker_to_retrieval_proxy_communication(self, test_services):
        """Test communication between multimodal worker and retrieval proxy"""
        # Mock services
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        # Test data flow: process content in multimodal worker, then search in retrieval proxy
        with patch('httpx.AsyncClient') as mock_client:
            # Mock multimodal worker response
            mock_response1 = Mock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = {
                "success": True,
                "content_id": "test_content_123",
                "embeddings": [0.1, 0.2, 0.3] * 170,  # 512 dimensions
                "metadata": {"content_type": "text"}
            }

            # Mock retrieval proxy response
            mock_response2 = Mock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {
                "success": True,
                "results": [
                    {
                        "content_id": "test_content_123",
                        "content": "Test content",
                        "score": 0.95
                    }
                ],
                "total_results": 1
            }

            mock_client.return_value.__aenter__.return_value.post.side_effect = [
                mock_response1,  # First call to multimodal worker
                mock_response2   # Second call to retrieval proxy
            ]

            # Test the communication flow
            async with httpx.AsyncClient() as client:
                # Step 1: Process content in multimodal worker
                process_response = await client.post(
                    f"{multimodal_worker['url']}{multimodal_worker['process_endpoint']}",
                    json={
                        "content_type": "text",
                        "content": "Test document for processing",
                        "metadata": {"source": "integration_test"}
                    }
                )

                assert process_response.status_code == 200
                process_data = process_response.json()
                assert process_data["success"] is True
                content_id = process_data["content_id"]

                # Step 2: Search for content in retrieval proxy
                search_response = await client.post(
                    f"{retrieval_proxy['url']}{retrieval_proxy['search_endpoint']}",
                    json={
                        "query": "test document",
                        "content_types": ["text"],
                        "limit": 10
                    }
                )

                assert search_response.status_code == 200
                search_data = search_response.json()
                assert search_data["success"] is True
                assert len(search_data["results"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ai_agents_to_retrieval_proxy_communication(self, test_services):
        """Test communication between AI agents and retrieval proxy"""
        # Mock services
        ai_agents = test_services["ai_agents"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock retrieval proxy response for search
            mock_search_response = Mock()
            mock_search_response.status_code = 200
            mock_search_response.json.return_value = {
                "success": True,
                "results": [
                    {
                        "content_id": "doc_1",
                        "content": "Relevant information for the query",
                        "score": 0.92
                    }
                ],
                "total_results": 1
            }

            # Mock AI agents response
            mock_agent_response = Mock()
            mock_agent_response.status_code = 200
            mock_agent_response.json.return_value = {
                "success": True,
                "result": "Based on the search results, here is the answer...",
                "execution_time_ms": 200
            }

            mock_client.return_value.__aenter__.return_value.post.side_effect = [
                mock_search_response,  # Search call to retrieval proxy
                mock_agent_response   # Agent execution response
            ]

            # Test the communication flow
            async with httpx.AsyncClient() as client:
                # Step 1: Agent uses search tool (which calls retrieval proxy)
                agent_response = await client.post(
                    f"{ai_agents['url']}{ai_agents['agents_endpoint']}/test_agent_123/execute",
                    json={
                        "task": "Search for information about machine learning",
                        "context": {"user_id": "test_user"}
                    }
                )

                assert agent_response.status_code == 200
                agent_data = agent_response.json()
                assert agent_data["success"] is True
                assert "result" in agent_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, test_services):
        """Test complete end-to-end workflow"""
        # Mock all services
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock responses for the complete workflow
            responses = [
                # 1. Process image in multimodal worker
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "img_123",
                    "embeddings": [0.1, 0.2, 0.3] * 170,
                    "metadata": {"content_type": "image", "caption": "A test image"}
                }),
                # 2. Process text in multimodal worker
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "text_123",
                    "embeddings": [0.4, 0.5, 0.6] * 170,
                    "metadata": {"content_type": "text"}
                }),
                # 3. Search in retrieval proxy
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [
                        {"content_id": "img_123", "content": "A test image", "score": 0.95},
                        {"content_id": "text_123", "content": "Test document", "score": 0.87}
                    ],
                    "total_results": 2
                }),
                # 4. Agent execution
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "result": "I found relevant information about your query.",
                    "execution_time_ms": 300
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Test complete workflow
            async with httpx.AsyncClient() as client:
                # Step 1: Process image
                img_response = await client.post(
                    f"{multimodal_worker['url']}/process/image",
                    json={
                        "image_data": "base64_encoded_image",
                        "metadata": {"filename": "test.jpg"}
                    }
                )
                assert img_response.status_code == 200

                # Step 2: Process text
                text_response = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={
                        "text": "This is a test document about machine learning.",
                        "metadata": {"source": "test"}
                    }
                )
                assert text_response.status_code == 200

                # Step 3: Search across all content
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={
                        "query": "machine learning",
                        "content_types": ["text", "image"],
                        "limit": 10
                    }
                )
                assert search_response.status_code == 200

                # Step 4: Agent processes the search results
                agent_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/test_agent/execute",
                    json={
                        "task": "Analyze the search results and provide insights",
                        "context": {"user_id": "test_user"}
                    }
                )
                assert agent_response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, test_services):
        """Test service health monitoring across all services"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock health check responses
            health_responses = [
                Mock(status_code=200, json=lambda: {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}),
                Mock(status_code=200, json=lambda: {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}),
                Mock(status_code=200, json=lambda: {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"})
            ]

            mock_client.return_value.__aenter__.return_value.get.side_effect = health_responses

            # Test health checks for all services
            async with httpx.AsyncClient() as client:
                for service_name, service_config in test_services.items():
                    health_response = await client.get(
                        f"{service_config['url']}{service_config['health_endpoint']}"
                    )
                    assert health_response.status_code == 200
                    health_data = health_response.json()
                    assert health_data["status"] == "healthy"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_propagation_between_services(self, test_services):
        """Test error propagation between services"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock error response from multimodal worker
            mock_error_response = Mock()
            mock_error_response.status_code = 500
            mock_error_response.json.return_value = {
                "success": False,
                "error": "Processing failed"
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_error_response

            # Test error handling
            async with httpx.AsyncClient() as client:
                # This should fail
                response = await client.post(
                    f"{multimodal_worker['url']}{multimodal_worker['process_endpoint']}",
                    json={
                        "content_type": "text",
                        "content": "Test content",
                        "metadata": {}
                    }
                )

                assert response.status_code == 500
                error_data = response.json()
                assert error_data["success"] is False
                assert "error" in error_data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_service_requests(self, test_services):
        """Test concurrent requests to multiple services"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "result": "test"}

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test concurrent requests
            async with httpx.AsyncClient() as client:
                tasks = [
                    client.post(f"{multimodal_worker['url']}/process/text", json={"text": "test1"}),
                    client.post(f"{multimodal_worker['url']}/process/text", json={"text": "test2"}),
                    client.post(f"{retrieval_proxy['url']}/search", json={"query": "test1"}),
                    client.post(f"{retrieval_proxy['url']}/search", json={"query": "test2"})
                ]

                responses = await asyncio.gather(*tasks)

                # All requests should succeed
                for response in responses:
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_consistency_across_services(self, test_services):
        """Test data consistency across services"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock consistent responses
            content_id = "consistent_test_123"
            
            process_response = Mock()
            process_response.status_code = 200
            process_response.json.return_value = {
                "success": True,
                "content_id": content_id,
                "embeddings": [0.1, 0.2, 0.3] * 170,
                "metadata": {"content_type": "text", "source": "consistency_test"}
            }

            search_response = Mock()
            search_response.status_code = 200
            search_response.json.return_value = {
                "success": True,
                "results": [
                    {
                        "content_id": content_id,
                        "content": "Test content for consistency",
                        "score": 0.95,
                        "metadata": {"content_type": "text", "source": "consistency_test"}
                    }
                ],
                "total_results": 1
            }

            mock_client.return_value.__aenter__.return_value.post.side_effect = [
                process_response,
                search_response
            ]

            # Test data consistency
            async with httpx.AsyncClient() as client:
                # Process content
                process_result = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={
                        "text": "Test content for consistency",
                        "metadata": {"source": "consistency_test"}
                    }
                )

                assert process_result.status_code == 200
                process_data = process_result.json()
                stored_content_id = process_data["content_id"]

                # Search for the same content
                search_result = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={
                        "query": "consistency test",
                        "content_types": ["text"],
                        "limit": 10
                    }
                )

                assert search_result.status_code == 200
                search_data = search_result.json()
                
                # Verify data consistency
                assert len(search_data["results"]) > 0
                found_content = search_data["results"][0]
                assert found_content["content_id"] == stored_content_id
                assert found_content["metadata"]["source"] == "consistency_test"
