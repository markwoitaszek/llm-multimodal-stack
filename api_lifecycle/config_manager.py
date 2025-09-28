#!/usr/bin/env python3
"""
API Configuration Management System
Part of Issue #46: API Lifecycle Management

This module provides comprehensive configuration management including:
- Environment-specific configurations
- Configuration validation and schema management
- Secret management and encryption
- Configuration versioning and rollback
- Dynamic configuration updates
- Configuration templates and inheritance
"""

import asyncio
import json
import yaml
import uuid
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pathlib import Path
import secrets
from cryptography.fernet import Fernet
import jsonschema
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """Configuration type enumeration"""
    APPLICATION = "application"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    SECURITY = "security"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"

class ConfigStatus(Enum):
    """Configuration status enumeration"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class SecretType(Enum):
    """Secret type enumeration"""
    API_KEY = "api_key"
    PASSWORD = "password"
    TOKEN = "token"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    DATABASE_URL = "database_url"

@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    schema_id: str
    name: str
    config_type: ConfigType
    version: str
    schema: Dict[str, Any]
    required_fields: List[str] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Secret:
    """Secret configuration"""
    secret_id: str
    name: str
    secret_type: SecretType
    encrypted_value: str
    environment: str
    created_date: str
    last_updated: str
    expires_date: Optional[str] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)

@dataclass
class Configuration:
    """Configuration instance"""
    config_id: str
    name: str
    config_type: ConfigType
    environment: str
    version: str
    status: ConfigStatus
    data: Dict[str, Any]
    schema_id: Optional[str] = None
    parent_config: Optional[str] = None
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    tags: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)  # Secret IDs

@dataclass
class ConfigTemplate:
    """Configuration template"""
    template_id: str
    name: str
    config_type: ConfigType
    template_data: Dict[str, Any]
    variables: List[str] = field(default_factory=list)
    description: str = ""
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())

class ConfigManager:
    """Manages API configurations"""
    
    def __init__(self, data_dir: Path, encryption_key: Optional[bytes] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Encryption
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Storage
        self.configurations: Dict[str, Configuration] = {}
        self.schemas: Dict[str, ConfigSchema] = {}
        self.secrets: Dict[str, Secret] = {}
        self.templates: Dict[str, ConfigTemplate] = {}
        self.config_history: List[Dict[str, Any]] = []
        
        # Configuration files
        self.configs_file = self.data_dir / "configurations.json"
        self.schemas_file = self.data_dir / "schemas.json"
        self.secrets_file = self.data_dir / "secrets.json"
        self.templates_file = self.data_dir / "templates.json"
        self.history_file = self.data_dir / "history.json"
        
        # Load existing data
        self._load_data()
        
        # Initialize default schemas
        self._initialize_default_schemas()
    
    def _load_data(self):
        """Load configuration data from files"""
        try:
            # Load configurations
            if self.configs_file.exists():
                with open(self.configs_file, 'r') as f:
                    data = json.load(f)
                    for config_id, config_data in data.items():
                        config_data['config_type'] = ConfigType(config_data['config_type'])
                        config_data['status'] = ConfigStatus(config_data['status'])
                        self.configurations[config_id] = Configuration(**config_data)
            
            # Load schemas
            if self.schemas_file.exists():
                with open(self.schemas_file, 'r') as f:
                    data = json.load(f)
                    for schema_id, schema_data in data.items():
                        schema_data['config_type'] = ConfigType(schema_data['config_type'])
                        self.schemas[schema_id] = ConfigSchema(**schema_data)
            
            # Load secrets
            if self.secrets_file.exists():
                with open(self.secrets_file, 'r') as f:
                    data = json.load(f)
                    for secret_id, secret_data in data.items():
                        secret_data['secret_type'] = SecretType(secret_data['secret_type'])
                        self.secrets[secret_id] = Secret(**secret_data)
            
            # Load templates
            if self.templates_file.exists():
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                    for template_id, template_data in data.items():
                        template_data['config_type'] = ConfigType(template_data['config_type'])
                        self.templates[template_id] = ConfigTemplate(**template_data)
            
            # Load history
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    self.config_history = json.load(f)
            
            logger.info(f"Loaded {len(self.configurations)} configurations, {len(self.schemas)} schemas, {len(self.secrets)} secrets")
            
        except Exception as e:
            logger.error(f"Error loading configuration data: {e}")
    
    def _save_data(self):
        """Save configuration data to files"""
        try:
            # Save configurations
            configs_data = {}
            for config_id, config in self.configurations.items():
                config_dict = asdict(config)
                config_dict['config_type'] = config.config_type.value
                config_dict['status'] = config.status.value
                configs_data[config_id] = config_dict
            
            with open(self.configs_file, 'w') as f:
                json.dump(configs_data, f, indent=2)
            
            # Save schemas
            schemas_data = {}
            for schema_id, schema in self.schemas.items():
                schema_dict = asdict(schema)
                schema_dict['config_type'] = schema.config_type.value
                schemas_data[schema_id] = schema_dict
            
            with open(self.schemas_file, 'w') as f:
                json.dump(schemas_data, f, indent=2)
            
            # Save secrets
            secrets_data = {}
            for secret_id, secret in self.secrets.items():
                secret_dict = asdict(secret)
                secret_dict['secret_type'] = secret.secret_type.value
                secrets_data[secret_id] = secret_dict
            
            with open(self.secrets_file, 'w') as f:
                json.dump(secrets_data, f, indent=2)
            
            # Save templates
            templates_data = {}
            for template_id, template in self.templates.items():
                template_dict = asdict(template)
                template_dict['config_type'] = template.config_type.value
                templates_data[template_id] = template_dict
            
            with open(self.templates_file, 'w') as f:
                json.dump(templates_data, f, indent=2)
            
            # Save history
            with open(self.history_file, 'w') as f:
                json.dump(self.config_history, f, indent=2)
            
            logger.info("Configuration data saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving configuration data: {e}")
    
    def _initialize_default_schemas(self):
        """Initialize default configuration schemas"""
        if not self.schemas:
            # Application configuration schema
            app_schema = ConfigSchema(
                schema_id="app-config-v1",
                name="Application Configuration",
                config_type=ConfigType.APPLICATION,
                version="1.0.0",
                schema={
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string"},
                        "version": {"type": "string"},
                        "debug": {"type": "boolean"},
                        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "host": {"type": "string"},
                        "timeout": {"type": "integer", "minimum": 1}
                    },
                    "required": ["app_name", "version", "port", "host"]
                },
                required_fields=["app_name", "version", "port", "host"],
                default_values={
                    "debug": False,
                    "log_level": "INFO",
                    "timeout": 30
                }
            )
            
            # Database configuration schema
            db_schema = ConfigSchema(
                schema_id="db-config-v1",
                name="Database Configuration",
                config_type=ConfigType.DATABASE,
                version="1.0.0",
                schema={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "database": {"type": "string"},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "pool_size": {"type": "integer", "minimum": 1},
                        "timeout": {"type": "integer", "minimum": 1}
                    },
                    "required": ["host", "port", "database", "username"]
                },
                required_fields=["host", "port", "database", "username"],
                default_values={
                    "pool_size": 10,
                    "timeout": 30
                }
            )
            
            self.schemas["app-config-v1"] = app_schema
            self.schemas["db-config-v1"] = db_schema
            self._save_data()
    
    def create_schema(
        self,
        schema_id: str,
        name: str,
        config_type: ConfigType,
        version: str,
        schema: Dict[str, Any],
        required_fields: List[str] = None,
        default_values: Dict[str, Any] = None
    ) -> ConfigSchema:
        """Create a configuration schema"""
        if schema_id in self.schemas:
            raise ValueError(f"Schema {schema_id} already exists")
        
        config_schema = ConfigSchema(
            schema_id=schema_id,
            name=name,
            config_type=config_type,
            version=version,
            schema=schema,
            required_fields=required_fields or [],
            default_values=default_values or {}
        )
        
        self.schemas[schema_id] = config_schema
        self._save_data()
        
        logger.info(f"Created configuration schema: {schema_id}")
        return config_schema
    
    def create_configuration(
        self,
        config_id: str,
        name: str,
        config_type: ConfigType,
        environment: str,
        data: Dict[str, Any],
        schema_id: Optional[str] = None,
        parent_config: Optional[str] = None,
        description: str = "",
        tags: List[str] = None
    ) -> Configuration:
        """Create a configuration"""
        if config_id in self.configurations:
            raise ValueError(f"Configuration {config_id} already exists")
        
        # Validate against schema if provided
        if schema_id:
            self._validate_configuration_data(data, schema_id)
        
        # Apply default values from schema
        if schema_id and schema_id in self.schemas:
            schema = self.schemas[schema_id]
            for key, value in schema.default_values.items():
                if key not in data:
                    data[key] = value
        
        configuration = Configuration(
            config_id=config_id,
            name=name,
            config_type=config_type,
            environment=environment,
            version="1.0.0",
            status=ConfigStatus.DRAFT,
            data=data,
            schema_id=schema_id,
            parent_config=parent_config,
            description=description,
            tags=tags or []
        )
        
        self.configurations[config_id] = configuration
        self._save_data()
        
        # Record in history
        self._record_config_change(config_id, "created", data)
        
        logger.info(f"Created configuration: {config_id}")
        return configuration
    
    def _validate_configuration_data(self, data: Dict[str, Any], schema_id: str):
        """Validate configuration data against schema"""
        if schema_id not in self.schemas:
            raise ValueError(f"Schema {schema_id} not found")
        
        schema = self.schemas[schema_id]
        
        try:
            jsonschema.validate(data, schema.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e.message}")
        
        # Check required fields
        for field in schema.required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' is missing")
    
    def update_configuration(
        self,
        config_id: str,
        data: Dict[str, Any],
        version: Optional[str] = None,
        description: str = ""
    ) -> Configuration:
        """Update a configuration"""
        if config_id not in self.configurations:
            raise ValueError(f"Configuration {config_id} not found")
        
        configuration = self.configurations[config_id]
        
        # Validate against schema if provided
        if configuration.schema_id:
            self._validate_configuration_data(data, configuration.schema_id)
        
        # Record old data for history
        old_data = configuration.data.copy()
        
        # Update configuration
        configuration.data = data
        configuration.last_updated = datetime.now().isoformat()
        
        if version:
            configuration.version = version
        
        if description:
            configuration.description = description
        
        self._save_data()
        
        # Record in history
        self._record_config_change(config_id, "updated", data, old_data)
        
        logger.info(f"Updated configuration: {config_id}")
        return configuration
    
    def activate_configuration(self, config_id: str) -> Configuration:
        """Activate a configuration"""
        if config_id not in self.configurations:
            raise ValueError(f"Configuration {config_id} not found")
        
        configuration = self.configurations[config_id]
        configuration.status = ConfigStatus.ACTIVE
        configuration.last_updated = datetime.now().isoformat()
        
        self._save_data()
        
        # Record in history
        self._record_config_change(config_id, "activated", configuration.data)
        
        logger.info(f"Activated configuration: {config_id}")
        return configuration
    
    def deprecate_configuration(self, config_id: str) -> Configuration:
        """Deprecate a configuration"""
        if config_id not in self.configurations:
            raise ValueError(f"Configuration {config_id} not found")
        
        configuration = self.configurations[config_id]
        configuration.status = ConfigStatus.DEPRECATED
        configuration.last_updated = datetime.now().isoformat()
        
        self._save_data()
        
        # Record in history
        self._record_config_change(config_id, "deprecated", configuration.data)
        
        logger.info(f"Deprecated configuration: {config_id}")
        return configuration
    
    def archive_configuration(self, config_id: str) -> Configuration:
        """Archive a configuration"""
        if config_id not in self.configurations:
            raise ValueError(f"Configuration {config_id} not found")
        
        configuration = self.configurations[config_id]
        configuration.status = ConfigStatus.ARCHIVED
        configuration.last_updated = datetime.now().isoformat()
        
        self._save_data()
        
        # Record in history
        self._record_config_change(config_id, "archived", configuration.data)
        
        logger.info(f"Archived configuration: {config_id}")
        return configuration
    
    def create_secret(
        self,
        secret_id: str,
        name: str,
        secret_type: SecretType,
        value: str,
        environment: str,
        expires_date: Optional[str] = None,
        description: str = "",
        tags: List[str] = None
    ) -> Secret:
        """Create a secret"""
        if secret_id in self.secrets:
            raise ValueError(f"Secret {secret_id} already exists")
        
        # Encrypt the secret value
        encrypted_value = self.cipher.encrypt(value.encode()).decode()
        
        secret = Secret(
            secret_id=secret_id,
            name=name,
            secret_type=secret_type,
            encrypted_value=encrypted_value,
            environment=environment,
            created_date=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            expires_date=expires_date,
            description=description,
            tags=tags or []
        )
        
        self.secrets[secret_id] = secret
        self._save_data()
        
        logger.info(f"Created secret: {secret_id}")
        return secret
    
    def get_secret_value(self, secret_id: str) -> str:
        """Get decrypted secret value"""
        if secret_id not in self.secrets:
            raise ValueError(f"Secret {secret_id} not found")
        
        secret = self.secrets[secret_id]
        
        # Check if secret has expired
        if secret.expires_date:
            expires = datetime.fromisoformat(secret.expires_date)
            if datetime.now() > expires:
                raise ValueError(f"Secret {secret_id} has expired")
        
        # Decrypt the secret value
        try:
            decrypted_value = self.cipher.decrypt(secret.encrypted_value.encode()).decode()
            return decrypted_value
        except Exception as e:
            raise ValueError(f"Failed to decrypt secret {secret_id}: {e}")
    
    def update_secret(
        self,
        secret_id: str,
        value: str,
        expires_date: Optional[str] = None
    ) -> Secret:
        """Update a secret"""
        if secret_id not in self.secrets:
            raise ValueError(f"Secret {secret_id} not found")
        
        secret = self.secrets[secret_id]
        
        # Encrypt the new value
        secret.encrypted_value = self.cipher.encrypt(value.encode()).decode()
        secret.last_updated = datetime.now().isoformat()
        
        if expires_date:
            secret.expires_date = expires_date
        
        self._save_data()
        
        logger.info(f"Updated secret: {secret_id}")
        return secret
    
    def create_template(
        self,
        template_id: str,
        name: str,
        config_type: ConfigType,
        template_data: Dict[str, Any],
        variables: List[str] = None,
        description: str = ""
    ) -> ConfigTemplate:
        """Create a configuration template"""
        if template_id in self.templates:
            raise ValueError(f"Template {template_id} already exists")
        
        template = ConfigTemplate(
            template_id=template_id,
            name=name,
            config_type=config_type,
            template_data=template_data,
            variables=variables or [],
            description=description
        )
        
        self.templates[template_id] = template
        self._save_data()
        
        logger.info(f"Created configuration template: {template_id}")
        return template
    
    def generate_config_from_template(
        self,
        template_id: str,
        config_id: str,
        name: str,
        environment: str,
        variables: Dict[str, Any],
        schema_id: Optional[str] = None
    ) -> Configuration:
        """Generate configuration from template"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        # Generate configuration data from template
        config_data = self._process_template(template.template_data, variables)
        
        # Create configuration
        configuration = self.create_configuration(
            config_id=config_id,
            name=name,
            config_type=template.config_type,
            environment=environment,
            data=config_data,
            schema_id=schema_id,
            description=f"Generated from template {template_id}"
        )
        
        logger.info(f"Generated configuration {config_id} from template {template_id}")
        return configuration
    
    def _process_template(self, template_data: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Process template with variables"""
        import re
        
        def replace_variables(obj):
            if isinstance(obj, dict):
                return {k: replace_variables(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_variables(item) for item in obj]
            elif isinstance(obj, str):
                # Replace ${variable} patterns
                pattern = r'\$\{([^}]+)\}'
                return re.sub(pattern, lambda m: str(variables.get(m.group(1), m.group(0))), obj)
            else:
                return obj
        
        return replace_variables(template_data)
    
    def get_configuration(self, config_id: str) -> Optional[Configuration]:
        """Get configuration by ID"""
        return self.configurations.get(config_id)
    
    def list_configurations(
        self,
        config_type: Optional[ConfigType] = None,
        environment: Optional[str] = None,
        status: Optional[ConfigStatus] = None
    ) -> List[Configuration]:
        """List configurations with optional filters"""
        configurations = list(self.configurations.values())
        
        if config_type:
            configurations = [c for c in configurations if c.config_type == config_type]
        
        if environment:
            configurations = [c for c in configurations if c.environment == environment]
        
        if status:
            configurations = [c for c in configurations if c.status == status]
        
        # Sort by last updated (newest first)
        configurations.sort(key=lambda c: c.last_updated, reverse=True)
        
        return configurations
    
    def get_configuration_for_environment(
        self,
        config_name: str,
        environment: str,
        config_type: ConfigType
    ) -> Optional[Configuration]:
        """Get active configuration for specific environment"""
        configurations = self.list_configurations(
            config_type=config_type,
            environment=environment,
            status=ConfigStatus.ACTIVE
        )
        
        # Find by name
        for config in configurations:
            if config.name == config_name:
                return config
        
        return None
    
    def export_configuration(self, config_id: str, format: str = "json") -> str:
        """Export configuration in specified format"""
        if config_id not in self.configurations:
            raise ValueError(f"Configuration {config_id} not found")
        
        configuration = self.configurations[config_id]
        
        if format == "json":
            return json.dumps(asdict(configuration), indent=2)
        elif format == "yaml":
            return yaml.dump(asdict(configuration), default_flow_style=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_configuration(self, config_data: str, format: str = "json") -> Configuration:
        """Import configuration from specified format"""
        if format == "json":
            data = json.loads(config_data)
        elif format == "yaml":
            data = yaml.safe_load(config_data)
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        # Create configuration from imported data
        config_id = data.get("config_id", str(uuid.uuid4()))
        
        configuration = Configuration(
            config_id=config_id,
            name=data["name"],
            config_type=ConfigType(data["config_type"]),
            environment=data["environment"],
            version=data.get("version", "1.0.0"),
            status=ConfigStatus(data.get("status", "draft")),
            data=data["data"],
            schema_id=data.get("schema_id"),
            parent_config=data.get("parent_config"),
            description=data.get("description", ""),
            tags=data.get("tags", [])
        )
        
        self.configurations[config_id] = configuration
        self._save_data()
        
        logger.info(f"Imported configuration: {config_id}")
        return configuration
    
    def _record_config_change(
        self,
        config_id: str,
        action: str,
        new_data: Dict[str, Any],
        old_data: Optional[Dict[str, Any]] = None
    ):
        """Record configuration change in history"""
        change_record = {
            "change_id": str(uuid.uuid4()),
            "config_id": config_id,
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "new_data": new_data,
            "old_data": old_data
        }
        
        self.config_history.append(change_record)
        
        # Keep only last 1000 changes
        if len(self.config_history) > 1000:
            self.config_history = self.config_history[-1000:]
    
    def get_configuration_history(self, config_id: str) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        return [
            change for change in self.config_history
            if change["config_id"] == config_id
        ]
    
    def rollback_configuration(self, config_id: str, change_id: str) -> Configuration:
        """Rollback configuration to a previous state"""
        history = self.get_configuration_history(config_id)
        
        # Find the change to rollback to
        target_change = None
        for change in history:
            if change["change_id"] == change_id:
                target_change = change
                break
        
        if not target_change:
            raise ValueError(f"Change {change_id} not found for configuration {config_id}")
        
        if config_id not in self.configurations:
            raise ValueError(f"Configuration {config_id} not found")
        
        configuration = self.configurations[config_id]
        
        # Rollback to the target state
        if target_change["old_data"]:
            configuration.data = target_change["old_data"]
            configuration.last_updated = datetime.now().isoformat()
            
            self._save_data()
            
            # Record rollback in history
            self._record_config_change(config_id, "rollback", configuration.data)
            
            logger.info(f"Rolled back configuration {config_id} to change {change_id}")
        
        return configuration
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        summary = {
            "total_configurations": len(self.configurations),
            "by_type": {},
            "by_environment": {},
            "by_status": {},
            "total_secrets": len(self.secrets),
            "total_schemas": len(self.schemas),
            "total_templates": len(self.templates)
        }
        
        # Count by type
        for config in self.configurations.values():
            config_type = config.config_type.value
            summary["by_type"][config_type] = summary["by_type"].get(config_type, 0) + 1
            
            # Count by environment
            env = config.environment
            summary["by_environment"][env] = summary["by_environment"].get(env, 0) + 1
            
            # Count by status
            status = config.status.value
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        return summary

async def main():
    """Main function to demonstrate config manager"""
    data_dir = Path("./config_data")
    manager = ConfigManager(data_dir)
    
    # Create a configuration
    config = manager.create_configuration(
        "app-dev",
        "Application Development Config",
        ConfigType.APPLICATION,
        "development",
        {
            "app_name": "My API",
            "version": "1.0.0",
            "debug": True,
            "log_level": "DEBUG",
            "port": 8000,
            "host": "localhost",
            "timeout": 30
        },
        schema_id="app-config-v1"
    )
    
    print(f"Created configuration: {config.config_id}")
    
    # Activate the configuration
    manager.activate_configuration("app-dev")
    print("Activated configuration")
    
    # Create a secret
    secret = manager.create_secret(
        "db-password-dev",
        "Database Password Dev",
        SecretType.PASSWORD,
        "secretpassword123",
        "development"
    )
    
    print(f"Created secret: {secret.secret_id}")
    
    # Get secret value
    password = manager.get_secret_value("db-password-dev")
    print(f"Retrieved secret value: {password[:5]}...")
    
    # Get configuration summary
    summary = manager.get_configuration_summary()
    print(f"Configuration summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())