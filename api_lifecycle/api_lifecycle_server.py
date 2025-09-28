#!/usr/bin/env python3
"""
API Lifecycle Management Server
Part of Issue #46: API Lifecycle Management

This FastAPI server provides comprehensive API lifecycle management including:
- Version management endpoints
- Deployment management endpoints
- Configuration management endpoints
- Monitoring and alerting endpoints
- Documentation and reporting endpoints
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Import our lifecycle management modules
from version_manager import (
    VersionManager, APIVersion, APIChange, VersionPolicy, VersionStatus, 
    ChangeType, MigrationStrategy
)
from deployment_manager import (
    DeploymentManager, Deployment, DeploymentConfig, DeploymentStatus,
    Environment, DeploymentStrategy
)
from config_manager import (
    ConfigManager, Configuration, ConfigSchema, Secret, ConfigTemplate,
    ConfigType, ConfigStatus, SecretType
)
from monitoring_manager import (
    MonitoringManager, Alert, AlertRule, HealthCheck, Incident, SLA,
    AlertSeverity, AlertStatus, MetricType, HealthStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="API Lifecycle Management",
    description="Comprehensive API lifecycle management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
version_manager: Optional[VersionManager] = None
deployment_manager: Optional[DeploymentManager] = None
config_manager: Optional[ConfigManager] = None
monitoring_manager: Optional[MonitoringManager] = None

# Pydantic models for API requests/responses
class VersionCreateRequest(BaseModel):
    version: str
    description: str = ""
    parent_version: Optional[str] = None
    policy_id: str = "default"

class ChangeCreateRequest(BaseModel):
    change_type: str
    description: str
    affected_endpoints: List[str]
    breaking_changes: List[str] = []
    migration_notes: str = ""
    impact_level: str = "low"

class DeploymentCreateRequest(BaseModel):
    config_id: str
    deployment_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ConfigCreateRequest(BaseModel):
    config_id: str
    name: str
    config_type: str
    environment: str
    data: Dict[str, Any]
    schema_id: Optional[str] = None
    parent_config: Optional[str] = None
    description: str = ""
    tags: List[str] = []

class SecretCreateRequest(BaseModel):
    secret_id: str
    name: str
    secret_type: str
    value: str
    environment: str
    expires_date: Optional[str] = None
    description: str = ""
    tags: List[str] = []

class AlertRuleCreateRequest(BaseModel):
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str
    threshold: float
    severity: str
    cooldown_minutes: int = 5
    notification_channels: List[str] = []

class HealthCheckCreateRequest(BaseModel):
    check_id: str
    name: str
    url: str
    method: str = "GET"
    expected_status: int = 200
    timeout: int = 30
    interval_seconds: int = 60
    headers: Dict[str, str] = {}
    body: Optional[str] = None

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize managers on startup"""
    global version_manager, deployment_manager, config_manager, monitoring_manager
    
    data_dir = Path("./lifecycle_data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize managers
    version_manager = VersionManager(data_dir / "versions")
    deployment_manager = DeploymentManager(data_dir / "deployments")
    config_manager = ConfigManager(data_dir / "configs")
    monitoring_manager = MonitoringManager(data_dir / "monitoring")
    
    # Start monitoring
    monitoring_manager.start_monitoring()
    
    logger.info("API Lifecycle Management server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global monitoring_manager
    
    if monitoring_manager:
        monitoring_manager.stop_monitoring()
    
    logger.info("API Lifecycle Management server stopped")

# Dependency functions
def get_version_manager() -> VersionManager:
    if not version_manager:
        raise HTTPException(status_code=500, detail="Version manager not initialized")
    return version_manager

def get_deployment_manager() -> DeploymentManager:
    if not deployment_manager:
        raise HTTPException(status_code=500, detail="Deployment manager not initialized")
    return deployment_manager

def get_config_manager() -> ConfigManager:
    if not config_manager:
        raise HTTPException(status_code=500, detail="Config manager not initialized")
    return config_manager

def get_monitoring_manager() -> MonitoringManager:
    if not monitoring_manager:
        raise HTTPException(status_code=500, detail="Monitoring manager not initialized")
    return monitoring_manager

# Version Management Endpoints
@app.get("/api/v1/versions")
async def list_versions(
    status: Optional[str] = Query(None),
    vm: VersionManager = Depends(get_version_manager)
):
    """List API versions"""
    try:
        version_status = VersionStatus(status) if status else None
        versions = vm.list_versions(version_status)
        return {"versions": [version.__dict__ for version in versions]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/versions")
async def create_version(
    request: VersionCreateRequest,
    vm: VersionManager = Depends(get_version_manager)
):
    """Create a new API version"""
    try:
        version = vm.create_version(
            request.version,
            request.description,
            request.parent_version,
            request.policy_id
        )
        return {"version": version.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/versions/{version}")
async def get_version(
    version: str,
    vm: VersionManager = Depends(get_version_manager)
):
    """Get a specific version"""
    try:
        api_version = vm.get_version(version)
        if not api_version:
            raise HTTPException(status_code=404, detail="Version not found")
        return {"version": api_version.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/versions/{version}/changes")
async def add_change(
    version: str,
    request: ChangeCreateRequest,
    vm: VersionManager = Depends(get_version_manager)
):
    """Add a change to a version"""
    try:
        change_type = ChangeType(request.change_type)
        change = vm.add_change(
            version,
            change_type,
            request.description,
            request.affected_endpoints,
            request.breaking_changes,
            request.migration_notes,
            request.impact_level
        )
        return {"change": change.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/versions/{version}/release")
async def release_version(
    version: str,
    release_date: Optional[str] = None,
    vm: VersionManager = Depends(get_version_manager)
):
    """Release a version"""
    try:
        api_version = vm.release_version(version, release_date)
        return {"version": api_version.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/versions/{version}/deprecate")
async def deprecate_version(
    version: str,
    deprecation_date: Optional[str] = None,
    policy_id: str = "default",
    vm: VersionManager = Depends(get_version_manager)
):
    """Deprecate a version"""
    try:
        api_version = vm.deprecate_version(version, deprecation_date, policy_id)
        return {"version": api_version.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/versions/{from_version}/compatibility/{to_version}")
async def check_compatibility(
    from_version: str,
    to_version: str,
    vm: VersionManager = Depends(get_version_manager)
):
    """Check compatibility between versions"""
    try:
        compatibility = vm.check_compatibility(from_version, to_version)
        return {"compatibility": compatibility}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Deployment Management Endpoints
@app.get("/api/v1/deployments")
async def list_deployments(
    environment: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    dm: DeploymentManager = Depends(get_deployment_manager)
):
    """List deployments"""
    try:
        env = Environment(environment) if environment else None
        deploy_status = DeploymentStatus(status) if status else None
        deployments = dm.list_deployments(env, deploy_status)
        return {"deployments": [deployment.__dict__ for deployment in deployments]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/deployments")
async def create_deployment(
    request: DeploymentCreateRequest,
    dm: DeploymentManager = Depends(get_deployment_manager)
):
    """Create a deployment"""
    try:
        deployment = dm.deploy(
            request.config_id,
            request.deployment_id,
            request.metadata
        )
        return {"deployment": deployment.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/deployments/{deployment_id}")
async def get_deployment(
    deployment_id: str,
    dm: DeploymentManager = Depends(get_deployment_manager)
):
    """Get a specific deployment"""
    try:
        deployment = dm.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        return {"deployment": deployment.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/deployments/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    dm: DeploymentManager = Depends(get_deployment_manager)
):
    """Get deployment logs"""
    try:
        logs = dm.get_deployment_logs(deployment_id)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/deployments/{deployment_id}/rollback")
async def rollback_deployment(
    deployment_id: str,
    reason: str = "Manual rollback",
    dm: DeploymentManager = Depends(get_deployment_manager)
):
    """Rollback a deployment"""
    try:
        success = dm.rollback(deployment_id, reason)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Configuration Management Endpoints
@app.get("/api/v1/configurations")
async def list_configurations(
    config_type: Optional[str] = Query(None),
    environment: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    cm: ConfigManager = Depends(get_config_manager)
):
    """List configurations"""
    try:
        cfg_type = ConfigType(config_type) if config_type else None
        cfg_status = ConfigStatus(status) if status else None
        configurations = cm.list_configurations(cfg_type, environment, cfg_status)
        return {"configurations": [config.__dict__ for config in configurations]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/configurations")
async def create_configuration(
    request: ConfigCreateRequest,
    cm: ConfigManager = Depends(get_config_manager)
):
    """Create a configuration"""
    try:
        config_type = ConfigType(request.config_type)
        configuration = cm.create_configuration(
            request.config_id,
            request.name,
            config_type,
            request.environment,
            request.data,
            request.schema_id,
            request.parent_config,
            request.description,
            request.tags
        )
        return {"configuration": configuration.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/configurations/{config_id}")
async def get_configuration(
    config_id: str,
    cm: ConfigManager = Depends(get_config_manager)
):
    """Get a specific configuration"""
    try:
        configuration = cm.get_configuration(config_id)
        if not configuration:
            raise HTTPException(status_code=404, detail="Configuration not found")
        return {"configuration": configuration.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/v1/configurations/{config_id}")
async def update_configuration(
    config_id: str,
    data: Dict[str, Any],
    version: Optional[str] = None,
    description: str = "",
    cm: ConfigManager = Depends(get_config_manager)
):
    """Update a configuration"""
    try:
        configuration = cm.update_configuration(config_id, data, version, description)
        return {"configuration": configuration.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/configurations/{config_id}/activate")
async def activate_configuration(
    config_id: str,
    cm: ConfigManager = Depends(get_config_manager)
):
    """Activate a configuration"""
    try:
        configuration = cm.activate_configuration(config_id)
        return {"configuration": configuration.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/secrets")
async def create_secret(
    request: SecretCreateRequest,
    cm: ConfigManager = Depends(get_config_manager)
):
    """Create a secret"""
    try:
        secret_type = SecretType(request.secret_type)
        secret = cm.create_secret(
            request.secret_id,
            request.name,
            secret_type,
            request.value,
            request.environment,
            request.expires_date,
            request.description,
            request.tags
        )
        return {"secret": secret.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/secrets/{secret_id}/value")
async def get_secret_value(
    secret_id: str,
    cm: ConfigManager = Depends(get_config_manager)
):
    """Get secret value (decrypted)"""
    try:
        value = cm.get_secret_value(secret_id)
        return {"value": value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Monitoring and Alerting Endpoints
@app.get("/api/v1/alerts")
async def list_alerts(
    status: Optional[str] = Query(None),
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """List alerts"""
    try:
        if status:
            alert_status = AlertStatus(status)
            alerts = [alert for alert in mm.alerts.values() if alert.status == alert_status]
        else:
            alerts = list(mm.alerts.values())
        
        return {"alerts": [alert.__dict__ for alert in alerts]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/alerts/active")
async def get_active_alerts(
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Get active alerts"""
    try:
        alerts = mm.get_active_alerts()
        return {"alerts": [alert.__dict__ for alert in alerts]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/alert-rules")
async def create_alert_rule(
    request: AlertRuleCreateRequest,
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Create an alert rule"""
    try:
        severity = AlertSeverity(request.severity)
        rule = mm.create_alert_rule(
            request.rule_id,
            request.name,
            request.description,
            request.metric_name,
            request.condition,
            request.threshold,
            severity,
            request.cooldown_minutes,
            request.notification_channels
        )
        return {"rule": rule.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str,
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Acknowledge an alert"""
    try:
        alert = mm.acknowledge_alert(alert_id, acknowledged_by)
        return {"alert": alert.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Resolve an alert"""
    try:
        alert = mm.resolve_alert(alert_id)
        return {"alert": alert.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/health-checks")
async def create_health_check(
    request: HealthCheckCreateRequest,
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Create a health check"""
    try:
        health_check = mm.create_health_check(
            request.check_id,
            request.name,
            request.url,
            request.method,
            request.expected_status,
            request.timeout,
            request.interval_seconds,
            request.headers,
            request.body
        )
        return {"health_check": health_check.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/health-checks/{check_id}/run")
async def run_health_check(
    check_id: str,
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Run a health check"""
    try:
        health_status = await mm.run_health_check(check_id)
        return {"health_status": health_status.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/health-checks/{check_id}/status")
async def get_health_status(
    check_id: str,
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Get health status for a check"""
    try:
        health_status = mm.get_health_status(check_id)
        if not health_status:
            raise HTTPException(status_code=404, detail="Health check not found")
        return {"health_status": health_status.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/health-checks/{check_id}/uptime")
async def get_uptime_percentage(
    check_id: str,
    period_hours: int = Query(24),
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Get uptime percentage for a health check"""
    try:
        uptime = mm.get_uptime_percentage(check_id, period_hours)
        return {"uptime_percentage": uptime}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Metrics Endpoints
@app.post("/api/v1/metrics")
async def record_metric(
    name: str,
    value: float,
    metric_type: str = "gauge",
    labels: Dict[str, str] = {},
    description: str = "",
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Record a metric"""
    try:
        mtype = MetricType(metric_type)
        metric = mm.record_metric(name, value, mtype, labels, description)
        return {"metric": metric.__dict__}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/metrics/{metric_name}")
async def get_metrics(
    metric_name: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    labels: Optional[str] = Query(None),
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Get metrics"""
    try:
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        labels_dict = json.loads(labels) if labels else None
        
        metrics = mm.get_metrics(metric_name, start_dt, end_dt, labels_dict)
        return {"metrics": [metric.__dict__ for metric in metrics]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/metrics/{metric_name}/summary")
async def get_metric_summary(
    metric_name: str,
    period_hours: int = Query(24),
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Get metric summary"""
    try:
        summary = mm.get_metric_summary(metric_name, period_hours)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Summary and Dashboard Endpoints
@app.get("/api/v1/summary")
async def get_lifecycle_summary(
    vm: VersionManager = Depends(get_version_manager),
    dm: DeploymentManager = Depends(get_deployment_manager),
    cm: ConfigManager = Depends(get_config_manager),
    mm: MonitoringManager = Depends(get_monitoring_manager)
):
    """Get comprehensive lifecycle summary"""
    try:
        version_summary = vm.get_version_summary()
        deployment_summary = dm.get_deployment_summary()
        config_summary = cm.get_configuration_summary()
        monitoring_summary = mm.get_monitoring_summary()
        
        return {
            "versions": version_summary,
            "deployments": deployment_summary,
            "configurations": config_summary,
            "monitoring": monitoring_summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "api-lifecycle-management"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "API Lifecycle Management",
        "version": "1.0.0",
        "description": "Comprehensive API lifecycle management system",
        "endpoints": {
            "versions": "/api/v1/versions",
            "deployments": "/api/v1/deployments",
            "configurations": "/api/v1/configurations",
            "monitoring": "/api/v1/alerts",
            "health_checks": "/api/v1/health-checks",
            "metrics": "/api/v1/metrics",
            "summary": "/api/v1/summary",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "api_lifecycle_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )