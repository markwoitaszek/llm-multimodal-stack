#!/usr/bin/env python3
"""
Connector Builder Tool
Part of Issue #10: API Connector Ecosystem

This module provides tools for building custom connectors including:
- Visual connector builder interface
- Code generation for custom connectors
- Configuration management
- Testing and validation tools
- Documentation generation
"""

import asyncio
import json
import yaml
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging
import uuid

from connector_framework import (
    ConnectorConfig, ConnectorEndpoint, AuthenticationType, DataFormat,
    BaseConnector, ConnectorRegistry, ConnectorManager
)
from prebuilt_connectors import create_connector

logger = logging.getLogger(__name__)

class ConnectorBuilder:
    """Tool for building custom connectors"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("./generated_connectors")
        self.output_dir.mkdir(exist_ok=True)
        self.templates_dir = Path(__file__).parent / "templates"
        self.registry = ConnectorRegistry()
        self.manager = ConnectorManager(self.registry)
    
    def create_connector_spec(
        self,
        name: str,
        description: str,
        base_url: str,
        authentication_type: str = "api_key",
        endpoints: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a connector specification"""
        connector_id = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        
        spec = {
            "connector_id": connector_id,
            "name": name,
            "description": description,
            "version": "1.0.0",
            "base_url": base_url,
            "authentication_type": authentication_type,
            "auth_config": {},
            "headers": {
                "Content-Type": "application/json",
                "User-Agent": f"{name} Connector/1.0.0"
            },
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1.0,
            "rate_limit": None,
            "rate_limit_window": 60,
            "data_format": "json",
            "endpoints": self._normalize_endpoints(endpoints or []),
            "custom_config": {}
        }
        
        return spec
    
    def _normalize_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize endpoints to ensure they have all required fields"""
        normalized = []
        for endpoint in endpoints:
            normalized_endpoint = {
                "name": endpoint.get("name", ""),
                "path": endpoint.get("path", ""),
                "method": endpoint.get("method", "GET").upper(),
                "description": endpoint.get("description", ""),
                "parameters": endpoint.get("parameters", {}),
                "request_schema": endpoint.get("request_schema", {}),
                "response_schema": endpoint.get("response_schema", {}),
                "authentication_required": endpoint.get("authentication_required", True),
                "rate_limit": endpoint.get("rate_limit")
            }
            normalized.append(normalized_endpoint)
        return normalized
    
    def add_endpoint(
        self,
        spec: Dict[str, Any],
        name: str,
        path: str,
        method: str = "GET",
        description: str = "",
        parameters: Dict[str, Any] = None,
        request_schema: Dict[str, Any] = None,
        response_schema: Dict[str, Any] = None,
        authentication_required: bool = True,
        rate_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add an endpoint to connector specification"""
        endpoint = {
            "name": name,
            "path": path,
            "method": method.upper(),
            "description": description,
            "parameters": parameters or {},
            "request_schema": request_schema or {},
            "response_schema": response_schema or {},
            "authentication_required": authentication_required,
            "rate_limit": rate_limit
        }
        
        spec["endpoints"].append(endpoint)
        return spec
    
    def generate_connector_code(self, spec: Dict[str, Any]) -> str:
        """Generate Python code for a custom connector"""
        connector_name = spec["name"].replace(" ", "")
        class_name = f"{connector_name}Connector"
        
        # Generate imports
        imports = [
            "import asyncio",
            "import json",
            "import time",
            "from typing import Dict, List, Optional, Any",
            "from datetime import datetime",
            "import logging",
            "",
            "from connector_framework import (",
            "    BaseConnector, ConnectorConfig, ConnectorEndpoint, ConnectorResponse,",
            "    AuthenticationType, DataFormat, ConnectorError, AuthenticationError",
            ")",
            "",
            "logger = logging.getLogger(__name__)",
            ""
        ]
        
        # Generate class definition
        class_code = [
            f"class {class_name}(BaseConnector):",
            '    """{}"""'.format(spec["description"]),
            "",
            "    def _initialize_endpoints(self):",
            '        """Initialize {} endpoints"""'.format(spec["name"]),
            "        self.endpoints = {"
        ]
        
        # Generate endpoints
        for endpoint in spec["endpoints"]:
            endpoint_code = [
                f'            "{endpoint["name"]}": ConnectorEndpoint(',
                f'                name="{endpoint["name"]}",',
                f'                path="{endpoint["path"]}",',
                f'                method="{endpoint["method"]}",',
                f'                description="{endpoint["description"]}",'
            ]
            
            if endpoint.get("parameters"):
                endpoint_code.append(f'                parameters={json.dumps(endpoint["parameters"])},')
            
            if endpoint.get("request_schema"):
                endpoint_code.append(f'                request_schema={json.dumps(endpoint["request_schema"])},')
            
            if endpoint.get("response_schema"):
                endpoint_code.append(f'                response_schema={json.dumps(endpoint["response_schema"])},')
            
            endpoint_code.append(f'                authentication_required={endpoint["authentication_required"]},')
            
            if endpoint.get("rate_limit"):
                endpoint_code.append(f'                rate_limit={endpoint["rate_limit"]}')
            
            endpoint_code.append("            ),")
            class_code.extend(endpoint_code)
        
        class_code.append("        }")
        class_code.append("")
        
        # Generate authentication method
        auth_method = self._generate_auth_method(spec)
        class_code.extend(auth_method)
        
        # Generate test connection method
        test_method = self._generate_test_method(spec)
        class_code.extend(test_method)
        
        # Combine all code
        full_code = "\n".join(imports + class_code)
        
        return full_code
    
    def _generate_auth_method(self, spec: Dict[str, Any]) -> List[str]:
        """Generate authentication method"""
        auth_type = spec["authentication_type"]
        
        if auth_type == "none":
            return [
                "    async def authenticate(self) -> bool:",
                '        """Authenticate with the service"""',
                "        return True",
                ""
            ]
        elif auth_type == "api_key":
            return [
                "    async def authenticate(self) -> bool:",
                '        """Authenticate with the service"""',
                "        if self.config.authentication_type != AuthenticationType.API_KEY:",
                '            raise AuthenticationError("Service requires API key authentication")',
                "",
                "        api_key = self.config.auth_config.get('api_key')",
                "        if not api_key:",
                '            raise AuthenticationError("API key not provided")',
                "",
                "        return True",
                ""
            ]
        elif auth_type == "bearer":
            return [
                "    async def authenticate(self) -> bool:",
                '        """Authenticate with the service"""',
                "        if self.config.authentication_type != AuthenticationType.BEARER:",
                '            raise AuthenticationError("Service requires Bearer token authentication")',
                "",
                "        token = self.config.auth_config.get('token')",
                "        if not token:",
                '            raise AuthenticationError("Bearer token not provided")',
                "",
                "        return True",
                ""
            ]
        elif auth_type == "basic":
            return [
                "    async def authenticate(self) -> bool:",
                '        """Authenticate with the service"""',
                "        if self.config.authentication_type != AuthenticationType.BASIC:",
                '            raise AuthenticationError("Service requires Basic authentication")',
                "",
                "        username = self.config.auth_config.get('username')",
                "        password = self.config.auth_config.get('password')",
                "        if not username or not password:",
                '            raise AuthenticationError("Username and password required")',
                "",
                "        return True",
                ""
            ]
        else:
            return [
                "    async def authenticate(self) -> bool:",
                '        """Authenticate with the service"""',
                "        # Implement custom authentication logic here",
                "        return True",
                ""
            ]
    
    def _generate_test_method(self, spec: Dict[str, Any]) -> List[str]:
        """Generate test connection method"""
        test_endpoint = None
        for endpoint in spec["endpoints"]:
            if endpoint["method"] == "GET" and not endpoint.get("parameters"):
                test_endpoint = endpoint["name"]
                break
        
        if test_endpoint:
            return [
                "    async def test_connection(self) -> bool:",
                '        """Test connection to the service"""',
                "        try:",
                f"            response = await self.make_request('{test_endpoint}')",
                "            return response.success and response.status_code == 200",
                "        except Exception as e:",
                f'            logger.error(f"{spec["name"]} connection test failed: {{e}}")',
                "            return False",
                ""
            ]
        else:
            return [
                "    async def test_connection(self) -> bool:",
                '        """Test connection to the service"""',
                "        # Implement connection test logic here",
                "        return True",
                ""
            ]
    
    def save_connector_spec(self, spec: Dict[str, Any], filename: str = None) -> Path:
        """Save connector specification to file"""
        if not filename:
            filename = f"{spec['connector_id']}.yaml"
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w') as f:
            yaml.dump(spec, f, default_flow_style=False, indent=2)
        
        logger.info(f"Connector specification saved to {file_path}")
        return file_path
    
    def save_connector_code(self, code: str, filename: str = None) -> Path:
        """Save generated connector code to file"""
        if not filename:
            # Extract class name from code
            lines = code.split('\n')
            for line in lines:
                if line.startswith('class ') and line.endswith('(BaseConnector):'):
                    class_name = line.split()[1].split('(')[0]
                    filename = f"{class_name.lower()}.py"
                    break
            else:
                filename = "custom_connector.py"
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w') as f:
            f.write(code)
        
        logger.info(f"Connector code saved to {file_path}")
        return file_path
    
    def generate_documentation(self, spec: Dict[str, Any]) -> str:
        """Generate documentation for a connector"""
        doc_lines = [
            f"# {spec['name']} Connector",
            "",
            spec["description"],
            "",
            "## Configuration",
            "",
            "### Basic Configuration",
            f"- **Base URL**: `{spec['base_url']}`",
            f"- **Authentication**: `{spec['authentication_type']}`",
            f"- **Timeout**: `{spec['timeout']}` seconds",
            f"- **Retry Attempts**: `{spec['retry_attempts']}`",
            "",
            "### Authentication Configuration",
        ]
        
        auth_type = spec["authentication_type"]
        if auth_type == "api_key":
            doc_lines.extend([
                "```yaml",
                "auth_config:",
                "  api_key: 'your-api-key'",
                "  header_name: 'X-API-Key'  # Optional",
                "```"
            ])
        elif auth_type == "bearer":
            doc_lines.extend([
                "```yaml",
                "auth_config:",
                "  token: 'your-bearer-token'",
                "```"
            ])
        elif auth_type == "basic":
            doc_lines.extend([
                "```yaml",
                "auth_config:",
                "  username: 'your-username'",
                "  password: 'your-password'",
                "```"
            ])
        
        doc_lines.extend([
            "",
            "## Endpoints",
            ""
        ])
        
        for endpoint in spec["endpoints"]:
            doc_lines.extend([
                f"### {endpoint['name']}",
                "",
                f"**Description**: {endpoint['description']}",
                f"**Method**: `{endpoint['method']}`",
                f"**Path**: `{endpoint['path']}`",
                f"**Authentication Required**: {endpoint['authentication_required']}",
                ""
            ])
            
            if endpoint.get("parameters"):
                doc_lines.extend([
                    "**Parameters**:",
                    "```yaml",
                    yaml.dump(endpoint["parameters"], default_flow_style=False, indent=2),
                    "```",
                    ""
                ])
            
            if endpoint.get("request_schema"):
                doc_lines.extend([
                    "**Request Schema**:",
                    "```json",
                    json.dumps(endpoint["request_schema"], indent=2),
                    "```",
                    ""
                ])
            
            if endpoint.get("response_schema"):
                doc_lines.extend([
                    "**Response Schema**:",
                    "```json",
                    json.dumps(endpoint["response_schema"], indent=2),
                    "```",
                    ""
                ])
        
        doc_lines.extend([
            "## Usage Example",
            "",
            "```python",
            "from connector_framework import ConnectorConfig, AuthenticationType",
            f"from {spec['connector_id']} import {spec['name'].replace(' ', '')}Connector",
            "",
            "# Create configuration",
            "config = ConnectorConfig(",
            f'    connector_id="{spec["connector_id"]}",',
            f'    name="{spec["name"]}",',
            f'    base_url="{spec["base_url"]}",',
            f'    authentication_type=AuthenticationType.{spec["authentication_type"].upper()},',
            "    auth_config={",
            "        'api_key': 'your-api-key'  # Adjust based on auth type",
            "    }",
            ")",
            "",
            "# Create and start connector",
            f"connector = {spec['name'].replace(' ', '')}Connector(config)",
            "await connector.start()",
            "",
            "# Make requests",
            "response = await connector.make_request('endpoint_name', params={'key': 'value'})",
            "print(response.data)",
            "```",
            "",
            f"Generated on: {datetime.now().isoformat()}"
        ])
        
        return "\n".join(doc_lines)
    
    def save_documentation(self, documentation: str, filename: str = None) -> Path:
        """Save documentation to file"""
        if not filename:
            filename = "README.md"
        
        file_path = self.output_dir / filename
        
        with open(file_path, 'w') as f:
            f.write(documentation)
        
        logger.info(f"Documentation saved to {file_path}")
        return file_path
    
    async def test_connector(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Test a connector specification"""
        results = {
            "spec_valid": True,
            "errors": [],
            "warnings": [],
            "endpoint_tests": {}
        }
        
        try:
            # Validate specification
            required_fields = ["name", "base_url", "authentication_type"]
            for field in required_fields:
                if field not in spec:
                    results["errors"].append(f"Missing required field: {field}")
                    results["spec_valid"] = False
            
            # Validate endpoints
            for endpoint in spec.get("endpoints", []):
                endpoint_name = endpoint.get("name", "unnamed")
                endpoint_errors = []
                
                if "path" not in endpoint:
                    endpoint_errors.append("Missing path")
                
                if "method" not in endpoint:
                    endpoint_errors.append("Missing method")
                
                if endpoint_errors:
                    results["endpoint_tests"][endpoint_name] = {
                        "valid": False,
                        "errors": endpoint_errors
                    }
                else:
                    results["endpoint_tests"][endpoint_name] = {
                        "valid": True,
                        "errors": []
                    }
            
            # Test connector creation (if possible)
            try:
                config = ConnectorConfig(
                    connector_id=spec["connector_id"],
                    name=spec["name"],
                    description=spec["description"],
                    version=spec["version"],
                    base_url=spec["base_url"],
                    authentication_type=AuthenticationType(spec["authentication_type"]),
                    auth_config=spec.get("auth_config", {}),
                    headers=spec.get("headers", {}),
                    timeout=spec.get("timeout", 30),
                    retry_attempts=spec.get("retry_attempts", 3),
                    data_format=DataFormat(spec.get("data_format", "json"))
                )
                
                # Try to create a custom connector
                connector = create_connector("custom_rest", config)
                results["connector_creation"] = "success"
                
            except Exception as e:
                results["connector_creation"] = f"failed: {str(e)}"
                results["warnings"].append(f"Could not create connector: {e}")
            
        except Exception as e:
            results["spec_valid"] = False
            results["errors"].append(f"Specification validation failed: {e}")
        
        return results
    
    def build_complete_connector(
        self,
        name: str,
        description: str,
        base_url: str,
        authentication_type: str = "api_key",
        endpoints: List[Dict[str, Any]] = None,
        test_connector: bool = True
    ) -> Dict[str, Any]:
        """Build a complete connector with all files"""
        # Create specification
        spec = self.create_connector_spec(name, description, base_url, authentication_type, endpoints)
        
        # Generate code
        code = self.generate_connector_code(spec)
        
        # Generate documentation
        documentation = self.generate_documentation(spec)
        
        # Save files
        spec_file = self.save_connector_spec(spec)
        code_file = self.save_connector_code(code)
        doc_file = self.save_documentation(documentation)
        
        result = {
            "spec": spec,
            "spec_file": spec_file,
            "code_file": code_file,
            "doc_file": doc_file,
            "code": code,
            "documentation": documentation
        }
        
        # Test connector if requested
        if test_connector:
            test_results = asyncio.run(self.test_connector(spec))
            result["test_results"] = test_results
        
        return result

# Example usage and templates
EXAMPLE_ENDPOINTS = {
    "weather_api": [
        {
            "name": "get_current_weather",
            "path": "/current",
            "method": "GET",
            "description": "Get current weather for a location",
            "parameters": {
                "q": "London",
                "key": "your-api-key"
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "temperature": {"type": "number"},
                    "condition": {"type": "string"}
                }
            }
        },
        {
            "name": "get_forecast",
            "path": "/forecast",
            "method": "GET",
            "description": "Get weather forecast for a location",
            "parameters": {
                "q": "London",
                "days": "5"
            }
        }
    ],
    "news_api": [
        {
            "name": "get_top_headlines",
            "path": "/top-headlines",
            "method": "GET",
            "description": "Get top news headlines",
            "parameters": {
                "country": "us",
                "category": "technology"
            }
        },
        {
            "name": "search_articles",
            "path": "/everything",
            "method": "GET",
            "description": "Search for news articles",
            "parameters": {
                "q": "artificial intelligence",
                "sortBy": "publishedAt"
            }
        }
    ]
}

async def main():
    """Main function to demonstrate connector builder"""
    builder = ConnectorBuilder()
    
    # Example: Build a weather API connector
    print("Building Weather API Connector...")
    
    weather_connector = builder.build_complete_connector(
        name="Weather API",
        description="Connector for weather data API",
        base_url="https://api.weatherapi.com/v1",
        authentication_type="api_key",
        endpoints=EXAMPLE_ENDPOINTS["weather_api"]
    )
    
    print(f"Connector built successfully!")
    print(f"Spec file: {weather_connector['spec_file']}")
    print(f"Code file: {weather_connector['code_file']}")
    print(f"Documentation: {weather_connector['doc_file']}")
    
    if "test_results" in weather_connector:
        test_results = weather_connector["test_results"]
        print(f"\nTest Results:")
        print(f"Spec valid: {test_results['spec_valid']}")
        if test_results["errors"]:
            print(f"Errors: {test_results['errors']}")
        if test_results["warnings"]:
            print(f"Warnings: {test_results['warnings']}")

if __name__ == "__main__":
    asyncio.run(main())