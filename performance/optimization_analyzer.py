"""
Performance Optimization Analyzer for LLM Multimodal Stack
"""
import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import statistics
import numpy as np
from pathlib import Path
import sqlite3
import threading

logger = logging.getLogger(__name__)

@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""
    type: str  # 'cpu', 'memory', 'disk', 'network', 'database', 'api'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    impact: str
    recommendation: str
    metrics: Dict[str, Any]
    timestamp: datetime

@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    category: str  # 'database', 'caching', 'api', 'infrastructure', 'code'
    priority: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    expected_improvement: str
    implementation_effort: str
    cost_impact: str
    metrics_affected: List[str]

class PerformanceOptimizationAnalyzer:
    """Advanced performance optimization analyzer"""
    
    def __init__(self):
        self.bottlenecks: List[PerformanceBottleneck] = []
        self.recommendations: List[OptimizationRecommendation] = []
        self.analysis_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        # Performance thresholds for analysis
        self.thresholds = {
            "cpu_percent": 70.0,
            "memory_percent": 80.0,
            "disk_io_mb_per_sec": 50.0,
            "network_mb_per_sec": 25.0,
            "api_response_time_ms": 1000,
            "database_query_time_ms": 100,
            "cache_hit_rate_percent": 80.0,
            "error_rate_percent": 5.0
        }
    
    def analyze_performance_data(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance data and identify bottlenecks"""
        logger.info("Starting performance analysis")
        
        analysis_start = datetime.utcnow()
        
        # Clear previous analysis
        with self._lock:
            self.bottlenecks.clear()
            self.recommendations.clear()
        
        # Analyze different aspects
        system_analysis = self._analyze_system_metrics(metrics_data.get("system_metrics", []))
        api_analysis = self._analyze_api_metrics(metrics_data.get("metrics", {}))
        database_analysis = self._analyze_database_metrics(metrics_data.get("metrics", {}))
        cache_analysis = self._analyze_cache_metrics(metrics_data.get("metrics", {}))
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Create analysis summary
        analysis_summary = {
            "analysis_timestamp": analysis_start.isoformat(),
            "analysis_duration_seconds": (datetime.utcnow() - analysis_start).total_seconds(),
            "total_bottlenecks": len(self.bottlenecks),
            "critical_bottlenecks": len([b for b in self.bottlenecks if b.severity == "critical"]),
            "high_priority_bottlenecks": len([b for b in self.bottlenecks if b.severity in ["critical", "high"]]),
            "total_recommendations": len(self.recommendations),
            "critical_recommendations": len([r for r in self.recommendations if r.priority == "critical"]),
            "system_health_score": self._calculate_health_score(),
            "bottlenecks": [
                {
                    "type": b.type,
                    "severity": b.severity,
                    "description": b.description,
                    "impact": b.impact,
                    "recommendation": b.recommendation,
                    "metrics": b.metrics,
                    "timestamp": b.timestamp.isoformat()
                }
                for b in self.bottlenecks
            ],
            "recommendations": [
                {
                    "category": r.category,
                    "priority": r.priority,
                    "title": r.title,
                    "description": r.description,
                    "expected_improvement": r.expected_improvement,
                    "implementation_effort": r.implementation_effort,
                    "cost_impact": r.cost_impact,
                    "metrics_affected": r.metrics_affected
                }
                for r in self.recommendations
            ]
        }
        
        # Store analysis history
        with self._lock:
            self.analysis_history.append(analysis_summary)
            if len(self.analysis_history) > 100:  # Keep last 100 analyses
                self.analysis_history.pop(0)
        
        logger.info(f"Performance analysis completed: {len(self.bottlenecks)} bottlenecks, {len(self.recommendations)} recommendations")
        
        return analysis_summary
    
    def _analyze_system_metrics(self, system_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze system-level performance metrics"""
        if not system_metrics:
            return {}
        
        # Calculate averages over time window
        recent_metrics = system_metrics[-100:] if len(system_metrics) > 100 else system_metrics
        
        avg_cpu = statistics.mean([m.get("cpu_percent", 0) for m in recent_metrics])
        avg_memory = statistics.mean([m.get("memory_percent", 0) for m in recent_metrics])
        max_cpu = max([m.get("cpu_percent", 0) for m in recent_metrics])
        max_memory = max([m.get("memory_percent", 0) for m in recent_metrics])
        
        # Check for CPU bottlenecks
        if avg_cpu > self.thresholds["cpu_percent"]:
            severity = "critical" if avg_cpu > 90 else "high" if avg_cpu > 80 else "medium"
            self.bottlenecks.append(PerformanceBottleneck(
                type="cpu",
                severity=severity,
                description=f"High CPU usage: {avg_cpu:.1f}% average, {max_cpu:.1f}% peak",
                impact="Reduced system responsiveness and potential service degradation",
                recommendation="Scale horizontally, optimize CPU-intensive operations, or upgrade hardware",
                metrics={"avg_cpu_percent": avg_cpu, "max_cpu_percent": max_cpu},
                timestamp=datetime.utcnow()
            ))
        
        # Check for memory bottlenecks
        if avg_memory > self.thresholds["memory_percent"]:
            severity = "critical" if avg_memory > 95 else "high" if avg_memory > 90 else "medium"
            self.bottlenecks.append(PerformanceBottleneck(
                type="memory",
                severity=severity,
                description=f"High memory usage: {avg_memory:.1f}% average, {max_memory:.1f}% peak",
                impact="Potential out-of-memory errors and system instability",
                recommendation="Optimize memory usage, implement memory caching, or increase RAM",
                metrics={"avg_memory_percent": avg_memory, "max_memory_percent": max_memory},
                timestamp=datetime.utcnow()
            ))
        
        return {
            "avg_cpu_percent": avg_cpu,
            "avg_memory_percent": avg_memory,
            "max_cpu_percent": max_cpu,
            "max_memory_percent": max_memory
        }
    
    def _analyze_api_metrics(self, api_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze API performance metrics"""
        api_analysis = {}
        
        for metric_name, metrics in api_metrics.items():
            if not metrics or not metric_name.endswith("_ms"):
                continue
            
            recent_metrics = metrics[-100:] if len(metrics) > 100 else metrics
            response_times = [m.get("value", 0) for m in recent_metrics]
            
            if not response_times:
                continue
            
            avg_response_time = statistics.mean(response_times)
            p95_response_time = np.percentile(response_times, 95)
            p99_response_time = np.percentile(response_times, 99)
            
            api_analysis[metric_name] = {
                "avg_response_time_ms": avg_response_time,
                "p95_response_time_ms": p95_response_time,
                "p99_response_time_ms": p99_response_time,
                "request_count": len(response_times)
            }
            
            # Check for slow API responses
            threshold = self.thresholds.get("api_response_time_ms", 1000)
            if avg_response_time > threshold:
                severity = "critical" if avg_response_time > threshold * 2 else "high" if avg_response_time > threshold * 1.5 else "medium"
                self.bottlenecks.append(PerformanceBottleneck(
                    type="api",
                    severity=severity,
                    description=f"Slow API response: {metric_name} averaging {avg_response_time:.1f}ms",
                    impact="Poor user experience and potential timeout errors",
                    recommendation="Optimize API logic, implement caching, or scale backend services",
                    metrics={"avg_response_time_ms": avg_response_time, "p95_response_time_ms": p95_response_time},
                    timestamp=datetime.utcnow()
                ))
        
        return api_analysis
    
    def _analyze_database_metrics(self, db_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze database performance metrics"""
        db_analysis = {}
        
        # Look for database-related metrics
        db_metric_names = [name for name in db_metrics.keys() if "database" in name.lower() or "query" in name.lower()]
        
        for metric_name in db_metric_names:
            metrics = db_metrics[metric_name]
            if not metrics:
                continue
            
            recent_metrics = metrics[-100:] if len(metrics) > 100 else metrics
            query_times = [m.get("value", 0) for m in recent_metrics]
            
            if not query_times:
                continue
            
            avg_query_time = statistics.mean(query_times)
            p95_query_time = np.percentile(query_times, 95)
            
            db_analysis[metric_name] = {
                "avg_query_time_ms": avg_query_time,
                "p95_query_time_ms": p95_query_time,
                "query_count": len(query_times)
            }
            
            # Check for slow database queries
            threshold = self.thresholds.get("database_query_time_ms", 100)
            if avg_query_time > threshold:
                severity = "critical" if avg_query_time > threshold * 5 else "high" if avg_query_time > threshold * 2 else "medium"
                self.bottlenecks.append(PerformanceBottleneck(
                    type="database",
                    severity=severity,
                    description=f"Slow database query: {metric_name} averaging {avg_query_time:.1f}ms",
                    impact="Reduced application performance and potential timeouts",
                    recommendation="Add database indexes, optimize queries, or implement query caching",
                    metrics={"avg_query_time_ms": avg_query_time, "p95_query_time_ms": p95_query_time},
                    timestamp=datetime.utcnow()
                ))
        
        return db_analysis
    
    def _analyze_cache_metrics(self, cache_metrics: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze cache performance metrics"""
        cache_analysis = {}
        
        # Look for cache-related metrics
        cache_metric_names = [name for name in cache_metrics.keys() if "cache" in name.lower() or "hit_rate" in name.lower()]
        
        for metric_name in cache_metric_names:
            metrics = cache_metrics[metric_name]
            if not metrics:
                continue
            
            recent_metrics = metrics[-100:] if len(metrics) > 100 else metrics
            hit_rates = [m.get("value", 0) for m in recent_metrics]
            
            if not hit_rates:
                continue
            
            avg_hit_rate = statistics.mean(hit_rates)
            cache_analysis[metric_name] = {
                "avg_hit_rate_percent": avg_hit_rate,
                "measurement_count": len(hit_rates)
            }
            
            # Check for low cache hit rates
            threshold = self.thresholds.get("cache_hit_rate_percent", 80)
            if avg_hit_rate < threshold:
                severity = "high" if avg_hit_rate < threshold * 0.5 else "medium"
                self.bottlenecks.append(PerformanceBottleneck(
                    type="cache",
                    severity=severity,
                    description=f"Low cache hit rate: {metric_name} averaging {avg_hit_rate:.1f}%",
                    impact="Increased database load and slower response times",
                    recommendation="Review cache strategy, increase cache size, or optimize cache keys",
                    metrics={"avg_hit_rate_percent": avg_hit_rate},
                    timestamp=datetime.utcnow()
                ))
        
        return cache_analysis
    
    def _generate_recommendations(self):
        """Generate optimization recommendations based on identified bottlenecks"""
        # Group bottlenecks by type
        bottleneck_types = {}
        for bottleneck in self.bottlenecks:
            if bottleneck.type not in bottleneck_types:
                bottleneck_types[bottleneck.type] = []
            bottleneck_types[bottleneck.type].append(bottleneck)
        
        # Generate recommendations for each bottleneck type
        for bottleneck_type, bottlenecks in bottleneck_types.items():
            if bottleneck_type == "cpu":
                self._generate_cpu_recommendations(bottlenecks)
            elif bottleneck_type == "memory":
                self._generate_memory_recommendations(bottlenecks)
            elif bottleneck_type == "api":
                self._generate_api_recommendations(bottlenecks)
            elif bottleneck_type == "database":
                self._generate_database_recommendations(bottlenecks)
            elif bottleneck_type == "cache":
                self._generate_cache_recommendations(bottlenecks)
    
    def _generate_cpu_recommendations(self, bottlenecks: List[PerformanceBottleneck]):
        """Generate CPU optimization recommendations"""
        critical_bottlenecks = [b for b in bottlenecks if b.severity == "critical"]
        
        if critical_bottlenecks:
            self.recommendations.append(OptimizationRecommendation(
                category="infrastructure",
                priority="critical",
                title="Immediate CPU Scaling Required",
                description="System experiencing critical CPU bottlenecks requiring immediate scaling",
                expected_improvement="50-80% reduction in response times",
                implementation_effort="High - requires infrastructure changes",
                cost_impact="High - additional compute resources needed",
                metrics_affected=["cpu_percent", "api_response_time_ms"]
            ))
        
        self.recommendations.append(OptimizationRecommendation(
            category="code",
            priority="high",
            title="Optimize CPU-Intensive Operations",
            description="Profile and optimize CPU-intensive code paths",
            expected_improvement="20-40% reduction in CPU usage",
            implementation_effort="Medium - code optimization required",
            cost_impact="Low - no additional infrastructure needed",
            metrics_affected=["cpu_percent", "api_response_time_ms"]
        ))
    
    def _generate_memory_recommendations(self, bottlenecks: List[PerformanceBottleneck]):
        """Generate memory optimization recommendations"""
        self.recommendations.append(OptimizationRecommendation(
            category="infrastructure",
            priority="high",
            title="Increase Memory Resources",
            description="Add more RAM to handle current memory requirements",
            expected_improvement="Prevent out-of-memory errors",
            implementation_effort="Medium - infrastructure scaling",
            cost_impact="Medium - additional memory costs",
            metrics_affected=["memory_percent", "api_response_time_ms"]
        ))
        
        self.recommendations.append(OptimizationRecommendation(
            category="caching",
            priority="medium",
            title="Implement Memory Caching Strategy",
            description="Optimize memory usage with intelligent caching",
            expected_improvement="30-50% reduction in memory pressure",
            implementation_effort="Medium - caching implementation",
            cost_impact="Low - software optimization",
            metrics_affected=["memory_percent", "cache_hit_rate_percent"]
        ))
    
    def _generate_api_recommendations(self, bottlenecks: List[PerformanceBottleneck]):
        """Generate API optimization recommendations"""
        self.recommendations.append(OptimizationRecommendation(
            category="api",
            priority="high",
            title="Implement API Response Caching",
            description="Cache API responses to reduce backend load",
            expected_improvement="60-80% reduction in response times for cached requests",
            implementation_effort="Medium - caching layer implementation",
            cost_impact="Low - software optimization",
            metrics_affected=["api_response_time_ms", "cache_hit_rate_percent"]
        ))
        
        self.recommendations.append(OptimizationRecommendation(
            category="api",
            priority="medium",
            title="Optimize API Endpoints",
            description="Review and optimize slow API endpoints",
            expected_improvement="20-40% reduction in response times",
            implementation_effort="Medium - code optimization",
            cost_impact="Low - development effort",
            metrics_affected=["api_response_time_ms"]
        ))
    
    def _generate_database_recommendations(self, bottlenecks: List[PerformanceBottleneck]):
        """Generate database optimization recommendations"""
        self.recommendations.append(OptimizationRecommendation(
            category="database",
            priority="high",
            title="Add Database Indexes",
            description="Create indexes for frequently queried columns",
            expected_improvement="50-90% reduction in query times",
            implementation_effort="Low - DBA task",
            cost_impact="Low - minimal storage overhead",
            metrics_affected=["database_query_time_ms"]
        ))
        
        self.recommendations.append(OptimizationRecommendation(
            category="database",
            priority="medium",
            title="Implement Query Optimization",
            description="Optimize slow database queries",
            expected_improvement="30-60% reduction in query times",
            implementation_effort="Medium - query analysis and optimization",
            cost_impact="Low - development effort",
            metrics_affected=["database_query_time_ms"]
        ))
    
    def _generate_cache_recommendations(self, bottlenecks: List[PerformanceBottleneck]):
        """Generate cache optimization recommendations"""
        self.recommendations.append(OptimizationRecommendation(
            category="caching",
            priority="high",
            title="Optimize Cache Strategy",
            description="Review and improve cache hit rates",
            expected_improvement="20-40% improvement in cache hit rates",
            implementation_effort="Medium - cache strategy review",
            cost_impact="Low - configuration changes",
            metrics_affected=["cache_hit_rate_percent", "api_response_time_ms"]
        ))
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        if not self.bottlenecks:
            return 100.0
        
        # Weight bottlenecks by severity
        severity_weights = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        total_weight = sum(severity_weights.get(b.severity, 1) for b in self.bottlenecks)
        
        # Calculate score (lower is better)
        max_possible_weight = len(self.bottlenecks) * 4
        health_score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        
        return round(health_score, 1)
    
    def get_analysis_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get analysis history for specified number of days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with self._lock:
            return [
                analysis for analysis in self.analysis_history
                if datetime.fromisoformat(analysis["analysis_timestamp"]) >= cutoff_date
            ]
    
    def export_analysis_report(self, format: str = "json") -> str:
        """Export comprehensive analysis report"""
        if format == "json":
            report = {
                "analysis_summary": {
                    "total_analyses": len(self.analysis_history),
                    "current_health_score": self._calculate_health_score(),
                    "total_bottlenecks": len(self.bottlenecks),
                    "total_recommendations": len(self.recommendations)
                },
                "current_bottlenecks": [
                    {
                        "type": b.type,
                        "severity": b.severity,
                        "description": b.description,
                        "impact": b.impact,
                        "recommendation": b.recommendation,
                        "metrics": b.metrics,
                        "timestamp": b.timestamp.isoformat()
                    }
                    for b in self.bottlenecks
                ],
                "current_recommendations": [
                    {
                        "category": r.category,
                        "priority": r.priority,
                        "title": r.title,
                        "description": r.description,
                        "expected_improvement": r.expected_improvement,
                        "implementation_effort": r.implementation_effort,
                        "cost_impact": r.cost_impact,
                        "metrics_affected": r.metrics_affected
                    }
                    for r in self.recommendations
                ],
                "analysis_history": self.analysis_history[-10:],  # Last 10 analyses
                "exported_at": datetime.utcnow().isoformat()
            }
            return json.dumps(report, indent=2)
        
        return ""

# Global analyzer instance
optimization_analyzer = PerformanceOptimizationAnalyzer()