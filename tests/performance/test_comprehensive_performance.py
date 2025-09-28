"""
Comprehensive performance tests with real benchmarks for the LLM Multimodal Stack
"""
import pytest
import pytest_asyncio
import asyncio
import time
import numpy as np
import psutil
import os
import json
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx
from typing import List, Dict, Any, Tuple
from PIL import Image
import io
import statistics

from tests.conftest import test_services, performance_thresholds


class TestComprehensivePerformance:
    """Comprehensive performance tests with real benchmarks"""

    @pytest.fixture
    def performance_test_data(self):
        """Create comprehensive test data for performance testing"""
        # Create realistic test documents of varying sizes
        documents = {
            "small": "Machine learning is a subset of artificial intelligence.",
            "medium": """
            Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models.
            It enables computer systems to improve their performance on a specific task through experience.
            The field has applications in computer vision, natural language processing, and robotics.
            """,
            "large": """
            Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models
            that enable computer systems to improve their performance on a specific task through experience.
            The field has applications in computer vision, natural language processing, robotics, and many other domains.
            
            There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning.
            Supervised learning uses labeled training data to learn a mapping from inputs to outputs.
            Unsupervised learning finds hidden patterns in data without labeled examples.
            Reinforcement learning learns through interaction with an environment and receiving rewards or penalties.
            
            Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers.
            These networks can learn complex patterns in data and have achieved state-of-the-art results in many tasks.
            Convolutional neural networks are particularly effective for image recognition tasks.
            Recurrent neural networks are well-suited for sequential data like text and time series.
            
            The field of machine learning continues to evolve rapidly with new architectures, algorithms, and applications
            being developed regularly. Recent advances include transformer architectures, attention mechanisms, and
            large language models that have revolutionized natural language processing.
            """
        }
        
        # Create test images of varying sizes
        images = {}
        for size_name, dimensions in [("small", (100, 100)), ("medium", (512, 512)), ("large", (1024, 1024))]:
            img = Image.new('RGB', dimensions, color='blue')
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            images[size_name] = img_buffer.getvalue()
        
        return {
            "documents": documents,
            "images": images,
            "queries": [
                "machine learning artificial intelligence",
                "deep learning neural networks",
                "computer vision natural language processing",
                "supervised unsupervised reinforcement learning",
                "transformer attention mechanisms"
            ]
        }

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_end_to_end_workflow_performance(self, test_services, performance_test_data, performance_thresholds):
        """Test complete end-to-end workflow performance with real data"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            workflow_metrics = {
                "processing_times": [],
                "search_times": [],
                "agent_times": [],
                "total_workflow_time": 0
            }
            
            workflow_start = time.time()
            
            # Step 1: Process documents with performance measurement
            document_ids = []
            for doc_size, doc_content in performance_test_data["documents"].items():
                step_start = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": doc_content,
                        "document_name": f"perf_test_{doc_size}.txt",
                        "metadata": {"size": doc_size, "source": "performance_test"}
                    }
                )
                
                step_time = time.time() - step_start
                workflow_metrics["processing_times"].append(step_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                document_ids.append(result["content_id"])
            
            # Step 2: Process images with performance measurement
            image_ids = []
            for img_size, img_data in performance_test_data["images"].items():
                step_start = time.time()
                
                files = {'file': (f"perf_test_{img_size}.jpg", img_data, 'image/jpeg')}
                data = {
                    'document_name': f"perf_test_{img_size}.jpg",
                    'metadata': json.dumps({"size": img_size, "source": "performance_test"})
                }
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/image",
                    files=files,
                    data=data
                )
                
                step_time = time.time() - step_start
                workflow_metrics["processing_times"].append(step_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                image_ids.append(result["content_id"])
            
            # Step 3: Search operations with performance measurement
            for query in performance_test_data["queries"]:
                step_start = time.time()
                
                response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": query,
                        "modalities": ["text", "image"],
                        "limit": 10,
                        "score_threshold": 0.3
                    }
                )
                
                step_time = time.time() - step_start
                workflow_metrics["search_times"].append(step_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
            
            # Step 4: Agent operations with performance measurement
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Performance Test Agent",
                    "goal": "Execute tasks efficiently and provide performance insights",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 5,
                    "user_id": "performance_test_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            for i, query in enumerate(performance_test_data["queries"][:3]):  # Test first 3 queries
                step_start = time.time()
                
                execution_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                    json={
                        "task": f"Analyze search results for '{query}' and provide insights",
                        "user_id": "performance_test_user"
                    }
                )
                
                step_time = time.time() - step_start
                workflow_metrics["agent_times"].append(step_time)
                
                assert execution_response.status_code == 200
                execution_result = execution_response.json()
                assert execution_result["success"] is True
            
            workflow_metrics["total_workflow_time"] = time.time() - workflow_start
            
            # Performance validation
            avg_processing_time = statistics.mean(workflow_metrics["processing_times"])
            avg_search_time = statistics.mean(workflow_metrics["search_times"])
            avg_agent_time = statistics.mean(workflow_metrics["agent_times"])
            
            # Validate against thresholds
            assert avg_processing_time < performance_thresholds["text_processing_time"], \
                f"Average processing time {avg_processing_time:.2f}s exceeds threshold {performance_thresholds['text_processing_time']}s"
            
            assert avg_search_time < performance_thresholds["search_response_time"], \
                f"Average search time {avg_search_time:.2f}s exceeds threshold {performance_thresholds['search_response_time']}s"
            
            assert avg_agent_time < performance_thresholds["agent_execution_time"], \
                f"Average agent time {avg_agent_time:.2f}s exceeds threshold {performance_thresholds['agent_execution_time']}s"
            
            # Total workflow should complete within reasonable time
            assert workflow_metrics["total_workflow_time"] < 300.0, \
                f"Total workflow time {workflow_metrics['total_workflow_time']:.2f}s exceeds 300s limit"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_scalability_under_load(self, test_services, performance_test_data):
        """Test system scalability under various load conditions"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Test different load levels
            load_levels = [
                {"name": "light", "concurrent_requests": 5, "total_requests": 25},
                {"name": "medium", "concurrent_requests": 10, "total_requests": 50},
                {"name": "heavy", "concurrent_requests": 20, "total_requests": 100}
            ]
            
            scalability_results = {}
            
            for load_level in load_levels:
                print(f"Testing {load_level['name']} load: {load_level['concurrent_requests']} concurrent, {load_level['total_requests']} total")
                
                # Create concurrent processing tasks
                processing_tasks = []
                for i in range(load_level["total_requests"]):
                    doc_content = performance_test_data["documents"]["medium"]
                    task = client.post(
                        f"{multimodal_worker['url']}/api/v1/process/text",
                        json={
                            "text": f"{doc_content} - Load test {i}",
                            "document_name": f"load_test_{load_level['name']}_{i}.txt",
                            "metadata": {"load_level": load_level["name"], "request_id": i}
                        }
                    )
                    processing_tasks.append(task)
                
                # Execute with controlled concurrency
                start_time = time.time()
                semaphore = asyncio.Semaphore(load_level["concurrent_requests"])
                
                async def limited_request(task):
                    async with semaphore:
                        return await task
                
                limited_tasks = [limited_request(task) for task in processing_tasks]
                responses = await asyncio.gather(*limited_tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Analyze results
                successful_requests = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
                success_rate = successful_requests / load_level["total_requests"]
                throughput = successful_requests / total_time
                
                scalability_results[load_level["name"]] = {
                    "total_requests": load_level["total_requests"],
                    "successful_requests": successful_requests,
                    "success_rate": success_rate,
                    "total_time": total_time,
                    "throughput": throughput
                }
                
                # Validate performance
                assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80% for {load_level['name']} load"
                assert throughput >= 1.0, f"Throughput {throughput:.2f} req/s below 1.0 for {load_level['name']} load"
            
            # Validate scalability characteristics
            light_throughput = scalability_results["light"]["throughput"]
            medium_throughput = scalability_results["medium"]["throughput"]
            heavy_throughput = scalability_results["heavy"]["throughput"]
            
            # System should maintain reasonable performance under increased load
            assert heavy_throughput >= light_throughput * 0.5, \
                f"Heavy load throughput {heavy_throughput:.2f} too low compared to light load {light_throughput:.2f}"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, test_services, performance_test_data):
        """Test memory usage patterns under various load conditions"""
        multimodal_worker = test_services["multimodal_worker"]
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            memory_measurements = []
            
            # Test memory usage during processing
            for i in range(50):
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": performance_test_data["documents"]["large"],
                        "document_name": f"memory_test_{i}.txt",
                        "metadata": {"test_type": "memory_usage", "iteration": i}
                    }
                )
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                # Measure memory every 10 requests
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = current_memory - initial_memory
                    memory_measurements.append({
                        "iteration": i,
                        "memory_mb": current_memory,
                        "memory_increase_mb": memory_increase
                    })
            
            # Analyze memory usage patterns
            max_memory_increase = max(m["memory_increase_mb"] for m in memory_measurements)
            final_memory_increase = memory_measurements[-1]["memory_increase_mb"]
            
            # Memory usage should be reasonable
            assert max_memory_increase < 500, \
                f"Maximum memory increase {max_memory_increase:.2f}MB exceeds 500MB limit"
            
            # Memory should not grow unbounded (some growth is expected, but not excessive)
            assert final_memory_increase < 200, \
                f"Final memory increase {final_memory_increase:.2f}MB exceeds 200MB limit"
            
            # Memory growth should be relatively linear, not exponential
            if len(memory_measurements) >= 3:
                early_growth = memory_measurements[1]["memory_increase_mb"] - memory_measurements[0]["memory_increase_mb"]
                late_growth = memory_measurements[-1]["memory_increase_mb"] - memory_measurements[-2]["memory_increase_mb"]
                
                # Late growth should not be significantly higher than early growth
                assert late_growth <= early_growth * 2, \
                    "Memory growth appears to be accelerating (potential memory leak)"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_response_time_consistency(self, test_services, performance_test_data):
        """Test response time consistency across multiple requests"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test processing response time consistency
            processing_times = []
            for i in range(30):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": performance_test_data["documents"]["medium"],
                        "document_name": f"consistency_test_{i}.txt",
                        "metadata": {"test_type": "consistency", "iteration": i}
                    }
                )
                
                end_time = time.time()
                processing_times.append(end_time - start_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
            
            # Test search response time consistency
            search_times = []
            for i in range(30):
                start_time = time.time()
                
                response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": f"consistency test query {i}",
                        "modalities": ["text"],
                        "limit": 10
                    }
                )
                
                end_time = time.time()
                search_times.append(end_time - start_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
            
            # Analyze consistency
            processing_stats = {
                "mean": statistics.mean(processing_times),
                "std": statistics.stdev(processing_times),
                "min": min(processing_times),
                "max": max(processing_times),
                "cv": statistics.stdev(processing_times) / statistics.mean(processing_times)  # Coefficient of variation
            }
            
            search_stats = {
                "mean": statistics.mean(search_times),
                "std": statistics.stdev(search_times),
                "min": min(search_times),
                "max": max(search_times),
                "cv": statistics.stdev(search_times) / statistics.mean(search_times)
            }
            
            # Response times should be consistent (low coefficient of variation)
            assert processing_stats["cv"] < 0.5, \
                f"Processing response time coefficient of variation {processing_stats['cv']:.3f} too high (inconsistent)"
            
            assert search_stats["cv"] < 0.5, \
                f"Search response time coefficient of variation {search_stats['cv']:.3f} too high (inconsistent)"
            
            # No single request should be extremely slow
            assert processing_stats["max"] < processing_stats["mean"] * 3, \
                f"Maximum processing time {processing_stats['max']:.2f}s too high compared to mean {processing_stats['mean']:.2f}s"
            
            assert search_stats["max"] < search_stats["mean"] * 3, \
                f"Maximum search time {search_stats['max']:.2f}s too high compared to mean {search_stats['mean']:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self, test_services, performance_test_data):
        """Test system performance under concurrent user simulation"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Simulate multiple concurrent users
            num_users = 10
            requests_per_user = 5
            
            async def simulate_user(user_id: int):
                """Simulate a single user's workflow"""
                user_metrics = {
                    "user_id": user_id,
                    "processing_times": [],
                    "search_times": [],
                    "agent_times": [],
                    "success_count": 0,
                    "error_count": 0
                }
                
                for request_id in range(requests_per_user):
                    try:
                        # User processes content
                        start_time = time.time()
                        response = await client.post(
                            f"{multimodal_worker['url']}/api/v1/process/text",
                            json={
                                "text": f"{performance_test_data['documents']['medium']} - User {user_id} Request {request_id}",
                                "document_name": f"user_{user_id}_request_{request_id}.txt",
                                "metadata": {"user_id": user_id, "request_id": request_id}
                            }
                        )
                        processing_time = time.time() - start_time
                        user_metrics["processing_times"].append(processing_time)
                        
                        if response.status_code == 200:
                            user_metrics["success_count"] += 1
                        else:
                            user_metrics["error_count"] += 1
                            continue
                        
                        # User searches for content
                        start_time = time.time()
                        response = await client.post(
                            f"{retrieval_proxy['url']}/api/v1/search",
                            json={
                                "query": f"user {user_id} request {request_id}",
                                "modalities": ["text"],
                                "limit": 5
                            }
                        )
                        search_time = time.time() - start_time
                        user_metrics["search_times"].append(search_time)
                        
                        if response.status_code != 200:
                            user_metrics["error_count"] += 1
                            continue
                        
                        # User creates and uses an agent (every other request)
                        if request_id % 2 == 0:
                            start_time = time.time()
                            
                            # Create agent
                            agent_response = await client.post(
                                f"{ai_agents['url']}/api/v1/agents",
                                json={
                                    "name": f"User {user_id} Agent {request_id}",
                                    "goal": "Help user with tasks",
                                    "tools": ["search_content"],
                                    "user_id": f"user_{user_id}"
                                }
                            )
                            
                            if agent_response.status_code == 200:
                                agent_result = agent_response.json()
                                agent_id = agent_result["agent_id"]
                                
                                # Execute agent task
                                execution_response = await client.post(
                                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                                    json={
                                        "task": f"Help user {user_id} with request {request_id}",
                                        "user_id": f"user_{user_id}"
                                    }
                                )
                                
                                agent_time = time.time() - start_time
                                user_metrics["agent_times"].append(agent_time)
                                
                                if execution_response.status_code != 200:
                                    user_metrics["error_count"] += 1
                                else:
                                    user_metrics["success_count"] += 1
                            else:
                                user_metrics["error_count"] += 1
                        
                    except Exception as e:
                        user_metrics["error_count"] += 1
                        print(f"User {user_id} request {request_id} failed: {e}")
                
                return user_metrics
            
            # Run concurrent user simulation
            start_time = time.time()
            user_tasks = [simulate_user(user_id) for user_id in range(num_users)]
            user_results = await asyncio.gather(*user_tasks)
            total_time = time.time() - start_time
            
            # Analyze results
            total_requests = num_users * requests_per_user
            total_successes = sum(result["success_count"] for result in user_results)
            total_errors = sum(result["error_count"] for result in user_results)
            overall_success_rate = total_successes / (total_successes + total_errors)
            
            # Calculate performance metrics
            all_processing_times = []
            all_search_times = []
            all_agent_times = []
            
            for result in user_results:
                all_processing_times.extend(result["processing_times"])
                all_search_times.extend(result["search_times"])
                all_agent_times.extend(result["agent_times"])
            
            avg_processing_time = statistics.mean(all_processing_times) if all_processing_times else 0
            avg_search_time = statistics.mean(all_search_times) if all_search_times else 0
            avg_agent_time = statistics.mean(all_agent_times) if all_agent_times else 0
            
            # Validate performance under concurrent load
            assert overall_success_rate >= 0.8, \
                f"Overall success rate {overall_success_rate:.2%} below 80% under concurrent load"
            
            assert avg_processing_time < 5.0, \
                f"Average processing time {avg_processing_time:.2f}s too high under concurrent load"
            
            assert avg_search_time < 2.0, \
                f"Average search time {avg_search_time:.2f}s too high under concurrent load"
            
            if all_agent_times:
                assert avg_agent_time < 10.0, \
                    f"Average agent time {avg_agent_time:.2f}s too high under concurrent load"
            
            # System should handle concurrent users efficiently
            requests_per_second = total_requests / total_time
            assert requests_per_second >= 1.0, \
                f"System throughput {requests_per_second:.2f} req/s too low under concurrent load"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_resource_utilization_benchmarks(self, test_services, performance_test_data):
        """Test resource utilization patterns and benchmarks"""
        multimodal_worker = test_services["multimodal_worker"]
        
        # Monitor system resources
        process = psutil.Process(os.getpid())
        initial_cpu_percent = process.cpu_percent()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resource_measurements = []
            
            # Test resource usage during sustained load
            for i in range(100):
                # Measure resources before request
                cpu_before = process.cpu_percent()
                memory_before = process.memory_info().rss / 1024 / 1024
                
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": performance_test_data["documents"]["large"],
                        "document_name": f"resource_test_{i}.txt",
                        "metadata": {"test_type": "resource_utilization", "iteration": i}
                    }
                )
                
                end_time = time.time()
                
                # Measure resources after request
                cpu_after = process.cpu_percent()
                memory_after = process.memory_info().rss / 1024 / 1024
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                # Record measurements
                resource_measurements.append({
                    "iteration": i,
                    "request_time": end_time - start_time,
                    "cpu_before": cpu_before,
                    "cpu_after": cpu_after,
                    "memory_before": memory_before,
                    "memory_after": memory_after,
                    "memory_delta": memory_after - memory_before
                })
                
                # Small delay to allow resource monitoring
                await asyncio.sleep(0.1)
            
            # Analyze resource utilization
            avg_request_time = statistics.mean([m["request_time"] for m in resource_measurements])
            max_memory_usage = max([m["memory_after"] for m in resource_measurements])
            memory_growth = max_memory_usage - initial_memory
            avg_cpu_usage = statistics.mean([m["cpu_after"] for m in resource_measurements])
            
            # Resource utilization should be reasonable
            assert avg_request_time < 3.0, \
                f"Average request time {avg_request_time:.2f}s too high"
            
            assert memory_growth < 300, \
                f"Memory growth {memory_growth:.2f}MB too high"
            
            assert avg_cpu_usage < 80, \
                f"Average CPU usage {avg_cpu_usage:.1f}% too high"
            
            # Memory should not grow unbounded
            final_memory = resource_measurements[-1]["memory_after"]
            assert final_memory < initial_memory + 200, \
                f"Final memory usage {final_memory:.2f}MB too high compared to initial {initial_memory:.2f}MB"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_degradation_analysis(self, test_services, performance_test_data):
        """Test and analyze performance degradation patterns"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # Test performance over extended period
            performance_windows = []
            window_size = 20  # requests per window
            num_windows = 10
            
            for window in range(num_windows):
                window_times = []
                
                for i in range(window_size):
                    start_time = time.time()
                    
                    response = await client.post(
                        f"{multimodal_worker['url']}/api/v1/process/text",
                        json={
                            "text": performance_test_data["documents"]["medium"],
                            "document_name": f"degradation_test_window_{window}_request_{i}.txt",
                            "metadata": {"window": window, "request": i}
                        }
                    )
                    
                    end_time = time.time()
                    window_times.append(end_time - start_time)
                    
                    assert response.status_code == 200
                    result = response.json()
                    assert result["success"] is True
                
                # Calculate window statistics
                window_stats = {
                    "window": window,
                    "mean_time": statistics.mean(window_times),
                    "std_time": statistics.stdev(window_times),
                    "min_time": min(window_times),
                    "max_time": max(window_times)
                }
                performance_windows.append(window_stats)
                
                # Small delay between windows
                await asyncio.sleep(1.0)
            
            # Analyze performance degradation
            early_performance = performance_windows[0]["mean_time"]
            late_performance = performance_windows[-1]["mean_time"]
            performance_degradation = (late_performance - early_performance) / early_performance
            
            # Performance should not degrade significantly
            assert performance_degradation < 0.5, \
                f"Performance degraded by {performance_degradation:.1%}, which is too high"
            
            # Check for performance trends
            window_means = [w["mean_time"] for w in performance_windows]
            performance_trend = statistics.correlation(list(range(num_windows)), window_means)
            
            # Performance trend should not be strongly positive (degrading)
            assert performance_trend < 0.7, \
                f"Performance shows strong degrading trend (correlation: {performance_trend:.3f})"
            
            # All windows should maintain reasonable performance
            for window in performance_windows:
                assert window["mean_time"] < 5.0, \
                    f"Window {window['window']} mean time {window['mean_time']:.2f}s too high"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_benchmark_comparison(self, test_services, performance_test_data):
        """Test performance against established benchmarks"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        # Define benchmark targets
        benchmarks = {
            "text_processing": {"target": 1.0, "tolerance": 0.5},  # 1.0s target, 50% tolerance
            "search_response": {"target": 0.5, "tolerance": 0.3},  # 0.5s target, 30% tolerance
            "concurrent_throughput": {"target": 10.0, "tolerance": 0.2}  # 10 req/s target, 20% tolerance
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            benchmark_results = {}
            
            # Benchmark 1: Text processing performance
            processing_times = []
            for i in range(20):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": performance_test_data["documents"]["large"],
                        "document_name": f"benchmark_processing_{i}.txt",
                        "metadata": {"benchmark": "text_processing"}
                    }
                )
                
                end_time = time.time()
                processing_times.append(end_time - start_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
            
            avg_processing_time = statistics.mean(processing_times)
            benchmark_results["text_processing"] = {
                "actual": avg_processing_time,
                "target": benchmarks["text_processing"]["target"],
                "tolerance": benchmarks["text_processing"]["tolerance"],
                "meets_benchmark": avg_processing_time <= benchmarks["text_processing"]["target"] * (1 + benchmarks["text_processing"]["tolerance"])
            }
            
            # Benchmark 2: Search response performance
            search_times = []
            for i in range(20):
                start_time = time.time()
                
                response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": f"benchmark search query {i}",
                        "modalities": ["text"],
                        "limit": 10
                    }
                )
                
                end_time = time.time()
                search_times.append(end_time - start_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
            
            avg_search_time = statistics.mean(search_times)
            benchmark_results["search_response"] = {
                "actual": avg_search_time,
                "target": benchmarks["search_response"]["target"],
                "tolerance": benchmarks["search_response"]["tolerance"],
                "meets_benchmark": avg_search_time <= benchmarks["search_response"]["target"] * (1 + benchmarks["search_response"]["tolerance"])
            }
            
            # Benchmark 3: Concurrent throughput
            concurrent_requests = 20
            start_time = time.time()
            
            tasks = []
            for i in range(concurrent_requests):
                task = client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": performance_test_data["documents"]["medium"],
                        "document_name": f"benchmark_concurrent_{i}.txt",
                        "metadata": {"benchmark": "concurrent_throughput"}
                    }
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            end_time = time.time()
            
            total_time = end_time - start_time
            throughput = concurrent_requests / total_time
            
            benchmark_results["concurrent_throughput"] = {
                "actual": throughput,
                "target": benchmarks["concurrent_throughput"]["target"],
                "tolerance": benchmarks["concurrent_throughput"]["tolerance"],
                "meets_benchmark": throughput >= benchmarks["concurrent_throughput"]["target"] * (1 - benchmarks["concurrent_throughput"]["tolerance"])
            }
            
            # Validate benchmarks
            for benchmark_name, result in benchmark_results.items():
                assert result["meets_benchmark"], \
                    f"Benchmark '{benchmark_name}' failed: actual {result['actual']:.3f}, target {result['target']:.3f} (±{result['tolerance']:.1%})"
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True