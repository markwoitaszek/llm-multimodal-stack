"""
Performance monitoring and reporting tests for the LLM Multimodal Stack
"""
import pytest
import pytest_asyncio
import asyncio
import time
import json
import statistics
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx
from typing import List, Dict, Any, Tuple
import numpy as np

from tests.conftest import test_services, performance_thresholds


class TestPerformanceMonitoring:
    """Test cases for performance monitoring and reporting"""

    @pytest.fixture
    def monitoring_test_data(self):
        """Create test data for performance monitoring"""
        return {
            "documents": [
                "Machine learning is a subset of artificial intelligence.",
                "Deep learning uses neural networks with multiple layers.",
                "Natural language processing enables computers to understand human language.",
                "Computer vision allows machines to interpret visual information.",
                "Reinforcement learning learns through interaction with an environment."
            ],
            "queries": [
                "machine learning artificial intelligence",
                "deep learning neural networks",
                "natural language processing",
                "computer vision",
                "reinforcement learning"
            ]
        }

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, test_services, monitoring_test_data):
        """Test collection of comprehensive performance metrics"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        ai_agents = test_services["ai_agents"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Initialize metrics collection
            metrics = {
                "processing_metrics": [],
                "search_metrics": [],
                "agent_metrics": [],
                "system_metrics": []
            }
            
            # Collect processing metrics
            for i, document in enumerate(monitoring_test_data["documents"]):
                start_time = time.time()
                start_cpu = time.process_time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": document,
                        "document_name": f"monitoring_test_{i}.txt",
                        "metadata": {"test_type": "performance_monitoring", "iteration": i}
                    }
                )
                
                end_time = time.time()
                end_cpu = time.process_time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                metrics["processing_metrics"].append({
                    "iteration": i,
                    "response_time": end_time - start_time,
                    "cpu_time": end_cpu - start_cpu,
                    "content_length": len(document),
                    "success": True,
                    "timestamp": end_time
                })
            
            # Collect search metrics
            for i, query in enumerate(monitoring_test_data["queries"]):
                start_time = time.time()
                start_cpu = time.process_time()
                
                response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": query,
                        "modalities": ["text"],
                        "limit": 10,
                        "score_threshold": 0.3
                    }
                )
                
                end_time = time.time()
                end_cpu = time.process_time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                metrics["search_metrics"].append({
                    "iteration": i,
                    "response_time": end_time - start_time,
                    "cpu_time": end_cpu - start_cpu,
                    "query_length": len(query),
                    "results_count": len(result.get("results", [])),
                    "success": True,
                    "timestamp": end_time
                })
            
            # Collect agent metrics
            agent_response = await client.post(
                f"{ai_agents['url']}/api/v1/agents",
                json={
                    "name": "Performance Monitoring Agent",
                    "goal": "Execute tasks for performance monitoring",
                    "tools": ["search_content", "generate_text"],
                    "memory_window": 5,
                    "user_id": "monitoring_test_user"
                }
            )
            
            assert agent_response.status_code == 200
            agent_result = agent_response.json()
            agent_id = agent_result["agent_id"]
            
            for i, query in enumerate(monitoring_test_data["queries"][:3]):  # Test first 3 queries
                start_time = time.time()
                start_cpu = time.process_time()
                
                execution_response = await client.post(
                    f"{ai_agents['url']}/api/v1/agents/{agent_id}/execute",
                    json={
                        "task": f"Analyze search results for '{query}'",
                        "user_id": "monitoring_test_user"
                    }
                )
                
                end_time = time.time()
                end_cpu = time.process_time()
                
                assert execution_response.status_code == 200
                execution_result = execution_response.json()
                assert execution_result["success"] is True
                
                metrics["agent_metrics"].append({
                    "iteration": i,
                    "response_time": end_time - start_time,
                    "cpu_time": end_cpu - start_cpu,
                    "task_length": len(query),
                    "success": True,
                    "timestamp": end_time
                })
            
            # Analyze collected metrics
            self._analyze_performance_metrics(metrics)

    def _analyze_performance_metrics(self, metrics: Dict[str, List[Dict]]):
        """Analyze collected performance metrics"""
        # Analyze processing metrics
        processing_times = [m["response_time"] for m in metrics["processing_metrics"]]
        processing_stats = {
            "mean": statistics.mean(processing_times),
            "median": statistics.median(processing_times),
            "std": statistics.stdev(processing_times),
            "min": min(processing_times),
            "max": max(processing_times),
            "p95": np.percentile(processing_times, 95),
            "p99": np.percentile(processing_times, 99)
        }
        
        # Analyze search metrics
        search_times = [m["response_time"] for m in metrics["search_metrics"]]
        search_stats = {
            "mean": statistics.mean(search_times),
            "median": statistics.median(search_times),
            "std": statistics.stdev(search_times),
            "min": min(search_times),
            "max": max(search_times),
            "p95": np.percentile(search_times, 95),
            "p99": np.percentile(search_times, 99)
        }
        
        # Analyze agent metrics
        agent_times = [m["response_time"] for m in metrics["agent_metrics"]]
        agent_stats = {
            "mean": statistics.mean(agent_times),
            "median": statistics.median(agent_times),
            "std": statistics.stdev(agent_times),
            "min": min(agent_times),
            "max": max(agent_times),
            "p95": np.percentile(agent_times, 95),
            "p99": np.percentile(agent_times, 99)
        }
        
        # Validate performance characteristics
        assert processing_stats["mean"] < performance_thresholds["text_processing_time"], \
            f"Processing mean time {processing_stats['mean']:.2f}s exceeds threshold"
        
        assert search_stats["mean"] < performance_thresholds["search_response_time"], \
            f"Search mean time {search_stats['mean']:.2f}s exceeds threshold"
        
        assert agent_stats["mean"] < performance_thresholds["agent_execution_time"], \
            f"Agent mean time {agent_stats['mean']:.2f}s exceeds threshold"
        
        # Validate consistency (low standard deviation)
        assert processing_stats["std"] < processing_stats["mean"] * 0.5, \
            f"Processing time standard deviation {processing_stats['std']:.2f}s too high"
        
        assert search_stats["std"] < search_stats["mean"] * 0.5, \
            f"Search time standard deviation {search_stats['std']:.2f}s too high"
        
        assert agent_stats["std"] < agent_stats["mean"] * 0.5, \
            f"Agent time standard deviation {agent_stats['std']:.2f}s too high"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_trend_analysis(self, test_services, monitoring_test_data):
        """Test performance trend analysis over time"""
        multimodal_worker = test_services["multimodal_worker"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Collect performance data over time
            time_series_data = []
            num_measurements = 50
            
            for i in range(num_measurements):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])],
                        "document_name": f"trend_test_{i}.txt",
                        "metadata": {"test_type": "trend_analysis", "measurement": i}
                    }
                )
                
                end_time = time.time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                time_series_data.append({
                    "measurement": i,
                    "response_time": end_time - start_time,
                    "timestamp": end_time
                })
                
                # Small delay between measurements
                await asyncio.sleep(0.1)
            
            # Analyze trends
            response_times = [d["response_time"] for d in time_series_data]
            
            # Calculate trend using linear regression
            x = list(range(len(response_times)))
            y = response_times
            
            # Simple linear regression
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            # Calculate correlation coefficient
            mean_x = sum_x / n
            mean_y = sum_y / n
            
            numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
            denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
            denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))
            
            correlation = numerator / (denominator_x * denominator_y) ** 0.5
            
            # Analyze trend characteristics
            trend_analysis = {
                "slope": slope,
                "intercept": intercept,
                "correlation": correlation,
                "trend_direction": "improving" if slope < 0 else "degrading" if slope > 0 else "stable",
                "trend_strength": abs(correlation)
            }
            
            # Validate trend characteristics
            assert abs(slope) < 0.01, \
                f"Performance trend slope {slope:.4f} too steep (performance degrading or improving too rapidly)"
            
            assert abs(correlation) < 0.7, \
                f"Performance correlation {correlation:.3f} too strong (performance showing strong trend)"
            
            # Performance should be relatively stable
            early_performance = statistics.mean(response_times[:10])
            late_performance = statistics.mean(response_times[-10:])
            performance_change = (late_performance - early_performance) / early_performance
            
            assert abs(performance_change) < 0.3, \
                f"Performance change {performance_change:.1%} too large over time"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_anomaly_detection(self, test_services, monitoring_test_data):
        """Test detection of performance anomalies"""
        multimodal_worker = test_services["multimodal_worker"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Collect baseline performance data
            baseline_data = []
            num_baseline = 30
            
            for i in range(num_baseline):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])],
                        "document_name": f"baseline_test_{i}.txt",
                        "metadata": {"test_type": "anomaly_detection", "phase": "baseline"}
                    }
                )
                
                end_time = time.time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                baseline_data.append(end_time - start_time)
                
                await asyncio.sleep(0.1)
            
            # Calculate baseline statistics
            baseline_mean = statistics.mean(baseline_data)
            baseline_std = statistics.stdev(baseline_data)
            
            # Define anomaly thresholds (3 standard deviations)
            anomaly_threshold_high = baseline_mean + 3 * baseline_std
            anomaly_threshold_low = baseline_mean - 3 * baseline_std
            
            # Test anomaly detection
            test_data = []
            num_test = 20
            
            for i in range(num_test):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])],
                        "document_name": f"anomaly_test_{i}.txt",
                        "metadata": {"test_type": "anomaly_detection", "phase": "test"}
                    }
                )
                
                end_time = time.time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                response_time = end_time - start_time
                test_data.append(response_time)
                
                await asyncio.sleep(0.1)
            
            # Detect anomalies
            anomalies = []
            for i, response_time in enumerate(test_data):
                is_anomaly = response_time > anomaly_threshold_high or response_time < anomaly_threshold_low
                if is_anomaly:
                    anomalies.append({
                        "measurement": i,
                        "response_time": response_time,
                        "baseline_mean": baseline_mean,
                        "deviation": (response_time - baseline_mean) / baseline_std
                    })
            
            # Validate anomaly detection
            anomaly_rate = len(anomalies) / num_test
            
            # Anomaly rate should be low (less than 10% under normal conditions)
            assert anomaly_rate < 0.1, \
                f"Anomaly rate {anomaly_rate:.1%} too high, indicating performance issues"
            
            # If anomalies are detected, they should be within reasonable bounds
            for anomaly in anomalies:
                assert abs(anomaly["deviation"]) < 5, \
                    f"Anomaly deviation {anomaly['deviation']:.2f} too extreme"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_reporting(self, test_services, monitoring_test_data):
        """Test generation of performance reports"""
        multimodal_worker = test_services["multimodal_worker"]
        retrieval_proxy = test_services["retrieval_proxy"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Collect comprehensive performance data
            performance_data = {
                "processing": [],
                "search": [],
                "system": []
            }
            
            # Collect processing performance data
            for i in range(20):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])],
                        "document_name": f"report_test_{i}.txt",
                        "metadata": {"test_type": "performance_reporting"}
                    }
                )
                
                end_time = time.time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                performance_data["processing"].append({
                    "response_time": end_time - start_time,
                    "content_length": len(monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])]),
                    "success": True
                })
            
            # Collect search performance data
            for i in range(20):
                start_time = time.time()
                
                response = await client.post(
                    f"{retrieval_proxy['url']}/api/v1/search",
                    json={
                        "query": monitoring_test_data["queries"][i % len(monitoring_test_data["queries"])],
                        "modalities": ["text"],
                        "limit": 10
                    }
                )
                
                end_time = time.time()
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                performance_data["search"].append({
                    "response_time": end_time - start_time,
                    "query_length": len(monitoring_test_data["queries"][i % len(monitoring_test_data["queries"])]),
                    "results_count": len(result.get("results", [])),
                    "success": True
                })
            
            # Generate performance report
            report = self._generate_performance_report(performance_data)
            
            # Validate report structure and content
            assert "summary" in report
            assert "processing" in report
            assert "search" in report
            assert "recommendations" in report
            
            # Validate summary statistics
            summary = report["summary"]
            assert "total_requests" in summary
            assert "success_rate" in summary
            assert "avg_response_time" in summary
            assert "performance_grade" in summary
            
            assert summary["total_requests"] == 40  # 20 processing + 20 search
            assert summary["success_rate"] == 1.0  # All requests should succeed
            
            # Validate performance grade
            assert summary["performance_grade"] in ["A", "B", "C", "D", "F"]
            
            # Validate recommendations
            recommendations = report["recommendations"]
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0

    def _generate_performance_report(self, performance_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Generate a comprehensive performance report"""
        report = {
            "summary": {},
            "processing": {},
            "search": {},
            "recommendations": []
        }
        
        # Calculate summary statistics
        total_requests = sum(len(data) for data in performance_data.values())
        successful_requests = sum(
            sum(1 for item in data if item.get("success", False))
            for data in performance_data.values()
        )
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Calculate average response times
        all_response_times = []
        for data in performance_data.values():
            all_response_times.extend([item["response_time"] for item in data])
        
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        
        # Determine performance grade
        if avg_response_time < 1.0 and success_rate >= 0.99:
            performance_grade = "A"
        elif avg_response_time < 2.0 and success_rate >= 0.95:
            performance_grade = "B"
        elif avg_response_time < 5.0 and success_rate >= 0.90:
            performance_grade = "C"
        elif avg_response_time < 10.0 and success_rate >= 0.80:
            performance_grade = "D"
        else:
            performance_grade = "F"
        
        report["summary"] = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "performance_grade": performance_grade
        }
        
        # Analyze processing performance
        if performance_data["processing"]:
            processing_times = [item["response_time"] for item in performance_data["processing"]]
            report["processing"] = {
                "count": len(processing_times),
                "avg_time": statistics.mean(processing_times),
                "min_time": min(processing_times),
                "max_time": max(processing_times),
                "std_time": statistics.stdev(processing_times)
            }
        
        # Analyze search performance
        if performance_data["search"]:
            search_times = [item["response_time"] for item in performance_data["search"]]
            report["search"] = {
                "count": len(search_times),
                "avg_time": statistics.mean(search_times),
                "min_time": min(search_times),
                "max_time": max(search_times),
                "std_time": statistics.stdev(search_times)
            }
        
        # Generate recommendations
        if avg_response_time > 2.0:
            report["recommendations"].append("Consider optimizing response times - current average is above 2 seconds")
        
        if success_rate < 0.95:
            report["recommendations"].append("Improve reliability - success rate is below 95%")
        
        if performance_grade in ["D", "F"]:
            report["recommendations"].append("Performance requires immediate attention")
        
        if not report["recommendations"]:
            report["recommendations"].append("Performance is within acceptable parameters")
        
        return report

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_alerting(self, test_services, monitoring_test_data):
        """Test performance alerting mechanisms"""
        multimodal_worker = test_services["multimodal_worker"]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Simulate performance degradation scenario
            alerts = []
            
            # Collect baseline performance
            baseline_times = []
            for i in range(10):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])],
                        "document_name": f"alert_baseline_{i}.txt",
                        "metadata": {"test_type": "alerting", "phase": "baseline"}
                    }
                )
                
                end_time = time.time()
                baseline_times.append(end_time - start_time)
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                await asyncio.sleep(0.1)
            
            baseline_mean = statistics.mean(baseline_times)
            baseline_std = statistics.stdev(baseline_times)
            
            # Define alert thresholds
            warning_threshold = baseline_mean + 2 * baseline_std
            critical_threshold = baseline_mean + 3 * baseline_std
            
            # Test alerting with simulated degraded performance
            for i in range(20):
                start_time = time.time()
                
                response = await client.post(
                    f"{multimodal_worker['url']}/api/v1/process/text",
                    json={
                        "text": monitoring_test_data["documents"][i % len(monitoring_test_data["documents"])],
                        "document_name": f"alert_test_{i}.txt",
                        "metadata": {"test_type": "alerting", "phase": "test"}
                    }
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                assert response.status_code == 200
                result = response.json()
                assert result["success"] is True
                
                # Check for alerts
                if response_time > critical_threshold:
                    alerts.append({
                        "type": "critical",
                        "message": f"Critical performance degradation detected: {response_time:.2f}s > {critical_threshold:.2f}s",
                        "timestamp": end_time,
                        "value": response_time,
                        "threshold": critical_threshold
                    })
                elif response_time > warning_threshold:
                    alerts.append({
                        "type": "warning",
                        "message": f"Performance warning: {response_time:.2f}s > {warning_threshold:.2f}s",
                        "timestamp": end_time,
                        "value": response_time,
                        "threshold": warning_threshold
                    })
                
                await asyncio.sleep(0.1)
            
            # Validate alerting system
            # Under normal conditions, we shouldn't have too many alerts
            total_alerts = len(alerts)
            critical_alerts = len([a for a in alerts if a["type"] == "critical"])
            warning_alerts = len([a for a in alerts if a["type"] == "warning"])
            
            # Alert rates should be reasonable
            alert_rate = total_alerts / 20
            assert alert_rate < 0.3, \
                f"Alert rate {alert_rate:.1%} too high under normal conditions"
            
            # Critical alerts should be rare
            critical_rate = critical_alerts / 20
            assert critical_rate < 0.1, \
                f"Critical alert rate {critical_rate:.1%} too high"
            
            # Validate alert content
            for alert in alerts:
                assert "type" in alert
                assert "message" in alert
                assert "timestamp" in alert
                assert "value" in alert
                assert "threshold" in alert
                assert alert["type"] in ["warning", "critical"]
                assert alert["value"] > alert["threshold"]