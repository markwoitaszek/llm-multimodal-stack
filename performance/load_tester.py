"""
Advanced Load Testing Framework for LLM Multimodal Stack
"""
import asyncio
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
import httpx
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class LoadTestConfig:
    """Load test configuration"""
    name: str
    duration_seconds: int = 60
    concurrent_users: int = 10
    ramp_up_seconds: int = 10
    ramp_down_seconds: int = 10
    think_time_seconds: float = 1.0
    max_errors: int = 100
    timeout_seconds: int = 30
    base_url: str = "http://localhost:8000"
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    user_agents: List[str] = field(default_factory=lambda: [
        "LoadTester/1.0",
        "Mozilla/5.0 (compatible; LoadTester)",
        "Python-httpx/0.24.0"
    ])

@dataclass
class LoadTestResult:
    """Individual load test result"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    error: Optional[str] = None
    response_size_bytes: int = 0
    user_id: str = ""

@dataclass
class LoadTestSummary:
    """Load test summary statistics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float
    duration_seconds: float
    start_time: datetime
    end_time: datetime

class LoadTester:
    """Advanced load testing framework"""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[LoadTestResult] = []
        self.running = False
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._stop_event = asyncio.Event()
        self._semaphore = asyncio.Semaphore(config.concurrent_users)
        
        # HTTP client configuration
        self.client_config = {
            "timeout": httpx.Timeout(config.timeout_seconds),
            "limits": httpx.Limits(max_keepalive_connections=config.concurrent_users * 2)
        }
    
    async def run_load_test(self) -> LoadTestSummary:
        """Run the load test"""
        logger.info(f"Starting load test: {self.config.name}")
        logger.info(f"Duration: {self.config.duration_seconds}s, Users: {self.config.concurrent_users}")
        
        self.running = True
        self.start_time = datetime.utcnow()
        self.results.clear()
        
        # Create tasks for concurrent users
        tasks = []
        for user_id in range(self.config.concurrent_users):
            task = asyncio.create_task(self._user_loop(f"user_{user_id}"))
            tasks.append(task)
        
        # Wait for test duration
        try:
            await asyncio.wait_for(
                self._stop_event.wait(),
                timeout=self.config.duration_seconds
            )
        except asyncio.TimeoutError:
            pass
        
        # Stop all user tasks
        self.running = False
        for task in tasks:
            task.cancel()
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.end_time = datetime.utcnow()
        
        # Generate summary
        summary = self._generate_summary()
        
        logger.info(f"Load test completed: {summary.total_requests} requests, "
                   f"{summary.requests_per_second:.2f} RPS, "
                   f"{summary.error_rate_percent:.2f}% error rate")
        
        return summary
    
    async def _user_loop(self, user_id: str):
        """Individual user simulation loop"""
        async with httpx.AsyncClient(**self.client_config) as client:
            while self.running and not self._stop_event.is_set():
                try:
                    # Select random endpoint
                    endpoint_config = random.choice(self.config.endpoints)
                    
                    # Wait for think time
                    if self.config.think_time_seconds > 0:
                        await asyncio.sleep(random.uniform(0.5, self.config.think_time_seconds * 2))
                    
                    # Execute request
                    await self._execute_request(client, endpoint_config, user_id)
                    
                except Exception as e:
                    logger.error(f"Error in user loop {user_id}: {e}")
                    await asyncio.sleep(1)
    
    async def _execute_request(self, client: httpx.AsyncClient, endpoint_config: Dict[str, Any], user_id: str):
        """Execute a single request"""
        async with self._semaphore:
            start_time = time.time()
            error = None
            status_code = 0
            response_size = 0
            
            try:
                url = f"{self.config.base_url}{endpoint_config['path']}"
                method = endpoint_config.get('method', 'GET').upper()
                headers = {
                    "User-Agent": random.choice(self.config.user_agents),
                    "Content-Type": "application/json"
                }
                
                # Prepare request data
                data = None
                if method in ['POST', 'PUT', 'PATCH']:
                    data = endpoint_config.get('data', {})
                    if isinstance(data, dict):
                        data = json.dumps(data)
                
                # Execute request
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    content=data
                )
                
                status_code = response.status_code
                response_size = len(response.content)
                
                # Check for errors
                if status_code >= 400:
                    error = f"HTTP {status_code}: {response.text[:100]}"
                
            except httpx.TimeoutException:
                error = "Request timeout"
            except httpx.ConnectError:
                error = "Connection error"
            except Exception as e:
                error = str(e)
            
            # Record result
            response_time_ms = (time.time() - start_time) * 1000
            
            result = LoadTestResult(
                endpoint=endpoint_config['path'],
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                timestamp=datetime.utcnow(),
                error=error,
                response_size_bytes=response_size,
                user_id=user_id
            )
            
            self.results.append(result)
            
            # Check error limit
            if len([r for r in self.results if r.error]) >= self.config.max_errors:
                logger.warning("Maximum error limit reached, stopping test")
                self._stop_event.set()
    
    def _generate_summary(self) -> LoadTestSummary:
        """Generate load test summary"""
        if not self.results:
            return LoadTestSummary(
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_response_time_ms=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                p50_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                error_rate_percent=0,
                duration_seconds=0,
                start_time=self.start_time or datetime.utcnow(),
                end_time=self.end_time or datetime.utcnow()
            )
        
        successful_requests = [r for r in self.results if not r.error]
        failed_requests = [r for r in self.results if r.error]
        
        response_times = [r.response_time_ms for r in self.results]
        
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        return LoadTestSummary(
            total_requests=len(self.results),
            successful_requests=len(successful_requests),
            failed_requests=len(failed_requests),
            avg_response_time_ms=statistics.mean(response_times),
            min_response_time_ms=min(response_times),
            max_response_time_ms=max(response_times),
            p50_response_time_ms=np.percentile(response_times, 50),
            p95_response_time_ms=np.percentile(response_times, 95),
            p99_response_time_ms=np.percentile(response_times, 99),
            requests_per_second=len(self.results) / duration if duration > 0 else 0,
            error_rate_percent=(len(failed_requests) / len(self.results)) * 100,
            duration_seconds=duration,
            start_time=self.start_time or datetime.utcnow(),
            end_time=self.end_time or datetime.utcnow()
        )
    
    def get_results_by_endpoint(self) -> Dict[str, List[LoadTestResult]]:
        """Get results grouped by endpoint"""
        grouped = {}
        for result in self.results:
            if result.endpoint not in grouped:
                grouped[result.endpoint] = []
            grouped[result.endpoint].append(result)
        return grouped
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get error summary by error type"""
        error_counts = {}
        for result in self.results:
            if result.error:
                error_type = result.error.split(':')[0] if ':' in result.error else result.error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts
    
    def export_results(self, format: str = "json") -> str:
        """Export test results"""
        if format == "json":
            data = {
                "config": {
                    "name": self.config.name,
                    "duration_seconds": self.config.duration_seconds,
                    "concurrent_users": self.config.concurrent_users,
                    "base_url": self.config.base_url
                },
                "summary": {
                    "total_requests": len(self.results),
                    "successful_requests": len([r for r in self.results if not r.error]),
                    "failed_requests": len([r for r in self.results if r.error]),
                    "avg_response_time_ms": statistics.mean([r.response_time_ms for r in self.results]) if self.results else 0,
                    "requests_per_second": len(self.results) / ((self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 1),
                    "error_rate_percent": (len([r for r in self.results if r.error]) / len(self.results)) * 100 if self.results else 0
                },
                "results": [
                    {
                        "endpoint": r.endpoint,
                        "method": r.method,
                        "status_code": r.status_code,
                        "response_time_ms": r.response_time_ms,
                        "timestamp": r.timestamp.isoformat(),
                        "error": r.error,
                        "response_size_bytes": r.response_size_bytes,
                        "user_id": r.user_id
                    }
                    for r in self.results
                ]
            }
            return json.dumps(data, indent=2)
        
        return ""

class LoadTestSuite:
    """Suite of load tests for comprehensive testing"""
    
    def __init__(self):
        self.tests: List[LoadTester] = []
        self.results: List[LoadTestSummary] = []
    
    def add_test(self, config: LoadTestConfig):
        """Add a load test to the suite"""
        self.tests.append(LoadTester(config))
    
    async def run_suite(self) -> List[LoadTestSummary]:
        """Run all tests in the suite"""
        self.results.clear()
        
        for i, test in enumerate(self.tests):
            logger.info(f"Running test {i+1}/{len(self.tests)}: {test.config.name}")
            
            try:
                result = await test.run_load_test()
                self.results.append(result)
                
                # Wait between tests
                if i < len(self.tests) - 1:
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"Test {test.config.name} failed: {e}")
        
        return self.results
    
    def generate_suite_report(self) -> Dict[str, Any]:
        """Generate comprehensive suite report"""
        if not self.results:
            return {}
        
        return {
            "suite_summary": {
                "total_tests": len(self.results),
                "total_requests": sum(r.total_requests for r in self.results),
                "total_successful_requests": sum(r.successful_requests for r in self.results),
                "total_failed_requests": sum(r.failed_requests for r in self.results),
                "overall_error_rate": (sum(r.failed_requests for r in self.results) / sum(r.total_requests for r in self.results)) * 100 if sum(r.total_requests for r in self.results) > 0 else 0,
                "avg_requests_per_second": statistics.mean([r.requests_per_second for r in self.results]),
                "avg_response_time_ms": statistics.mean([r.avg_response_time_ms for r in self.results])
            },
            "test_results": [
                {
                    "name": test.config.name,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "avg_response_time_ms": result.avg_response_time_ms,
                    "p95_response_time_ms": result.p95_response_time_ms,
                    "requests_per_second": result.requests_per_second,
                    "error_rate_percent": result.error_rate_percent
                }
                for test, result in zip(self.tests, self.results)
            ]
        }

# Predefined load test configurations
def create_basic_load_test(base_url: str = "http://localhost:8000") -> LoadTestConfig:
    """Create basic load test configuration"""
    return LoadTestConfig(
        name="Basic Load Test",
        duration_seconds=60,
        concurrent_users=10,
        base_url=base_url,
        endpoints=[
            {"path": "/health", "method": "GET"},
            {"path": "/api/v1/process/text", "method": "POST", "data": {"content": "Test content"}},
            {"path": "/api/v1/search", "method": "POST", "data": {"query": "test query"}}
        ]
    )

def create_stress_test(base_url: str = "http://localhost:8000") -> LoadTestConfig:
    """Create stress test configuration"""
    return LoadTestConfig(
        name="Stress Test",
        duration_seconds=300,
        concurrent_users=50,
        ramp_up_seconds=30,
        base_url=base_url,
        endpoints=[
            {"path": "/health", "method": "GET"},
            {"path": "/api/v1/process/text", "method": "POST", "data": {"content": "Stress test content"}},
            {"path": "/api/v1/search", "method": "POST", "data": {"query": "stress test query"}},
            {"path": "/api/v1/agents", "method": "GET"}
        ]
    )

def create_spike_test(base_url: str = "http://localhost:8000") -> LoadTestConfig:
    """Create spike test configuration"""
    return LoadTestConfig(
        name="Spike Test",
        duration_seconds=120,
        concurrent_users=100,
        ramp_up_seconds=5,
        ramp_down_seconds=5,
        base_url=base_url,
        endpoints=[
            {"path": "/health", "method": "GET"},
            {"path": "/api/v1/process/text", "method": "POST", "data": {"content": "Spike test content"}}
        ]
    )