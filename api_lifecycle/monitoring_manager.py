#!/usr/bin/env python3
"""
API Monitoring and Alerting System
Part of Issue #46: API Lifecycle Management

This module provides comprehensive API monitoring including:
- Health monitoring and status checks
- Performance metrics collection
- Alert management and notifications
- SLA monitoring and reporting
- Incident tracking and management
- Dashboard and reporting capabilities
"""

import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import requests
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import statistics
from collections import defaultdict, deque
import threading
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status enumeration"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class MetricType(Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class Metric:
    """Metric data point"""
    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    timestamp: str
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""

@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., "value > 100"
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 5
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    triggered_at: str
    resolved_at: Optional[str] = None
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """Health check definition"""
    check_id: str
    name: str
    url: str
    method: str = "GET"
    expected_status: int = 200
    timeout: int = 30
    interval_seconds: int = 60
    enabled: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None

@dataclass
class HealthStatus:
    """Health status result"""
    check_id: str
    status: HealthStatus
    response_time_ms: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SLA:
    """SLA definition"""
    sla_id: str
    name: str
    description: str
    target_uptime_percent: float
    target_response_time_ms: float
    measurement_period_days: int = 30
    enabled: bool = True

@dataclass
class Incident:
    """Incident record"""
    incident_id: str
    title: str
    description: str
    severity: AlertSeverity
    status: str  # open, investigating, resolved, closed
    created_at: str
    resolved_at: Optional[str] = None
    assigned_to: Optional[str] = None
    alerts: List[str] = field(default_factory=list)  # Alert IDs
    timeline: List[Dict[str, Any]] = field(default_factory=list)

class MonitoringManager:
    """Manages API monitoring and alerting"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Storage
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alerts: Dict[str, Alert] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_statuses: Dict[str, List[HealthStatus]] = defaultdict(list)
        self.slas: Dict[str, SLA] = {}
        self.incidents: Dict[str, Incident] = {}
        
        # Configuration files
        self.metrics_file = self.data_dir / "metrics.json"
        self.rules_file = self.data_dir / "alert_rules.json"
        self.alerts_file = self.data_dir / "alerts.json"
        self.health_file = self.data_dir / "health_checks.json"
        self.slas_file = self.data_dir / "slas.json"
        self.incidents_file = self.data_dir / "incidents.json"
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Notification settings
        self.notification_config = {
            "email": {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_emails": []
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "headers": {}
            }
        }
        
        # Load existing data
        self._load_data()
        
        # Initialize default SLAs
        self._initialize_default_slas()
    
    def _load_data(self):
        """Load monitoring data from files"""
        try:
            # Load metrics
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    for metric_name, metric_list in data.items():
                        self.metrics[metric_name] = [
                            Metric(**metric_data) for metric_data in metric_list
                        ]
            
            # Load alert rules
            if self.rules_file.exists():
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                    for rule_id, rule_data in data.items():
                        rule_data['severity'] = AlertSeverity(rule_data['severity'])
                        self.alert_rules[rule_id] = AlertRule(**rule_data)
            
            # Load alerts
            if self.alerts_file.exists():
                with open(self.alerts_file, 'r') as f:
                    data = json.load(f)
                    for alert_id, alert_data in data.items():
                        alert_data['severity'] = AlertSeverity(alert_data['severity'])
                        alert_data['status'] = AlertStatus(alert_data['status'])
                        self.alerts[alert_id] = Alert(**alert_data)
            
            # Load health checks
            if self.health_file.exists():
                with open(self.health_file, 'r') as f:
                    data = json.load(f)
                    for check_id, check_data in data.items():
                        self.health_checks[check_id] = HealthCheck(**check_data)
            
            # Load SLAs
            if self.slas_file.exists():
                with open(self.slas_file, 'r') as f:
                    data = json.load(f)
                    for sla_id, sla_data in data.items():
                        self.slas[sla_id] = SLA(**sla_data)
            
            # Load incidents
            if self.incidents_file.exists():
                with open(self.incidents_file, 'r') as f:
                    data = json.load(f)
                    for incident_id, incident_data in data.items():
                        incident_data['severity'] = AlertSeverity(incident_data['severity'])
                        self.incidents[incident_id] = Incident(**incident_data)
            
            logger.info(f"Loaded {len(self.alert_rules)} alert rules, {len(self.alerts)} alerts, {len(self.health_checks)} health checks")
            
        except Exception as e:
            logger.error(f"Error loading monitoring data: {e}")
    
    def _save_data(self):
        """Save monitoring data to files"""
        try:
            # Save metrics
            metrics_data = {}
            for metric_name, metric_list in self.metrics.items():
                metrics_data[metric_name] = [asdict(metric) for metric in metric_list]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Save alert rules
            rules_data = {}
            for rule_id, rule in self.alert_rules.items():
                rule_dict = asdict(rule)
                rule_dict['severity'] = rule.severity.value
                rules_data[rule_id] = rule_dict
            
            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            # Save alerts
            alerts_data = {}
            for alert_id, alert in self.alerts.items():
                alert_dict = asdict(alert)
                alert_dict['severity'] = alert.severity.value
                alert_dict['status'] = alert.status.value
                alerts_data[alert_id] = alert_dict
            
            with open(self.alerts_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            # Save health checks
            health_data = {check_id: asdict(check) for check_id, check in self.health_checks.items()}
            with open(self.health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
            # Save SLAs
            slas_data = {sla_id: asdict(sla) for sla_id, sla in self.slas.items()}
            with open(self.slas_file, 'w') as f:
                json.dump(slas_data, f, indent=2)
            
            # Save incidents
            incidents_data = {}
            for incident_id, incident in self.incidents.items():
                incident_dict = asdict(incident)
                incident_dict['severity'] = incident.severity.value
                incidents_data[incident_id] = incident_dict
            
            with open(self.incidents_file, 'w') as f:
                json.dump(incidents_data, f, indent=2)
            
            logger.info("Monitoring data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving monitoring data: {e}")
    
    def _initialize_default_slas(self):
        """Initialize default SLAs"""
        if not self.slas:
            # API availability SLA
            availability_sla = SLA(
                sla_id="api-availability",
                name="API Availability",
                description="API service availability SLA",
                target_uptime_percent=99.9,
                target_response_time_ms=500,
                measurement_period_days=30
            )
            
            # Response time SLA
            response_time_sla = SLA(
                sla_id="api-response-time",
                name="API Response Time",
                description="API response time SLA",
                target_uptime_percent=95.0,
                target_response_time_ms=1000,
                measurement_period_days=30
            )
            
            self.slas["api-availability"] = availability_sla
            self.slas["api-response-time"] = response_time_sla
            self._save_data()
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Dict[str, str] = None,
        description: str = ""
    ) -> Metric:
        """Record a metric"""
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now().isoformat(),
            labels=labels or {},
            description=description
        )
        
        self.metrics[name].append(metric)
        
        # Keep only last 1000 metrics per name
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
        
        # Check alert rules
        self._check_alert_rules(name, value, labels or {})
        
        logger.debug(f"Recorded metric {name}: {value}")
        return metric
    
    def _check_alert_rules(self, metric_name: str, value: float, labels: Dict[str, str]):
        """Check alert rules for a metric"""
        for rule_id, rule in self.alert_rules.items():
            if not rule.enabled or rule.metric_name != metric_name:
                continue
            
            # Check cooldown
            last_alert_time = self.last_alert_times.get(rule_id)
            if last_alert_time:
                cooldown_end = last_alert_time + timedelta(minutes=rule.cooldown_minutes)
                if datetime.now() < cooldown_end:
                    continue
            
            # Check condition
            if self._evaluate_condition(value, rule.condition, rule.threshold):
                self._trigger_alert(rule, value, labels)
                self.last_alert_times[rule_id] = datetime.now()
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            if ">" in condition:
                return value > threshold
            elif "<" in condition:
                return value < threshold
            elif ">=" in condition:
                return value >= threshold
            elif "<=" in condition:
                return value <= threshold
            elif "==" in condition or "=" in condition:
                return value == threshold
            else:
                return False
        except Exception:
            return False
    
    def _trigger_alert(self, rule: AlertRule, value: float, labels: Dict[str, str]):
        """Trigger an alert"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            triggered_at=datetime.now().isoformat(),
            metric_value=value,
            threshold=rule.threshold,
            labels=labels
        )
        
        self.alerts[alert.alert_id] = alert
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.warning(f"Alert triggered: {alert.name} (severity: {alert.severity.value})")
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        # Email notification
        if self.notification_config["email"]["enabled"]:
            self._send_email_notification(alert)
        
        # Webhook notification
        if self.notification_config["webhook"]["enabled"]:
            self._send_webhook_notification(alert)
    
    def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        try:
            config = self.notification_config["email"]
            
            msg = MimeMultipart()
            msg['From'] = config["from_email"]
            msg['To'] = ", ".join(config["to_emails"])
            msg['Subject'] = f"ALERT: {alert.name} - {alert.severity.value.upper()}"
            
            body = f"""
Alert Details:
- Name: {alert.name}
- Description: {alert.description}
- Severity: {alert.severity.value.upper()}
- Triggered At: {alert.triggered_at}
- Metric Value: {alert.metric_value}
- Threshold: {alert.threshold}
- Labels: {alert.labels}
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification"""
        try:
            config = self.notification_config["webhook"]
            
            payload = {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "description": alert.description,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "triggered_at": alert.triggered_at,
                "metric_value": alert.metric_value,
                "threshold": alert.threshold,
                "labels": alert.labels
            }
            
            response = requests.post(
                config["url"],
                json=payload,
                headers=config["headers"],
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook notification sent for alert {alert.alert_id}")
            else:
                logger.error(f"Webhook notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    def create_alert_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        metric_name: str,
        condition: str,
        threshold: float,
        severity: AlertSeverity,
        cooldown_minutes: int = 5,
        notification_channels: List[str] = None
    ) -> AlertRule:
        """Create an alert rule"""
        if rule_id in self.alert_rules:
            raise ValueError(f"Alert rule {rule_id} already exists")
        
        rule = AlertRule(
            rule_id=rule_id,
            name=name,
            description=description,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
            cooldown_minutes=cooldown_minutes,
            notification_channels=notification_channels or []
        )
        
        self.alert_rules[rule_id] = rule
        self._save_data()
        
        logger.info(f"Created alert rule: {rule_id}")
        return rule
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> Alert:
        """Acknowledge an alert"""
        if alert_id not in self.alerts:
            raise ValueError(f"Alert {alert_id} not found")
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now().isoformat()
        alert.acknowledged_by = acknowledged_by
        
        self._save_data()
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> Alert:
        """Resolve an alert"""
        if alert_id not in self.alerts:
            raise ValueError(f"Alert {alert_id} not found")
        
        alert = self.alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(f"Alert {alert_id} resolved")
        return alert
    
    def create_health_check(
        self,
        check_id: str,
        name: str,
        url: str,
        method: str = "GET",
        expected_status: int = 200,
        timeout: int = 30,
        interval_seconds: int = 60,
        headers: Dict[str, str] = None,
        body: Optional[str] = None
    ) -> HealthCheck:
        """Create a health check"""
        if check_id in self.health_checks:
            raise ValueError(f"Health check {check_id} already exists")
        
        health_check = HealthCheck(
            check_id=check_id,
            name=name,
            url=url,
            method=method,
            expected_status=expected_status,
            timeout=timeout,
            interval_seconds=interval_seconds,
            headers=headers or {},
            body=body
        )
        
        self.health_checks[check_id] = health_check
        self._save_data()
        
        logger.info(f"Created health check: {check_id}")
        return health_check
    
    async def run_health_check(self, check_id: str) -> HealthStatus:
        """Run a health check"""
        if check_id not in self.health_checks:
            raise ValueError(f"Health check {check_id} not found")
        
        health_check = self.health_checks[check_id]
        
        start_time = time.time()
        
        try:
            response = requests.request(
                method=health_check.method,
                url=health_check.url,
                headers=health_check.headers,
                data=health_check.body,
                timeout=health_check.timeout
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == health_check.expected_status:
                status = HealthStatus.HEALTHY
                error_message = None
            else:
                status = HealthStatus.UNHEALTHY
                error_message = f"Expected status {health_check.expected_status}, got {response.status_code}"
            
            health_status = HealthStatus(
                check_id=check_id,
                status=status,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                error_message=error_message,
                details={"response_text": response.text[:500]}
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            health_status = HealthStatus(
                check_id=check_id,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
        
        # Store health status
        self.health_statuses[check_id].append(health_status)
        
        # Keep only last 1000 health checks per check_id
        if len(self.health_statuses[check_id]) > 1000:
            self.health_statuses[check_id] = self.health_statuses[check_id][-1000:]
        
        # Record metrics
        self.record_metric(
            f"health_check_response_time_{check_id}",
            health_status.response_time_ms,
            MetricType.GAUGE,
            {"check_id": check_id, "status": health_status.status.value}
        )
        
        self.record_metric(
            f"health_check_status_{check_id}",
            1 if health_status.status == HealthStatus.HEALTHY else 0,
            MetricType.GAUGE,
            {"check_id": check_id}
        )
        
        return health_status
    
    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Run health checks
                for check_id, health_check in self.health_checks.items():
                    if health_check.enabled:
                        asyncio.run(self.run_health_check(check_id))
                
                # Sleep for a short interval
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)
    
    def get_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[Metric]:
        """Get metrics with optional filtering"""
        if metric_name not in self.metrics:
            return []
        
        metrics = self.metrics[metric_name]
        
        # Filter by time range
        if start_time:
            metrics = [m for m in metrics if datetime.fromisoformat(m.timestamp) >= start_time]
        
        if end_time:
            metrics = [m for m in metrics if datetime.fromisoformat(m.timestamp) <= end_time]
        
        # Filter by labels
        if labels:
            filtered_metrics = []
            for metric in metrics:
                match = True
                for key, value in labels.items():
                    if metric.labels.get(key) != value:
                        match = False
                        break
                if match:
                    filtered_metrics.append(metric)
            metrics = filtered_metrics
        
        return metrics
    
    def get_metric_summary(self, metric_name: str, period_hours: int = 24) -> Dict[str, Any]:
        """Get metric summary for a period"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)
        
        metrics = self.get_metrics(metric_name, start_time, end_time)
        
        if not metrics:
            return {"count": 0}
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "percentile_95": self._percentile(values, 95),
            "percentile_99": self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get active alerts"""
        return [
            alert for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]
    
    def get_health_status(self, check_id: str) -> Optional[HealthStatus]:
        """Get latest health status for a check"""
        if check_id not in self.health_statuses:
            return None
        
        statuses = self.health_statuses[check_id]
        return statuses[-1] if statuses else None
    
    def get_uptime_percentage(self, check_id: str, period_hours: int = 24) -> float:
        """Get uptime percentage for a health check"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=period_hours)
        
        if check_id not in self.health_statuses:
            return 0.0
        
        statuses = [
            status for status in self.health_statuses[check_id]
            if start_time <= datetime.fromisoformat(status.timestamp) <= end_time
        ]
        
        if not statuses:
            return 0.0
        
        healthy_count = sum(1 for status in statuses if status.status == HealthStatus.HEALTHY)
        return (healthy_count / len(statuses)) * 100
    
    def create_incident(
        self,
        incident_id: str,
        title: str,
        description: str,
        severity: AlertSeverity,
        alert_ids: List[str] = None
    ) -> Incident:
        """Create an incident"""
        if incident_id in self.incidents:
            raise ValueError(f"Incident {incident_id} already exists")
        
        incident = Incident(
            incident_id=incident_id,
            title=title,
            description=description,
            severity=severity,
            status="open",
            created_at=datetime.now().isoformat(),
            alerts=alert_ids or []
        )
        
        # Add initial timeline entry
        incident.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "action": "incident_created",
            "description": "Incident created",
            "user": "system"
        })
        
        self.incidents[incident_id] = incident
        self._save_data()
        
        logger.info(f"Created incident: {incident_id}")
        return incident
    
    def update_incident_status(
        self,
        incident_id: str,
        status: str,
        description: str = "",
        user: str = "system"
    ) -> Incident:
        """Update incident status"""
        if incident_id not in self.incidents:
            raise ValueError(f"Incident {incident_id} not found")
        
        incident = self.incidents[incident_id]
        old_status = incident.status
        incident.status = status
        
        if status == "resolved":
            incident.resolved_at = datetime.now().isoformat()
        
        # Add timeline entry
        incident.timeline.append({
            "timestamp": datetime.now().isoformat(),
            "action": "status_changed",
            "description": f"Status changed from {old_status} to {status}. {description}",
            "user": user
        })
        
        self._save_data()
        
        logger.info(f"Updated incident {incident_id} status to {status}")
        return incident
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        summary = {
            "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
            "total_alert_rules": len(self.alert_rules),
            "active_alerts": len(self.get_active_alerts()),
            "total_health_checks": len(self.health_checks),
            "total_incidents": len(self.incidents),
            "open_incidents": len([i for i in self.incidents.values() if i.status == "open"]),
            "monitoring_active": self.monitoring_active
        }
        
        # Health check summary
        health_summary = {}
        for check_id in self.health_checks.keys():
            uptime = self.get_uptime_percentage(check_id, 24)
            health_summary[check_id] = {
                "uptime_24h": uptime,
                "status": self.get_health_status(check_id).status.value if self.get_health_status(check_id) else "unknown"
            }
        
        summary["health_checks"] = health_summary
        
        return summary

async def main():
    """Main function to demonstrate monitoring manager"""
    data_dir = Path("./monitoring_data")
    manager = MonitoringManager(data_dir)
    
    # Create a health check
    health_check = manager.create_health_check(
        "api-health",
        "API Health Check",
        "http://localhost:8000/health",
        interval_seconds=30
    )
    
    print(f"Created health check: {health_check.check_id}")
    
    # Create an alert rule
    alert_rule = manager.create_alert_rule(
        "high-response-time",
        "High Response Time",
        "API response time is too high",
        "health_check_response_time_api-health",
        ">",
        1000,
        AlertSeverity.HIGH
    )
    
    print(f"Created alert rule: {alert_rule.rule_id}")
    
    # Record some metrics
    manager.record_metric("api_requests", 100, MetricType.COUNTER)
    manager.record_metric("api_response_time", 500, MetricType.GAUGE)
    
    print("Recorded metrics")
    
    # Run health check
    health_status = await manager.run_health_check("api-health")
    print(f"Health check result: {health_status.status.value}")
    
    # Get monitoring summary
    summary = manager.get_monitoring_summary()
    print(f"Monitoring summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())