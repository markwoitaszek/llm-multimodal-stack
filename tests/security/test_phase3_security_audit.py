"""
Phase 3 Security Audit and Hardening Tests
Comprehensive security tests for production readiness
"""
import pytest
import pytest_asyncio
import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add security module to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "security"))

from security_auditor import security_auditor, SecurityVulnerability
from security_hardening import security_hardener

from tests.conftest import test_services


class TestPhase3SecurityAudit:
    """Phase 3 security audit and hardening tests"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_docker_compose(self, temp_workspace):
        """Create mock Docker Compose file with security issues"""
        docker_compose_content = """
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
    ports:
      - "5432:5432"
    privileged: true
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    
  minio:
    image: minio/minio
    environment:
      - MINIO_ROOT_PASSWORD=minioadmin
    ports:
      - "9000:9000"
    
  litellm:
    image: litellm/litellm
    environment:
      - LITELLM_MASTER_KEY=sk-1234
      - LITELLM_SALT_KEY=sk-salt-1234
    
  user-management:
    image: user-management
    environment:
      - JWT_SECRET_KEY=your-secret-key-change-in-production
"""
        
        docker_file = temp_workspace / "docker-compose.yml"
        docker_file.write_text(docker_compose_content)
        return docker_file
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_audit_comprehensive(self, temp_workspace, mock_docker_compose):
        """Test comprehensive security audit"""
        # Set up auditor with temp workspace
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run comprehensive audit
        result = await auditor.run_comprehensive_audit()
        
        # Validate audit results
        assert result.total_vulnerabilities > 0
        assert result.critical_vulnerabilities > 0
        assert result.high_vulnerabilities > 0
        assert result.security_score < 100
        assert len(result.vulnerabilities) > 0
        assert len(result.recommendations) > 0
        
        # Check for specific vulnerabilities
        vulnerability_types = [v.category for v in result.vulnerabilities]
        assert 'authentication' in vulnerability_types
        assert 'authorization' in vulnerability_types
        assert 'configuration' in vulnerability_types
        
        # Check severity distribution
        severities = [v.severity for v in result.vulnerabilities]
        assert 'critical' in severities
        assert 'high' in severities
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_hardcoded_credentials_detection(self, temp_workspace, mock_docker_compose):
        """Test detection of hardcoded credentials"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run authentication audit
        await auditor._audit_authentication_security()
        
        # Check for hardcoded password vulnerabilities
        password_vulns = [v for v in auditor.vulnerabilities 
                         if 'password' in v.title.lower() and v.severity == 'critical']
        assert len(password_vulns) > 0
        
        # Check for hardcoded secret vulnerabilities
        secret_vulns = [v for v in auditor.vulnerabilities 
                       if 'secret' in v.title.lower() and v.severity in ['critical', 'high']]
        assert len(secret_vulns) > 0
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_privilege_escalation_detection(self, temp_workspace, mock_docker_compose):
        """Test detection of privilege escalation vulnerabilities"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run authorization audit
        await auditor._audit_authorization_security()
        
        # Check for privileged container vulnerabilities
        privileged_vulns = [v for v in auditor.vulnerabilities 
                           if v.id == 'privileged_containers']
        assert len(privileged_vulns) > 0
        assert privileged_vulns[0].severity == 'high'
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_network_security_audit(self, temp_workspace, mock_docker_compose):
        """Test network security audit"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run network security audit
        await auditor._audit_network_security()
        
        # Check for exposed port vulnerabilities
        exposed_port_vulns = [v for v in auditor.vulnerabilities 
                             if 'exposed_port' in v.id]
        assert len(exposed_port_vulns) > 0
        
        # Check for network segmentation vulnerabilities
        network_seg_vulns = [v for v in auditor.vulnerabilities 
                            if v.id == 'no_network_segmentation']
        assert len(network_seg_vulns) > 0
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_configuration_security_audit(self, temp_workspace, mock_docker_compose):
        """Test configuration security audit"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run configuration security audit
        await auditor._audit_configuration_security()
        
        # Check for resource limit vulnerabilities
        resource_vulns = [v for v in auditor.vulnerabilities 
                         if v.id == 'no_resource_limits']
        assert len(resource_vulns) > 0
        
        # Check for health check vulnerabilities
        health_vulns = [v for v in auditor.vulnerabilities 
                       if v.id == 'no_health_checks']
        assert len(health_vulns) > 0
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_hardening_comprehensive(self, temp_workspace):
        """Test comprehensive security hardening"""
        # Set up hardener with temp workspace
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Run comprehensive hardening
        result = await hardener.run_comprehensive_hardening()
        
        # Validate hardening results
        assert result['total_changes'] > 0
        assert result['status'] == 'completed'
        assert len(result['changes']) > 0
        
        # Check for specific hardening actions
        change_types = [change['action'] for change in result['changes']]
        assert 'generate_strong_passwords' in change_types
        assert 'update_docker_compose_security' in change_types
        assert 'create_secure_env_template' in change_types
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_password_generation(self, temp_workspace):
        """Test strong password generation"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Generate strong passwords
        await hardener._generate_strong_passwords()
        
        # Check if secure environment file was created
        secure_env_file = temp_workspace / ".env.secure"
        assert secure_env_file.exists()
        
        # Check password strength
        with open(secure_env_file, 'r') as f:
            content = f.read()
            
            # Check for strong passwords (at least 32 characters)
            password_lines = [line for line in content.split('\n') 
                            if 'PASSWORD' in line and '=' in line]
            for line in password_lines:
                password = line.split('=')[1]
                assert len(password) >= 32
                assert any(c.isupper() for c in password)  # Has uppercase
                assert any(c.islower() for c in password)  # Has lowercase
                assert any(c.isdigit() for c in password)  # Has digits
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_docker_compose_security_update(self, temp_workspace, mock_docker_compose):
        """Test Docker Compose security updates"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Update Docker Compose security
        await hardener._update_docker_compose_security()
        
        # Check if default passwords were replaced
        with open(mock_docker_compose, 'r') as f:
            content = f.read()
            
            # Check that default passwords are replaced with environment variables
            assert 'POSTGRES_PASSWORD=${POSTGRES_PASSWORD}' in content
            assert 'MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}' in content
            assert 'LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}' in content
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_secure_env_template_creation(self, temp_workspace):
        """Test secure environment template creation"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Create secure environment template
        await hardener._create_secure_env_template()
        
        # Check if template was created
        template_file = temp_workspace / ".env.secure.template"
        assert template_file.exists()
        
        # Check template content
        with open(template_file, 'r') as f:
            content = f.read()
            
            # Check for placeholder values
            assert 'CHANGE_ME_STRONG_PASSWORD_32_CHARS' in content
            assert 'CHANGE_ME_STRONG_API_KEY_64_CHARS' in content
            assert 'CHANGE_ME_STRONG_SECRET_KEY_32_CHARS' in content
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_network_segmentation_configuration(self, temp_workspace):
        """Test network segmentation configuration"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Configure network segmentation
        await hardener._configure_network_segmentation()
        
        # Check if configuration was created
        config_file = temp_workspace / "configs" / "network_segmentation.yaml"
        assert config_file.exists()
        
        # Check configuration content
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
            assert 'networks' in config
            assert 'frontend' in config['networks']
            assert 'backend' in config['networks']
            assert 'database' in config['networks']
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_encryption_configuration(self, temp_workspace):
        """Test encryption configuration"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Configure encryption
        await hardener._enable_data_encryption()
        
        # Check if configuration was created
        config_file = temp_workspace / "configs" / "encryption_config.yaml"
        assert config_file.exists()
        
        # Check configuration content
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
            assert 'data_at_rest' in config
            assert 'data_in_transit' in config
            assert config['data_at_rest']['enabled'] is True
            assert config['data_in_transit']['enabled'] is True
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_resource_limits_configuration(self, temp_workspace):
        """Test resource limits configuration"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Configure resource limits
        await hardener._configure_resource_limits()
        
        # Check if configuration was created
        config_file = temp_workspace / "configs" / "resource_limits.yaml"
        assert config_file.exists()
        
        # Check configuration content
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
            assert 'services' in config
            assert 'postgres' in config['services']
            assert 'redis' in config['services']
            assert 'memory_limit' in config['services']['postgres']
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_monitoring_configuration(self, temp_workspace):
        """Test security monitoring configuration"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Configure security monitoring
        await hardener._configure_security_monitoring()
        
        # Check if configuration was created
        config_file = temp_workspace / "configs" / "security_monitoring.yaml"
        assert config_file.exists()
        
        # Check configuration content
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
            assert 'security_monitoring' in config
            assert config['security_monitoring']['enabled'] is True
            assert 'monitors' in config['security_monitoring']
            assert 'alerts' in config['security_monitoring']
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_audit_report_generation(self, temp_workspace, mock_docker_compose):
        """Test security audit report generation"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run audit
        result = await auditor.run_comprehensive_audit()
        
        # Generate report
        report = auditor.generate_security_report("json")
        
        # Validate report
        assert report is not None
        report_data = json.loads(report)
        
        assert 'audit_summary' in report_data
        assert 'vulnerabilities' in report_data
        assert 'recommendations' in report_data
        assert 'compliance_status' in report_data
        
        # Check summary data
        summary = report_data['audit_summary']
        assert 'total_vulnerabilities' in summary
        assert 'security_score' in summary
        assert summary['total_vulnerabilities'] > 0
        assert summary['security_score'] < 100
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_hardening_report_generation(self, temp_workspace):
        """Test security hardening report generation"""
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        
        # Run hardening
        result = await hardener.run_comprehensive_hardening()
        
        # Generate report
        report = hardener.generate_hardening_report("json")
        
        # Validate report
        assert report is not None
        report_data = json.loads(report)
        
        assert 'hardening_summary' in report_data
        assert 'changes' in report_data
        assert 'next_steps' in report_data
        
        # Check summary data
        summary = report_data['hardening_summary']
        assert 'total_changes' in summary
        assert summary['total_changes'] > 0
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_compliance_framework_checks(self, temp_workspace, mock_docker_compose):
        """Test compliance framework checks"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run audit
        result = await auditor.run_comprehensive_audit()
        
        # Check compliance status
        assert 'compliance_status' in result.__dict__
        compliance_status = result.compliance_status
        
        # Check that compliance frameworks are evaluated
        assert len(compliance_status) > 0
        
        # Check specific frameworks
        assert 'owasp_top_10' in compliance_status
        assert 'cis_docker' in compliance_status
        assert 'nist_cybersecurity' in compliance_status
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_vulnerability_severity_classification(self, temp_workspace, mock_docker_compose):
        """Test vulnerability severity classification"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run audit
        result = await auditor.run_comprehensive_audit()
        
        # Check severity distribution
        severities = [v.severity for v in result.vulnerabilities]
        severity_counts = {severity: severities.count(severity) for severity in set(severities)}
        
        # Should have critical and high severity vulnerabilities
        assert 'critical' in severity_counts
        assert 'high' in severity_counts
        assert severity_counts['critical'] > 0
        assert severity_counts['high'] > 0
        
        # Check that critical vulnerabilities are properly identified
        critical_vulns = [v for v in result.vulnerabilities if v.severity == 'critical']
        for vuln in critical_vulns:
            assert vuln.severity == 'critical'
            assert vuln.impact is not None
            assert vuln.remediation is not None
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_recommendations_generation(self, temp_workspace, mock_docker_compose):
        """Test security recommendations generation"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run audit
        result = await auditor.run_comprehensive_audit()
        
        # Check recommendations
        assert len(result.recommendations) > 0
        
        # Check for specific recommendation categories
        recommendations_text = ' '.join(result.recommendations).lower()
        assert 'authentication' in recommendations_text or 'password' in recommendations_text
        assert 'encryption' in recommendations_text or 'tls' in recommendations_text
        assert 'monitoring' in recommendations_text or 'logging' in recommendations_text
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_security_score_calculation(self, temp_workspace, mock_docker_compose):
        """Test security score calculation"""
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        
        # Run audit
        result = await auditor.run_comprehensive_audit()
        
        # Check security score
        assert 0 <= result.security_score <= 100
        assert result.security_score < 100  # Should be less than perfect due to vulnerabilities
        
        # Check that score reflects vulnerability severity
        critical_count = result.critical_vulnerabilities
        high_count = result.high_vulnerabilities
        
        if critical_count > 0:
            assert result.security_score < 50  # Should be low with critical vulnerabilities
        elif high_count > 0:
            assert result.security_score < 80  # Should be moderate with high vulnerabilities
    
    @pytest.mark.security
    @pytest.mark.asyncio
    async def test_integration_security_audit_and_hardening(self, temp_workspace, mock_docker_compose):
        """Test integration of security audit and hardening"""
        # Run security audit
        auditor = security_auditor
        auditor.workspace_path = temp_workspace
        audit_result = await auditor.run_comprehensive_audit()
        
        # Run security hardening
        hardener = security_hardener
        hardener.workspace_path = temp_workspace
        hardening_result = await hardener.run_comprehensive_hardening()
        
        # Validate both results
        assert audit_result.total_vulnerabilities > 0
        assert hardening_result['total_changes'] > 0
        
        # Check that hardening addresses audit findings
        hardening_actions = [change['action'] for change in hardening_result['changes']]
        
        # Should have actions that address authentication issues
        auth_actions = [action for action in hardening_actions if 'password' in action or 'auth' in action]
        assert len(auth_actions) > 0
        
        # Should have actions that address configuration issues
        config_actions = [action for action in hardening_actions if 'config' in action or 'docker' in action]
        assert len(config_actions) > 0


if __name__ == "__main__":
    pytest.main([__file__])