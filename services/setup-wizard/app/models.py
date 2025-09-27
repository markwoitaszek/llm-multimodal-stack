"""
Data models for Setup Wizard Service
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class SetupStep(str, Enum):
    """Setup wizard steps"""
    WELCOME = "welcome"
    SYSTEM_CHECK = "system_check"
    MODEL_SELECTION = "model_selection"
    STORAGE_CONFIG = "storage_config"
    SECURITY_CONFIG = "security_config"
    DEPLOYMENT_CONFIG = "deployment_config"
    VALIDATION = "validation"
    DEPLOYMENT = "deployment"
    COMPLETION = "completion"


class SystemCheckResult(BaseModel):
    """System check results"""
    docker_installed: bool
    docker_compose_installed: bool
    nvidia_gpu_available: bool
    nvidia_docker_available: bool
    disk_space_gb: float
    memory_gb: float
    ports_available: List[int]
    conflicts: List[str]


class ModelOption(BaseModel):
    """Model selection option"""
    id: str
    name: str
    description: str
    size_gb: float
    memory_required_gb: float
    recommended: bool = False
    requires_approval: bool = False


class StorageConfig(BaseModel):
    """Storage configuration"""
    use_nvme: bool = False
    nvme_path: str = "/mnt/nvme"
    local_path: str = "./data"
    cache_path: str = "/tmp/cache"


class SecurityConfig(BaseModel):
    """Security configuration"""
    generate_secure_passwords: bool = True
    custom_passwords: Dict[str, str] = Field(default_factory=dict)
    enable_ssl: bool = False
    domain: Optional[str] = None


class DeploymentConfig(BaseModel):
    """Deployment configuration"""
    deployment_type: str = "development"  # development, production
    enable_monitoring: bool = True
    enable_n8n: bool = True
    scale_workers: int = 1


class SetupState(BaseModel):
    """Current setup state"""
    current_step: SetupStep
    completed_steps: List[SetupStep] = Field(default_factory=list)
    system_check: Optional[SystemCheckResult] = None
    selected_model: Optional[str] = None
    storage_config: Optional[StorageConfig] = None
    security_config: Optional[SecurityConfig] = None
    deployment_config: Optional[DeploymentConfig] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SetupProgress(BaseModel):
    """Setup progress tracking"""
    session_id: str
    state: SetupState
    progress_percentage: float
    current_task: str
    estimated_time_remaining: Optional[int] = None  # seconds


class ValidationResult(BaseModel):
    """Configuration validation result"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class DeploymentStatus(BaseModel):
    """Deployment status"""
    status: str  # pending, running, completed, failed
    progress: float
    current_service: str
    completed_services: List[str] = Field(default_factory=list)
    failed_services: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
