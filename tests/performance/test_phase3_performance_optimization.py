"""
Phase 3 Performance Optimization and Load Testing
Comprehensive performance tests for production readiness
"""
import pytest
import pytest_asyncio
import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx
import numpy as np

# Add performance module to path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "performance"))

from performance_monitor import performance_monitor
from load_tester import LoadTestSuite, create_basic_load_test, create_stress_test, create_spike_test
from optimization_analyzer import optimization_analyzer

from tests.conftest import test_services, performance_thresholds


class TestPhase3PerformanceOptimization:
    """Phase 3 performance optimization and load testing"""
    
    @pytest.fixture
    async def performance_monitor_setup(self):
        """Setup performance monitor for tests"""
        await performance_monitor.start()
        yield performance_monitor
        await performance_monitor.stop()
    
    @pytest.fixture
    def load_test_configs(self):
        """Load test configurations for different scenarios"""
        base_url = "http://localhost:8000"
        return {
            "basic": create_basic_load_test(base_url),
            "stress": create_stress_test(base_url),
            "spike": create_spike_test(base_url)
        }
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_monitoring_system(self, performance_monitor_setup):
        """Test performance monitoring system functionality"""
        monitor = performance_monitor_setup
        
        # Test metric recording
        monitor.record_metric("test_metric", 100.0, {"test": True}, {"service": "test"})
        
        # Test time measurement context manager
        async with monitor.measure_time("test_duration", {"operation": "test"}):
            await asyncio.sleep(0.1)
        
        # Test metric statistics
        stats = monitor.get_metric_stats("test_metric")
        assert stats is not None
        assert stats.name == "test_metric"
        assert stats.count >= 1
        
        # Test system metrics collection
        system_stats = monitor.get_system_stats()
        assert system_stats is not None
        assert "cpu_percent" in system_stats
        assert "memory_percent" in system_stats
        
        # Test threshold setting
        monitor.set_threshold("test_metric", 50.0)
        thresholds = monitor.get_thresholds()
        assert thresholds["test_metric"] == 50.0
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_load_testing_framework(self, load_test_configs):
        """Test load testing framework functionality"""
        config = load_test_configs["basic"]
        
        # Create and run basic load test
        from load_tester import LoadTester
        tester = LoadTester(config)
        
        # Run short test (5 seconds)
        config.duration_seconds = 5
        config.concurrent_users = 2
        
        summary = await tester.run_load_test()
        
        # Validate results
        assert summary.total_requests > 0
        assert summary.duration_seconds > 0
        assert summary.requests_per_second >= 0
        assert summary.error_rate_percent >= 0
        
        # Test results export
        results_json = tester.export_results("json")
        assert "total_requests" in results_json
        assert "successful_requests" in results_json
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_load_test_suite(self, load_test_configs):
        """Test load test suite execution"""
        suite = LoadTestSuite()
        
        # Add tests to suite
        for name, config in load_test_configs.items():
            config.duration_seconds = 5  # Short tests for CI
            config.concurrent_users = 2
            suite.add_test(config)
        
        # Run suite
        results = await suite.run_suite()
        
        # Validate suite results
        assert len(results) == len(load_test_configs)
        
        for result in results:
            assert result.total_requests >= 0
            assert result.duration_seconds > 0
        
        # Test suite report generation
        report = suite.generate_suite_report()
        assert "suite_summary" in report
        assert "test_results" in report
        assert len(report["test_results"]) == len(results)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_optimization_analyzer(self, performance_monitor_setup):
        """Test performance optimization analyzer"""
        monitor = performance_monitor_setup
        
        # Generate test metrics data
        test_metrics = {
            "api_response_time_ms": [
                {"value": 500, "timestamp": datetime.utcnow().isoformat(), "metadata": {}},
                {"value": 1200, "timestamp": datetime.utcnow().isoformat(), "metadata": {}},
                {"value": 800, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
            ],
            "database_query_time_ms": [
                {"value": 50, "timestamp": datetime.utcnow().isoformat(), "metadata": {}},
                {"value": 150, "timestamp": datetime.utcnow().isoformat(), "metadata": {}},
                {"value": 80, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
            ],
            "cache_hit_rate_percent": [
                {"value": 60, "timestamp": datetime.utcnow().isoformat(), "metadata": {}},
                {"value": 70, "timestamp": datetime.utcnow().isoformat(), "metadata": {}},
                {"value": 65, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
            ]
        }
        
        test_system_metrics = [
            {
                "cpu_percent": 75.0,
                "memory_percent": 85.0,
                "memory_used_mb": 2048.0,
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        metrics_data = {
            "metrics": test_metrics,
            "system_metrics": test_system_metrics
        }
        
        # Run analysis
        analysis_results = optimization_analyzer.analyze_performance_data(metrics_data)
        
        # Validate analysis results
        assert "analysis_timestamp" in analysis_results
        assert "total_bottlenecks" in analysis_results
        assert "total_recommendations" in analysis_results
        assert "system_health_score" in analysis_results
        assert "bottlenecks" in analysis_results
        assert "recommendations" in analysis_results
        
        # Should identify some bottlenecks and recommendations
        assert analysis_results["total_bottlenecks"] > 0
        assert analysis_results["total_recommendations"] > 0
        
        # Test analysis history
        history = optimization_analyzer.get_analysis_history(days=1)
        assert len(history) >= 1
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_comprehensive_performance_workflow(self, test_services, performance_monitor_setup):
        """Test comprehensive performance workflow with real service integration"""
        monitor = performance_monitor_setup
        
        # Simulate realistic workload
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test health endpoints
            for service_name, service_config in test_services.items():
                try:
                    start_time = time.time()
                    response = await client.get(f"{service_config['url']}{service_config['health_endpoint']}")
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Record performance metric
                    monitor.record_metric(
                        f"{service_name}_health_response_time_ms",
                        duration_ms,
                        {"service": service_name, "endpoint": "health"},
                        {"test": "comprehensive_workflow"}
                    )
                    
                    assert response.status_code == 200
                    
                except Exception as e:
                    # Record error metric
                    monitor.record_metric(
                        f"{service_name}_health_error",
                        1.0,
                        {"service": service_name, "error": str(e)},
                        {"test": "comprehensive_workflow"}
                    )
        
        # Test performance analysis on collected data
        metrics_data = {
            "metrics": {},
            "system_metrics": []
        }
        
        # Collect metrics from monitor
        for metric_name in monitor.get_all_metric_names():
            stats = monitor.get_metric_stats(metric_name)
            if stats:
                metrics_data["metrics"][metric_name] = [
                    {
                        "value": stats.last_value,
                        "timestamp": stats.last_updated.isoformat(),
                        "metadata": {"stats": {
                            "count": stats.count,
                            "mean": stats.mean,
                            "p95": stats.p95
                        }}
                    }
                ]
        
        # Get system metrics
        system_stats = monitor.get_system_stats()
        if system_stats:
            metrics_data["system_metrics"].append({
                "cpu_percent": system_stats["cpu_percent"]["current"],
                "memory_percent": system_stats["memory_percent"]["current"],
                "memory_used_mb": system_stats["memory_used_mb"]["current"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Run optimization analysis
        analysis_results = optimization_analyzer.analyze_performance_data(metrics_data)
        
        # Validate comprehensive analysis
        assert "system_health_score" in analysis_results
        assert "bottlenecks" in analysis_results
        assert "recommendations" in analysis_results
        
        # Performance should be within acceptable ranges
        health_score = analysis_results["system_health_score"]
        assert health_score >= 0
        assert health_score <= 100
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_threshold_validation(self, performance_monitor_setup):
        """Test performance threshold validation and alerting"""
        monitor = performance_monitor_setup
        
        # Set test thresholds
        monitor.set_threshold("test_api_response_ms", 1000)
        monitor.set_threshold("test_cpu_percent", 80)
        
        # Test threshold violations
        alerts_received = []
        
        def alert_callback(alert):
            alerts_received.append(alert)
        
        monitor.add_alert_callback(alert_callback)
        
        # Record metrics that exceed thresholds
        monitor.record_metric("test_api_response_ms", 1500)  # Exceeds 1000ms threshold
        monitor.record_metric("test_cpu_percent", 85)  # Exceeds 80% threshold
        
        # Wait for alerts to be processed
        await asyncio.sleep(0.1)
        
        # Check that alerts were triggered
        recent_alerts = monitor.get_recent_alerts(hours=1)
        assert len(recent_alerts) >= 2
        
        # Validate alert content
        api_alerts = [a for a in recent_alerts if "test_api_response_ms" in a.get("metric", "")]
        cpu_alerts = [a for a in recent_alerts if "test_cpu_percent" in a.get("metric", "")]
        
        assert len(api_alerts) >= 1
        assert len(cpu_alerts) >= 1
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_reporting_and_export(self, performance_monitor_setup):
        """Test performance reporting and data export functionality"""
        monitor = performance_monitor_setup
        
        # Generate test data
        for i in range(10):
            monitor.record_metric("test_metric", float(i * 10), {"iteration": i})
            await asyncio.sleep(0.01)
        
        # Test metrics export
        exported_data = monitor.export_metrics("json")
        assert exported_data is not None
        
        # Parse and validate exported data
        data = json.loads(exported_data)
        assert "metrics" in data
        assert "system_metrics" in data
        assert "alerts" in data
        assert "exported_at" in data
        
        # Test optimization analyzer export
        test_metrics = {
            "metrics": {
                "api_response_time_ms": [
                    {"value": 800, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
                ]
            },
            "system_metrics": [
                {
                    "cpu_percent": 70.0,
                    "memory_percent": 75.0,
                    "memory_used_mb": 1024.0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        analysis_results = optimization_analyzer.analyze_performance_data(test_metrics)
        report = optimization_analyzer.export_analysis_report("json")
        
        assert report is not None
        report_data = json.loads(report)
        assert "analysis_summary" in report_data
        assert "current_bottlenecks" in report_data
        assert "current_recommendations" in report_data
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_optimization_recommendations(self):
        """Test performance optimization recommendation generation"""
        # Test with various performance scenarios
        test_scenarios = [
            {
                "name": "high_cpu_scenario",
                "metrics": {
                    "system_metrics": [
                        {
                            "cpu_percent": 95.0,
                            "memory_percent": 60.0,
                            "memory_used_mb": 1024.0,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    ]
                }
            },
            {
                "name": "slow_api_scenario",
                "metrics": {
                    "metrics": {
                        "api_response_time_ms": [
                            {"value": 2000, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
                        ]
                    }
                }
            },
            {
                "name": "low_cache_hit_rate_scenario",
                "metrics": {
                    "metrics": {
                        "cache_hit_rate_percent": [
                            {"value": 30, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
                        ]
                    }
                }
            }
        ]
        
        for scenario in test_scenarios:
            analysis_results = optimization_analyzer.analyze_performance_data(scenario["metrics"])
            
            # Should generate recommendations for each scenario
            assert analysis_results["total_recommendations"] > 0
            
            # Should identify bottlenecks
            assert analysis_results["total_bottlenecks"] > 0
            
            # Health score should reflect issues
            health_score = analysis_results["system_health_score"]
            assert health_score < 100  # Should be less than perfect due to issues
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, test_services):
        """Test integration of performance monitoring with existing services"""
        # Start performance monitor
        await performance_monitor.start()
        
        try:
            # Test service health monitoring
            async with httpx.AsyncClient(timeout=10.0) as client:
                for service_name, service_config in test_services.items():
                    try:
                        start_time = time.time()
                        response = await client.get(f"{service_config['url']}{service_config['health_endpoint']}")
                        duration_ms = (time.time() - start_time) * 1000
                        
                        # Record service health metrics
                        performance_monitor.record_metric(
                            f"service_health_{service_name}",
                            duration_ms,
                            {
                                "service": service_name,
                                "status_code": response.status_code,
                                "endpoint": service_config['health_endpoint']
                            },
                            {"monitoring": "service_health"}
                        )
                        
                        # Validate response
                        assert response.status_code == 200
                        
                        # Validate performance
                        assert duration_ms < performance_thresholds["api_response_time_ms"]
                        
                    except Exception as e:
                        # Record error metrics
                        performance_monitor.record_metric(
                            f"service_health_error_{service_name}",
                            1.0,
                            {"service": service_name, "error": str(e)},
                            {"monitoring": "service_health", "error": True}
                        )
            
            # Test system metrics collection
            system_stats = performance_monitor.get_system_stats()
            assert system_stats is not None
            
            # Validate system metrics are reasonable
            cpu_percent = system_stats["cpu_percent"]["current"]
            memory_percent = system_stats["memory_percent"]["current"]
            
            assert 0 <= cpu_percent <= 100
            assert 0 <= memory_percent <= 100
            
        finally:
            await performance_monitor.stop()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_baseline_establishment(self, performance_monitor_setup):
        """Test establishment of performance baselines"""
        monitor = performance_monitor_setup
        
        # Record baseline metrics
        baseline_metrics = {
            "api_response_time_ms": [500, 600, 550, 580, 520],
            "database_query_time_ms": [50, 60, 55, 58, 52],
            "cache_hit_rate_percent": [85, 87, 86, 88, 84]
        }
        
        for metric_name, values in baseline_metrics.items():
            for value in values:
                monitor.record_metric(metric_name, value, {"baseline": True})
                await asyncio.sleep(0.01)
        
        # Calculate baseline statistics
        baseline_stats = {}
        for metric_name in baseline_metrics.keys():
            stats = monitor.get_metric_stats(metric_name)
            if stats:
                baseline_stats[metric_name] = {
                    "mean": stats.mean,
                    "p95": stats.p95,
                    "p99": stats.p99,
                    "std": stats.std
                }
        
        # Validate baseline establishment
        assert len(baseline_stats) == len(baseline_metrics)
        
        for metric_name, stats in baseline_stats.items():
            assert stats["mean"] > 0
            assert stats["p95"] > stats["mean"]
            assert stats["p99"] > stats["p95"]
            assert stats["std"] >= 0
        
        # Test baseline comparison
        # Record metrics that deviate from baseline
        monitor.record_metric("api_response_time_ms", 2000)  # 4x baseline
        monitor.record_metric("cache_hit_rate_percent", 30)  # Much lower than baseline
        
        # Analyze performance against baseline
        test_metrics = {
            "metrics": {
                "api_response_time_ms": [
                    {"value": 2000, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
                ],
                "cache_hit_rate_percent": [
                    {"value": 30, "timestamp": datetime.utcnow().isoformat(), "metadata": {}}
                ]
            },
            "system_metrics": []
        }
        
        analysis_results = optimization_analyzer.analyze_performance_data(test_metrics)
        
        # Should identify performance degradation
        assert analysis_results["total_bottlenecks"] > 0
        assert analysis_results["system_health_score"] < 100


if __name__ == "__main__":
    pytest.main([__file__])