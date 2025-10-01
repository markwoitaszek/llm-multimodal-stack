"""Performance metrics module - stub implementation"""
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Track performance metrics"""
    
    def __init__(self):
        logger.info("PerformanceMetrics initialized")
    
    async def initialize(self):
        """Initialize performance metrics"""
        logger.info("PerformanceMetrics initialized successfully")
    
    async def start_metrics_collection(self):
        """Start collecting metrics"""
        logger.info("Metrics collection started")
    
    async def get_workflow_metrics(self, workflow_id: str, period: str):
        """Get workflow performance metrics"""
        return {
            "workflow_id": workflow_id,
            "period": period,
            "avg_execution_time": 0,
            "success_rate": 100.0,
            "total_executions": 0
        }

