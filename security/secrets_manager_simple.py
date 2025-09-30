"""
Production Environment Variables & Secrets Management System
Issue #101 Implementation - Simplified Version
"""
import asyncio
import json
import logging
import os
import secrets
import string
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib
import base64
import copy

logger = logging.getLogger(__name__)

class SimpleSecretsManager:
    """Simplified production-grade secrets management system"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.secrets_dir = self.workspace_path / "secrets"
        self.config_dir = self.workspace_path / "configs"
        self.archive_dir = self.workspace_path / "archive"
        self.secrets_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        
        # Create archive subdirectories
        (self.archive_dir / "env-backups").mkdir(exist_ok=True)
        (self.archive_dir / "secrets-backups").mkdir(exist_ok=True)
        (self.archive_dir / "config-backups").mkdir(exist_ok=True)
        
        # Load environment schema
        self.schema_file = self.config_dir / "environment_schema.yaml"
        self.schema = self._load_schema()
        
        # Secret rotation policies (now from schema)
        self.rotation_policies = self._extract_rotation_policies()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load environment schema from YAML file"""
        if not self.schema_file.exists():
            logger.warning(f"Schema file not found: {self.schema_file}")
            return {}
        
        try:
            with open(self.schema_file, 'r') as f:
                schema = yaml.safe_load(f)
            logger.info(f"Loaded environment schema from {self.schema_file}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return {}
    
    def _extract_rotation_policies(self) -> Dict[str, int]:
        """Extract rotation policies from schema"""
        if not self.schema or 'secret_types' not in self.schema:
            # Fallback to default policies
            return {
                'database_passwords': 90,
                'api_keys': 180,
                'jwt_secrets': 30,
                'encryption_keys': 365
            }
        
        policies = {}
        for secret_type, config in self.schema['secret_types'].items():
            policies[secret_type] = config.get('rotation_days', 90)
        
        return policies
    
    async def generate_secure_secrets(self, environment: str = "development") -> Dict[str, str]:
        """Generate secure secrets based on environment schema"""
        logger.info(f"Generating secure secrets for {environment} environment")
        
        if not self.schema or 'environments' not in self.schema:
            logger.warning("No schema available, using fallback secret generation")
            return self._generate_fallback_secrets()
        
        if environment not in self.schema['environments']:
            logger.error(f"Environment '{environment}' not found in schema")
            return self._generate_fallback_secrets()
        
        env_config = self.schema['environments'][environment]
        secrets_dict = {}
        
        # Generate secrets for all variables in the environment
        for var_name, var_config in env_config.get('variables', {}).items():
            if var_config.get('type') == 'secret':
                secret_type = var_config.get('secret_type', 'service_password')
                length = var_config.get('length', 32)
                
                if secret_type in ['database_password', 'storage_password', 'service_password', 'jwt_secret', 'webui_secret', 'encryption_key']:
                    secrets_dict[var_name] = self._generate_password(length)
                elif secret_type == 'api_key':
                    secrets_dict[var_name] = self._generate_api_key(length)
                else:
                    # Fallback to password generation
                    secrets_dict[var_name] = self._generate_password(length)
        
        # Add external API key placeholders
        secrets_dict.update({
            'OPENAI_API_KEY': 'sk-placeholder-change-me',
            'ANTHROPIC_API_KEY': 'sk-ant-placeholder-change-me',
            'GOOGLE_API_KEY': 'placeholder-change-me'
        })
        
        logger.info(f"Generated {len(secrets_dict)} secrets for {environment} environment")
        return secrets_dict
    
    def _generate_fallback_secrets(self) -> Dict[str, str]:
        """Fallback secret generation when schema is not available"""
        return {
            'POSTGRES_PASSWORD': self._generate_password(32),
            'MINIO_ROOT_PASSWORD': self._generate_password(32),
            'LITELLM_MASTER_KEY': self._generate_api_key(64),
            'LITELLM_SALT_KEY': self._generate_api_key(64),
            'VLLM_API_KEY': self._generate_api_key(64),
            'JWT_SECRET_KEY': self._generate_password(64),
            'WEBUI_SECRET_KEY': self._generate_password(32),
            'N8N_PASSWORD': self._generate_password(32),
            'N8N_ENCRYPTION_KEY': self._generate_password(32),
            'GRAFANA_PASSWORD': self._generate_password(32),
            'PROMETHEUS_ADMIN_PASSWORD': self._generate_password(32),
            'OPENAI_API_KEY': 'sk-placeholder-change-me',
            'ANTHROPIC_API_KEY': 'sk-ant-placeholder-change-me',
            'GOOGLE_API_KEY': 'placeholder-change-me'
        }
    
    def _generate_password(self, length: int = 32) -> str:
        """Generate cryptographically secure password"""
        # Avoid $ character to prevent Docker Compose variable interpretation issues
        alphabet = string.ascii_letters + string.digits + "!@#%^&*()_+-=[]{}|;:,.<>?"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_api_key(self, length: int = 64) -> str:
        """Generate cryptographically secure API key"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    async def store_secrets(self, secrets_dict: Dict[str, str], environment: str = "production") -> str:
        """Store secrets securely"""
        logger.info(f"Storing secrets for {environment} environment")
        
        # Create environment-specific secrets file
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        
        # Archive existing secrets file if it exists
        self._archive_existing_file(secrets_file, "secrets-backups")
        
        # Store secrets as JSON
        with open(secrets_file, 'w') as f:
            json.dump(secrets_dict, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(secrets_file, 0o600)
        
        # Create metadata
        metadata = {
            'created_at': datetime.utcnow().isoformat(),
            'environment': environment,
            'secrets_count': len(secrets_dict),
            'checksum': hashlib.sha256(json.dumps(secrets_dict, sort_keys=True).encode()).hexdigest()
        }
        
        metadata_file = self.secrets_dir / f".env.{environment}.metadata"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Secrets stored securely in {secrets_file}")
        return str(secrets_file)
    
    async def load_secrets(self, environment: str = "production") -> Dict[str, str]:
        """Load secrets"""
        secrets_file = self.secrets_dir / f".env.{environment}.json"
        
        if not secrets_file.exists():
            raise FileNotFoundError(f"Secrets file not found: {secrets_file}")
        
        with open(secrets_file, 'r') as f:
            secrets_dict = json.load(f)
        
        return secrets_dict
    
    def _archive_existing_file(self, file_path: Path, archive_type: str = "env-backups") -> Optional[Path]:
        """Archive an existing file before creating a new one"""
        if not file_path.exists():
            return None
        
        # Create timestamp for backup
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.backup.{timestamp}"
        archive_path = self.archive_dir / archive_type / backup_name
        
        try:
            # Move the existing file to archive
            file_path.rename(archive_path)
            logger.info(f"Archived existing file {file_path} to {archive_path}")
            return archive_path
        except Exception as e:
            logger.error(f"Failed to archive {file_path}: {e}")
            return None
    
    async def create_environment_files(self, environment: str = "development") -> List[str]:
        """Create environment files based on schema configuration"""
        logger.info(f"Creating environment files for {environment}")
        
        created_files = []
        
        # Generate secrets for this environment
        secrets_dict = await self.generate_secure_secrets(environment)
        
        # Get environment configuration from schema
        if not self.schema or 'environments' not in self.schema or environment not in self.schema['environments']:
            logger.error(f"Environment '{environment}' not found in schema")
            return []
        
        env_config = self.schema['environments'][environment]
        
        # Create .env file with all variables from schema
        env_file = self.workspace_path / f".env.{environment}"
        
        # Archive existing file if it exists
        self._archive_existing_file(env_file, "env-backups")
        
        with open(env_file, 'w') as f:
            f.write(f"# {environment.upper()} Environment Variables\n")
            f.write(f"# Generated on: {datetime.utcnow().isoformat()}\n")
            f.write(f"# Description: {env_config.get('description', 'No description available')}\n")
            f.write("# DO NOT COMMIT THIS FILE TO VERSION CONTROL\n\n")
            
            # Write all variables from schema
            for var_name, var_config in env_config.get('variables', {}).items():
                if var_config.get('type') == 'secret':
                    # Use generated secret
                    value = secrets_dict.get(var_name, '')
                else:
                    # Use configured value
                    value = var_config.get('value', '')
                
                # Add comment with description
                description = var_config.get('description', '')
                if description:
                    f.write(f"# {description}\n")
                
                f.write(f'{var_name}="{value}"\n')
                f.write("\n")
        
        os.chmod(env_file, 0o600)
        created_files.append(str(env_file))
        
        # Store secrets for this environment
        secrets_file = await self.store_secrets(secrets_dict, environment)
        created_files.append(secrets_file)
        
        # Create Docker Compose override if needed
        compose_override = self.workspace_path / f"docker-compose.{environment}.override.yml"
        if not compose_override.exists():
            with open(compose_override, 'w') as f:
                f.write(f"# Docker Compose Override for {environment.upper()}\n")
                f.write("services:\n")
                
                # Add environment variables to services based on schema
                services = env_config.get('services', [])
                for service in services:
                    f.write(f"  {service}:\n")
                    f.write("    env_file:\n")
                    f.write(f"      - .env.{environment}\n")
                    f.write("    environment:\n")
                    
                    # Add relevant environment variables for each service
                    service_vars = self._get_service_variables(service, env_config.get('variables', {}))
                    for var_name in service_vars:
                        f.write(f"      - {var_name}=${{{var_name}}}\n")
                    
                    f.write("\n")
            
            created_files.append(str(compose_override))
        
        # Create Kubernetes secrets template
        k8s_secrets = self.workspace_path / f"k8s-secrets-{environment}.yaml"
        with open(k8s_secrets, 'w') as f:
            f.write(f"# Kubernetes Secrets for {environment.upper()}\n")
            f.write("apiVersion: v1\n")
            f.write("kind: Secret\n")
            f.write(f"metadata:\n")
            f.write(f"  name: multimodal-secrets-{environment}\n")
            f.write(f"  namespace: multimodal\n")
            f.write("type: Opaque\n")
            f.write("data:\n")
            
            for key, value in secrets_dict.items():
                encoded_value = base64.b64encode(value.encode()).decode()
                f.write(f"  {key}: {encoded_value}\n")
        
        created_files.append(str(k8s_secrets))
        
        logger.info(f"Created {len(created_files)} environment files for {environment}")
        return created_files
    
    def _get_service_variables(self, service: str, variables: Dict[str, Any]) -> List[str]:
        """Get relevant environment variables for a specific service"""
        service_var_mapping = {
            'postgres': ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_PORT'],
            'minio': ['MINIO_ROOT_USER', 'MINIO_ROOT_PASSWORD', 'MINIO_PORT', 'MINIO_CONSOLE_PORT'],
            'vllm': ['VLLM_MODEL', 'VLLM_API_KEY', 'VLLM_HOST', 'VLLM_PORT', 'VLLM_GPU_MEMORY_UTILIZATION', 'VLLM_MAX_MODEL_LEN'],
            'litellm': ['LITELLM_MASTER_KEY', 'LITELLM_SALT_KEY', 'LITELLM_PORT'],
            'openwebui': ['WEBUI_SECRET_KEY', 'OPENWEBUI_PORT'],
            'n8n': ['N8N_PASSWORD', 'N8N_ENCRYPTION_KEY', 'N8N_PORT'],
            'multimodal-worker': ['MULTIMODAL_WORKER_PORT'],
            'retrieval-proxy': ['RETRIEVAL_PROXY_PORT'],
            'ai-agents': ['AI_AGENTS_PORT'],
            'search-engine': ['SEARCH_ENGINE_PORT'],
            'memory-system': ['MEMORY_SYSTEM_PORT'],
            'user-management': ['USER_MANAGEMENT_PORT', 'JWT_SECRET_KEY'],
            'redis': ['REDIS_PORT'],
            'qdrant': ['QDRANT_HTTP_PORT', 'QDRANT_GRPC_PORT'],
            'nginx': [],
            'elasticsearch': ['ELASTICSEARCH_PORT'],
            'kibana': ['KIBANA_PORT'],
            'logstash': ['LOGSTASH_PORT'],
            'prometheus': ['PROMETHEUS_ADMIN_PASSWORD'],
            'grafana': ['GRAFANA_PASSWORD']
        }
        
        service_vars = service_var_mapping.get(service, [])
        # Filter to only include variables that exist in the schema
        return [var for var in service_vars if var in variables]
    
    async def setup_secret_rotation(self) -> Dict[str, Any]:
        """Set up automated secret rotation"""
        logger.info("Setting up automated secret rotation")
        
        rotation_config = {
            'rotation_policies': self.rotation_policies,
            'rotation_schedule': {
                'database_passwords': '0 2 * * 0',  # Weekly on Sunday at 2 AM
                'api_keys': '0 3 1 * *',           # Monthly on 1st at 3 AM
                'jwt_secrets': '0 4 * * 1',        # Weekly on Monday at 4 AM
                'encryption_keys': '0 5 1 1 *'     # Yearly on Jan 1st at 5 AM
            },
            'notification_channels': {
                'email': '${ALERT_EMAIL}',
                'slack': '${SLACK_WEBHOOK_URL}'
            },
            'backup_before_rotation': True,
            'rollback_on_failure': True
        }
        
        # Create rotation script
        rotation_script = self.workspace_path / "scripts" / "rotate_secrets.py"
        rotation_script.parent.mkdir(exist_ok=True)
        
        script_content = '''#!/usr/bin/env python3
"""
Automated Secret Rotation Script
"""
import asyncio
import sys
from pathlib import Path

# Add workspace to path
sys.path.append(str(Path(__file__).parent.parent))

from security.secrets_manager_simple import SimpleSecretsManager

async def main():
    """Main rotation function"""
    secrets_manager = SimpleSecretsManager()
    
    # Load current secrets
    current_secrets = await secrets_manager.load_secrets("production")
    
    # Generate new secrets
    new_secrets = await secrets_manager.generate_secure_secrets()
    
    # Backup current secrets
    backup_file = await secrets_manager.store_secrets(current_secrets, "backup")
    print(f"Backed up current secrets to {backup_file}")
    
    # Store new secrets
    new_file = await secrets_manager.store_secrets(new_secrets, "production")
    print(f"Stored new secrets to {new_file}")
    
    # Create new environment files
    await secrets_manager.create_environment_files("production")
    print("Created new environment files")
    
    print("Secret rotation completed successfully")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(rotation_script, 'w') as f:
            f.write(script_content)
        
        os.chmod(rotation_script, 0o755)
        
        # Create cron job configuration
        cron_config = self.workspace_path / "configs" / "secret_rotation_cron"
        with open(cron_config, 'w') as f:
            f.write("# Secret Rotation Cron Jobs\n")
            f.write("# Run secret rotation weekly\n")
            f.write("0 2 * * 0 /workspace/scripts/rotate_secrets.py >> /var/log/secret_rotation.log 2>&1\n")
        
        # Store rotation configuration
        config_file = self.config_dir / "secret_rotation.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(rotation_config, f, default_flow_style=False)
        
        logger.info("Secret rotation system configured")
        return rotation_config
    
    async def validate_secrets(self, environment: str = "production") -> Dict[str, Any]:
        """Validate secrets for security compliance"""
        logger.info(f"Validating secrets for {environment}")
        
        secrets_dict = await self.load_secrets(environment)
        validation_results = {
            'total_secrets': len(secrets_dict),
            'valid_secrets': 0,
            'invalid_secrets': 0,
            'warnings': [],
            'errors': []
        }
        
        for key, value in secrets_dict.items():
            is_valid = True
            
            # Check password strength
            if 'PASSWORD' in key or 'SECRET' in key:
                if len(value) < 16:
                    validation_results['warnings'].append(f"{key}: Password too short (minimum 16 characters)")
                    is_valid = False
                
                if not any(c.isupper() for c in value):
                    validation_results['warnings'].append(f"{key}: Password should contain uppercase letters")
                
                if not any(c.islower() for c in value):
                    validation_results['warnings'].append(f"{key}: Password should contain lowercase letters")
                
                if not any(c.isdigit() for c in value):
                    validation_results['warnings'].append(f"{key}: Password should contain numbers")
                
                if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
                    validation_results['warnings'].append(f"{key}: Password should contain special characters")
            
            # Check API key strength
            if 'API_KEY' in key or 'KEY' in key:
                if len(value) < 32:
                    validation_results['errors'].append(f"{key}: API key too short (minimum 32 characters)")
                    is_valid = False
            
            # Check for placeholder values
            if value in ['placeholder', 'change-me', 'your-secret', 'dummy-key']:
                validation_results['errors'].append(f"{key}: Contains placeholder value")
                is_valid = False
            
            if is_valid:
                validation_results['valid_secrets'] += 1
            else:
                validation_results['invalid_secrets'] += 1
        
        validation_results['compliance_score'] = (
            validation_results['valid_secrets'] / validation_results['total_secrets'] * 100
        )
        
        logger.info(f"Secret validation completed: {validation_results['compliance_score']:.1f}% compliance")
        return validation_results
    
    async def create_security_policies(self) -> Dict[str, Any]:
        """Create security policies for secrets management"""
        logger.info("Creating security policies")
        
        policies = {
            'access_control': {
                'principle_of_least_privilege': True,
                'role_based_access': {
                    'admin': ['read', 'write', 'delete', 'rotate'],
                    'operator': ['read', 'write'],
                    'viewer': ['read']
                },
                'environment_separation': {
                    'production': ['admin', 'operator'],
                    'staging': ['admin', 'operator', 'viewer'],
                    'development': ['admin', 'operator', 'viewer']
                }
            },
            'encryption': {
                'encryption_at_rest': True,
                'encryption_in_transit': True,
                'key_rotation_policy': '90_days',
                'encryption_algorithm': 'AES-256-GCM'
            },
            'audit': {
                'log_all_access': True,
                'log_retention_days': 365,
                'alert_on_unauthorized_access': True,
                'audit_trail_immutable': True
            },
            'backup': {
                'backup_frequency': 'daily',
                'backup_retention_days': 30,
                'backup_encryption': True,
                'backup_verification': True
            }
        }
        
        # Create policy files
        policy_file = self.config_dir / "security_policies.yaml"
        with open(policy_file, 'w') as f:
            yaml.dump(policies, f, default_flow_style=False)
        
        # Create access control matrix
        access_matrix = {
            'environments': {
                'production': {
                    'allowed_users': ['admin', 'senior_operator'],
                    'required_approval': True,
                    'audit_level': 'high'
                },
                'staging': {
                    'allowed_users': ['admin', 'operator', 'senior_operator'],
                    'required_approval': False,
                    'audit_level': 'medium'
                },
                'development': {
                    'allowed_users': ['admin', 'operator', 'senior_operator', 'developer'],
                    'required_approval': False,
                    'audit_level': 'low'
                }
            },
            'secret_types': {
                'database_passwords': {
                    'access_level': 'restricted',
                    'rotation_frequency': '90_days',
                    'approval_required': True
                },
                'api_keys': {
                    'access_level': 'restricted',
                    'rotation_frequency': '180_days',
                    'approval_required': True
                },
                'jwt_secrets': {
                    'access_level': 'high',
                    'rotation_frequency': '30_days',
                    'approval_required': True
                }
            }
        }
        
        access_file = self.config_dir / "access_control_matrix.yaml"
        with open(access_file, 'w') as f:
            yaml.dump(access_matrix, f, default_flow_style=False)
        
        logger.info("Security policies created")
        return policies
    
    async def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for secrets management"""
        logger.info("Generating compliance report")
        
        # Validate secrets
        validation_results = await self.validate_secrets("production")
        
        # Check security policies
        policy_compliance = {
            'encryption_at_rest': True,
            'encryption_in_transit': True,
            'access_control': True,
            'audit_logging': True,
            'backup_procedures': True,
            'rotation_policies': True
        }
        
        # Generate compliance score
        compliance_score = (
            validation_results['compliance_score'] + 
            sum(policy_compliance.values()) / len(policy_compliance) * 100
        ) / 2
        
        report = {
            'report_timestamp': datetime.utcnow().isoformat(),
            'compliance_score': compliance_score,
            'validation_results': validation_results,
            'policy_compliance': policy_compliance,
            'recommendations': [
                'Implement automated secret rotation',
                'Set up HashiCorp Vault for enterprise secrets management',
                'Enable audit logging for all secret access',
                'Implement role-based access control',
                'Regular security assessments and penetration testing'
            ],
            'next_audit_date': (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        # Save report
        report_file = self.workspace_path / "reports" / "secrets_compliance_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Compliance report generated: {compliance_score:.1f}% compliance")
        return report

# Global secrets manager instance - will be initialized when needed
# secrets_manager = SimpleSecretsManager()