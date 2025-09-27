"""
Configuration generator for setup wizard
"""

import os
import secrets
import string
from typing import Dict, Any, Optional
import logging

from .models import StorageConfig, SecurityConfig, DeploymentConfig, SetupState
from .config import settings

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """Generate configuration files based on setup choices"""
    
    def __init__(self):
        self.env_template = self._load_env_template()
    
    def _load_env_template(self) -> str:
        """Load environment template"""
        return """# Database Configuration
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD={postgres_password}

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD={minio_password}

# vLLM Configuration
VLLM_MODEL={vllm_model}
VLLM_API_KEY={vllm_api_key}

# LiteLLM Configuration
LITELLM_MASTER_KEY={litellm_master_key}
LITELLM_SALT_KEY={litellm_salt_key}

# OpenWebUI Configuration
WEBUI_SECRET_KEY={webui_secret_key}

# GPU Configuration
CUDA_VISIBLE_DEVICES=0

# Model Paths
MODELS_PATH=./models

# Storage Paths
QDRANT_DATA_PATH={qdrant_data_path}
POSTGRES_DATA_PATH={postgres_data_path}
MINIO_DATA_PATH={minio_data_path}
CACHE_PATH={cache_path}

# n8n Workflow Management
N8N_PASSWORD={n8n_password}
N8N_ENCRYPTION_KEY={n8n_encryption_key}

# Setup Wizard Configuration
SETUP_WIZARD_HOST=0.0.0.0
SETUP_WIZARD_PORT=8004
SETUP_WIZARD_DEBUG=false
"""
    
    def generate_password(self, length: int = 32) -> str:
        """Generate secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_api_key(self) -> str:
        """Generate API key"""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def generate_secrets(self, security_config: SecurityConfig) -> Dict[str, str]:
        """Generate all required secrets"""
        secrets_dict = {}
        
        if security_config.generate_secure_passwords:
            secrets_dict.update({
                "postgres_password": self.generate_password(),
                "minio_password": self.generate_password(),
                "vllm_api_key": self.generate_password(),
                "litellm_master_key": self.generate_api_key(),
                "litellm_salt_key": self.generate_api_key(),
                "webui_secret_key": self.generate_password(),
                "n8n_password": self.generate_password(),
                "n8n_encryption_key": self.generate_password()
            })
        else:
            # Use custom passwords if provided
            secrets_dict.update({
                "postgres_password": security_config.custom_passwords.get("postgres", "postgres"),
                "minio_password": security_config.custom_passwords.get("minio", "minioadmin"),
                "vllm_api_key": security_config.custom_passwords.get("vllm", "vllm-key"),
                "litellm_master_key": security_config.custom_passwords.get("litellm", "sk-litellm-key"),
                "litellm_salt_key": security_config.custom_passwords.get("litellm_salt", "sk-salt-key"),
                "webui_secret_key": security_config.custom_passwords.get("webui", "webui-secret"),
                "n8n_password": security_config.custom_passwords.get("n8n", "n8n-password"),
                "n8n_encryption_key": security_config.custom_passwords.get("n8n_encryption", "n8n-encryption-key")
            })
        
        return secrets_dict
    
    def generate_storage_paths(self, storage_config: StorageConfig) -> Dict[str, str]:
        """Generate storage paths based on configuration"""
        if storage_config.use_nvme and os.path.exists(storage_config.nvme_path):
            base_path = storage_config.nvme_path
        else:
            base_path = storage_config.local_path
        
        return {
            "qdrant_data_path": f"{base_path}/qdrant",
            "postgres_data_path": f"{base_path}/postgres",
            "minio_data_path": f"{base_path}/minio",
            "cache_path": storage_config.cache_path
        }
    
    def generate_env_file(self, setup_state: SetupState) -> str:
        """Generate .env file content"""
        # Generate secrets
        secrets_dict = self.generate_secrets(setup_state.security_config)
        
        # Generate storage paths
        storage_paths = self.generate_storage_paths(setup_state.storage_config)
        
        # Prepare template variables
        template_vars = {
            **secrets_dict,
            **storage_paths,
            "vllm_model": setup_state.selected_model
        }
        
        # Format template
        env_content = self.env_template.format(**template_vars)
        
        return env_content
    
    def write_env_file(self, setup_state: SetupState, env_path: str) -> bool:
        """Write .env file to disk"""
        try:
            env_content = self.generate_env_file(setup_state)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(env_path), exist_ok=True)
            
            # Write file
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            logger.info(f"Generated .env file at {env_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write .env file: {e}")
            return False
    
    def generate_docker_compose_override(self, setup_state: SetupState) -> str:
        """Generate docker-compose override for GPU support"""
        if not setup_state.system_check.nvidia_gpu_available:
            return ""
        
        return """version: '3.8'
services:
  vllm:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
  
  multimodal-worker:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
"""
    
    def write_docker_compose_override(self, setup_state: SetupState, override_path: str) -> bool:
        """Write docker-compose override file"""
        try:
            override_content = self.generate_docker_compose_override(setup_state)
            
            if override_content:
                with open(override_path, 'w') as f:
                    f.write(override_content)
                logger.info(f"Generated docker-compose override at {override_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to write docker-compose override: {e}")
            return False
    
    def create_directories(self, setup_state: SetupState) -> bool:
        """Create necessary directories"""
        try:
            storage_paths = self.generate_storage_paths(setup_state.storage_config)
            
            directories = [
                "models",
                "logs",
                storage_paths["qdrant_data_path"],
                storage_paths["postgres_data_path"],
                storage_paths["minio_data_path"],
                storage_paths["cache_path"]
            ]
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            return False
    
    def generate_setup_script(self, setup_state: SetupState) -> str:
        """Generate custom setup script based on choices"""
        script_content = f"""#!/bin/bash
set -e

echo "🚀 Starting Multimodal LLM Stack Setup..."
echo "Model: {setup_state.selected_model}"
echo "Storage: {'NVMe' if setup_state.storage_config.use_nvme else 'Local'}"
echo "Deployment: {setup_state.deployment_config.deployment_type}"

# Create directories
mkdir -p models logs
mkdir -p {self.generate_storage_paths(setup_state.storage_config)['qdrant_data_path']}
mkdir -p {self.generate_storage_paths(setup_state.storage_config)['postgres_data_path']}
mkdir -p {self.generate_storage_paths(setup_state.storage_config)['minio_data_path']}
mkdir -p {self.generate_storage_paths(setup_state.storage_config)['cache_path']}

# Set permissions
chmod +x scripts/*.sh

echo "✅ Setup preparation completed!"
echo "Next: docker-compose up -d"
"""
        
        return script_content
