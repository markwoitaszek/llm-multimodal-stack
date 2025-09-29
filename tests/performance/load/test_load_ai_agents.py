"""
Load testing for AI Agents service
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import httpx
import pytest
from locust import HttpUser, task, between
import json

class AIAgentsLoadTest(HttpUser):
    """Load test for AI Agents service"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup for each user"""
        self.agent_ids = []
        self.execution_ids = []
    
    @task(3)
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
    
    @task(2)
    def test_get_agents(self):
        """Test getting all agents"""
        response = self.client.get("/agents")
        assert response.status_code == 200
    
    @task(1)
    def test_create_agent(self):
        """Test creating an agent"""
        agent_data = {
            "name": f"Load Test Agent {time.time()}",
            "description": "Agent created during load testing",
            "goal": "Load testing",
            "tools": ["search_content", "generate_text"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = self.client.post("/agents", json=agent_data)
        if response.status_code == 201:
            agent_id = response.json()["agent_id"]
            self.agent_ids.append(agent_id)
    
    @task(2)
    def test_get_agent(self):
        """Test getting a specific agent"""
        if self.agent_ids:
            agent_id = self.agent_ids[0]
            response = self.client.get(f"/agents/{agent_id}")
            assert response.status_code == 200
    
    @task(1)
    def test_execute_agent(self):
        """Test executing an agent"""
        if self.agent_ids:
            agent_id = self.agent_ids[0]
            execution_data = {
                "task": f"Load test task {time.time()}",
                "user_id": "load_test_user"
            }
            
            response = self.client.post(f"/agents/{agent_id}/execute", json=execution_data)
            if response.status_code == 200:
                execution_id = response.json()["execution_id"]
                self.execution_ids.append(execution_id)
    
    @task(1)
    def test_get_execution(self):
        """Test getting an execution"""
        if self.execution_ids:
            execution_id = self.execution_ids[0]
            response = self.client.get(f"/executions/{execution_id}")
            assert response.status_code == 200
    
    @task(1)
    def test_get_statistics(self):
        """Test getting statistics"""
        response = self.client.get("/statistics")
        assert response.status_code == 200

class AIAgentsPerformanceTest:
    """Performance test for AI Agents service"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.results = []
    
    async def run_load_test(self, concurrent_users: int = 100, duration: int = 60):
        """Run load test with specified parameters"""
        print(f"Starting load test with {concurrent_users} concurrent users for {duration} seconds")
        
        # Create HTTP client
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            # Start load test
            start_time = time.time()
            end_time = start_time + duration
            
            # Create tasks for concurrent users
            tasks = []
            for i in range(concurrent_users):
                task = asyncio.create_task(self._user_simulation(client, i))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Calculate results
            self._calculate_results()
    
    async def _user_simulation(self, client: httpx.AsyncClient, user_id: int):
        """Simulate a single user"""
        agent_ids = []
        execution_ids = []
        
        while time.time() < time.time() + 60:  # Run for 60 seconds
            try:
                # Health check
                start_time = time.time()
                response = await client.get("/health")
                end_time = time.time()
                
                self.results.append({
                    "endpoint": "/health",
                    "method": "GET",
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "user_id": user_id,
                    "timestamp": time.time()
                })
                
                # Get agents
                start_time = time.time()
                response = await client.get("/agents")
                end_time = time.time()
                
                self.results.append({
                    "endpoint": "/agents",
                    "method": "GET",
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "user_id": user_id,
                    "timestamp": time.time()
                })
                
                # Create agent (occasionally)
                if len(agent_ids) < 5:  # Limit agents per user
                    start_time = time.time()
                    agent_data = {
                        "name": f"Load Test Agent {user_id}_{time.time()}",
                        "description": "Agent created during load testing",
                        "goal": "Load testing",
                        "tools": ["search_content", "generate_text"],
                        "model": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                    
                    response = await client.post("/agents", json=agent_data)
                    end_time = time.time()
                    
                    self.results.append({
                        "endpoint": "/agents",
                        "method": "POST",
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "user_id": user_id,
                        "timestamp": time.time()
                    })
                    
                    if response.status_code == 201:
                        agent_id = response.json()["agent_id"]
                        agent_ids.append(agent_id)
                
                # Execute agent (if we have agents)
                if agent_ids:
                    start_time = time.time()
                    execution_data = {
                        "task": f"Load test task {user_id}_{time.time()}",
                        "user_id": f"load_test_user_{user_id}"
                    }
                    
                    response = await client.post(f"/agents/{agent_ids[0]}/execute", json=execution_data)
                    end_time = time.time()
                    
                    self.results.append({
                        "endpoint": f"/agents/{agent_ids[0]}/execute",
                        "method": "POST",
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "user_id": user_id,
                        "timestamp": time.time()
                    })
                    
                    if response.status_code == 200:
                        execution_id = response.json()["execution_id"]
                        execution_ids.append(execution_id)
                
                # Get statistics
                start_time = time.time()
                response = await client.get("/statistics")
                end_time = time.time()
                
                self.results.append({
                    "endpoint": "/statistics",
                    "method": "GET",
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "user_id": user_id,
                    "timestamp": time.time()
                })
                
                # Wait between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error in user simulation {user_id}: {e}")
                await asyncio.sleep(1)
    
    def _calculate_results(self):
        """Calculate performance results"""
        if not self.results:
            print("No results to calculate")
            return
        
        # Group results by endpoint
        endpoint_results = {}
        for result in self.results:
            endpoint = result["endpoint"]
            if endpoint not in endpoint_results:
                endpoint_results[endpoint] = []
            endpoint_results[endpoint].append(result)
        
        # Calculate statistics for each endpoint
        print("\n=== Performance Test Results ===")
        print(f"Total requests: {len(self.results)}")
        
        for endpoint, results in endpoint_results.items():
            response_times = [r["response_time"] for r in results]
            status_codes = [r["status_code"] for r in results]
            
            success_count = sum(1 for code in status_codes if 200 <= code < 300)
            error_count = len(status_codes) - success_count
            
            print(f"\n{endpoint}:")
            print(f"  Requests: {len(results)}")
            print(f"  Success rate: {success_count/len(results)*100:.2f}%")
            print(f"  Error rate: {error_count/len(results)*100:.2f}%")
            print(f"  Min response time: {min(response_times):.3f}s")
            print(f"  Max response time: {max(response_times):.3f}s")
            print(f"  Avg response time: {statistics.mean(response_times):.3f}s")
            print(f"  Median response time: {statistics.median(response_times):.3f}s")
            print(f"  95th percentile: {self._percentile(response_times, 95):.3f}s")
            print(f"  99th percentile: {self._percentile(response_times, 99):.3f}s")
        
        # Overall statistics
        all_response_times = [r["response_time"] for r in self.results]
        all_status_codes = [r["status_code"] for r in self.results]
        
        overall_success = sum(1 for code in all_status_codes if 200 <= code < 300)
        overall_error = len(all_status_codes) - overall_success
        
        print(f"\nOverall:")
        print(f"  Total requests: {len(self.results)}")
        print(f"  Success rate: {overall_success/len(self.results)*100:.2f}%")
        print(f"  Error rate: {overall_error/len(self.results)*100:.2f}%")
        print(f"  Avg response time: {statistics.mean(all_response_times):.3f}s")
        print(f"  Median response time: {statistics.median(all_response_times):.3f}s")
        print(f"  95th percentile: {self._percentile(all_response_times, 95):.3f}s")
        print(f"  99th percentile: {self._percentile(all_response_times, 99):.3f}s")
        
        # Check performance requirements
        self._check_performance_requirements(all_response_times, overall_success, len(self.results))
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _check_performance_requirements(self, response_times: List[float], success_count: int, total_count: int):
        """Check if performance requirements are met"""
        print("\n=== Performance Requirements Check ===")
        
        # Response time requirement: <200ms
        avg_response_time = statistics.mean(response_times)
        if avg_response_time < 0.2:
            print(f"✅ Average response time: {avg_response_time:.3f}s (< 200ms)")
        else:
            print(f"❌ Average response time: {avg_response_time:.3f}s (>= 200ms)")
        
        # Success rate requirement: >95%
        success_rate = success_count / total_count * 100
        if success_rate > 95:
            print(f"✅ Success rate: {success_rate:.2f}% (> 95%)")
        else:
            print(f"❌ Success rate: {success_rate:.2f}% (<= 95%)")
        
        # 95th percentile requirement: <500ms
        p95 = self._percentile(response_times, 95)
        if p95 < 0.5:
            print(f"✅ 95th percentile: {p95:.3f}s (< 500ms)")
        else:
            print(f"❌ 95th percentile: {p95:.3f}s (>= 500ms)")
        
        # 99th percentile requirement: <1000ms
        p99 = self._percentile(response_times, 99)
        if p99 < 1.0:
            print(f"✅ 99th percentile: {p99:.3f}s (< 1000ms)")
        else:
            print(f"❌ 99th percentile: {p99:.3f}s (>= 1000ms)")

@pytest.mark.performance
class TestAIAgentsPerformance:
    """Performance tests for AI Agents service"""
    
    @pytest.mark.asyncio
    async def test_light_load(self):
        """Test light load (10 concurrent users)"""
        test = AIAgentsPerformanceTest()
        await test.run_load_test(concurrent_users=10, duration=30)
    
    @pytest.mark.asyncio
    async def test_medium_load(self):
        """Test medium load (50 concurrent users)"""
        test = AIAgentsPerformanceTest()
        await test.run_load_test(concurrent_users=50, duration=60)
    
    @pytest.mark.asyncio
    async def test_heavy_load(self):
        """Test heavy load (100 concurrent users)"""
        test = AIAgentsPerformanceTest()
        await test.run_load_test(concurrent_users=100, duration=120)
    
    @pytest.mark.asyncio
    async def test_stress_load(self):
        """Test stress load (200 concurrent users)"""
        test = AIAgentsPerformanceTest()
        await test.run_load_test(concurrent_users=200, duration=180)
    
    @pytest.mark.asyncio
    async def test_response_time_requirements(self):
        """Test that response times meet requirements"""
        test = AIAgentsPerformanceTest()
        await test.run_load_test(concurrent_users=100, duration=60)
        
        # Check that average response time is < 200ms
        all_response_times = [r["response_time"] for r in test.results]
        avg_response_time = statistics.mean(all_response_times)
        assert avg_response_time < 0.2, f"Average response time {avg_response_time:.3f}s exceeds 200ms requirement"
        
        # Check that 95th percentile is < 500ms
        p95 = test._percentile(all_response_times, 95)
        assert p95 < 0.5, f"95th percentile {p95:.3f}s exceeds 500ms requirement"
        
        # Check that 99th percentile is < 1000ms
        p99 = test._percentile(all_response_times, 99)
        assert p99 < 1.0, f"99th percentile {p99:.3f}s exceeds 1000ms requirement"
    
    @pytest.mark.asyncio
    async def test_success_rate_requirements(self):
        """Test that success rate meets requirements"""
        test = AIAgentsPerformanceTest()
        await test.run_load_test(concurrent_users=100, duration=60)
        
        # Check that success rate is > 95%
        all_status_codes = [r["status_code"] for r in test.results]
        success_count = sum(1 for code in all_status_codes if 200 <= code < 300)
        success_rate = success_count / len(all_status_codes) * 100
        assert success_rate > 95, f"Success rate {success_rate:.2f}% is below 95% requirement"
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self):
        """Test concurrent agent creation"""
        test = AIAgentsPerformanceTest()
        
        # Create multiple agents concurrently
        async with httpx.AsyncClient(base_url=test.base_url) as client:
            tasks = []
            for i in range(50):
                task = asyncio.create_task(self._create_agent(client, i))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # Check that all agents were created successfully
            success_count = sum(1 for result in results if result["status_code"] == 201)
            assert success_count == 50, f"Only {success_count}/50 agents created successfully"
    
    async def _create_agent(self, client: httpx.AsyncClient, index: int) -> Dict[str, Any]:
        """Create a single agent"""
        agent_data = {
            "name": f"Concurrent Agent {index}",
            "description": "Agent created during concurrent testing",
            "goal": "Concurrent testing",
            "tools": ["search_content", "generate_text"],
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        start_time = time.time()
        response = await client.post("/agents", json=agent_data)
        end_time = time.time()
        
        return {
            "status_code": response.status_code,
            "response_time": end_time - start_time,
            "index": index
        }