#!/usr/bin/env python3
"""
Comprehensive Test Suite for API Lifecycle Management
Part of Issue #46: API Lifecycle Management

This test suite covers:
- Version management functionality
- Deployment management functionality
- Configuration management functionality
- Monitoring and alerting functionality
- Integration testing
- Performance testing
- API endpoint validation
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import requests
import time

# Import the modules under test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'api_lifecycle'))

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

class TestVersionManager:
    """Test suite for version management"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def version_manager(self, temp_dir):
        """Create version manager instance"""
        return VersionManager(temp_dir)
    
    def test_create_version(self, version_manager):
        """Test version creation"""
        version = version_manager.create_version("1.0.0", "Initial version")
        
        assert version.version == "1.0.0"
        assert version.status == VersionStatus.DRAFT
        assert version.description == "Initial version"
        assert version in version_manager.versions.values()
    
    def test_add_change(self, version_manager):
        """Test adding changes to version"""
        version_manager.create_version("1.0.0", "Initial version")
        
        change = version_manager.add_change(
            "1.0.0",
            ChangeType.ADDITIVE,
            "Added new endpoint",
            ["/users"],
            impact_level="low"
        )
        
        assert change.change_type == ChangeType.ADDITIVE
        assert change.description == "Added new endpoint"
        assert change.affected_endpoints == ["/users"]
        
        version = version_manager.get_version("1.0.0")
        assert len(version.changes) == 1
        assert version.changes[0].change_id == change.change_id
    
    def test_release_version(self, version_manager):
        """Test version release"""
        version_manager.create_version("1.0.0", "Initial version")
        version = version_manager.release_version("1.0.0")
        
        assert version.status == VersionStatus.ACTIVE
        assert version.release_date is not None
    
    def test_deprecate_version(self, version_manager):
        """Test version deprecation"""
        version_manager.create_version("1.0.0", "Initial version")
        version_manager.release_version("1.0.0")
        version = version_manager.deprecate_version("1.0.0")
        
        assert version.status == VersionStatus.DEPRECATED
        assert version.deprecation_date is not None
    
    def test_compatibility_check(self, version_manager):
        """Test compatibility checking"""
        # Create version 1.0.0
        version_manager.create_version("1.0.0", "Initial version")
        version_manager.release_version("1.0.0")
        
        # Create version 2.0.0 with breaking changes
        version_manager.create_version("2.0.0", "Major update", parent_version="1.0.0")
        version_manager.add_change(
            "2.0.0",
            ChangeType.BREAKING,
            "Changed API structure",
            ["/users"],
            breaking_changes=["User ID format change"],
            impact_level="high"
        )
        
        compatibility = version_manager.check_compatibility("1.0.0", "2.0.0")
        
        assert compatibility["compatible"] == False
        assert compatibility["breaking_changes"] == 1
        assert compatibility["migration_complexity"] == "high"
    
    def test_migration_plan_generation(self, version_manager):
        """Test migration plan generation"""
        version_manager.create_version("1.0.0", "Initial version")
        version_manager.release_version("1.0.0")
        
        version_manager.create_version("2.0.0", "Major update")
        version_manager.add_change(
            "2.0.0",
            ChangeType.BREAKING,
            "Changed API structure",
            ["/users"],
            breaking_changes=["User ID format change"]
        )
        
        plan = version_manager.generate_migration_plan(
            "1.0.0", "2.0.0", MigrationStrategy.GRADUAL
        )
        
        assert plan["from_version"] == "1.0.0"
        assert plan["to_version"] == "2.0.0"
        assert plan["strategy"] == "gradual"
        assert len(plan["steps"]) > 0
        assert plan["estimated_duration"] is not None
    
    def test_version_listing(self, version_manager):
        """Test version listing with filters"""
        # Create multiple versions
        version_manager.create_version("1.0.0", "Version 1")
        version_manager.create_version("2.0.0", "Version 2")
        
        version_manager.release_version("1.0.0")
        version_manager.deprecate_version("1.0.0")
        
        # Test listing all versions
        all_versions = version_manager.list_versions()
        assert len(all_versions) == 2
        
        # Test filtering by status
        active_versions = version_manager.get_active_versions()
        assert len(active_versions) == 0  # 2.0.0 is still draft
        
        deprecated_versions = version_manager.get_deprecated_versions()
        assert len(deprecated_versions) == 1
        assert deprecated_versions[0].version == "1.0.0"
    
    def test_policy_management(self, version_manager):
        """Test version policy management"""
        policy = version_manager.create_policy(
            "custom-policy",
            "Custom Policy",
            "Custom version policy",
            deprecation_period_days=60,
            sunset_period_days=120,
            max_active_versions=5
        )
        
        assert policy.policy_id == "custom-policy"
        assert policy.deprecation_period_days == 60
        assert policy.max_active_versions == 5
        
        retrieved_policy = version_manager.get_policy("custom-policy")
        assert retrieved_policy.name == "Custom Policy"
    
    def test_version_summary(self, version_manager):
        """Test version summary generation"""
        version_manager.create_version("1.0.0", "Version 1")
        version_manager.create_version("2.0.0", "Version 2")
        
        version_manager.release_version("1.0.0")
        version_manager.add_change("2.0.0", ChangeType.BREAKING, "Breaking change", [])
        
        summary = version_manager.get_version_summary()
        
        assert summary["total_versions"] == 2
        assert summary["by_status"]["active"] == 1
        assert summary["by_status"]["draft"] == 1
        assert summary["breaking_changes_count"] == 1

class TestDeploymentManager:
    """Test suite for deployment management"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def deployment_manager(self, temp_dir):
        """Create deployment manager instance"""
        return DeploymentManager(temp_dir)
    
    def test_create_deployment_config(self, deployment_manager):
        """Test deployment configuration creation"""
        config = deployment_manager.create_deployment_config(
            "api-v1",
            "API Service v1",
            Environment.STAGING,
            DeploymentStrategy.BLUE_GREEN,
            "api:latest",
            replicas=2
        )
        
        assert config.config_id == "api-v1"
        assert config.name == "API Service v1"
        assert config.environment == Environment.STAGING
        assert config.strategy == DeploymentStrategy.BLUE_GREEN
        assert config.replicas == 2
    
    def test_deployment_creation(self, deployment_manager):
        """Test deployment creation"""
        # Create config first
        deployment_manager.create_deployment_config(
            "api-v1",
            "API Service v1",
            Environment.STAGING,
            DeploymentStrategy.BLUE_GREEN,
            "api:latest"
        )
        
        deployment = deployment_manager.deploy("api-v1")
        
        assert deployment.config.config_id == "api-v1"
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.deployment_id is not None
    
    def test_deployment_listing(self, deployment_manager):
        """Test deployment listing with filters"""
        # Create multiple deployments
        deployment_manager.create_deployment_config(
            "api-v1", "API v1", Environment.STAGING, DeploymentStrategy.BLUE_GREEN, "api:latest"
        )
        deployment_manager.create_deployment_config(
            "api-v2", "API v2", Environment.PRODUCTION, DeploymentStrategy.ROLLING, "api:v2"
        )
        
        deployment1 = deployment_manager.deploy("api-v1")
        deployment2 = deployment_manager.deploy("api-v2")
        
        # Test listing all deployments
        all_deployments = deployment_manager.list_deployments()
        assert len(all_deployments) == 2
        
        # Test filtering by environment
        staging_deployments = deployment_manager.list_deployments(Environment.STAGING)
        assert len(staging_deployments) == 1
        assert staging_deployments[0].config.environment == Environment.STAGING
    
    def test_deployment_logs(self, deployment_manager):
        """Test deployment log retrieval"""
        deployment_manager.create_deployment_config(
            "api-v1", "API v1", Environment.STAGING, DeploymentStrategy.BLUE_GREEN, "api:latest"
        )
        
        deployment = deployment_manager.deploy("api-v1")
        
        # Add some logs
        deployment_manager._add_log(deployment.deployment_id, "Test log message")
        
        logs = deployment_manager.get_deployment_logs(deployment.deployment_id)
        assert len(logs) > 0
        assert "Test log message" in logs[0]
    
    def test_rollback_functionality(self, deployment_manager):
        """Test deployment rollback"""
        deployment_manager.create_deployment_config(
            "api-v1", "API v1", Environment.STAGING, DeploymentStrategy.BLUE_GREEN, "api:latest"
        )
        
        deployment = deployment_manager.deploy("api-v1")
        
        # Simulate successful deployment
        deployment.status = DeploymentStatus.SUCCESS
        deployment_manager.deployments[deployment.deployment_id] = deployment
        
        # Test rollback
        success = deployment_manager.rollback(deployment.deployment_id, "Test rollback")
        
        assert success == True
        updated_deployment = deployment_manager.get_deployment(deployment.deployment_id)
        assert updated_deployment.status == DeploymentStatus.ROLLED_BACK
        assert updated_deployment.rollback_reason == "Test rollback"
    
    def test_environment_management(self, deployment_manager):
        """Test environment management"""
        env_config = deployment_manager.create_environment(
            "test-env",
            "Test Environment",
            "Test environment for testing",
            "https://test-api.example.com",
            "test-registry.com",
            "test-namespace",
            replicas=1
        )
        
        assert env_config["name"] == "Test Environment"
        assert env_config["base_url"] == "https://test-api.example.com"
        assert env_config["replicas"] == 1
        
        retrieved_env = deployment_manager.get_environment("test-env")
        assert retrieved_env["name"] == "Test Environment"
    
    def test_deployment_summary(self, deployment_manager):
        """Test deployment summary generation"""
        # Create and deploy multiple configurations
        deployment_manager.create_deployment_config(
            "api-v1", "API v1", Environment.STAGING, DeploymentStrategy.BLUE_GREEN, "api:latest"
        )
        deployment_manager.create_deployment_config(
            "api-v2", "API v2", Environment.PRODUCTION, DeploymentStrategy.ROLLING, "api:v2"
        )
        
        deployment1 = deployment_manager.deploy("api-v1")
        deployment2 = deployment_manager.deploy("api-v2")
        
        summary = deployment_manager.get_deployment_summary()
        
        assert summary["total_deployments"] == 2
        assert summary["by_environment"]["staging"] == 1
        assert summary["by_environment"]["production"] == 1
        assert summary["by_strategy"]["blue_green"] == 1
        assert summary["by_strategy"]["rolling"] == 1

class TestConfigManager:
    """Test suite for configuration management"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create config manager instance"""
        return ConfigManager(temp_dir)
    
    def test_create_configuration(self, config_manager):
        """Test configuration creation"""
        config = config_manager.create_configuration(
            "app-dev",
            "Application Development Config",
            ConfigType.APPLICATION,
            "development",
            {
                "app_name": "Test App",
                "port": 8000,
                "debug": True
            }
        )
        
        assert config.config_id == "app-dev"
        assert config.name == "Application Development Config"
        assert config.config_type == ConfigType.APPLICATION
        assert config.environment == "development"
        assert config.data["app_name"] == "Test App"
        assert config.data["port"] == 8000
    
    def test_configuration_validation(self, config_manager):
        """Test configuration validation against schema"""
        # Create a schema first
        schema = config_manager.create_schema(
            "app-schema",
            "Application Schema",
            ConfigType.APPLICATION,
            "1.0.0",
            {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string"},
                    "port": {"type": "integer", "minimum": 1, "maximum": 65535}
                },
                "required": ["app_name", "port"]
            },
            required_fields=["app_name", "port"]
        )
        
        # Test valid configuration
        config = config_manager.create_configuration(
            "app-valid",
            "Valid App Config",
            ConfigType.APPLICATION,
            "development",
            {"app_name": "Test App", "port": 8000},
            schema_id="app-schema"
        )
        
        assert config.config_id == "app-valid"
        
        # Test invalid configuration (missing required field)
        with pytest.raises(ValueError, match="Required field"):
            config_manager.create_configuration(
                "app-invalid",
                "Invalid App Config",
                ConfigType.APPLICATION,
                "development",
                {"app_name": "Test App"},  # Missing port
                schema_id="app-schema"
            )
    
    def test_configuration_update(self, config_manager):
        """Test configuration updates"""
        config = config_manager.create_configuration(
            "app-dev",
            "Application Development Config",
            ConfigType.APPLICATION,
            "development",
            {"app_name": "Test App", "port": 8000}
        )
        
        # Update configuration
        updated_config = config_manager.update_configuration(
            "app-dev",
            {"app_name": "Updated App", "port": 9000},
            version="1.1.0",
            description="Updated configuration"
        )
        
        assert updated_config.data["app_name"] == "Updated App"
        assert updated_config.data["port"] == 9000
        assert updated_config.version == "1.1.0"
        assert updated_config.description == "Updated configuration"
    
    def test_configuration_lifecycle(self, config_manager):
        """Test configuration lifecycle (draft -> active -> deprecated -> archived)"""
        config = config_manager.create_configuration(
            "app-dev",
            "Application Development Config",
            ConfigType.APPLICATION,
            "development",
            {"app_name": "Test App", "port": 8000}
        )
        
        assert config.status == ConfigStatus.DRAFT
        
        # Activate
        active_config = config_manager.activate_configuration("app-dev")
        assert active_config.status == ConfigStatus.ACTIVE
        
        # Deprecate
        deprecated_config = config_manager.deprecate_configuration("app-dev")
        assert deprecated_config.status == ConfigStatus.DEPRECATED
        
        # Archive
        archived_config = config_manager.archive_configuration("app-dev")
        assert archived_config.status == ConfigStatus.ARCHIVED
    
    def test_secret_management(self, config_manager):
        """Test secret creation and retrieval"""
        secret = config_manager.create_secret(
            "db-password",
            "Database Password",
            SecretType.PASSWORD,
            "secretpassword123",
            "development"
        )
        
        assert secret.secret_id == "db-password"
        assert secret.name == "Database Password"
        assert secret.secret_type == SecretType.PASSWORD
        assert secret.environment == "development"
        
        # Test secret value retrieval
        password = config_manager.get_secret_value("db-password")
        assert password == "secretpassword123"
    
    def test_secret_encryption(self, config_manager):
        """Test that secrets are properly encrypted"""
        secret = config_manager.create_secret(
            "test-secret",
            "Test Secret",
            SecretType.API_KEY,
            "plaintext-secret",
            "development"
        )
        
        # The stored value should be encrypted
        assert secret.encrypted_value != "plaintext-secret"
        assert len(secret.encrypted_value) > len("plaintext-secret")
        
        # But retrieval should return the original value
        retrieved_value = config_manager.get_secret_value("test-secret")
        assert retrieved_value == "plaintext-secret"
    
    def test_configuration_export_import(self, config_manager):
        """Test configuration export and import"""
        # Create and export configuration
        config = config_manager.create_configuration(
            "app-dev",
            "Application Development Config",
            ConfigType.APPLICATION,
            "development",
            {"app_name": "Test App", "port": 8000}
        )
        
        exported_json = config_manager.export_configuration("app-dev", "json")
        exported_data = json.loads(exported_json)
        
        assert exported_data["config_id"] == "app-dev"
        assert exported_data["data"]["app_name"] == "Test App"
        
        # Import configuration
        imported_config = config_manager.import_configuration(exported_json, "json")
        
        assert imported_config.config_id == "app-dev"
        assert imported_config.name == "Application Development Config"
        assert imported_config.data["app_name"] == "Test App"
    
    def test_configuration_history(self, config_manager):
        """Test configuration change history"""
        config = config_manager.create_configuration(
            "app-dev",
            "Application Development Config",
            ConfigType.APPLICATION,
            "development",
            {"app_name": "Test App", "port": 8000}
        )
        
        # Update configuration
        config_manager.update_configuration(
            "app-dev",
            {"app_name": "Updated App", "port": 9000}
        )
        
        # Get history
        history = config_manager.get_configuration_history("app-dev")
        
        assert len(history) == 2  # created + updated
        assert history[0]["action"] == "created"
        assert history[1]["action"] == "updated"
    
    def test_configuration_rollback(self, config_manager):
        """Test configuration rollback"""
        config = config_manager.create_configuration(
            "app-dev",
            "Application Development Config",
            ConfigType.APPLICATION,
            "development",
            {"app_name": "Test App", "port": 8000}
        )
        
        # Update configuration
        config_manager.update_configuration(
            "app-dev",
            {"app_name": "Updated App", "port": 9000}
        )
        
        # Get the update change ID
        history = config_manager.get_configuration_history("app-dev")
        update_change_id = history[1]["change_id"]
        
        # Rollback to previous state
        rolled_back_config = config_manager.rollback_configuration("app-dev", update_change_id)
        
        assert rolled_back_config.data["app_name"] == "Test App"
        assert rolled_back_config.data["port"] == 8000
    
    def test_configuration_summary(self, config_manager):
        """Test configuration summary generation"""
        # Create multiple configurations
        config_manager.create_configuration(
            "app-dev", "App Dev", ConfigType.APPLICATION, "development", {"port": 8000}
        )
        config_manager.create_configuration(
            "db-dev", "DB Dev", ConfigType.DATABASE, "development", {"host": "localhost"}
        )
        config_manager.create_configuration(
            "app-prod", "App Prod", ConfigType.APPLICATION, "production", {"port": 80}
        )
        
        summary = config_manager.get_configuration_summary()
        
        assert summary["total_configurations"] == 3
        assert summary["by_type"]["application"] == 2
        assert summary["by_type"]["database"] == 1
        assert summary["by_environment"]["development"] == 2
        assert summary["by_environment"]["production"] == 1

class TestMonitoringManager:
    """Test suite for monitoring and alerting"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def monitoring_manager(self, temp_dir):
        """Create monitoring manager instance"""
        return MonitoringManager(temp_dir)
    
    def test_metric_recording(self, monitoring_manager):
        """Test metric recording"""
        metric = monitoring_manager.record_metric(
            "api_requests",
            100,
            MetricType.COUNTER,
            {"endpoint": "/users"},
            "API request count"
        )
        
        assert metric.name == "api_requests"
        assert metric.value == 100
        assert metric.metric_type == MetricType.COUNTER
        assert metric.labels["endpoint"] == "/users"
        
        # Check that metric was stored
        metrics = monitoring_manager.get_metrics("api_requests")
        assert len(metrics) == 1
        assert metrics[0].metric_id == metric.metric_id
    
    def test_alert_rule_creation(self, monitoring_manager):
        """Test alert rule creation"""
        rule = monitoring_manager.create_alert_rule(
            "high-response-time",
            "High Response Time",
            "API response time is too high",
            "api_response_time",
            ">",
            1000,
            AlertSeverity.HIGH,
            cooldown_minutes=5
        )
        
        assert rule.rule_id == "high-response-time"
        assert rule.name == "High Response Time"
        assert rule.metric_name == "api_response_time"
        assert rule.condition == ">"
        assert rule.threshold == 1000
        assert rule.severity == AlertSeverity.HIGH
    
    def test_alert_triggering(self, monitoring_manager):
        """Test alert triggering"""
        # Create alert rule
        monitoring_manager.create_alert_rule(
            "high-response-time",
            "High Response Time",
            "API response time is too high",
            "api_response_time",
            ">",
            1000,
            AlertSeverity.HIGH
        )
        
        # Record metric that should trigger alert
        monitoring_manager.record_metric("api_response_time", 1500)
        
        # Check that alert was triggered
        active_alerts = monitoring_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].name == "High Response Time"
        assert active_alerts[0].metric_value == 1500
    
    def test_alert_acknowledgment(self, monitoring_manager):
        """Test alert acknowledgment"""
        # Create and trigger alert
        monitoring_manager.create_alert_rule(
            "test-alert",
            "Test Alert",
            "Test alert rule",
            "test_metric",
            ">",
            100,
            AlertSeverity.MEDIUM
        )
        
        monitoring_manager.record_metric("test_metric", 200)
        
        # Get the alert
        active_alerts = monitoring_manager.get_active_alerts()
        alert_id = active_alerts[0].alert_id
        
        # Acknowledge alert
        acknowledged_alert = monitoring_manager.acknowledge_alert(alert_id, "test-user")
        
        assert acknowledged_alert.status == AlertStatus.ACKNOWLEDGED
        assert acknowledged_alert.acknowledged_by == "test-user"
        assert acknowledged_alert.acknowledged_at is not None
    
    def test_alert_resolution(self, monitoring_manager):
        """Test alert resolution"""
        # Create and trigger alert
        monitoring_manager.create_alert_rule(
            "test-alert",
            "Test Alert",
            "Test alert rule",
            "test_metric",
            ">",
            100,
            AlertSeverity.MEDIUM
        )
        
        monitoring_manager.record_metric("test_metric", 200)
        
        # Get the alert
        active_alerts = monitoring_manager.get_active_alerts()
        alert_id = active_alerts[0].alert_id
        
        # Resolve alert
        resolved_alert = monitoring_manager.resolve_alert(alert_id)
        
        assert resolved_alert.status == AlertStatus.RESOLVED
        assert resolved_alert.resolved_at is not None
    
    def test_health_check_creation(self, monitoring_manager):
        """Test health check creation"""
        health_check = monitoring_manager.create_health_check(
            "api-health",
            "API Health Check",
            "http://localhost:8000/health",
            interval_seconds=30
        )
        
        assert health_check.check_id == "api-health"
        assert health_check.name == "API Health Check"
        assert health_check.url == "http://localhost:8000/health"
        assert health_check.interval_seconds == 30
    
    @pytest.mark.asyncio
    async def test_health_check_execution(self, monitoring_manager):
        """Test health check execution"""
        # Create health check
        monitoring_manager.create_health_check(
            "api-health",
            "API Health Check",
            "http://httpbin.org/status/200",  # Use httpbin for testing
            timeout=10
        )
        
        # Run health check
        health_status = await monitoring_manager.run_health_check("api-health")
        
        assert health_status.check_id == "api-health"
        assert health_status.status == HealthStatus.HEALTHY
        assert health_status.response_time_ms > 0
        assert health_status.status_code == 200
    
    def test_metric_summary(self, monitoring_manager):
        """Test metric summary generation"""
        # Record multiple metrics
        for i in range(10):
            monitoring_manager.record_metric("test_metric", i * 10)
        
        summary = monitoring_manager.get_metric_summary("test_metric", 24)
        
        assert summary["count"] == 10
        assert summary["min"] == 0
        assert summary["max"] == 90
        assert summary["mean"] == 45.0
        assert summary["median"] == 45.0
    
    def test_uptime_calculation(self, monitoring_manager):
        """Test uptime percentage calculation"""
        # Create health check
        monitoring_manager.create_health_check(
            "test-health",
            "Test Health Check",
            "http://localhost:8000/health"
        )
        
        # Simulate health check results
        for i in range(10):
            health_status = HealthStatus(
                check_id="test-health",
                status=HealthStatus.HEALTHY if i < 8 else HealthStatus.UNHEALTHY,
                response_time_ms=100.0,
                timestamp=datetime.now().isoformat()
            )
            monitoring_manager.health_statuses["test-health"].append(health_status)
        
        uptime = monitoring_manager.get_uptime_percentage("test-health", 24)
        
        assert uptime == 80.0  # 8 out of 10 healthy = 80%
    
    def test_incident_management(self, monitoring_manager):
        """Test incident creation and management"""
        # Create incident
        incident = monitoring_manager.create_incident(
            "incident-1",
            "API Outage",
            "API service is down",
            AlertSeverity.CRITICAL,
            alert_ids=["alert-1", "alert-2"]
        )
        
        assert incident.incident_id == "incident-1"
        assert incident.title == "API Outage"
        assert incident.severity == AlertSeverity.CRITICAL
        assert incident.status == "open"
        assert len(incident.alerts) == 2
        
        # Update incident status
        updated_incident = monitoring_manager.update_incident_status(
            "incident-1",
            "investigating",
            "Investigating the issue",
            "admin"
        )
        
        assert updated_incident.status == "investigating"
        assert len(updated_incident.timeline) == 2  # created + status change
    
    def test_monitoring_summary(self, monitoring_manager):
        """Test monitoring summary generation"""
        # Create some test data
        monitoring_manager.create_alert_rule(
            "test-rule", "Test Rule", "Test", "test_metric", ">", 100, AlertSeverity.HIGH
        )
        monitoring_manager.create_health_check(
            "test-health", "Test Health", "http://localhost:8000/health"
        )
        
        # Record some metrics
        monitoring_manager.record_metric("test_metric", 50)
        monitoring_manager.record_metric("test_metric", 150)  # Should trigger alert
        
        summary = monitoring_manager.get_monitoring_summary()
        
        assert summary["total_alert_rules"] == 1
        assert summary["total_health_checks"] == 1
        assert summary["active_alerts"] == 1
        assert summary["monitoring_active"] == False  # Not started in test

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def managers(self, temp_dir):
        """Create all manager instances"""
        return {
            "version": VersionManager(temp_dir / "versions"),
            "deployment": DeploymentManager(temp_dir / "deployments"),
            "config": ConfigManager(temp_dir / "configs"),
            "monitoring": MonitoringManager(temp_dir / "monitoring")
        }
    
    def test_complete_lifecycle(self, managers):
        """Test complete API lifecycle from version creation to deployment"""
        vm = managers["version"]
        dm = managers["deployment"]
        cm = managers["config"]
        mm = managers["monitoring"]
        
        # 1. Create API version
        version = vm.create_version("1.0.0", "Initial API version")
        vm.add_change("1.0.0", ChangeType.ADDITIVE, "Added user endpoints", ["/users"])
        vm.release_version("1.0.0")
        
        # 2. Create configuration
        config = cm.create_configuration(
            "api-config",
            "API Configuration",
            ConfigType.APPLICATION,
            "staging",
            {"port": 8000, "host": "0.0.0.0"}
        )
        cm.activate_configuration("api-config")
        
        # 3. Create deployment configuration
        deploy_config = dm.create_deployment_config(
            "api-deploy",
            "API Deployment",
            Environment.STAGING,
            DeploymentStrategy.BLUE_GREEN,
            "api:1.0.0"
        )
        
        # 4. Create health check
        health_check = mm.create_health_check(
            "api-health",
            "API Health Check",
            "http://localhost:8000/health"
        )
        
        # 5. Create alert rule
        alert_rule = mm.create_alert_rule(
            "high-response-time",
            "High Response Time",
            "API response time is too high",
            "api_response_time",
            ">",
            1000,
            AlertSeverity.HIGH
        )
        
        # 6. Deploy
        deployment = dm.deploy("api-deploy")
        
        # Verify all components are created
        assert vm.get_version("1.0.0") is not None
        assert cm.get_configuration("api-config") is not None
        assert dm.get_deployment(deployment.deployment_id) is not None
        assert mm.health_checks["api-health"] is not None
        assert mm.alert_rules["high-response-time"] is not None
    
    def test_version_migration_workflow(self, managers):
        """Test version migration workflow"""
        vm = managers["version"]
        dm = managers["deployment"]
        
        # Create version 1.0.0
        vm.create_version("1.0.0", "Initial version")
        vm.release_version("1.0.0")
        
        # Create version 2.0.0 with breaking changes
        vm.create_version("2.0.0", "Major update", parent_version="1.0.0")
        vm.add_change("2.0.0", ChangeType.BREAKING, "Changed API structure", ["/users"])
        
        # Generate migration plan
        plan = vm.generate_migration_plan("1.0.0", "2.0.0", MigrationStrategy.GRADUAL)
        
        # Execute migration
        migration = vm.execute_migration("1.0.0", "2.0.0", MigrationStrategy.GRADUAL)
        
        # Complete migration
        vm.complete_migration(migration["migration_id"], success=True)
        
        # Verify migration was recorded
        history = vm.get_migration_history()
        assert len(history) == 1
        assert history[0]["status"] == "completed"
    
    def test_configuration_environment_workflow(self, managers):
        """Test configuration across environments"""
        cm = managers["config"]
        
        # Create configurations for different environments
        dev_config = cm.create_configuration(
            "app-dev", "App Dev", ConfigType.APPLICATION, "development",
            {"debug": True, "port": 8000}
        )
        
        staging_config = cm.create_configuration(
            "app-staging", "App Staging", ConfigType.APPLICATION, "staging",
            {"debug": False, "port": 8000}
        )
        
        prod_config = cm.create_configuration(
            "app-prod", "App Prod", ConfigType.APPLICATION, "production",
            {"debug": False, "port": 80}
        )
        
        # Activate all configurations
        cm.activate_configuration("app-dev")
        cm.activate_configuration("app-staging")
        cm.activate_configuration("app-prod")
        
        # Verify configurations are environment-specific
        dev_active = cm.get_configuration_for_environment("App Dev", "development", ConfigType.APPLICATION)
        staging_active = cm.get_configuration_for_environment("App Staging", "staging", ConfigType.APPLICATION)
        prod_active = cm.get_configuration_for_environment("App Prod", "production", ConfigType.APPLICATION)
        
        assert dev_active.data["debug"] == True
        assert staging_active.data["debug"] == False
        assert prod_active.data["port"] == 80
    
    def test_monitoring_alert_workflow(self, managers):
        """Test monitoring and alerting workflow"""
        mm = managers["monitoring"]
        
        # Create health check
        mm.create_health_check(
            "api-health",
            "API Health Check",
            "http://localhost:8000/health"
        )
        
        # Create alert rule
        mm.create_alert_rule(
            "health-check-failed",
            "Health Check Failed",
            "API health check is failing",
            "health_check_status_api-health",
            "==",
            0,
            AlertSeverity.CRITICAL
        )
        
        # Record metrics that should trigger alert
        mm.record_metric("health_check_status_api-health", 0)  # Unhealthy
        
        # Check that alert was triggered
        active_alerts = mm.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].name == "Health Check Failed"
        
        # Create incident
        incident = mm.create_incident(
            "incident-1",
            "API Health Issue",
            "API health check is failing",
            AlertSeverity.CRITICAL,
            alert_ids=[active_alerts[0].alert_id]
        )
        
        # Acknowledge alert
        mm.acknowledge_alert(active_alerts[0].alert_id, "admin")
        
        # Resolve alert
        mm.record_metric("health_check_status_api-health", 1)  # Healthy
        mm.resolve_alert(active_alerts[0].alert_id)
        
        # Update incident
        mm.update_incident_status("incident-1", "resolved", "Issue resolved", "admin")
        
        # Verify workflow completion
        assert len(mm.get_active_alerts()) == 0
        assert incident.status == "resolved"

class TestPerformance:
    """Performance tests"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_metric_recording_performance(self, temp_dir):
        """Test metric recording performance"""
        mm = MonitoringManager(temp_dir)
        
        # Record 1000 metrics
        start_time = time.time()
        
        for i in range(1000):
            mm.record_metric(f"metric_{i % 10}", i, MetricType.GAUGE)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 5.0  # Less than 5 seconds
        
        # Verify metrics were recorded
        assert len(mm.metrics) == 10  # 10 different metric names
        total_metrics = sum(len(metrics) for metrics in mm.metrics.values())
        assert total_metrics == 1000
    
    def test_configuration_creation_performance(self, temp_dir):
        """Test configuration creation performance"""
        cm = ConfigManager(temp_dir)
        
        # Create 100 configurations
        start_time = time.time()
        
        for i in range(100):
            cm.create_configuration(
                f"config-{i}",
                f"Configuration {i}",
                ConfigType.APPLICATION,
                "development",
                {"value": i}
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 2.0  # Less than 2 seconds
        
        # Verify configurations were created
        assert len(cm.configurations) == 100
    
    def test_version_management_performance(self, temp_dir):
        """Test version management performance"""
        vm = VersionManager(temp_dir)
        
        # Create 50 versions with changes
        start_time = time.time()
        
        for i in range(50):
            version = f"1.{i}.0"
            vm.create_version(version, f"Version {i}")
            
            # Add multiple changes
            for j in range(5):
                vm.add_change(
                    version,
                    ChangeType.ADDITIVE,
                    f"Change {j}",
                    [f"/endpoint-{j}"]
                )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete in reasonable time
        assert duration < 3.0  # Less than 3 seconds
        
        # Verify versions and changes were created
        assert len(vm.versions) == 50
        total_changes = sum(len(version.changes) for version in vm.versions.values())
        assert total_changes == 250  # 50 versions * 5 changes each

if __name__ == "__main__":
    pytest.main([__file__, "-v"])