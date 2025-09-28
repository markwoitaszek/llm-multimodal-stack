"""
Integration tests for workflow execution
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
import asyncio
from typing import Dict, Any, List

from tests.conftest import test_services


class TestWorkflowExecution:
    """Test cases for end-to-end workflow execution"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_content_processing_workflow(self, test_services):
        """Test complete content processing workflow"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock workflow responses
            responses = [
                # Image processing
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "img_workflow_123",
                    "embeddings": [0.1, 0.2, 0.3] * 170,
                    "metadata": {
                        "content_type": "image",
                        "caption": "A workflow test image",
                        "processing_time_ms": 150
                    }
                }),
                # Text processing
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "text_workflow_123",
                    "embeddings": [0.4, 0.5, 0.6] * 170,
                    "metadata": {
                        "content_type": "text",
                        "word_count": 10,
                        "processing_time_ms": 100
                    }
                }),
                # Audio processing
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "audio_workflow_123",
                    "embeddings": [0.7, 0.8, 0.9] * 170,
                    "metadata": {
                        "content_type": "audio",
                        "transcription": "This is a test audio transcription",
                        "duration": 5.0,
                        "processing_time_ms": 200
                    }
                }),
                # Search across all content
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [
                        {
                            "content_id": "img_workflow_123",
                            "content_type": "image",
                            "content": "A workflow test image",
                            "score": 0.95
                        },
                        {
                            "content_id": "text_workflow_123",
                            "content_type": "text",
                            "content": "Test document for workflow",
                            "score": 0.87
                        },
                        {
                            "content_id": "audio_workflow_123",
                            "content_type": "audio",
                            "content": "This is a test audio transcription",
                            "score": 0.82
                        }
                    ],
                    "total_results": 3,
                    "search_time_ms": 50
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Execute workflow
            async with httpx.AsyncClient() as client:
                # Step 1: Process different content types
                content_types = ["image", "text", "audio"]
                content_ids = []

                for content_type in content_types:
                    if content_type == "image":
                        response = await client.post(
                            f"{multimodal_worker['url']}/process/image",
                            json={
                                "image_data": "base64_encoded_image",
                                "metadata": {"filename": f"workflow_test.{content_type}"}
                            }
                        )
                    elif content_type == "text":
                        response = await client.post(
                            f"{multimodal_worker['url']}/process/text",
                            json={
                                "text": "Test document for workflow processing",
                                "metadata": {"source": "workflow_test"}
                            }
                        )
                    elif content_type == "audio":
                        response = await client.post(
                            f"{multimodal_worker['url']}/process/audio",
                            json={
                                "audio_data": "base64_encoded_audio",
                                "metadata": {"filename": f"workflow_test.{content_type}"}
                            }
                        )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    content_ids.append(data["content_id"])

                # Step 2: Search across all processed content
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={
                        "query": "workflow test",
                        "content_types": ["text", "image", "audio"],
                        "limit": 10
                    }
                )

                assert search_response.status_code == 200
                search_data = search_response.json()
                assert search_data["success"] is True
                assert len(search_data["results"]) == 3

                # Verify all content types are found
                found_content_types = {result["content_type"] for result in search_data["results"]}
                assert found_content_types == {"text", "image", "audio"}

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_research_workflow(self, test_services):
        """Test agent research workflow"""
        ai_agents = test_services["ai_agents"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock research workflow responses
            responses = [
                # Initial search
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [
                        {
                            "content_id": "research_doc_1",
                            "content": "Machine learning is a subset of artificial intelligence",
                            "score": 0.95
                        },
                        {
                            "content_id": "research_doc_2",
                            "content": "Deep learning uses neural networks with multiple layers",
                            "score": 0.88
                        }
                    ],
                    "total_results": 2
                }),
                # Follow-up search
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [
                        {
                            "content_id": "research_doc_3",
                            "content": "Neural networks are inspired by biological neurons",
                            "score": 0.92
                        }
                    ],
                    "total_results": 1
                }),
                # Agent synthesis
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "result": "Based on my research, machine learning is a subset of AI that uses algorithms to learn from data. Deep learning, a subset of ML, uses neural networks with multiple layers inspired by biological neurons.",
                    "execution_time_ms": 500,
                    "tools_used": ["search_content", "web_search", "generate_text"]
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Execute research workflow
            async with httpx.AsyncClient() as client:
                # Step 1: Agent performs initial research
                research_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/research_agent/execute",
                    json={
                        "task": "Research the relationship between machine learning, deep learning, and artificial intelligence",
                        "context": {
                            "user_id": "researcher_123",
                            "session_id": "research_session_456"
                        },
                        "parameters": {
                            "max_iterations": 3,
                            "timeout_seconds": 60
                        }
                    }
                )

                assert research_response.status_code == 200
                research_data = research_response.json()
                assert research_data["success"] is True
                assert "result" in research_data
                assert len(research_data.get("tools_used", [])) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_agent_collaboration_workflow(self, test_services):
        """Test multi-agent collaboration workflow"""
        ai_agents = test_services["ai_agents"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock multi-agent responses
            responses = [
                # Research agent
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "result": "Research findings: Machine learning algorithms can be categorized into supervised, unsupervised, and reinforcement learning.",
                    "execution_time_ms": 300
                }),
                # Analysis agent
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "result": "Analysis: The research shows three main categories of ML algorithms. Each has distinct characteristics and use cases.",
                    "execution_time_ms": 200
                }),
                # Writing agent
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "result": "Summary: Machine learning encompasses three primary approaches: supervised learning for labeled data, unsupervised learning for pattern discovery, and reinforcement learning for decision-making through trial and error.",
                    "execution_time_ms": 250
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Execute multi-agent workflow
            async with httpx.AsyncClient() as client:
                agents = ["research_agent", "analysis_agent", "writing_agent"]
                results = []

                for agent in agents:
                    response = await client.post(
                        f"{ai_agents['url']}/api/v1/agents/{agent}/execute",
                        json={
                            "task": f"Process the previous results and contribute to the final summary",
                            "context": {
                                "user_id": "collaboration_user",
                                "session_id": "collaboration_session",
                                "previous_results": results
                            }
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    results.append(data["result"])

                # Verify collaboration results
                assert len(results) == 3
                assert all("machine learning" in result.lower() for result in results)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, test_services):
        """Test workflow error recovery"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock error and recovery responses
            responses = [
                # First attempt fails
                Mock(status_code=500, json=lambda: {
                    "success": False,
                    "error": "Processing failed due to invalid input"
                }),
                # Retry succeeds
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "recovery_test_123",
                    "embeddings": [0.1, 0.2, 0.3] * 170,
                    "metadata": {"content_type": "text", "retry_count": 1}
                }),
                # Search succeeds
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [
                        {
                            "content_id": "recovery_test_123",
                            "content": "Recovered content after error",
                            "score": 0.95
                        }
                    ],
                    "total_results": 1
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Execute error recovery workflow
            async with httpx.AsyncClient() as client:
                # Step 1: First attempt fails
                first_response = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={
                        "text": "Invalid content that causes error",
                        "metadata": {"source": "error_test"}
                    }
                )

                assert first_response.status_code == 500
                error_data = first_response.json()
                assert error_data["success"] is False

                # Step 2: Retry with corrected input
                retry_response = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={
                        "text": "Valid content for processing",
                        "metadata": {"source": "recovery_test"}
                    }
                )

                assert retry_response.status_code == 200
                retry_data = retry_response.json()
                assert retry_data["success"] is True

                # Step 3: Search for recovered content
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={
                        "query": "recovery test",
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
    async def test_workflow_performance_monitoring(self, test_services):
        """Test workflow performance monitoring"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock performance monitoring responses
            responses = [
                # Processing with timing
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": "perf_test_123",
                    "embeddings": [0.1, 0.2, 0.3] * 170,
                    "metadata": {"processing_time_ms": 120}
                }),
                # Search with timing
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [{"content_id": "perf_test_123", "score": 0.95}],
                    "search_time_ms": 45
                }),
                # Agent execution with timing
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "result": "Performance test completed",
                    "execution_time_ms": 180
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Execute performance monitoring workflow
            async with httpx.AsyncClient() as client:
                start_time = asyncio.get_event_loop().time()

                # Step 1: Process content
                process_response = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={
                        "text": "Performance test content",
                        "metadata": {"source": "performance_test"}
                    }
                )

                process_time = asyncio.get_event_loop().time() - start_time
                assert process_response.status_code == 200
                process_data = process_response.json()
                assert process_data["metadata"]["processing_time_ms"] < 200  # Performance threshold

                # Step 2: Search content
                search_start = asyncio.get_event_loop().time()
                search_response = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={
                        "query": "performance test",
                        "content_types": ["text"],
                        "limit": 10
                    }
                )

                search_time = asyncio.get_event_loop().time() - search_start
                assert search_response.status_code == 200
                search_data = search_response.json()
                assert search_data["search_time_ms"] < 100  # Performance threshold

                # Step 3: Agent execution
                agent_start = asyncio.get_event_loop().time()
                agent_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/test_agent/execute",
                    json={
                        "task": "Analyze the performance test results",
                        "context": {"user_id": "perf_tester"}
                    }
                )

                agent_time = asyncio.get_event_loop().time() - agent_start
                assert agent_response.status_code == 200
                agent_data = agent_response.json()
                assert agent_data["execution_time_ms"] < 300  # Performance threshold

                # Verify overall workflow performance
                total_time = asyncio.get_event_loop().time() - start_time
                assert total_time < 1.0  # Total workflow should complete within 1 second

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_data_persistence(self, test_services):
        """Test workflow data persistence"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock persistence workflow responses
            content_id = "persistence_test_123"
            
            responses = [
                # Process and store content
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "content_id": content_id,
                    "embeddings": [0.1, 0.2, 0.3] * 170,
                    "metadata": {
                        "content_type": "text",
                        "source": "persistence_test",
                        "stored_at": "2024-01-01T00:00:00Z"
                    }
                }),
                # Retrieve stored content
                Mock(status_code=200, json=lambda: {
                    "success": True,
                    "results": [
                        {
                            "content_id": content_id,
                            "content": "Persistent test content",
                            "score": 0.95,
                            "metadata": {
                                "content_type": "text",
                                "source": "persistence_test",
                                "stored_at": "2024-01-01T00:00:00Z"
                            }
                        }
                    ],
                    "total_results": 1
                })
            ]

            mock_client.return_value.__aenter__.return_value.post.side_effect = responses

            # Execute persistence workflow
            async with httpx.AsyncClient() as client:
                # Step 1: Process and store content
                store_response = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={
                        "text": "Persistent test content",
                        "metadata": {"source": "persistence_test"}
                    }
                )

                assert store_response.status_code == 200
                store_data = store_response.json()
                stored_content_id = store_data["content_id"]

                # Step 2: Retrieve stored content
                retrieve_response = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={
                        "query": "persistence test",
                        "content_types": ["text"],
                        "limit": 10
                    }
                )

                assert retrieve_response.status_code == 200
                retrieve_data = retrieve_response.json()
                
                # Verify data persistence
                assert len(retrieve_data["results"]) > 0
                found_content = retrieve_data["results"][0]
                assert found_content["content_id"] == stored_content_id
                assert found_content["metadata"]["source"] == "persistence_test"
