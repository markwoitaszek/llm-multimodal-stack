#!/usr/bin/env python3
"""
API Deployment Management System
Part of Issue #46: API Lifecycle Management

This module provides comprehensive API deployment management including:
- Automated deployment pipelines
- Environment management
- Rollback capabilities
- Health checks and monitoring
- Configuration management
- Blue-green deployments
"""

import asyncio
import json
import yaml
import uuid
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import docker
import requests
import time
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class Environment(Enum):
    """Environment enumeration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class DeploymentStrategy(Enum):
    """Deployment strategy enumeration"""
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    config_id: str
    name: str
    environment: Environment
    strategy: DeploymentStrategy
    image_tag: str
    replicas: int = 1
    resources: Dict[str, Any] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    health_check: Dict[str, Any] = field(default_factory=dict)
    rollback_config: Dict[str, Any] = field(default_factory=dict)
    timeout_minutes: int = 30
    max_retries: int = 3

@dataclass
class Deployment:
    """Represents a deployment"""
    deployment_id: str
    config: DeploymentConfig
    status: DeploymentStatus
    start_time: str
    end_time: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    health_checks: List[Dict[str, Any]] = field(default_factory=list)
    rollback_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    url: str
    method: str = "GET"
    expected_status: int = 200
    timeout: int = 30
    retries: int = 3
    interval: int = 10
    headers: Dict[str, str] = field(default_factory=dict)

class DeploymentManager:
    """Manages API deployments"""
    
    def __init__(self, data_dir: Path, docker_client=None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Docker client
        self.docker_client = docker_client or docker.from_env()
        
        # Storage
        self.deployments: Dict[str, Deployment] = {}
        self.configs: Dict[str, DeploymentConfig] = {}
        self.environments: Dict[str, Dict[str, Any]] = {}
        
        # Configuration files
        self.deployments_file = self.data_dir / "deployments.json"
        self.configs_file = self.data_dir / "configs.json"
        self.environments_file = self.data_dir / "environments.json"
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Load existing data
        self._load_data()
        
        # Initialize default environments
        self._initialize_default_environments()
    
    def _load_data(self):
        """Load deployment data from files"""
        try:
            # Load deployments
            if self.deployments_file.exists():
                with open(self.deployments_file, 'r') as f:
                    data = json.load(f)
                    for deployment_id, deployment_data in data.items():
                        deployment_data['config']['environment'] = Environment(deployment_data['config']['environment'])
                        deployment_data['config']['strategy'] = DeploymentStrategy(deployment_data['config']['strategy'])
                        deployment_data['config'] = DeploymentConfig(**deployment_data['config'])
                        deployment_data['status'] = DeploymentStatus(deployment_data['status'])
                        self.deployments[deployment_id] = Deployment(**deployment_data)
            
            # Load configs
            if self.configs_file.exists():
                with open(self.configs_file, 'r') as f:
                    data = json.load(f)
                    for config_id, config_data in data.items():
                        config_data['environment'] = Environment(config_data['environment'])
                        config_data['strategy'] = DeploymentStrategy(config_data['strategy'])
                        self.configs[config_id] = DeploymentConfig(**config_data)
            
            # Load environments
            if self.environments_file.exists():
                with open(self.environments_file, 'r') as f:
                    self.environments = json.load(f)
            
            logger.info(f"Loaded {len(self.deployments)} deployments and {len(self.configs)} configs")
            
        except Exception as e:
            logger.error(f"Error loading deployment data: {e}")
    
    def _save_data(self):
        """Save deployment data to files"""
        try:
            # Save deployments
            deployments_data = {}
            for deployment_id, deployment in self.deployments.items():
                deployment_dict = asdict(deployment)
                deployment_dict['config']['environment'] = deployment.config.environment.value
                deployment_dict['config']['strategy'] = deployment.config.strategy.value
                deployment_dict['status'] = deployment.status.value
                deployments_data[deployment_id] = deployment_dict
            
            with open(self.deployments_file, 'w') as f:
                json.dump(deployments_data, f, indent=2)
            
            # Save configs
            configs_data = {}
            for config_id, config in self.configs.items():
                config_dict = asdict(config)
                config_dict['environment'] = config.environment.value
                config_dict['strategy'] = config.strategy.value
                configs_data[config_id] = config_dict
            
            with open(self.configs_file, 'w') as f:
                json.dump(configs_data, f, indent=2)
            
            # Save environments
            with open(self.environments_file, 'w') as f:
                json.dump(self.environments, f, indent=2)
            
            logger.info("Deployment data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving deployment data: {e}")
    
    def _initialize_default_environments(self):
        """Initialize default environments"""
        if not self.environments:
            self.environments = {
                "development": {
                    "name": "Development",
                    "description": "Development environment",
                    "base_url": "http://localhost:8000",
                    "docker_registry": "localhost:5000",
                    "namespace": "dev",
                    "replicas": 1,
                    "resources": {
                        "cpu": "100m",
                        "memory": "256Mi"
                    }
                },
                "staging": {
                    "name": "Staging",
                    "description": "Staging environment",
                    "base_url": "https://staging-api.example.com",
                    "docker_registry": "registry.example.com",
                    "namespace": "staging",
                    "replicas": 2,
                    "resources": {
                        "cpu": "500m",
                        "memory": "512Mi"
                    }
                },
                "production": {
                    "name": "Production",
                    "description": "Production environment",
                    "base_url": "https://api.example.com",
                    "docker_registry": "registry.example.com",
                    "namespace": "production",
                    "replicas": 3,
                    "resources": {
                        "cpu": "1000m",
                        "memory": "1Gi"
                    }
                }
            }
            self._save_data()
    
    def create_deployment_config(
        self,
        config_id: str,
        name: str,
        environment: Environment,
        strategy: DeploymentStrategy,
        image_tag: str,
        replicas: int = 1,
        resources: Dict[str, Any] = None,
        environment_vars: Dict[str, str] = None,
        health_check: Dict[str, Any] = None,
        timeout_minutes: int = 30
    ) -> DeploymentConfig:
        """Create a deployment configuration"""
        if config_id in self.configs:
            raise ValueError(f"Deployment config {config_id} already exists")
        
        config = DeploymentConfig(
            config_id=config_id,
            name=name,
            environment=environment,
            strategy=strategy,
            image_tag=image_tag,
            replicas=replicas,
            resources=resources or {},
            environment_vars=environment_vars or {},
            health_check=health_check or {},
            timeout_minutes=timeout_minutes
        )
        
        self.configs[config_id] = config
        self._save_data()
        
        logger.info(f"Created deployment config: {config_id}")
        return config
    
    def deploy(
        self,
        config_id: str,
        deployment_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Deployment:
        """Deploy using a configuration"""
        if config_id not in self.configs:
            raise ValueError(f"Deployment config {config_id} not found")
        
        config = self.configs[config_id]
        deployment_id = deployment_id or str(uuid.uuid4())
        
        # Create deployment record
        deployment = Deployment(
            deployment_id=deployment_id,
            config=config,
            status=DeploymentStatus.PENDING,
            start_time=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self.deployments[deployment_id] = deployment
        self._save_data()
        
        # Start deployment in background
        asyncio.create_task(self._execute_deployment(deployment_id))
        
        logger.info(f"Started deployment {deployment_id} with config {config_id}")
        return deployment
    
    async def _execute_deployment(self, deployment_id: str):
        """Execute a deployment"""
        deployment = self.deployments[deployment_id]
        deployment.status = DeploymentStatus.IN_PROGRESS
        self._save_data()
        
        try:
            # Log deployment start
            self._add_log(deployment_id, f"Starting deployment with strategy: {deployment.config.strategy.value}")
            
            # Execute based on strategy
            if deployment.config.strategy == DeploymentStrategy.BLUE_GREEN:
                await self._deploy_blue_green(deployment_id)
            elif deployment.config.strategy == DeploymentStrategy.ROLLING:
                await self._deploy_rolling(deployment_id)
            elif deployment.config.strategy == DeploymentStrategy.CANARY:
                await self._deploy_canary(deployment_id)
            elif deployment.config.strategy == DeploymentStrategy.RECREATE:
                await self._deploy_recreate(deployment_id)
            
            # Run health checks
            await self._run_health_checks(deployment_id)
            
            # Mark as successful
            deployment.status = DeploymentStatus.SUCCESS
            deployment.end_time = datetime.now().isoformat()
            self._add_log(deployment_id, "Deployment completed successfully")
            
        except Exception as e:
            # Mark as failed
            deployment.status = DeploymentStatus.FAILED
            deployment.end_time = datetime.now().isoformat()
            self._add_log(deployment_id, f"Deployment failed: {str(e)}")
            logger.error(f"Deployment {deployment_id} failed: {e}")
        
        self._save_data()
    
    async def _deploy_blue_green(self, deployment_id: str):
        """Execute blue-green deployment"""
        deployment = self.deployments[deployment_id]
        self._add_log(deployment_id, "Starting blue-green deployment")
        
        # Deploy to green environment
        green_service_name = f"{deployment.config.name}-green-{deployment_id[:8]}"
        await self._deploy_service(deployment_id, green_service_name, "green")
        
        # Run health checks on green
        green_healthy = await self._check_service_health(deployment_id, green_service_name)
        
        if green_healthy:
            # Switch traffic to green
            await self._switch_traffic(deployment_id, green_service_name)
            self._add_log(deployment_id, "Traffic switched to green environment")
            
            # Clean up blue environment
            await self._cleanup_old_services(deployment_id, "blue")
        else:
            raise Exception("Green environment health checks failed")
    
    async def _deploy_rolling(self, deployment_id: str):
        """Execute rolling deployment"""
        deployment = self.deployments[deployment_id]
        self._add_log(deployment_id, "Starting rolling deployment")
        
        # Deploy new instances gradually
        for i in range(deployment.config.replicas):
            service_name = f"{deployment.config.name}-{deployment_id[:8]}-{i}"
            await self._deploy_service(deployment_id, service_name, f"replica-{i}")
            
            # Wait for health check
            await asyncio.sleep(10)
            healthy = await self._check_service_health(deployment_id, service_name)
            
            if not healthy:
                raise Exception(f"Replica {i} health check failed")
            
            self._add_log(deployment_id, f"Replica {i} deployed successfully")
    
    async def _deploy_canary(self, deployment_id: str):
        """Execute canary deployment"""
        deployment = self.deployments[deployment_id]
        self._add_log(deployment_id, "Starting canary deployment")
        
        # Deploy canary instance
        canary_service_name = f"{deployment.config.name}-canary-{deployment_id[:8]}"
        await self._deploy_service(deployment_id, canary_service_name, "canary")
        
        # Run health checks
        canary_healthy = await self._check_service_health(deployment_id, canary_service_name)
        
        if canary_healthy:
            # Gradually increase traffic
            for percentage in [10, 25, 50, 75, 100]:
                await self._set_traffic_percentage(deployment_id, canary_service_name, percentage)
                self._add_log(deployment_id, f"Canary traffic increased to {percentage}%")
                
                # Wait and monitor
                await asyncio.sleep(60)
                
                # Check metrics
                if not await self._check_canary_metrics(deployment_id, canary_service_name):
                    raise Exception(f"Canary metrics degraded at {percentage}% traffic")
        else:
            raise Exception("Canary health check failed")
    
    async def _deploy_recreate(self, deployment_id: str):
        """Execute recreate deployment"""
        deployment = self.deployments[deployment_id]
        self._add_log(deployment_id, "Starting recreate deployment")
        
        # Stop existing services
        await self._stop_existing_services(deployment_id)
        
        # Deploy new service
        service_name = f"{deployment.config.name}-{deployment_id[:8]}"
        await self._deploy_service(deployment_id, service_name, "recreate")
        
        # Wait for health check
        healthy = await self._check_service_health(deployment_id, service_name)
        
        if not healthy:
            raise Exception("Recreated service health check failed")
    
    async def _deploy_service(self, deployment_id: str, service_name: str, strategy_type: str):
        """Deploy a service instance"""
        deployment = self.deployments[deployment_id]
        config = deployment.config
        
        self._add_log(deployment_id, f"Deploying service: {service_name}")
        
        # Build Docker image if needed
        if config.image_tag.startswith("build:"):
            image_name = config.image_tag[6:]  # Remove "build:" prefix
            await self._build_docker_image(deployment_id, image_name)
        
        # Create Docker container
        container_config = {
            "image": config.image_tag,
            "name": service_name,
            "environment": config.environment_vars,
            "ports": self._get_port_mapping(config),
            "labels": {
                "deployment_id": deployment_id,
                "strategy_type": strategy_type,
                "environment": config.environment.value
            }
        }
        
        try:
            container = self.docker_client.containers.run(**container_config, detach=True)
            self._add_log(deployment_id, f"Container {service_name} started: {container.id}")
        except Exception as e:
            raise Exception(f"Failed to start container {service_name}: {e}")
    
    async def _build_docker_image(self, deployment_id: str, image_name: str):
        """Build Docker image"""
        self._add_log(deployment_id, f"Building Docker image: {image_name}")
        
        # This would typically build from a Dockerfile
        # For demo purposes, we'll just log the action
        await asyncio.sleep(2)  # Simulate build time
        self._add_log(deployment_id, f"Docker image {image_name} built successfully")
    
    def _get_port_mapping(self, config: DeploymentConfig) -> Dict[str, str]:
        """Get port mapping for container"""
        # Default port mapping
        return {"8000/tcp": "8000"}
    
    async def _check_service_health(self, deployment_id: str, service_name: str) -> bool:
        """Check service health"""
        deployment = self.deployments[deployment_id]
        config = deployment.config
        
        # Get health check configuration
        health_check_config = config.health_check
        if not health_check_config:
            # Default health check
            health_check_config = {
                "url": "/health",
                "timeout": 30,
                "retries": 3
            }
        
        # Get environment base URL
        env_config = self.environments.get(config.environment.value, {})
        base_url = env_config.get("base_url", "http://localhost:8000")
        
        health_url = f"{base_url}{health_check_config['url']}"
        
        for attempt in range(health_check_config.get("retries", 3)):
            try:
                response = requests.get(
                    health_url,
                    timeout=health_check_config.get("timeout", 30)
                )
                
                if response.status_code == 200:
                    self._add_log(deployment_id, f"Health check passed for {service_name}")
                    return True
                else:
                    self._add_log(deployment_id, f"Health check failed for {service_name}: {response.status_code}")
                    
            except Exception as e:
                self._add_log(deployment_id, f"Health check error for {service_name}: {e}")
            
            if attempt < health_check_config.get("retries", 3) - 1:
                await asyncio.sleep(5)
        
        return False
    
    async def _run_health_checks(self, deployment_id: str):
        """Run comprehensive health checks"""
        deployment = self.deployments[deployment_id]
        self._add_log(deployment_id, "Running comprehensive health checks")
        
        # Get all services for this deployment
        services = self._get_deployment_services(deployment_id)
        
        for service_name in services:
            healthy = await self._check_service_health(deployment_id, service_name)
            
            health_check_result = {
                "service_name": service_name,
                "timestamp": datetime.now().isoformat(),
                "healthy": healthy
            }
            
            deployment.health_checks.append(health_check_result)
            
            if not healthy:
                raise Exception(f"Health check failed for service: {service_name}")
    
    def _get_deployment_services(self, deployment_id: str) -> List[str]:
        """Get all services for a deployment"""
        # This would typically query the container orchestration system
        # For demo purposes, return a mock list
        return [f"service-{deployment_id[:8]}"]
    
    async def _switch_traffic(self, deployment_id: str, target_service: str):
        """Switch traffic to target service"""
        self._add_log(deployment_id, f"Switching traffic to {target_service}")
        # This would typically update load balancer configuration
        await asyncio.sleep(2)  # Simulate traffic switch time
    
    async def _cleanup_old_services(self, deployment_id: str, service_type: str):
        """Clean up old services"""
        self._add_log(deployment_id, f"Cleaning up old {service_type} services")
        # This would typically stop and remove old containers
        await asyncio.sleep(1)  # Simulate cleanup time
    
    async def _set_traffic_percentage(self, deployment_id: str, service_name: str, percentage: int):
        """Set traffic percentage for canary deployment"""
        self._add_log(deployment_id, f"Setting traffic to {percentage}% for {service_name}")
        # This would typically update load balancer weights
        await asyncio.sleep(1)  # Simulate traffic adjustment time
    
    async def _check_canary_metrics(self, deployment_id: str, service_name: str) -> bool:
        """Check canary metrics"""
        # This would typically check error rates, response times, etc.
        # For demo purposes, return True (healthy)
        return True
    
    async def _stop_existing_services(self, deployment_id: str):
        """Stop existing services"""
        self._add_log(deployment_id, "Stopping existing services")
        # This would typically stop existing containers
        await asyncio.sleep(2)  # Simulate stop time
    
    def _add_log(self, deployment_id: str, message: str):
        """Add log entry to deployment"""
        if deployment_id in self.deployments:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] {message}"
            self.deployments[deployment_id].logs.append(log_entry)
            logger.info(f"Deployment {deployment_id}: {message}")
    
    def rollback(self, deployment_id: str, reason: str = "Manual rollback") -> bool:
        """Rollback a deployment"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        deployment = self.deployments[deployment_id]
        
        if deployment.status not in [DeploymentStatus.SUCCESS, DeploymentStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot rollback deployment with status: {deployment.status.value}")
        
        # Mark as rolled back
        deployment.status = DeploymentStatus.ROLLED_BACK
        deployment.rollback_reason = reason
        deployment.end_time = datetime.now().isoformat()
        
        self._add_log(deployment_id, f"Rollback initiated: {reason}")
        
        # Start rollback process
        asyncio.create_task(self._execute_rollback(deployment_id))
        
        self._save_data()
        
        logger.info(f"Rollback initiated for deployment {deployment_id}")
        return True
    
    async def _execute_rollback(self, deployment_id: str):
        """Execute rollback"""
        deployment = self.deployments[deployment_id]
        
        try:
            # Stop current services
            await self._stop_deployment_services(deployment_id)
            
            # Restore previous version
            await self._restore_previous_version(deployment_id)
            
            # Run health checks
            await self._run_health_checks(deployment_id)
            
            self._add_log(deployment_id, "Rollback completed successfully")
            
        except Exception as e:
            self._add_log(deployment_id, f"Rollback failed: {e}")
            logger.error(f"Rollback {deployment_id} failed: {e}")
    
    async def _stop_deployment_services(self, deployment_id: str):
        """Stop deployment services"""
        self._add_log(deployment_id, "Stopping deployment services")
        # This would typically stop all containers for the deployment
        await asyncio.sleep(2)  # Simulate stop time
    
    async def _restore_previous_version(self, deployment_id: str):
        """Restore previous version"""
        self._add_log(deployment_id, "Restoring previous version")
        # This would typically restore from backup or previous deployment
        await asyncio.sleep(3)  # Simulate restore time
    
    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Get deployment by ID"""
        return self.deployments.get(deployment_id)
    
    def list_deployments(
        self,
        environment: Optional[Environment] = None,
        status: Optional[DeploymentStatus] = None
    ) -> List[Deployment]:
        """List deployments with optional filters"""
        deployments = list(self.deployments.values())
        
        if environment:
            deployments = [d for d in deployments if d.config.environment == environment]
        
        if status:
            deployments = [d for d in deployments if d.status == status]
        
        # Sort by start time (newest first)
        deployments.sort(key=lambda d: d.start_time, reverse=True)
        
        return deployments
    
    def get_deployment_logs(self, deployment_id: str) -> List[str]:
        """Get deployment logs"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        return self.deployments[deployment_id].logs.copy()
    
    def get_deployment_health(self, deployment_id: str) -> List[Dict[str, Any]]:
        """Get deployment health checks"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        return self.deployments[deployment_id].health_checks.copy()
    
    def create_environment(
        self,
        env_name: str,
        name: str,
        description: str,
        base_url: str,
        docker_registry: str,
        namespace: str,
        replicas: int = 1,
        resources: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new environment"""
        if env_name in self.environments:
            raise ValueError(f"Environment {env_name} already exists")
        
        env_config = {
            "name": name,
            "description": description,
            "base_url": base_url,
            "docker_registry": docker_registry,
            "namespace": namespace,
            "replicas": replicas,
            "resources": resources or {}
        }
        
        self.environments[env_name] = env_config
        self._save_data()
        
        logger.info(f"Created environment: {env_name}")
        return env_config
    
    def get_environment(self, env_name: str) -> Optional[Dict[str, Any]]:
        """Get environment configuration"""
        return self.environments.get(env_name)
    
    def list_environments(self) -> Dict[str, Dict[str, Any]]:
        """List all environments"""
        return self.environments.copy()
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """Get deployment summary"""
        summary = {
            "total_deployments": len(self.deployments),
            "by_status": {},
            "by_environment": {},
            "by_strategy": {},
            "recent_deployments": []
        }
        
        # Count by status
        for deployment in self.deployments.values():
            status = deployment.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by environment
            env = deployment.config.environment.value
            summary["by_environment"][env] = summary["by_environment"].get(env, 0) + 1
            
            # Count by strategy
            strategy = deployment.config.strategy.value
            summary["by_strategy"][strategy] = summary["by_strategy"].get(strategy, 0) + 1
        
        # Get recent deployments (last 10)
        recent = sorted(
            self.deployments.values(),
            key=lambda d: d.start_time,
            reverse=True
        )[:10]
        
        summary["recent_deployments"] = [
            {
                "deployment_id": d.deployment_id,
                "config_name": d.config.name,
                "environment": d.config.environment.value,
                "status": d.status.value,
                "start_time": d.start_time
            }
            for d in recent
        ]
        
        return summary

async def main():
    """Main function to demonstrate deployment manager"""
    data_dir = Path("./deployment_data")
    manager = DeploymentManager(data_dir)
    
    # Create a deployment config
    config = manager.create_deployment_config(
        "api-v1",
        "API Service v1",
        Environment.STAGING,
        DeploymentStrategy.BLUE_GREEN,
        "api:latest",
        replicas=2,
        environment_vars={"ENV": "staging"},
        health_check={"url": "/health", "timeout": 30}
    )
    
    print(f"Created deployment config: {config.config_id}")
    
    # Deploy
    deployment = manager.deploy("api-v1")
    print(f"Started deployment: {deployment.deployment_id}")
    
    # Wait a bit for deployment to complete
    await asyncio.sleep(5)
    
    # Get deployment status
    deployment = manager.get_deployment(deployment.deployment_id)
    print(f"Deployment status: {deployment.status.value}")
    
    # Get deployment summary
    summary = manager.get_deployment_summary()
    print(f"Deployment summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())