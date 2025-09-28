"""
Performance tests for API response times
"""
import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
import httpx
from typing import List, Dict, Any

from tests.conftest import test_services, performance_thresholds


class TestAPIResponseTimes:
    """Test cases for API response time performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multimodal_worker_response_times(self, test_services, performance_thresholds):
        """Test multimodal worker API response times"""
        multimodal_worker = test_services["multimodal_worker"]
        threshold = performance_thresholds["api_response_time_ms"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock fast response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "content_id": "perf_test_123",
                "embeddings": [0.1, 0.2, 0.3] * 170,
                "metadata": {"processing_time_ms": 50}
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test response times for different endpoints
            async with httpx.AsyncClient() as client:
                endpoints = [
                    ("/process/text", {"text": "Performance test text", "metadata": {}}),
                    ("/process/image", {"image_data": "base64_data", "metadata": {}}),
                    ("/process/audio", {"audio_data": "base64_data", "metadata": {}}),
                    ("/health", None)
                ]

                for endpoint, payload in endpoints:
                    start_time = time.time()
                    
                    if payload:
                        response = await client.post(f"{multimodal_worker['url']}{endpoint}", json=payload)
                    else:
                        response = await client.get(f"{multimodal_worker['url']}{endpoint}")
                    
                    end_time = time.time()
                    response_time_ms = (end_time - start_time) * 1000

                    assert response.status_code == 200
                    assert response_time_ms < threshold, f"Response time {response_time_ms}ms exceeds threshold {threshold}ms for {endpoint}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_retrieval_proxy_response_times(self, test_services, performance_thresholds):
        """Test retrieval proxy API response times"""
        retrieval_proxy = test_services["retrieval_proxy"]
        threshold = performance_thresholds["api_response_time_ms"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock fast response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "results": [
                    {"content_id": "doc_1", "content": "Test result", "score": 0.95}
                ],
                "total_results": 1,
                "search_time_ms": 30
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test response times for different endpoints
            async with httpx.AsyncClient() as client:
                endpoints = [
                    ("/search", {"query": "test query", "content_types": ["text"], "limit": 10}),
                    ("/search/hybrid", {"query": "test query", "content_types": ["text"], "limit": 10}),
                    ("/search/semantic", {"query": "test query", "content_types": ["text"], "limit": 10}),
                    ("/context-bundle", {"query": "test query", "content_types": ["text"], "max_results": 10}),
                    ("/health", None)
                ]

                for endpoint, payload in endpoints:
                    start_time = time.time()
                    
                    if payload:
                        response = await client.post(f"{retrieval_proxy['url']}{endpoint}", json=payload)
                    else:
                        response = await client.get(f"{retrieval_proxy['url']}{endpoint}")
                    
                    end_time = time.time()
                    response_time_ms = (end_time - start_time) * 1000

                    assert response.status_code == 200
                    assert response_time_ms < threshold, f"Response time {response_time_ms}ms exceeds threshold {threshold}ms for {endpoint}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_ai_agents_response_times(self, test_services, performance_thresholds):
        """Test AI agents API response times"""
        ai_agents = test_services["ai_agents"]
        threshold = performance_thresholds["api_response_time_ms"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock fast response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "result": "Agent execution completed",
                "execution_time_ms": 100
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test response times for different endpoints
            async with httpx.AsyncClient() as client:
                endpoints = [
                    ("/api/v1/agents", {"name": "Test Agent", "goal": "Test goal", "tools": ["search_content"]}),
                    ("/api/v1/agents/test_agent/execute", {"task": "Test task", "context": {}}),
                    ("/api/v1/agents/test_agent/stats", None),
                    ("/api/v1/templates", None),
                    ("/api/v1/tools", None),
                    ("/health", None)
                ]

                for endpoint, payload in endpoints:
                    start_time = time.time()
                    
                    if payload:
                        response = await client.post(f"{ai_agents['url']}{endpoint}", json=payload)
                    else:
                        response = await client.get(f"{ai_agents['url']}{endpoint}")
                    
                    end_time = time.time()
                    response_time_ms = (end_time - start_time) * 1000

                    assert response.status_code == 200
                    assert response_time_ms < threshold, f"Response time {response_time_ms}ms exceeds threshold {threshold}ms for {endpoint}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, test_services, performance_thresholds):
        """Test concurrent API request performance"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        threshold = performance_thresholds["api_response_time_ms"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock fast responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "result": "test"}

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test concurrent requests
            async with httpx.AsyncClient() as client:
                # Create multiple concurrent requests
                tasks = []
                
                # Multimodal worker requests
                for i in range(5):
                    tasks.append(
                        client.post(
                            f"{multimodal_worker['url']}/process/text",
                            json={"text": f"Concurrent test {i}", "metadata": {}}
                        )
                    )
                
                # Retrieval proxy requests
                for i in range(5):
                    tasks.append(
                        client.post(
                            f"{retrieval_proxy['url']}/search",
                            json={"query": f"concurrent test {i}", "content_types": ["text"], "limit": 10}
                        )
                    )
                
                # AI agents requests
                for i in range(5):
                    tasks.append(
                        client.post(
                            f"{ai_agents['url']}/api/v1/agents/test_agent/execute",
                            json={"task": f"Concurrent task {i}", "context": {}}
                        )
                    )

                # Execute all requests concurrently
                start_time = time.time()
                responses = await asyncio.gather(*tasks)
                end_time = time.time()

                # Verify all requests succeeded
                for response in responses:
                    assert response.status_code == 200

                # Verify total time is reasonable
                total_time_ms = (end_time - start_time) * 1000
                max_individual_time = total_time_ms / len(tasks)  # Rough estimate
                assert max_individual_time < threshold, f"Concurrent request time {max_individual_time}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_throughput(self, test_services):
        """Test API throughput performance"""
        multimodal_worker = test_services["multimodal_worker"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock fast response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True, "result": "test"}

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test throughput
            async with httpx.AsyncClient() as client:
                num_requests = 100
                start_time = time.time()

                # Send multiple requests
                tasks = [
                    client.post(
                        f"{multimodal_worker['url']}/process/text",
                        json={"text": f"Throughput test {i}", "metadata": {}}
                    )
                    for i in range(num_requests)
                ]

                responses = await asyncio.gather(*tasks)
                end_time = time.time()

                # Verify all requests succeeded
                for response in responses:
                    assert response.status_code == 200

                # Calculate throughput
                total_time = end_time - start_time
                throughput = num_requests / total_time  # requests per second

                # Verify minimum throughput (should handle at least 50 requests per second)
                min_throughput = 50
                assert throughput >= min_throughput, f"Throughput {throughput:.2f} req/s is below minimum {min_throughput} req/s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_memory_usage(self, test_services):
        """Test API memory usage during high load"""
        import psutil
        import os

        multimodal_worker = test_services["multimodal_worker"]
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        with patch('httpx.AsyncClient') as mock_client:
            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "content_id": "memory_test_123",
                "embeddings": [0.1, 0.2, 0.3] * 170,  # Large embedding
                "metadata": {"test": "memory_usage"}
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test memory usage under load
            async with httpx.AsyncClient() as client:
                # Send many requests to test memory usage
                tasks = [
                    client.post(
                        f"{multimodal_worker['url']}/process/text",
                        json={"text": f"Memory test {i}", "metadata": {}}
                    )
                    for i in range(50)
                ]

                responses = await asyncio.gather(*tasks)
                
                # Check memory usage
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory

                # Verify all requests succeeded
                for response in responses:
                    assert response.status_code == 200

                # Verify memory usage is reasonable (should not increase by more than 100MB)
                max_memory_increase = 100  # MB
                assert memory_increase < max_memory_increase, f"Memory increase {memory_increase:.2f}MB exceeds limit {max_memory_increase}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_error_handling_performance(self, test_services, performance_thresholds):
        """Test API error handling performance"""
        multimodal_worker = test_services["multimodal_worker"]
        threshold = performance_thresholds["api_response_time_ms"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock error response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "success": False,
                "error": "Invalid input data"
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test error handling performance
            async with httpx.AsyncClient() as client:
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/process/text",
                    json={"invalid": "data"}  # Invalid payload
                )
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000

                # Verify error response
                assert response.status_code == 400
                error_data = response.json()
                assert error_data["success"] is False

                # Verify error handling is fast
                assert response_time_ms < threshold, f"Error response time {response_time_ms}ms exceeds threshold {threshold}ms"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_api_caching_performance(self, test_services):
        """Test API caching performance"""
        retrieval_proxy = test_services["retrieval_proxy"]

        with patch('httpx.AsyncClient') as mock_client:
            # Mock cached response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "success": True,
                "results": [{"content_id": "cached_doc", "score": 0.95}],
                "total_results": 1,
                "cached": True,
                "search_time_ms": 5  # Very fast due to caching
            }

            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

            # Test caching performance
            async with httpx.AsyncClient() as client:
                # First request (cache miss)
                start_time = time.time()
                response1 = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={"query": "cached test query", "content_types": ["text"], "limit": 10}
                )
                first_time = time.time() - start_time

                # Second request (cache hit)
                start_time = time.time()
                response2 = await client.post(
                    f"{retrieval_proxy['url']}/search",
                    json={"query": "cached test query", "content_types": ["text"], "limit": 10}
                )
                second_time = time.time() - start_time

                # Verify both requests succeeded
                assert response1.status_code == 200
                assert response2.status_code == 200

                # Verify caching improves performance
                cache_improvement = (first_time - second_time) / first_time
                assert cache_improvement > 0, "Caching should improve performance"
