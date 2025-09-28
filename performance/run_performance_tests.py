#!/usr/bin/env python3
"""
Comprehensive Performance Testing Suite for LLM Multimodal Stack
"""
import asyncio
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add performance module to path
sys.path.append(str(Path(__file__).parent))

from performance_monitor import performance_monitor
from load_tester import LoadTestSuite, create_basic_load_test, create_stress_test, create_spike_test
from optimization_analyzer import optimization_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('performance_tests.log')
    ]
)
logger = logging.getLogger(__name__)

class PerformanceTestRunner:
    """Main performance test runner"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, Any] = {}
        self.start_time = datetime.utcnow()
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite"""
        logger.info("Starting comprehensive performance test suite")
        
        try:
            # Start performance monitoring
            await performance_monitor.start()
            
            # Run load tests
            load_test_results = await self._run_load_tests()
            
            # Collect performance metrics
            performance_metrics = await self._collect_performance_metrics()
            
            # Analyze performance data
            analysis_results = optimization_analyzer.analyze_performance_data(performance_metrics)
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(load_test_results, analysis_results)
            
            # Stop performance monitoring
            await performance_monitor.stop()
            
            self.results = report
            return report
            
        except Exception as e:
            logger.error(f"Performance test suite failed: {e}")
            raise
        finally:
            await performance_monitor.stop()
    
    async def _run_load_tests(self) -> Dict[str, Any]:
        """Run load test suite"""
        logger.info("Running load test suite")
        
        # Create test suite
        suite = LoadTestSuite()
        
        # Add different types of load tests
        suite.add_test(create_basic_load_test(self.base_url))
        suite.add_test(create_stress_test(self.base_url))
        suite.add_test(create_spike_test(self.base_url))
        
        # Run the suite
        test_results = await suite.run_suite()
        
        # Generate suite report
        suite_report = suite.generate_suite_report()
        
        return {
            "individual_tests": [
                {
                    "name": test.config.name,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "avg_response_time_ms": result.avg_response_time_ms,
                    "p95_response_time_ms": result.p95_response_time_ms,
                    "requests_per_second": result.requests_per_second,
                    "error_rate_percent": result.error_rate_percent,
                    "duration_seconds": result.duration_seconds
                }
                for test, result in zip(suite.tests, test_results)
            ],
            "suite_summary": suite_report["suite_summary"]
        }
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics from monitor"""
        logger.info("Collecting performance metrics")
        
        # Get all metric names
        metric_names = performance_monitor.get_all_metric_names()
        
        # Collect statistics for each metric
        metrics_data = {}
        for metric_name in metric_names:
            stats = performance_monitor.get_metric_stats(metric_name, window_minutes=10)
            if stats:
                metrics_data[metric_name] = [
                    {
                        "value": stats.last_value,
                        "timestamp": stats.last_updated.isoformat(),
                        "metadata": {"stats": {
                            "count": stats.count,
                            "mean": stats.mean,
                            "p95": stats.p95,
                            "p99": stats.p99
                        }}
                    }
                ]
        
        # Get system metrics
        system_stats = performance_monitor.get_system_stats(window_minutes=10)
        system_metrics = []
        if system_stats:
            system_metrics.append({
                "cpu_percent": system_stats["cpu_percent"]["current"],
                "memory_percent": system_stats["memory_percent"]["current"],
                "memory_used_mb": system_stats["memory_used_mb"]["current"],
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return {
            "metrics": metrics_data,
            "system_metrics": system_metrics
        }
    
    def _generate_comprehensive_report(self, load_test_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall performance score
        performance_score = self._calculate_performance_score(load_test_results, analysis_results)
        
        # Determine performance grade
        if performance_score >= 90:
            grade = "A"
        elif performance_score >= 80:
            grade = "B"
        elif performance_score >= 70:
            grade = "C"
        elif performance_score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        report = {
            "test_summary": {
                "test_suite": "Comprehensive Performance Test Suite",
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "base_url": self.base_url,
                "performance_score": performance_score,
                "performance_grade": grade
            },
            "load_test_results": load_test_results,
            "performance_analysis": analysis_results,
            "recommendations": {
                "immediate_actions": [
                    rec for rec in analysis_results.get("recommendations", [])
                    if rec.get("priority") == "critical"
                ],
                "high_priority_actions": [
                    rec for rec in analysis_results.get("recommendations", [])
                    if rec.get("priority") == "high"
                ],
                "medium_priority_actions": [
                    rec for rec in analysis_results.get("recommendations", [])
                    if rec.get("priority") == "medium"
                ]
            },
            "performance_thresholds": performance_monitor.get_thresholds(),
            "recent_alerts": performance_monitor.get_recent_alerts(hours=1)
        }
        
        return report
    
    def _calculate_performance_score(self, load_test_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        score = 100.0
        
        # Deduct points for load test issues
        suite_summary = load_test_results.get("suite_summary", {})
        error_rate = suite_summary.get("overall_error_rate", 0)
        if error_rate > 0:
            score -= min(error_rate * 2, 30)  # Up to 30 points for errors
        
        # Deduct points for bottlenecks
        bottlenecks = analysis_results.get("bottlenecks", [])
        for bottleneck in bottlenecks:
            severity = bottleneck.get("severity", "low")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            else:
                score -= 2
        
        # Deduct points for slow response times
        individual_tests = load_test_results.get("individual_tests", [])
        for test in individual_tests:
            avg_response_time = test.get("avg_response_time_ms", 0)
            if avg_response_time > 2000:  # 2 seconds
                score -= 10
            elif avg_response_time > 1000:  # 1 second
                score -= 5
        
        return max(0, min(100, score))
    
    def save_report(self, filename: str = None):
        """Save performance report to file"""
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Performance report saved to {filename}")
        return filename
    
    def print_summary(self):
        """Print performance test summary"""
        if not self.results:
            logger.warning("No results to display")
            return
        
        print("\n" + "="*80)
        print("PERFORMANCE TEST SUMMARY")
        print("="*80)
        
        summary = self.results.get("test_summary", {})
        print(f"Test Suite: {summary.get('test_suite', 'N/A')}")
        print(f"Duration: {summary.get('duration_seconds', 0):.1f} seconds")
        print(f"Performance Score: {summary.get('performance_score', 0):.1f}/100")
        print(f"Performance Grade: {summary.get('performance_grade', 'N/A')}")
        
        # Load test summary
        load_results = self.results.get("load_test_results", {})
        suite_summary = load_results.get("suite_summary", {})
        print(f"\nLoad Test Results:")
        print(f"  Total Requests: {suite_summary.get('total_requests', 0)}")
        print(f"  Success Rate: {100 - suite_summary.get('overall_error_rate', 0):.1f}%")
        print(f"  Avg RPS: {suite_summary.get('avg_requests_per_second', 0):.1f}")
        print(f"  Avg Response Time: {suite_summary.get('avg_response_time_ms', 0):.1f}ms")
        
        # Performance analysis summary
        analysis = self.results.get("performance_analysis", {})
        print(f"\nPerformance Analysis:")
        print(f"  System Health Score: {analysis.get('system_health_score', 0):.1f}/100")
        print(f"  Total Bottlenecks: {analysis.get('total_bottlenecks', 0)}")
        print(f"  Critical Issues: {analysis.get('critical_bottlenecks', 0)}")
        print(f"  Total Recommendations: {analysis.get('total_recommendations', 0)}")
        
        # Critical recommendations
        recommendations = self.results.get("recommendations", {})
        immediate_actions = recommendations.get("immediate_actions", [])
        if immediate_actions:
            print(f"\n🚨 IMMEDIATE ACTIONS REQUIRED:")
            for action in immediate_actions:
                print(f"  - {action.get('title', 'N/A')}")
        
        print("="*80)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run comprehensive performance tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for testing")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run performance tests
    runner = PerformanceTestRunner(args.base_url)
    
    try:
        results = await runner.run_comprehensive_tests()
        
        # Save report
        report_file = runner.save_report(args.output)
        
        # Print summary
        runner.print_summary()
        
        # Exit with appropriate code
        performance_score = results.get("test_summary", {}).get("performance_score", 0)
        if performance_score < 70:
            logger.error(f"Performance score {performance_score} is below acceptable threshold")
            sys.exit(1)
        else:
            logger.info(f"Performance test completed successfully with score {performance_score}")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())