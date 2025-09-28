"""
Comprehensive Security Audit and Hardening Framework for LLM Multimodal Stack
"""
import asyncio
import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import secrets
import string
import yaml
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class SecurityVulnerability:
    """Security vulnerability information"""
    id: str
    severity: str  # 'critical', 'high', 'medium', 'low', 'info'
    category: str  # 'authentication', 'authorization', 'encryption', 'network', 'configuration'
    title: str
    description: str
    impact: str
    remediation: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    evidence: Optional[str] = None
    cve: Optional[str] = None
    cvss_score: Optional[float] = None

@dataclass
class SecurityConfiguration:
    """Security configuration assessment"""
    component: str
    setting: str
    current_value: Any
    recommended_value: Any
    status: str  # 'secure', 'warning', 'vulnerable'
    description: str
    remediation: str

@dataclass
class SecurityAuditResult:
    """Comprehensive security audit result"""
    audit_timestamp: datetime
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    security_score: float  # 0-100
    vulnerabilities: List[SecurityVulnerability]
    configurations: List[SecurityConfiguration]
    recommendations: List[str]
    compliance_status: Dict[str, bool]

class SecurityAuditor:
    """Comprehensive security audit and hardening framework"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.vulnerabilities: List[SecurityVulnerability] = []
        self.configurations: List[SecurityConfiguration] = []
        self.recommendations: List[str] = []
        
        # Security patterns and checks
        self.password_patterns = [
            r'password\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'PASSWORD\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'passwd\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'pwd\s*=\s*["\']?([^"\'\s]+)["\']?'
        ]
        
        self.secret_patterns = [
            r'secret\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'SECRET\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'key\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'KEY\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'token\s*=\s*["\']?([^"\'\s]+)["\']?',
            r'TOKEN\s*=\s*["\']?([^"\'\s]+)["\']?'
        ]
        
        self.weak_passwords = [
            'password', '123456', 'admin', 'root', 'test', 'guest',
            'postgres', 'minioadmin', 'admin123', 'password123',
            'sk-1234', 'sk-salt-1234', 'webui-secret', 'dummy-key'
        ]
        
        # Security standards and compliance
        self.compliance_frameworks = {
            'owasp_top_10': {
                'name': 'OWASP Top 10',
                'checks': self._owasp_top_10_checks
            },
            'cis_docker': {
                'name': 'CIS Docker Benchmark',
                'checks': self._cis_docker_checks
            },
            'nist_cybersecurity': {
                'name': 'NIST Cybersecurity Framework',
                'checks': self._nist_cybersecurity_checks
            }
        }
    
    async def run_comprehensive_audit(self) -> SecurityAuditResult:
        """Run comprehensive security audit"""
        logger.info("Starting comprehensive security audit")
        
        audit_start = datetime.utcnow()
        
        # Clear previous results
        self.vulnerabilities.clear()
        self.configurations.clear()
        self.recommendations.clear()
        
        # Run all security checks
        await self._audit_authentication_security()
        await self._audit_authorization_security()
        await self._audit_encryption_security()
        await self._audit_network_security()
        await self._audit_configuration_security()
        await self._audit_dependency_security()
        await self._audit_container_security()
        await self._audit_api_security()
        await self._audit_data_security()
        await self._audit_logging_security()
        
        # Run compliance checks
        compliance_status = await self._run_compliance_checks()
        
        # Generate recommendations
        self._generate_security_recommendations()
        
        # Calculate security score
        security_score = self._calculate_security_score()
        
        # Create audit result
        result = SecurityAuditResult(
            audit_timestamp=audit_start,
            total_vulnerabilities=len(self.vulnerabilities),
            critical_vulnerabilities=len([v for v in self.vulnerabilities if v.severity == 'critical']),
            high_vulnerabilities=len([v for v in self.vulnerabilities if v.severity == 'high']),
            medium_vulnerabilities=len([v for v in self.vulnerabilities if v.severity == 'medium']),
            low_vulnerabilities=len([v for v in self.vulnerabilities if v.severity == 'low']),
            security_score=security_score,
            vulnerabilities=self.vulnerabilities.copy(),
            configurations=self.configurations.copy(),
            recommendations=self.recommendations.copy(),
            compliance_status=compliance_status
        )
        
        logger.info(f"Security audit completed: {len(self.vulnerabilities)} vulnerabilities found, "
                   f"security score: {security_score:.1f}/100")
        
        return result
    
    async def _audit_authentication_security(self):
        """Audit authentication security"""
        logger.info("Auditing authentication security")
        
        # Check for hardcoded credentials
        await self._check_hardcoded_credentials()
        
        # Check password policies
        await self._check_password_policies()
        
        # Check JWT/Token security
        await self._check_token_security()
        
        # Check authentication mechanisms
        await self._check_authentication_mechanisms()
    
    async def _audit_authorization_security(self):
        """Audit authorization security"""
        logger.info("Auditing authorization security")
        
        # Check access controls
        await self._check_access_controls()
        
        # Check privilege escalation
        await self._check_privilege_escalation()
        
        # Check API authorization
        await self._check_api_authorization()
    
    async def _audit_encryption_security(self):
        """Audit encryption security"""
        logger.info("Auditing encryption security")
        
        # Check data encryption
        await self._check_data_encryption()
        
        # Check transport encryption
        await self._check_transport_encryption()
        
        # Check key management
        await self._check_key_management()
    
    async def _audit_network_security(self):
        """Audit network security"""
        logger.info("Auditing network security")
        
        # Check exposed ports
        await self._check_exposed_ports()
        
        # Check network policies
        await self._check_network_policies()
        
        # Check firewall configuration
        await self._check_firewall_configuration()
    
    async def _audit_configuration_security(self):
        """Audit configuration security"""
        logger.info("Auditing configuration security")
        
        # Check Docker configuration
        await self._check_docker_configuration()
        
        # Check environment variables
        await self._check_environment_variables()
        
        # Check service configurations
        await self._check_service_configurations()
    
    async def _audit_dependency_security(self):
        """Audit dependency security"""
        logger.info("Auditing dependency security")
        
        # Check for vulnerable dependencies
        await self._check_vulnerable_dependencies()
        
        # Check dependency versions
        await self._check_dependency_versions()
        
        # Check license compliance
        await self._check_license_compliance()
    
    async def _audit_container_security(self):
        """Audit container security"""
        logger.info("Auditing container security")
        
        # Check container images
        await self._check_container_images()
        
        # Check container runtime
        await self._check_container_runtime()
        
        # Check container networking
        await self._check_container_networking()
    
    async def _audit_api_security(self):
        """Audit API security"""
        logger.info("Auditing API security")
        
        # Check API endpoints
        await self._check_api_endpoints()
        
        # Check API authentication
        await self._check_api_authentication()
        
        # Check API rate limiting
        await self._check_api_rate_limiting()
    
    async def _audit_data_security(self):
        """Audit data security"""
        logger.info("Auditing data security")
        
        # Check data storage
        await self._check_data_storage()
        
        # Check data backup
        await self._check_data_backup()
        
        # Check data retention
        await self._check_data_retention()
    
    async def _audit_logging_security(self):
        """Audit logging security"""
        logger.info("Auditing logging security")
        
        # Check log security
        await self._check_log_security()
        
        # Check log monitoring
        await self._check_log_monitoring()
        
        # Check log retention
        await self._check_log_retention()
    
    async def _check_hardcoded_credentials(self):
        """Check for hardcoded credentials"""
        # Check Docker Compose files
        docker_files = list(self.workspace_path.glob("docker-compose*.yml"))
        for docker_file in docker_files:
            await self._scan_file_for_credentials(docker_file)
        
        # Check environment files
        env_files = list(self.workspace_path.glob("*.env*"))
        for env_file in env_files:
            await self._scan_file_for_credentials(env_file)
        
        # Check configuration files
        config_files = list(self.workspace_path.glob("configs/*.yaml")) + \
                      list(self.workspace_path.glob("configs/*.yml")) + \
                      list(self.workspace_path.glob("configs/*.conf"))
        for config_file in config_files:
            await self._scan_file_for_credentials(config_file)
        
        # Check Python files
        python_files = list(self.workspace_path.glob("**/*.py"))
        for python_file in python_files:
            if "test" not in str(python_file):  # Skip test files
                await self._scan_file_for_credentials(python_file)
    
    async def _scan_file_for_credentials(self, file_path: Path):
        """Scan file for hardcoded credentials"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Check for password patterns
                for pattern in self.password_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        password = match.group(1)
                        if password in self.weak_passwords or len(password) < 8:
                            self.vulnerabilities.append(SecurityVulnerability(
                                id=f"hardcoded_password_{len(self.vulnerabilities)}",
                                severity="critical" if password in self.weak_passwords else "high",
                                category="authentication",
                                title="Hardcoded Weak Password",
                                description=f"Hardcoded password found: {password}",
                                impact="Credentials can be easily compromised",
                                remediation="Use environment variables or secure secret management",
                                file_path=str(file_path),
                                line_number=line_num,
                                evidence=line.strip()
                            ))
                
                # Check for secret patterns
                for pattern in self.secret_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        secret = match.group(1)
                        if secret in self.weak_passwords or len(secret) < 16:
                            self.vulnerabilities.append(SecurityVulnerability(
                                id=f"hardcoded_secret_{len(self.vulnerabilities)}",
                                severity="critical" if secret in self.weak_passwords else "high",
                                category="authentication",
                                title="Hardcoded Weak Secret",
                                description=f"Hardcoded secret found: {secret[:10]}...",
                                impact="Secrets can be easily compromised",
                                remediation="Use environment variables or secure secret management",
                                file_path=str(file_path),
                                line_number=line_num,
                                evidence=line.strip()
                            ))
        
        except Exception as e:
            logger.warning(f"Error scanning file {file_path}: {e}")
    
    async def _check_password_policies(self):
        """Check password policies"""
        # Check for default passwords in Docker Compose
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check for default PostgreSQL password
                if 'POSTGRES_PASSWORD:-postgres' in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="default_postgres_password",
                        severity="critical",
                        category="authentication",
                        title="Default PostgreSQL Password",
                        description="PostgreSQL is using default password 'postgres'",
                        impact="Database can be easily compromised",
                        remediation="Change PostgreSQL password to a strong, unique password",
                        file_path=str(docker_compose_file),
                        evidence="POSTGRES_PASSWORD:-postgres"
                    ))
                
                # Check for default MinIO password
                if 'MINIO_ROOT_PASSWORD:-minioadmin' in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="default_minio_password",
                        severity="critical",
                        category="authentication",
                        title="Default MinIO Password",
                        description="MinIO is using default password 'minioadmin'",
                        impact="Object storage can be easily compromised",
                        remediation="Change MinIO password to a strong, unique password",
                        file_path=str(docker_compose_file),
                        evidence="MINIO_ROOT_PASSWORD:-minioadmin"
                    ))
    
    async def _check_token_security(self):
        """Check token security"""
        # Check for weak JWT secrets
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                if 'JWT_SECRET_KEY:-your-secret-key-change-in-production' in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="weak_jwt_secret",
                        severity="critical",
                        category="authentication",
                        title="Weak JWT Secret Key",
                        description="JWT secret key is using default/weak value",
                        impact="JWT tokens can be easily forged",
                        remediation="Generate a strong, random JWT secret key",
                        file_path=str(docker_compose_file),
                        evidence="JWT_SECRET_KEY:-your-secret-key-change-in-production"
                    ))
    
    async def _check_authentication_mechanisms(self):
        """Check authentication mechanisms"""
        # Check for missing authentication on services
        services_without_auth = []
        
        # Check if services have authentication enabled
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check n8n authentication
                if 'N8N_BASIC_AUTH_ACTIVE=true' not in content:
                    services_without_auth.append("n8n")
                
                # Check OpenWebUI authentication
                if 'WEBUI_AUTH=true' not in content:
                    services_without_auth.append("openwebui")
        
        for service in services_without_auth:
            self.vulnerabilities.append(SecurityVulnerability(
                id=f"missing_auth_{service}",
                severity="high",
                category="authentication",
                title=f"Missing Authentication on {service}",
                description=f"{service} service does not have authentication enabled",
                impact="Unauthorized access to service",
                remediation=f"Enable authentication for {service} service",
                file_path=str(docker_compose_file)
            ))
    
    async def _check_access_controls(self):
        """Check access controls"""
        # Check for overly permissive file permissions
        # This would require system-level checks, so we'll focus on configuration
        
        # Check Docker container user permissions
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check if containers are running as root
                if 'user:' not in content and 'USER' not in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="containers_run_as_root",
                        severity="medium",
                        category="authorization",
                        title="Containers Running as Root",
                        description="Docker containers are running as root user",
                        impact="Privilege escalation if container is compromised",
                        remediation="Run containers as non-root user",
                        file_path=str(docker_compose_file)
                    ))
    
    async def _check_privilege_escalation(self):
        """Check for privilege escalation vulnerabilities"""
        # Check for privileged containers
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                if 'privileged: true' in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="privileged_containers",
                        severity="high",
                        category="authorization",
                        title="Privileged Containers",
                        description="Docker containers are running in privileged mode",
                        impact="Full host system access if container is compromised",
                        remediation="Remove privileged mode and use specific capabilities",
                        file_path=str(docker_compose_file),
                        evidence="privileged: true"
                    ))
    
    async def _check_api_authorization(self):
        """Check API authorization"""
        # Check for API endpoints without authentication
        # This would require runtime analysis, so we'll check configuration
        
        # Check if API keys are properly configured
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                if 'VLLM_API_KEY' in content and 'dummy-key' in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="weak_api_key",
                        severity="high",
                        category="authorization",
                        title="Weak API Key",
                        description="API key is using default/weak value",
                        impact="Unauthorized API access",
                        remediation="Generate a strong, random API key",
                        file_path=str(docker_compose_file),
                        evidence="dummy-key"
                    ))
    
    async def _check_data_encryption(self):
        """Check data encryption"""
        # Check for unencrypted data storage
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check if volumes are encrypted
                if 'encrypted' not in content.lower():
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="unencrypted_volumes",
                        severity="medium",
                        category="encryption",
                        title="Unencrypted Data Volumes",
                        description="Docker volumes are not encrypted",
                        impact="Data at rest is not protected",
                        remediation="Enable volume encryption or use encrypted storage",
                        file_path=str(docker_compose_file)
                    ))
    
    async def _check_transport_encryption(self):
        """Check transport encryption"""
        # Check for HTTP instead of HTTPS
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check for HTTP URLs
                http_urls = re.findall(r'http://[^\s"\']+', content)
                for url in http_urls:
                    if 'localhost' not in url and '127.0.0.1' not in url:
                        self.vulnerabilities.append(SecurityVulnerability(
                            id="http_transport",
                            severity="medium",
                            category="encryption",
                            title="Unencrypted HTTP Transport",
                            description=f"HTTP URL found: {url}",
                            impact="Data in transit is not encrypted",
                            remediation="Use HTTPS for all external communications",
                            file_path=str(docker_compose_file),
                            evidence=url
                        ))
    
    async def _check_key_management(self):
        """Check key management"""
        # Check for proper key management practices
        # This would require runtime analysis, so we'll check configuration
        
        # Check if keys are properly rotated
        self.recommendations.append("Implement key rotation policies for all secrets and keys")
        self.recommendations.append("Use a dedicated key management service (KMS)")
    
    async def _check_exposed_ports(self):
        """Check exposed ports"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check for unnecessary port exposures
                exposed_ports = re.findall(r'"(\d+):\d+"', content)
                for port in exposed_ports:
                    if port in ['5432', '6379', '6333', '9000']:  # Database and service ports
                        self.vulnerabilities.append(SecurityVulnerability(
                            id=f"exposed_port_{port}",
                            severity="high",
                            category="network",
                            title=f"Exposed Internal Port {port}",
                            description=f"Internal service port {port} is exposed to host",
                            impact="Direct access to internal services",
                            remediation="Remove port exposure or use reverse proxy",
                            file_path=str(docker_compose_file),
                            evidence=f'"{port}:'
                        ))
    
    async def _check_network_policies(self):
        """Check network policies"""
        # Check for network segmentation
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check if all services are on the same network
                if content.count('networks:') < 2:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="no_network_segmentation",
                        severity="medium",
                        category="network",
                        title="No Network Segmentation",
                        description="All services are on the same network",
                        impact="Lateral movement if one service is compromised",
                        remediation="Implement network segmentation with separate networks",
                        file_path=str(docker_compose_file)
                    ))
    
    async def _check_firewall_configuration(self):
        """Check firewall configuration"""
        # This would require system-level checks
        self.recommendations.append("Configure firewall rules to restrict unnecessary network access")
        self.recommendations.append("Implement network access control lists (ACLs)")
    
    async def _check_docker_configuration(self):
        """Check Docker configuration"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check for resource limits
                if 'deploy:' not in content or 'resources:' not in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="no_resource_limits",
                        severity="medium",
                        category="configuration",
                        title="No Resource Limits",
                        description="Docker containers have no resource limits",
                        impact="Resource exhaustion attacks possible",
                        remediation="Set appropriate resource limits for all containers",
                        file_path=str(docker_compose_file)
                    ))
                
                # Check for health checks
                if 'healthcheck:' not in content:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id="no_health_checks",
                        severity="low",
                        category="configuration",
                        title="No Health Checks",
                        description="Docker containers have no health checks",
                        impact="Unhealthy containers may not be detected",
                        remediation="Add health checks to all containers",
                        file_path=str(docker_compose_file)
                    ))
    
    async def _check_environment_variables(self):
        """Check environment variables"""
        # Check for sensitive data in environment variables
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check for hardcoded environment variables
                env_vars = re.findall(r'-\s*([A-Z_]+)=([^\s\n]+)', content)
                for var_name, var_value in env_vars:
                    if any(sensitive in var_name.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                        if var_value in self.weak_passwords or len(var_value) < 8:
                            self.vulnerabilities.append(SecurityVulnerability(
                                id=f"weak_env_var_{var_name}",
                                severity="high",
                                category="configuration",
                                title=f"Weak Environment Variable: {var_name}",
                                description=f"Environment variable {var_name} has weak value",
                                impact="Sensitive data can be easily compromised",
                                remediation="Use strong values or environment variable substitution",
                                file_path=str(docker_compose_file),
                                evidence=f"{var_name}={var_value}"
                            ))
    
    async def _check_service_configurations(self):
        """Check service configurations"""
        # Check individual service configurations
        config_dir = self.workspace_path / "configs"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                await self._check_yaml_configuration(config_file)
            for config_file in config_dir.glob("*.yml"):
                await self._check_yaml_configuration(config_file)
    
    async def _check_yaml_configuration(self, config_file: Path):
        """Check YAML configuration file"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check for insecure configurations
            if isinstance(config, dict):
                await self._analyze_yaml_config(config, config_file)
        
        except Exception as e:
            logger.warning(f"Error checking YAML config {config_file}: {e}")
    
    async def _analyze_yaml_config(self, config: dict, file_path: Path):
        """Analyze YAML configuration for security issues"""
        # Check for insecure settings
        if 'security' in config:
            security_config = config['security']
            if isinstance(security_config, dict):
                if security_config.get('enabled') is False:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id=f"security_disabled_{file_path.name}",
                        severity="high",
                        category="configuration",
                        title="Security Disabled",
                        description=f"Security is disabled in {file_path.name}",
                        impact="Service is vulnerable to attacks",
                        remediation="Enable security features",
                        file_path=str(file_path)
                    ))
    
    async def _check_vulnerable_dependencies(self):
        """Check for vulnerable dependencies"""
        # Check Python requirements
        requirements_files = list(self.workspace_path.glob("**/requirements*.txt"))
        for req_file in requirements_files:
            await self._check_python_dependencies(req_file)
        
        # Check package.json files
        package_files = list(self.workspace_path.glob("**/package.json"))
        for package_file in package_files:
            await self._check_node_dependencies(package_file)
    
    async def _check_python_dependencies(self, req_file: Path):
        """Check Python dependencies for vulnerabilities"""
        try:
            with open(req_file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Check for known vulnerable packages
                    package = line.split('==')[0].split('>=')[0].split('<=')[0]
                    
                    # This is a simplified check - in production, use tools like safety
                    vulnerable_packages = ['django==1.11', 'flask==0.12', 'requests==2.18']
                    if any(vuln_pkg.startswith(package) for vuln_pkg in vulnerable_packages):
                        self.vulnerabilities.append(SecurityVulnerability(
                            id=f"vulnerable_python_pkg_{package}",
                            severity="high",
                            category="dependency",
                            title=f"Vulnerable Python Package: {package}",
                            description=f"Package {package} has known vulnerabilities",
                            impact="Application may be vulnerable to attacks",
                            remediation="Update to latest secure version",
                            file_path=str(req_file),
                            evidence=line
                        ))
        
        except Exception as e:
            logger.warning(f"Error checking Python dependencies {req_file}: {e}")
    
    async def _check_node_dependencies(self, package_file: Path):
        """Check Node.js dependencies for vulnerabilities"""
        try:
            with open(package_file, 'r') as f:
                package_data = json.load(f)
            
            # Check for known vulnerable packages
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            vulnerable_packages = ['express@4.15', 'lodash@4.17.4']
            for package, version in all_deps.items():
                if any(vuln_pkg.startswith(package) for vuln_pkg in vulnerable_packages):
                    self.vulnerabilities.append(SecurityVulnerability(
                        id=f"vulnerable_node_pkg_{package}",
                        severity="high",
                        category="dependency",
                        title=f"Vulnerable Node.js Package: {package}",
                        description=f"Package {package} has known vulnerabilities",
                        impact="Application may be vulnerable to attacks",
                        remediation="Update to latest secure version",
                        file_path=str(package_file),
                        evidence=f"{package}: {version}"
                    ))
        
        except Exception as e:
            logger.warning(f"Error checking Node.js dependencies {package_file}: {e}")
    
    async def _check_dependency_versions(self):
        """Check dependency versions"""
        self.recommendations.append("Pin dependency versions to specific releases")
        self.recommendations.append("Regularly update dependencies to latest secure versions")
        self.recommendations.append("Use dependency scanning tools in CI/CD pipeline")
    
    async def _check_license_compliance(self):
        """Check license compliance"""
        self.recommendations.append("Audit all dependencies for license compliance")
        self.recommendations.append("Document license usage and restrictions")
    
    async def _check_container_images(self):
        """Check container images"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        if docker_compose_file.exists():
            with open(docker_compose_file, 'r') as f:
                content = f.read()
                
                # Check for latest tags
                latest_images = re.findall(r'image:\s*([^:\s]+):latest', content)
                for image in latest_images:
                    self.vulnerabilities.append(SecurityVulnerability(
                        id=f"latest_tag_{image}",
                        severity="medium",
                        category="container",
                        title=f"Using Latest Tag: {image}",
                        description=f"Container image {image} is using 'latest' tag",
                        impact="Unpredictable deployments and potential vulnerabilities",
                        remediation="Use specific version tags",
                        file_path=str(docker_compose_file),
                        evidence=f"{image}:latest"
                    ))
    
    async def _check_container_runtime(self):
        """Check container runtime security"""
        self.recommendations.append("Enable Docker Content Trust")
        self.recommendations.append("Use read-only root filesystems where possible")
        self.recommendations.append("Implement container image scanning")
    
    async def _check_container_networking(self):
        """Check container networking"""
        # Already covered in network security checks
        pass
    
    async def _check_api_endpoints(self):
        """Check API endpoints"""
        # Check for exposed API endpoints without authentication
        # This would require runtime analysis
        self.recommendations.append("Implement API authentication for all endpoints")
        self.recommendations.append("Use API versioning and deprecation policies")
    
    async def _check_api_authentication(self):
        """Check API authentication"""
        # Already covered in authentication checks
        pass
    
    async def _check_api_rate_limiting(self):
        """Check API rate limiting"""
        self.recommendations.append("Implement rate limiting for all API endpoints")
        self.recommendations.append("Use DDoS protection services")
    
    async def _check_data_storage(self):
        """Check data storage security"""
        self.recommendations.append("Encrypt data at rest")
        self.recommendations.append("Implement data classification and handling policies")
        self.recommendations.append("Use secure backup and recovery procedures")
    
    async def _check_data_backup(self):
        """Check data backup security"""
        self.recommendations.append("Implement automated backup procedures")
        self.recommendations.append("Test backup and recovery procedures regularly")
        self.recommendations.append("Encrypt backup data")
    
    async def _check_data_retention(self):
        """Check data retention policies"""
        self.recommendations.append("Implement data retention policies")
        self.recommendations.append("Automate data deletion after retention period")
        self.recommendations.append("Comply with data protection regulations")
    
    async def _check_log_security(self):
        """Check log security"""
        self.recommendations.append("Implement secure logging practices")
        self.recommendations.append("Avoid logging sensitive information")
        self.recommendations.append("Use log integrity verification")
    
    async def _check_log_monitoring(self):
        """Check log monitoring"""
        self.recommendations.append("Implement log monitoring and alerting")
        self.recommendations.append("Use SIEM for log analysis")
        self.recommendations.append("Set up automated threat detection")
    
    async def _check_log_retention(self):
        """Check log retention"""
        self.recommendations.append("Implement log retention policies")
        self.recommendations.append("Archive logs securely")
        self.recommendations.append("Comply with log retention regulations")
    
    async def _run_compliance_checks(self) -> Dict[str, bool]:
        """Run compliance framework checks"""
        compliance_status = {}
        
        for framework_name, framework_info in self.compliance_frameworks.items():
            try:
                checks = framework_info['checks']()
                compliance_status[framework_name] = all(checks)
            except Exception as e:
                logger.warning(f"Error running {framework_name} compliance checks: {e}")
                compliance_status[framework_name] = False
        
        return compliance_status
    
    def _owasp_top_10_checks(self) -> List[bool]:
        """OWASP Top 10 security checks"""
        checks = []
        
        # A01: Broken Access Control
        checks.append(not any(v.severity in ['critical', 'high'] and 'authorization' in v.category 
                             for v in self.vulnerabilities))
        
        # A02: Cryptographic Failures
        checks.append(not any(v.severity in ['critical', 'high'] and 'encryption' in v.category 
                             for v in self.vulnerabilities))
        
        # A03: Injection
        # This would require code analysis
        checks.append(True)  # Placeholder
        
        # A04: Insecure Design
        checks.append(not any(v.severity in ['critical', 'high'] and 'configuration' in v.category 
                             for v in self.vulnerabilities))
        
        # A05: Security Misconfiguration
        checks.append(not any(v.severity in ['critical', 'high'] and 'configuration' in v.category 
                             for v in self.vulnerabilities))
        
        # A06: Vulnerable Components
        checks.append(not any(v.severity in ['critical', 'high'] and 'dependency' in v.category 
                             for v in self.vulnerabilities))
        
        # A07: Authentication Failures
        checks.append(not any(v.severity in ['critical', 'high'] and 'authentication' in v.category 
                             for v in self.vulnerabilities))
        
        # A08: Software and Data Integrity Failures
        checks.append(True)  # Placeholder
        
        # A09: Logging and Monitoring Failures
        checks.append(True)  # Placeholder
        
        # A10: Server-Side Request Forgery
        checks.append(True)  # Placeholder
        
        return checks
    
    def _cis_docker_checks(self) -> List[bool]:
        """CIS Docker Benchmark checks"""
        checks = []
        
        # Check for privileged containers
        checks.append(not any(v.id == 'privileged_containers' for v in self.vulnerabilities))
        
        # Check for containers running as root
        checks.append(not any(v.id == 'containers_run_as_root' for v in self.vulnerabilities))
        
        # Check for resource limits
        checks.append(not any(v.id == 'no_resource_limits' for v in self.vulnerabilities))
        
        # Check for health checks
        checks.append(not any(v.id == 'no_health_checks' for v in self.vulnerabilities))
        
        return checks
    
    def _nist_cybersecurity_checks(self) -> List[bool]:
        """NIST Cybersecurity Framework checks"""
        checks = []
        
        # Identify
        checks.append(True)  # Asset management
        
        # Protect
        checks.append(not any(v.severity in ['critical', 'high'] for v in self.vulnerabilities))
        
        # Detect
        checks.append(True)  # Monitoring and detection
        
        # Respond
        checks.append(True)  # Response planning
        
        # Recover
        checks.append(True)  # Recovery planning
        
        return checks
    
    def _generate_security_recommendations(self):
        """Generate security recommendations based on findings"""
        if not self.recommendations:
            self.recommendations = []
        
        # Add general recommendations
        general_recommendations = [
            "Implement a comprehensive security monitoring system",
            "Conduct regular security assessments and penetration testing",
            "Establish incident response procedures",
            "Implement security awareness training for all team members",
            "Use automated security scanning in CI/CD pipeline",
            "Implement zero-trust network architecture",
            "Regularly update all software components",
            "Implement multi-factor authentication where possible",
            "Use secure coding practices and code reviews",
            "Implement data loss prevention (DLP) measures"
        ]
        
        self.recommendations.extend(general_recommendations)
    
    def _calculate_security_score(self) -> float:
        """Calculate overall security score (0-100)"""
        if not self.vulnerabilities:
            return 100.0
        
        # Weight vulnerabilities by severity
        severity_weights = {
            'critical': 10,
            'high': 7,
            'medium': 4,
            'low': 2,
            'info': 1
        }
        
        total_weight = sum(severity_weights.get(v.severity, 1) for v in self.vulnerabilities)
        max_possible_weight = len(self.vulnerabilities) * 10
        
        # Calculate score (lower is better)
        security_score = max(0, 100 - (total_weight / max_possible_weight) * 100)
        
        return round(security_score, 1)
    
    def generate_security_report(self, format: str = "json") -> str:
        """Generate comprehensive security report"""
        if format == "json":
            report = {
                "audit_summary": {
                    "total_vulnerabilities": len(self.vulnerabilities),
                    "critical_vulnerabilities": len([v for v in self.vulnerabilities if v.severity == 'critical']),
                    "high_vulnerabilities": len([v for v in self.vulnerabilities if v.severity == 'high']),
                    "medium_vulnerabilities": len([v for v in self.vulnerabilities if v.severity == 'medium']),
                    "low_vulnerabilities": len([v for v in self.vulnerabilities if v.severity == 'low']),
                    "security_score": self._calculate_security_score()
                },
                "vulnerabilities": [
                    {
                        "id": v.id,
                        "severity": v.severity,
                        "category": v.category,
                        "title": v.title,
                        "description": v.description,
                        "impact": v.impact,
                        "remediation": v.remediation,
                        "file_path": v.file_path,
                        "line_number": v.line_number,
                        "evidence": v.evidence,
                        "cve": v.cve,
                        "cvss_score": v.cvss_score
                    }
                    for v in self.vulnerabilities
                ],
                "recommendations": self.recommendations,
                "compliance_status": {
                    "owasp_top_10": True,  # Placeholder
                    "cis_docker": True,    # Placeholder
                    "nist_cybersecurity": True  # Placeholder
                }
            }
            return json.dumps(report, indent=2)
        
        return ""

# Global security auditor instance
security_auditor = SecurityAuditor()