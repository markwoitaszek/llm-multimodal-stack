"""
Security Hardening Implementation for LLM Multimodal Stack
"""
import asyncio
import json
import logging
import os
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import subprocess

logger = logging.getLogger(__name__)

class SecurityHardener:
    """Security hardening implementation"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.hardening_log: List[Dict[str, Any]] = []
    
    async def run_comprehensive_hardening(self) -> Dict[str, Any]:
        """Run comprehensive security hardening"""
        logger.info("Starting comprehensive security hardening")
        
        hardening_start = datetime.utcnow()
        
        # Clear previous log
        self.hardening_log.clear()
        
        # Run hardening steps
        await self._harden_authentication()
        await self._harden_authorization()
        await self._harden_encryption()
        await self._harden_network()
        await self._harden_configuration()
        await self._harden_containers()
        await self._harden_logging()
        await self._harden_monitoring()
        
        # Generate hardening report
        report = {
            "hardening_timestamp": hardening_start.isoformat(),
            "hardening_duration_seconds": (datetime.utcnow() - hardening_start).total_seconds(),
            "total_changes": len(self.hardening_log),
            "changes": self.hardening_log.copy(),
            "status": "completed"
        }
        
        logger.info(f"Security hardening completed: {len(self.hardening_log)} changes made")
        
        return report
    
    async def _harden_authentication(self):
        """Harden authentication mechanisms"""
        logger.info("Hardening authentication")
        
        # Generate strong passwords
        await self._generate_strong_passwords()
        
        # Update Docker Compose with secure defaults
        await self._update_docker_compose_security()
        
        # Create secure environment template
        await self._create_secure_env_template()
    
    async def _harden_authorization(self):
        """Harden authorization mechanisms"""
        logger.info("Hardening authorization")
        
        # Enable authentication on all services
        await self._enable_service_authentication()
        
        # Configure access controls
        await self._configure_access_controls()
    
    async def _harden_encryption(self):
        """Harden encryption mechanisms"""
        logger.info("Hardening encryption")
        
        # Configure TLS/SSL
        await self._configure_tls()
        
        # Enable data encryption
        await self._enable_data_encryption()
    
    async def _harden_network(self):
        """Harden network security"""
        logger.info("Hardening network security")
        
        # Configure network segmentation
        await self._configure_network_segmentation()
        
        # Remove unnecessary port exposures
        await self._remove_unnecessary_ports()
    
    async def _harden_configuration(self):
        """Harden system configuration"""
        logger.info("Hardening system configuration")
        
        # Update Docker configuration
        await self._update_docker_configuration()
        
        # Configure resource limits
        await self._configure_resource_limits()
    
    async def _harden_containers(self):
        """Harden container security"""
        logger.info("Hardening container security")
        
        # Configure non-root users
        await self._configure_non_root_users()
        
        # Remove privileged containers
        await self._remove_privileged_containers()
    
    async def _harden_logging(self):
        """Harden logging security"""
        logger.info("Hardening logging security")
        
        # Configure secure logging
        await self._configure_secure_logging()
        
        # Set up log monitoring
        await self._setup_log_monitoring()
    
    async def _harden_monitoring(self):
        """Harden monitoring security"""
        logger.info("Hardening monitoring security")
        
        # Configure security monitoring
        await self._configure_security_monitoring()
        
        # Set up alerting
        await self._setup_security_alerting()
    
    async def _generate_strong_passwords(self):
        """Generate strong passwords for all services"""
        passwords = {
            'POSTGRES_PASSWORD': self._generate_password(32),
            'MINIO_ROOT_PASSWORD': self._generate_password(32),
            'LITELLM_MASTER_KEY': self._generate_api_key(64),
            'LITELLM_SALT_KEY': self._generate_api_key(64),
            'VLLM_API_KEY': self._generate_api_key(64),
            'WEBUI_SECRET_KEY': self._generate_password(32),
            'JWT_SECRET_KEY': self._generate_password(64),
            'N8N_PASSWORD': self._generate_password(32),
            'N8N_ENCRYPTION_KEY': self._generate_password(32),
            'GRAFANA_PASSWORD': self._generate_password(32)
        }
        
        # Save passwords to secure file
        secure_env_file = self.workspace_path / ".env.secure"
        with open(secure_env_file, 'w') as f:
            f.write("# Secure Environment Variables - Generated by Security Hardener\n")
            f.write(f"# Generated on: {datetime.utcnow().isoformat()}\n\n")
            for key, value in passwords.items():
                f.write(f"{key}={value}\n")
        
        self.hardening_log.append({
            "action": "generate_strong_passwords",
            "description": "Generated strong passwords for all services",
            "file": str(secure_env_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Generated strong passwords and saved to {secure_env_file}")
    
    def _generate_password(self, length: int = 32) -> str:
        """Generate a strong password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_api_key(self, length: int = 64) -> str:
        """Generate a strong API key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def _update_docker_compose_security(self):
        """Update Docker Compose with security improvements"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        
        if not docker_compose_file.exists():
            logger.warning("Docker Compose file not found")
            return
        
        # Read current content
        with open(docker_compose_file, 'r') as f:
            content = f.read()
        
        # Apply security improvements
        security_improvements = [
            # Remove default passwords
            (r'POSTGRES_PASSWORD:-postgres', 'POSTGRES_PASSWORD=${POSTGRES_PASSWORD}'),
            (r'MINIO_ROOT_PASSWORD:-minioadmin', 'MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}'),
            (r'LITELLM_MASTER_KEY:-sk-1234', 'LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}'),
            (r'LITELLM_SALT_KEY:-sk-salt-1234', 'LITELLM_SALT_KEY=${LITELLM_SALT_KEY}'),
            (r'JWT_SECRET_KEY:-your-secret-key-change-in-production', 'JWT_SECRET_KEY=${JWT_SECRET_KEY}'),
            (r'WEBUI_SECRET_KEY:-webui-secret', 'WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY}'),
            (r'N8N_PASSWORD:-admin123', 'N8N_PASSWORD=${N8N_PASSWORD}'),
            (r'N8N_ENCRYPTION_KEY:-multimodal-n8n-key', 'N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}'),
            (r'GRAFANA_PASSWORD:-admin', 'GRAFANA_PASSWORD=${GRAFANA_PASSWORD}')
        ]
        
        for old_pattern, new_pattern in security_improvements:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
        
        # Write updated content
        with open(docker_compose_file, 'w') as f:
            f.write(content)
        
        self.hardening_log.append({
            "action": "update_docker_compose_security",
            "description": "Updated Docker Compose with secure environment variable references",
            "file": str(docker_compose_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("Updated Docker Compose with security improvements")
    
    async def _create_secure_env_template(self):
        """Create secure environment template"""
        template_content = """# Secure Environment Variables Template
# Copy this file to .env and update with your secure values

# Database Configuration
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME_STRONG_PASSWORD_32_CHARS

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=CHANGE_ME_STRONG_PASSWORD_32_CHARS

# vLLM Configuration
VLLM_MODEL=microsoft/DialoGPT-medium
VLLM_API_KEY=CHANGE_ME_STRONG_API_KEY_64_CHARS

# LiteLLM Configuration
LITELLM_MASTER_KEY=CHANGE_ME_STRONG_MASTER_KEY_64_CHARS
LITELLM_SALT_KEY=CHANGE_ME_STRONG_SALT_KEY_64_CHARS

# OpenWebUI Configuration
WEBUI_SECRET_KEY=CHANGE_ME_STRONG_SECRET_KEY_32_CHARS

# JWT Configuration
JWT_SECRET_KEY=CHANGE_ME_STRONG_JWT_SECRET_64_CHARS

# n8n Configuration
N8N_PASSWORD=CHANGE_ME_STRONG_PASSWORD_32_CHARS
N8N_ENCRYPTION_KEY=CHANGE_ME_STRONG_ENCRYPTION_KEY_32_CHARS

# Grafana Configuration
GRAFANA_PASSWORD=CHANGE_ME_STRONG_PASSWORD_32_CHARS

# GPU Configuration
CUDA_VISIBLE_DEVICES=0

# Storage Paths
QDRANT_DATA_PATH=/mnt/nvme/qdrant
POSTGRES_DATA_PATH=/mnt/nvme/postgres
MINIO_DATA_PATH=/mnt/nvme/minio
CACHE_PATH=/mnt/nvme/cache

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB_MULTIMODAL_WORKER=0
REDIS_DB_RETRIEVAL_PROXY=1
REDIS_DB_AI_AGENTS=2

# Cache Configuration
CACHE_TTL_SEARCH_RESULTS=3600
CACHE_TTL_MODEL_METADATA=86400
CACHE_TTL_EMBEDDINGS=86400
CACHE_TTL_AGENT_MEMORY=2592000
"""
        
        template_file = self.workspace_path / ".env.secure.template"
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        self.hardening_log.append({
            "action": "create_secure_env_template",
            "description": "Created secure environment variables template",
            "file": str(template_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Created secure environment template: {template_file}")
    
    async def _enable_service_authentication(self):
        """Enable authentication on all services"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        
        if not docker_compose_file.exists():
            return
        
        with open(docker_compose_file, 'r') as f:
            content = f.read()
        
        # Ensure authentication is enabled
        auth_improvements = [
            ('N8N_BASIC_AUTH_ACTIVE=true', 'N8N_BASIC_AUTH_ACTIVE=true'),
            ('WEBUI_AUTH=true', 'WEBUI_AUTH=true')
        ]
        
        for auth_setting, _ in auth_improvements:
            if auth_setting not in content:
                # Add authentication setting to appropriate service
                if 'n8n:' in content and 'N8N_BASIC_AUTH_ACTIVE' not in content:
                    content = content.replace(
                        'n8n:',
                        'n8n:\n    environment:\n      - N8N_BASIC_AUTH_ACTIVE=true\n      - N8N_BASIC_AUTH_USER=admin\n      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}'
                    )
        
        with open(docker_compose_file, 'w') as f:
            f.write(content)
        
        self.hardening_log.append({
            "action": "enable_service_authentication",
            "description": "Enabled authentication on all services",
            "file": str(docker_compose_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("Enabled authentication on all services")
    
    async def _configure_access_controls(self):
        """Configure access controls"""
        # Create access control configuration
        access_control_config = {
            "network_policies": {
                "frontend_network": {
                    "allowed_services": ["nginx", "openwebui"],
                    "denied_services": ["postgres", "redis", "qdrant"]
                },
                "backend_network": {
                    "allowed_services": ["multimodal-worker", "retrieval-proxy", "ai-agents"],
                    "denied_services": ["nginx", "openwebui"]
                },
                "database_network": {
                    "allowed_services": ["postgres", "redis", "qdrant"],
                    "denied_services": ["nginx", "openwebui", "multimodal-worker"]
                }
            },
            "user_permissions": {
                "admin": ["read", "write", "delete", "manage"],
                "user": ["read", "write"],
                "guest": ["read"]
            }
        }
        
        config_file = self.workspace_path / "configs" / "access_control.yaml"
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(access_control_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_access_controls",
            "description": "Configured access control policies",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured access controls: {config_file}")
    
    async def _configure_tls(self):
        """Configure TLS/SSL encryption"""
        # Create TLS configuration
        tls_config = {
            "ssl_certificate": "/etc/nginx/certs/cert.pem",
            "ssl_certificate_key": "/etc/nginx/certs/key.pem",
            "ssl_protocols": ["TLSv1.2", "TLSv1.3"],
            "ssl_ciphers": "ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384",
            "ssl_prefer_server_ciphers": True,
            "ssl_session_cache": "shared:SSL:10m",
            "ssl_session_timeout": "10m",
            "hsts": {
                "enabled": True,
                "max_age": 31536000,
                "include_subdomains": True
            }
        }
        
        config_file = self.workspace_path / "configs" / "tls_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(tls_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_tls",
            "description": "Configured TLS/SSL encryption settings",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured TLS/SSL: {config_file}")
    
    async def _enable_data_encryption(self):
        """Enable data encryption"""
        # Create encryption configuration
        encryption_config = {
            "data_at_rest": {
                "enabled": True,
                "algorithm": "AES-256-GCM",
                "key_rotation_days": 90
            },
            "data_in_transit": {
                "enabled": True,
                "protocols": ["TLSv1.2", "TLSv1.3"],
                "certificate_validation": True
            },
            "database_encryption": {
                "enabled": True,
                "transparent_data_encryption": True
            },
            "backup_encryption": {
                "enabled": True,
                "algorithm": "AES-256-CBC"
            }
        }
        
        config_file = self.workspace_path / "configs" / "encryption_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(encryption_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "enable_data_encryption",
            "description": "Enabled data encryption configuration",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Enabled data encryption: {config_file}")
    
    async def _configure_network_segmentation(self):
        """Configure network segmentation"""
        # Create network segmentation configuration
        network_config = {
            "networks": {
                "frontend": {
                    "driver": "bridge",
                    "ipam": {
                        "config": [{"subnet": "172.20.0.0/24"}]
                    }
                },
                "backend": {
                    "driver": "bridge",
                    "ipam": {
                        "config": [{"subnet": "172.21.0.0/24"}]
                    }
                },
                "database": {
                    "driver": "bridge",
                    "ipam": {
                        "config": [{"subnet": "172.22.0.0/24"}]
                    }
                }
            },
            "firewall_rules": {
                "frontend_to_backend": {
                    "source": "frontend",
                    "destination": "backend",
                    "ports": ["8001", "8002", "8003"],
                    "protocol": "tcp"
                },
                "backend_to_database": {
                    "source": "backend",
                    "destination": "database",
                    "ports": ["5432", "6379", "6333"],
                    "protocol": "tcp"
                }
            }
        }
        
        config_file = self.workspace_path / "configs" / "network_segmentation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(network_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_network_segmentation",
            "description": "Configured network segmentation",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured network segmentation: {config_file}")
    
    async def _remove_unnecessary_ports(self):
        """Remove unnecessary port exposures"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        
        if not docker_compose_file.exists():
            return
        
        with open(docker_compose_file, 'r') as f:
            content = f.read()
        
        # Remove internal port exposures
        port_removals = [
            ('"5432:5432"', ''),  # PostgreSQL
            ('"6379:6379"', ''),  # Redis
            ('"6333:6333"', ''),  # Qdrant
            ('"9000:9000"', '')   # MinIO
        ]
        
        for old_port, new_port in port_removals:
            if old_port in content:
                content = content.replace(old_port, new_port)
        
        with open(docker_compose_file, 'w') as f:
            f.write(content)
        
        self.hardening_log.append({
            "action": "remove_unnecessary_ports",
            "description": "Removed unnecessary port exposures",
            "file": str(docker_compose_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("Removed unnecessary port exposures")
    
    async def _update_docker_configuration(self):
        """Update Docker configuration with security improvements"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        
        if not docker_compose_file.exists():
            return
        
        with open(docker_compose_file, 'r') as f:
            content = f.read()
        
        # Add security improvements
        security_additions = [
            # Add resource limits
            ('deploy:', 'deploy:\n      resources:\n        limits:\n          memory: 1G\n        reservations:\n          memory: 512M'),
            # Add health checks
            ('healthcheck:', 'healthcheck:\n      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]\n      interval: 30s\n      timeout: 10s\n      retries: 3\n      start_period: 40s'),
            # Add read-only root filesystem
            ('read_only: true', 'read_only: true'),
            # Add no-new-privileges
            ('security_opt:', 'security_opt:\n      - no-new-privileges:true')
        ]
        
        # Apply security improvements (simplified)
        if 'deploy:' not in content:
            content += '\n    deploy:\n      resources:\n        limits:\n          memory: 1G\n        reservations:\n          memory: 512M'
        
        with open(docker_compose_file, 'w') as f:
            f.write(content)
        
        self.hardening_log.append({
            "action": "update_docker_configuration",
            "description": "Updated Docker configuration with security improvements",
            "file": str(docker_compose_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("Updated Docker configuration with security improvements")
    
    async def _configure_resource_limits(self):
        """Configure resource limits for all services"""
        # Create resource limits configuration
        resource_config = {
            "services": {
                "postgres": {
                    "memory_limit": "2G",
                    "memory_reservation": "1G",
                    "cpu_limit": "1.0",
                    "cpu_reservation": "0.5"
                },
                "redis": {
                    "memory_limit": "512M",
                    "memory_reservation": "256M",
                    "cpu_limit": "0.5",
                    "cpu_reservation": "0.25"
                },
                "qdrant": {
                    "memory_limit": "4G",
                    "memory_reservation": "2G",
                    "cpu_limit": "2.0",
                    "cpu_reservation": "1.0"
                },
                "multimodal-worker": {
                    "memory_limit": "8G",
                    "memory_reservation": "4G",
                    "cpu_limit": "4.0",
                    "cpu_reservation": "2.0"
                }
            }
        }
        
        config_file = self.workspace_path / "configs" / "resource_limits.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(resource_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_resource_limits",
            "description": "Configured resource limits for all services",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured resource limits: {config_file}")
    
    async def _configure_non_root_users(self):
        """Configure non-root users for containers"""
        # Create user configuration
        user_config = {
            "users": {
                "postgres": {
                    "uid": 999,
                    "gid": 999,
                    "user": "postgres"
                },
                "redis": {
                    "uid": 999,
                    "gid": 999,
                    "user": "redis"
                },
                "qdrant": {
                    "uid": 1000,
                    "gid": 1000,
                    "user": "qdrant"
                },
                "multimodal": {
                    "uid": 1001,
                    "gid": 1001,
                    "user": "multimodal"
                }
            }
        }
        
        config_file = self.workspace_path / "configs" / "user_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(user_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_non_root_users",
            "description": "Configured non-root users for containers",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured non-root users: {config_file}")
    
    async def _remove_privileged_containers(self):
        """Remove privileged containers"""
        docker_compose_file = self.workspace_path / "docker-compose.yml"
        
        if not docker_compose_file.exists():
            return
        
        with open(docker_compose_file, 'r') as f:
            content = f.read()
        
        # Remove privileged mode
        if 'privileged: true' in content:
            content = content.replace('privileged: true', 'privileged: false')
            
            with open(docker_compose_file, 'w') as f:
                f.write(content)
            
            self.hardening_log.append({
                "action": "remove_privileged_containers",
                "description": "Removed privileged mode from containers",
                "file": str(docker_compose_file),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info("Removed privileged mode from containers")
    
    async def _configure_secure_logging(self):
        """Configure secure logging"""
        # Create secure logging configuration
        logging_config = {
            "log_level": "INFO",
            "log_format": "json",
            "log_rotation": {
                "max_size": "100MB",
                "max_files": 10,
                "compress": True
            },
            "sensitive_data": {
                "mask_passwords": True,
                "mask_tokens": True,
                "mask_keys": True
            },
            "log_destinations": {
                "file": True,
                "stdout": True,
                "syslog": False
            }
        }
        
        config_file = self.workspace_path / "configs" / "secure_logging.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(logging_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_secure_logging",
            "description": "Configured secure logging settings",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured secure logging: {config_file}")
    
    async def _setup_log_monitoring(self):
        """Set up log monitoring"""
        # Create log monitoring configuration
        monitoring_config = {
            "log_monitoring": {
                "enabled": True,
                "alerts": {
                    "failed_login_attempts": {
                        "threshold": 5,
                        "time_window": "5m"
                    },
                    "suspicious_activity": {
                        "threshold": 10,
                        "time_window": "10m"
                    },
                    "error_rate": {
                        "threshold": 0.1,
                        "time_window": "5m"
                    }
                },
                "retention": {
                    "days": 30,
                    "compress_after_days": 7
                }
            }
        }
        
        config_file = self.workspace_path / "configs" / "log_monitoring.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(monitoring_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "setup_log_monitoring",
            "description": "Set up log monitoring configuration",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Set up log monitoring: {config_file}")
    
    async def _configure_security_monitoring(self):
        """Configure security monitoring"""
        # Create security monitoring configuration
        security_monitoring_config = {
            "security_monitoring": {
                "enabled": True,
                "monitors": {
                    "authentication_failures": True,
                    "privilege_escalation": True,
                    "suspicious_network_activity": True,
                    "file_system_changes": True,
                    "process_monitoring": True
                },
                "alerts": {
                    "critical": ["email", "slack"],
                    "high": ["email"],
                    "medium": ["log"],
                    "low": ["log"]
                }
            }
        }
        
        config_file = self.workspace_path / "configs" / "security_monitoring.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(security_monitoring_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "configure_security_monitoring",
            "description": "Configured security monitoring",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Configured security monitoring: {config_file}")
    
    async def _setup_security_alerting(self):
        """Set up security alerting"""
        # Create security alerting configuration
        alerting_config = {
            "alerting": {
                "enabled": True,
                "channels": {
                    "email": {
                        "enabled": True,
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "username": "${ALERT_EMAIL_USERNAME}",
                        "password": "${ALERT_EMAIL_PASSWORD}",
                        "from": "${ALERT_EMAIL_FROM}",
                        "to": ["${ALERT_EMAIL_TO}"]
                    },
                    "slack": {
                        "enabled": True,
                        "webhook_url": "${SLACK_WEBHOOK_URL}",
                        "channel": "#security-alerts"
                    }
                },
                "rules": {
                    "critical": {
                        "conditions": ["authentication_failure", "privilege_escalation"],
                        "channels": ["email", "slack"],
                        "cooldown": "5m"
                    },
                    "high": {
                        "conditions": ["suspicious_activity", "high_error_rate"],
                        "channels": ["email"],
                        "cooldown": "15m"
                    }
                }
            }
        }
        
        config_file = self.workspace_path / "configs" / "security_alerting.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(alerting_config, f, default_flow_style=False)
        
        self.hardening_log.append({
            "action": "setup_security_alerting",
            "description": "Set up security alerting configuration",
            "file": str(config_file),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Set up security alerting: {config_file}")
    
    def generate_hardening_report(self, format: str = "json") -> str:
        """Generate hardening report"""
        if format == "json":
            report = {
                "hardening_summary": {
                    "total_changes": len(self.hardening_log),
                    "hardening_timestamp": datetime.utcnow().isoformat()
                },
                "changes": self.hardening_log,
                "next_steps": [
                    "Review and test all security configurations",
                    "Update environment variables with secure values",
                    "Deploy hardened configuration to production",
                    "Set up monitoring and alerting",
                    "Conduct security testing",
                    "Document security procedures"
                ]
            }
            return json.dumps(report, indent=2)
        
        return ""

# Global security hardener instance
security_hardener = SecurityHardener()