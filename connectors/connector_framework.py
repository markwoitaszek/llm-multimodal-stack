#!/usr/bin/env python3
"""
API Connector Framework for Multimodal LLM Stack
Part of Issue #10: API Connector Ecosystem

This module provides a comprehensive connector framework including:
- Universal connector interface and base classes
- Connector registry and management
- Data transformation and mapping
- Authentication and security handling
- Error handling and retry logic
- Monitoring and logging
"""

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import aiohttp
import yaml
from pathlib import Path
import hashlib
import hmac
import base64
from urllib.parse import urlencode, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectorStatus(Enum):
    """Connector status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"
    TESTING = "testing"

class AuthenticationType(Enum):
    """Authentication type enumeration"""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    BEARER = "bearer"
    CUSTOM = "custom"

class DataFormat(Enum):
    """Data format enumeration"""
    JSON = "json"
    XML = "xml"
    FORM = "form"
    TEXT = "text"
    BINARY = "binary"

@dataclass
class ConnectorConfig:
    """Connector configuration"""
    connector_id: str
    name: str
    description: str
    version: str
    base_url: str
    authentication_type: AuthenticationType
    auth_config: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    rate_limit: Optional[int] = None
    rate_limit_window: int = 60
    data_format: DataFormat = DataFormat.JSON
    custom_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConnectorEndpoint:
    """Connector endpoint definition"""
    name: str
    path: str
    method: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    request_schema: Dict[str, Any] = field(default_factory=dict)
    response_schema: Dict[str, Any] = field(default_factory=dict)
    authentication_required: bool = True
    rate_limit: Optional[int] = None

@dataclass
class ConnectorResponse:
    """Standardized connector response"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ConnectorMetrics:
    """Connector performance metrics"""
    connector_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    last_request_time: Optional[str] = None
    error_count: int = 0
    rate_limit_hits: int = 0

class ConnectorError(Exception):
    """Base exception for connector errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class AuthenticationError(ConnectorError):
    """Authentication-related errors"""
    pass

class RateLimitError(ConnectorError):
    """Rate limit exceeded errors"""
    pass

class ConfigurationError(ConnectorError):
    """Configuration-related errors"""
    pass

class BaseConnector(ABC):
    """Base class for all connectors"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.status = ConnectorStatus.INACTIVE
        self.metrics = ConnectorMetrics(connector_id=config.connector_id)
        self.session: Optional[aiohttp.ClientSession] = None
        self.endpoints: Dict[str, ConnectorEndpoint] = {}
        self.rate_limit_tracker: Dict[str, List[float]] = {}
        
        # Initialize endpoints
        self._initialize_endpoints()
    
    @abstractmethod
    def _initialize_endpoints(self):
        """Initialize connector endpoints"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the service"""
        pass
    
    async def make_request(
        self,
        endpoint_name: str,
        params: Dict[str, Any] = None,
        data: Any = None,
        headers: Dict[str, str] = None
    ) -> ConnectorResponse:
        """Make a request to a connector endpoint"""
        try:
            # Check if endpoint exists
            if endpoint_name not in self.endpoints:
                raise ConnectorError(f"Endpoint '{endpoint_name}' not found")
            
            endpoint = self.endpoints[endpoint_name]
            
            # Check rate limits
            await self._check_rate_limit(endpoint)
            
            # Prepare request
            url = self._build_url(endpoint.path, params)
            request_headers = self._prepare_headers(headers)
            request_data = self._prepare_data(data)
            
            # Make request
            start_time = time.time()
            async with self.session.request(
                method=endpoint.method,
                url=url,
                headers=request_headers,
                data=request_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                response_time = time.time() - start_time
                
                # Update metrics
                self._update_metrics(response.status, response_time)
                
                # Parse response
                response_data = await self._parse_response(response)
                
                return ConnectorResponse(
                    success=200 <= response.status < 400,
                    data=response_data,
                    status_code=response.status,
                    headers=dict(response.headers),
                    metadata={
                        "response_time": response_time,
                        "endpoint": endpoint_name,
                        "connector_id": self.config.connector_id
                    }
                )
                
        except asyncio.TimeoutError:
            raise ConnectorError("Request timeout", "TIMEOUT")
        except aiohttp.ClientError as e:
            raise ConnectorError(f"Client error: {str(e)}", "CLIENT_ERROR")
        except Exception as e:
            raise ConnectorError(f"Unexpected error: {str(e)}", "UNEXPECTED_ERROR")
    
    def _build_url(self, path: str, params: Dict[str, Any] = None) -> str:
        """Build full URL from path and parameters"""
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        if params:
            url += f"?{urlencode(params)}"
        return url
    
    def _prepare_headers(self, additional_headers: Dict[str, str] = None) -> Dict[str, str]:
        """Prepare request headers"""
        headers = self.config.headers.copy()
        
        # Add authentication headers
        if self.config.authentication_type != AuthenticationType.NONE:
            auth_headers = self._get_auth_headers()
            headers.update(auth_headers)
        
        # Add additional headers
        if additional_headers:
            headers.update(additional_headers)
        
        return headers
    
    def _prepare_data(self, data: Any) -> Any:
        """Prepare request data based on format"""
        if data is None:
            return None
        
        if self.config.data_format == DataFormat.JSON:
            return json.dumps(data)
        elif self.config.data_format == DataFormat.FORM:
            return data
        else:
            return data
    
    async def _parse_response(self, response: aiohttp.ClientResponse) -> Any:
        """Parse response based on content type"""
        content_type = response.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type:
            return await response.json()
        elif 'application/xml' in content_type or 'text/xml' in content_type:
            return await response.text()
        else:
            return await response.text()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        auth_config = self.config.auth_config
        
        if self.config.authentication_type == AuthenticationType.API_KEY:
            api_key = auth_config.get('api_key')
            header_name = auth_config.get('header_name', 'X-API-Key')
            return {header_name: api_key}
        
        elif self.config.authentication_type == AuthenticationType.BEARER:
            token = auth_config.get('token')
            return {'Authorization': f'Bearer {token}'}
        
        elif self.config.authentication_type == AuthenticationType.BASIC:
            username = auth_config.get('username')
            password = auth_config.get('password')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {'Authorization': f'Basic {credentials}'}
        
        elif self.config.authentication_type == AuthenticationType.OAUTH2:
            token = auth_config.get('access_token')
            return {'Authorization': f'Bearer {token}'}
        
        return {}
    
    async def _check_rate_limit(self, endpoint: ConnectorEndpoint):
        """Check and enforce rate limits"""
        if not endpoint.rate_limit and not self.config.rate_limit:
            return
        
        rate_limit = endpoint.rate_limit or self.config.rate_limit
        window = self.config.rate_limit_window
        
        # Get current time
        now = time.time()
        
        # Clean old entries
        if endpoint.name in self.rate_limit_tracker:
            self.rate_limit_tracker[endpoint.name] = [
                t for t in self.rate_limit_tracker[endpoint.name]
                if now - t < window
            ]
        else:
            self.rate_limit_tracker[endpoint.name] = []
        
        # Check if rate limit exceeded
        if len(self.rate_limit_tracker[endpoint.name]) >= rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded for endpoint '{endpoint.name}'",
                "RATE_LIMIT_EXCEEDED"
            )
        
        # Add current request
        self.rate_limit_tracker[endpoint.name].append(now)
    
    def _update_metrics(self, status_code: int, response_time: float):
        """Update connector metrics"""
        self.metrics.total_requests += 1
        self.metrics.last_request_time = datetime.now().isoformat()
        
        if 200 <= status_code < 400:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
            self.metrics.error_count += 1
        
        # Update average response time
        total_time = self.metrics.average_response_time * (self.metrics.total_requests - 1)
        self.metrics.average_response_time = (total_time + response_time) / self.metrics.total_requests
    
    async def start(self):
        """Start the connector"""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Authenticate
            if not await self.authenticate():
                raise AuthenticationError("Authentication failed")
            
            # Test connection
            if not await self.test_connection():
                raise ConnectorError("Connection test failed")
            
            self.status = ConnectorStatus.ACTIVE
            logger.info(f"Connector '{self.config.name}' started successfully")
            
        except Exception as e:
            self.status = ConnectorStatus.ERROR
            logger.error(f"Failed to start connector '{self.config.name}': {e}")
            raise
    
    async def stop(self):
        """Stop the connector"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.status = ConnectorStatus.INACTIVE
        logger.info(f"Connector '{self.config.name}' stopped")
    
    def get_endpoints(self) -> Dict[str, ConnectorEndpoint]:
        """Get available endpoints"""
        return self.endpoints.copy()
    
    def get_metrics(self) -> ConnectorMetrics:
        """Get connector metrics"""
        return self.metrics
    
    def get_status(self) -> ConnectorStatus:
        """Get connector status"""
        return self.status

class ConnectorRegistry:
    """Registry for managing connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.connector_types: Dict[str, Type[BaseConnector]] = {}
        self.configs: Dict[str, ConnectorConfig] = {}
    
    def register_connector_type(self, name: str, connector_class: Type[BaseConnector]):
        """Register a connector type"""
        self.connector_types[name] = connector_class
        logger.info(f"Registered connector type: {name}")
    
    def create_connector(self, config: ConnectorConfig, connector_type: str) -> BaseConnector:
        """Create a new connector instance"""
        if connector_type not in self.connector_types:
            raise ConfigurationError(f"Unknown connector type: {connector_type}")
        
        connector_class = self.connector_types[connector_type]
        connector = connector_class(config)
        
        self.connectors[config.connector_id] = connector
        self.configs[config.connector_id] = config
        
        logger.info(f"Created connector: {config.name} ({config.connector_id})")
        return connector
    
    def get_connector(self, connector_id: str) -> Optional[BaseConnector]:
        """Get a connector by ID"""
        return self.connectors.get(connector_id)
    
    def list_connectors(self) -> List[Dict[str, Any]]:
        """List all connectors"""
        return [
            {
                "id": connector_id,
                "name": config.name,
                "status": connector.status.value,
                "type": type(connector).__name__,
                "metrics": asdict(connector.get_metrics())
            }
            for connector_id, connector in self.connectors.items()
            for config in [self.configs[connector_id]]
        ]
    
    async def start_connector(self, connector_id: str):
        """Start a connector"""
        connector = self.get_connector(connector_id)
        if not connector:
            raise ConfigurationError(f"Connector not found: {connector_id}")
        
        await connector.start()
    
    async def stop_connector(self, connector_id: str):
        """Stop a connector"""
        connector = self.get_connector(connector_id)
        if not connector:
            raise ConfigurationError(f"Connector not found: {connector_id}")
        
        await connector.stop()
    
    async def start_all_connectors(self):
        """Start all connectors"""
        for connector_id in self.connectors:
            try:
                await self.start_connector(connector_id)
            except Exception as e:
                logger.error(f"Failed to start connector {connector_id}: {e}")
    
    async def stop_all_connectors(self):
        """Stop all connectors"""
        for connector_id in self.connectors:
            try:
                await self.stop_connector(connector_id)
            except Exception as e:
                logger.error(f"Failed to stop connector {connector_id}: {e}")

class DataTransformer:
    """Data transformation utilities"""
    
    @staticmethod
    def transform_data(
        data: Any,
        mapping: Dict[str, str],
        source_format: str = "json",
        target_format: str = "json"
    ) -> Any:
        """Transform data using field mapping"""
        if not data or not mapping:
            return data
        
        if source_format == "json" and target_format == "json":
            return DataTransformer._transform_json_to_json(data, mapping)
        else:
            # Add more transformation logic as needed
            return data
    
    @staticmethod
    def _transform_json_to_json(data: Any, mapping: Dict[str, str]) -> Any:
        """Transform JSON data using field mapping"""
        if isinstance(data, dict):
            transformed = {}
            for source_field, target_field in mapping.items():
                if source_field in data:
                    transformed[target_field] = data[source_field]
            return transformed
        elif isinstance(data, list):
            return [DataTransformer._transform_json_to_json(item, mapping) for item in data]
        else:
            return data
    
    @staticmethod
    def validate_data(data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against a schema"""
        # Simplified validation - in production, use a proper schema validator
        if not schema:
            return True
        
        if isinstance(data, dict):
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    return False
        
        return True

class ConnectorManager:
    """High-level connector management"""
    
    def __init__(self, registry: ConnectorRegistry):
        self.registry = registry
        self.transformers: Dict[str, DataTransformer] = {}
    
    async def create_connector_from_config(
        self,
        config_path: str,
        connector_type: str
    ) -> BaseConnector:
        """Create connector from configuration file"""
        config_data = self._load_config(config_path)
        config = ConnectorConfig(**config_data)
        
        return self.registry.create_connector(config, connector_type)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        path = Path(config_path)
        
        if path.suffix == '.json':
            with open(path, 'r') as f:
                return json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        else:
            raise ConfigurationError(f"Unsupported config format: {path.suffix}")
    
    async def execute_connector_request(
        self,
        connector_id: str,
        endpoint_name: str,
        params: Dict[str, Any] = None,
        data: Any = None,
        transform_mapping: Dict[str, str] = None
    ) -> ConnectorResponse:
        """Execute a request through a connector with optional data transformation"""
        connector = self.registry.get_connector(connector_id)
        if not connector:
            raise ConfigurationError(f"Connector not found: {connector_id}")
        
        # Make request
        response = await connector.make_request(endpoint_name, params, data)
        
        # Transform data if mapping provided
        if transform_mapping and response.success and response.data:
            response.data = DataTransformer.transform_data(
                response.data,
                transform_mapping,
                "json",
                "json"
            )
        
        return response
    
    def get_connector_health(self, connector_id: str) -> Dict[str, Any]:
        """Get connector health information"""
        connector = self.registry.get_connector(connector_id)
        if not connector:
            return {"status": "not_found"}
        
        metrics = connector.get_metrics()
        return {
            "status": connector.get_status().value,
            "metrics": asdict(metrics),
            "endpoints": list(connector.get_endpoints().keys()),
            "last_check": datetime.now().isoformat()
        }
    
    def get_all_connector_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health information for all connectors"""
        return {
            connector_id: self.get_connector_health(connector_id)
            for connector_id in self.registry.connectors.keys()
        }

# Import required modules
try:
    import aiohttp
except ImportError:
    logger.warning("aiohttp not available. Install with: pip install aiohttp")
    raise

try:
    import yaml
except ImportError:
    logger.warning("PyYAML not available. Install with: pip install PyYAML")
    raise

async def main():
    """Main function to demonstrate connector framework"""
    # Create registry
    registry = ConnectorRegistry()
    manager = ConnectorManager(registry)
    
    # Example usage
    print("Connector Framework initialized")
    print(f"Available connector types: {list(registry.connector_types.keys())}")
    print(f"Active connectors: {len(registry.connectors)}")

if __name__ == "__main__":
    asyncio.run(main())