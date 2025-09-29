#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 3 API Connector Ecosystem
Part of Issue #10: API Connector Ecosystem

This test suite validates:
- Connector framework functionality
- Pre-built connectors
- Connector builder tools
- Connector management server
- Integration and performance
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import uuid

# Import the modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "connectors"))

from connector_framework import (
    ConnectorConfig, ConnectorEndpoint, ConnectorResponse, ConnectorStatus,
    AuthenticationType, DataFormat, ConnectorError, AuthenticationError,
    BaseConnector, ConnectorRegistry, ConnectorManager, DataTransformer
)
from prebuilt_connectors import (
    OpenAIConnector, SlackConnector, GitHubConnector, CustomRESTConnector,
    create_connector
)
from connector_builder import ConnectorBuilder
from connector_server import ConnectorServer

class TestConnectorConfig:
    """Test connector configuration functionality"""
    
    def test_connector_config_creation(self):
        """Test creating connector configuration"""
        config = ConnectorConfig(
            connector_id="test_connector",
            name="Test Connector",
            description="A test connector",
            version="1.0.0",
            base_url="https://api.example.com",
            authentication_type=AuthenticationType.API_KEY,
            auth_config={"api_key": "test-key"},
            headers={"Content-Type": "application/json"},
            timeout=30,
            retry_attempts=3,
            data_format=DataFormat.JSON
        )
        
        assert config.connector_id == "test_connector"
        assert config.name == "Test Connector"
        assert config.base_url == "https://api.example.com"
        assert config.authentication_type == AuthenticationType.API_KEY
        assert config.auth_config["api_key"] == "test-key"
        assert config.timeout == 30
    
    def test_connector_endpoint_creation(self):
        """Test creating connector endpoint"""
        endpoint = ConnectorEndpoint(
            name="test_endpoint",
            path="/test",
            method="GET",
            description="Test endpoint",
            parameters={"param1": "value1"},
            request_schema={"type": "object"},
            response_schema={"type": "object"},
            authentication_required=True,
            rate_limit=100
        )
        
        assert endpoint.name == "test_endpoint"
        assert endpoint.path == "/test"
        assert endpoint.method == "GET"
        assert endpoint.parameters["param1"] == "value1"
        assert endpoint.rate_limit == 100

class TestDataTransformer:
    """Test data transformation functionality"""
    
    def test_json_to_json_transformation(self):
        """Test JSON to JSON data transformation"""
        data = {
            "user_id": 123,
            "user_name": "John Doe",
            "user_email": "john@example.com"
        }
        
        mapping = {
            "user_id": "id",
            "user_name": "name",
            "user_email": "email"
        }
        
        transformed = DataTransformer.transform_data(data, mapping, "json", "json")
        
        expected = {
            "id": 123,
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        assert transformed == expected
    
    def test_list_transformation(self):
        """Test transformation of list data"""
        data = [
            {"user_id": 1, "user_name": "Alice"},
            {"user_id": 2, "user_name": "Bob"}
        ]
        
        mapping = {
            "user_id": "id",
            "user_name": "name"
        }
        
        transformed = DataTransformer.transform_data(data, mapping, "json", "json")
        
        expected = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        assert transformed == expected
    
    def test_data_validation(self):
        """Test data validation against schema"""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }
        
        schema = {
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        
        is_valid = DataTransformer.validate_data(data, schema)
        assert is_valid
        
        # Test invalid data
        invalid_data = {
            "name": "John Doe"
            # Missing required email field
        }
        
        is_valid = DataTransformer.validate_data(invalid_data, schema)
        assert not is_valid

class TestConnectorRegistry:
    """Test connector registry functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.registry = ConnectorRegistry()
    
    def test_register_connector_type(self):
        """Test registering connector types"""
        class TestConnector(BaseConnector):
            def _initialize_endpoints(self):
                self.endpoints = {}
            
            async def authenticate(self) -> bool:
                return True
            
            async def test_connection(self) -> bool:
                return True
        
        self.registry.register_connector_type("test", TestConnector)
        
        assert "test" in self.registry.connector_types
        assert self.registry.connector_types["test"] == TestConnector
    
    def test_create_connector(self):
        """Test creating connector instances"""
        class TestConnector(BaseConnector):
            def _initialize_endpoints(self):
                self.endpoints = {
                    "test": ConnectorEndpoint(
                        name="test",
                        path="/test",
                        method="GET",
                        description="Test endpoint"
                    )
                }
            
            async def authenticate(self) -> bool:
                return True
            
            async def test_connection(self) -> bool:
                return True
        
        self.registry.register_connector_type("test", TestConnector)
        
        config = ConnectorConfig(
            connector_id="test_connector",
            name="Test Connector",
            description="Test",
            version="1.0.0",
            base_url="https://api.example.com",
            authentication_type=AuthenticationType.NONE
        )
        
        connector = self.registry.create_connector(config, "test")
        
        assert connector is not None
        assert connector.config.connector_id == "test_connector"
        assert "test_connector" in self.registry.connectors
        assert "test_connector" in self.registry.configs
    
    def test_list_connectors(self):
        """Test listing connectors"""
        class TestConnector(BaseConnector):
            def _initialize_endpoints(self):
                self.endpoints = {}
            
            async def authenticate(self) -> bool:
                return True
            
            async def test_connection(self) -> bool:
                return True
        
        self.registry.register_connector_type("test", TestConnector)
        
        config = ConnectorConfig(
            connector_id="test_connector",
            name="Test Connector",
            description="Test",
            version="1.0.0",
            base_url="https://api.example.com",
            authentication_type=AuthenticationType.NONE
        )
        
        self.registry.create_connector(config, "test")
        
        connectors = self.registry.list_connectors()
        
        assert len(connectors) == 1
        assert connectors[0]["id"] == "test_connector"
        assert connectors[0]["name"] == "Test Connector"

class TestPrebuiltConnectors:
    """Test pre-built connectors"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_openai_connector_initialization(self):
        """Test OpenAI connector initialization"""
        config = ConnectorConfig(
            connector_id="openai_test",
            name="OpenAI Test",
            description="Test OpenAI connector",
            version="1.0.0",
            base_url="https://api.openai.com",
            authentication_type=AuthenticationType.BEARER,
            auth_config={"token": "test-token"}
        )
        
        connector = OpenAIConnector(config)
        
        assert connector.config.name == "OpenAI Test"
        assert "chat_completions" in connector.endpoints
        assert "completions" in connector.endpoints
        assert "embeddings" in connector.endpoints
        assert "models" in connector.endpoints
    
    def test_slack_connector_initialization(self):
        """Test Slack connector initialization"""
        config = ConnectorConfig(
            connector_id="slack_test",
            name="Slack Test",
            description="Test Slack connector",
            version="1.0.0",
            base_url="https://slack.com/api",
            authentication_type=AuthenticationType.BEARER,
            auth_config={"token": "test-token"}
        )
        
        connector = SlackConnector(config)
        
        assert connector.config.name == "Slack Test"
        assert "post_message" in connector.endpoints
        assert "get_channels" in connector.endpoints
        assert "get_users" in connector.endpoints
        assert "upload_file" in connector.endpoints
    
    def test_github_connector_initialization(self):
        """Test GitHub connector initialization"""
        config = ConnectorConfig(
            connector_id="github_test",
            name="GitHub Test",
            description="Test GitHub connector",
            version="1.0.0",
            base_url="https://api.github.com",
            authentication_type=AuthenticationType.BEARER,
            auth_config={"token": "test-token"}
        )
        
        connector = GitHubConnector(config)
        
        assert connector.config.name == "GitHub Test"
        assert "get_repos" in connector.endpoints
        assert "get_repo" in connector.endpoints
        assert "create_issue" in connector.endpoints
        assert "get_commits" in connector.endpoints
        assert "search_repos" in connector.endpoints
    
    def test_custom_rest_connector_initialization(self):
        """Test custom REST connector initialization"""
        config = ConnectorConfig(
            connector_id="custom_test",
            name="Custom Test",
            description="Test custom REST connector",
            version="1.0.0",
            base_url="https://api.example.com",
            authentication_type=AuthenticationType.API_KEY,
            auth_config={"api_key": "test-key"},
            custom_config={
                "endpoints": [
                    {
                        "name": "test_endpoint",
                        "path": "/test",
                        "method": "GET",
                        "description": "Test endpoint"
                    }
                ]
            }
        )
        
        connector = CustomRESTConnector(config)
        
        assert connector.config.name == "Custom Test"
        assert "test_endpoint" in connector.endpoints
    
    def test_connector_factory(self):
        """Test connector factory function"""
        config = ConnectorConfig(
            connector_id="factory_test",
            name="Factory Test",
            description="Test factory",
            version="1.0.0",
            base_url="https://api.example.com",
            authentication_type=AuthenticationType.NONE
        )
        
        # Test creating different connector types
        openai_connector = create_connector("openai", config)
        assert isinstance(openai_connector, OpenAIConnector)
        
        slack_connector = create_connector("slack", config)
        assert isinstance(slack_connector, SlackConnector)
        
        github_connector = create_connector("github", config)
        assert isinstance(github_connector, GitHubConnector)
        
        custom_connector = create_connector("custom_rest", config)
        assert isinstance(custom_connector, CustomRESTConnector)
        
        # Test unknown connector type
        with pytest.raises(ValueError):
            create_connector("unknown", config)

class TestConnectorBuilder:
    """Test connector builder functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.builder = ConnectorBuilder(output_dir=Path(self.temp_dir))
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_connector_spec(self):
        """Test creating connector specification"""
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key"
        )
        
        assert spec["name"] == "Test API"
        assert spec["description"] == "A test API connector"
        assert spec["base_url"] == "https://api.test.com"
        assert spec["authentication_type"] == "api_key"
        assert "connector_id" in spec
        assert "endpoints" in spec
    
    def test_add_endpoint(self):
        """Test adding endpoints to connector specification"""
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com"
        )
        
        spec = self.builder.add_endpoint(
            spec,
            name="get_data",
            path="/data",
            method="GET",
            description="Get data from API",
            parameters={"limit": 10}
        )
        
        assert len(spec["endpoints"]) == 1
        endpoint = spec["endpoints"][0]
        assert endpoint["name"] == "get_data"
        assert endpoint["path"] == "/data"
        assert endpoint["method"] == "GET"
        assert endpoint["parameters"]["limit"] == 10
    
    def test_generate_connector_code(self):
        """Test generating connector code"""
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key"
        )
        
        spec = self.builder.add_endpoint(
            spec,
            name="get_data",
            path="/data",
            method="GET",
            description="Get data from API"
        )
        
        code = self.builder.generate_connector_code(spec)
        
        assert "class TestAPIConnector(BaseConnector):" in code
        assert "def _initialize_endpoints(self):" in code
        assert "async def authenticate(self) -> bool:" in code
        assert "async def test_connection(self) -> bool:" in code
        assert '"get_data"' in code
        assert '"/data"' in code
    
    def test_generate_documentation(self):
        """Test generating documentation"""
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key"
        )
        
        spec = self.builder.add_endpoint(
            spec,
            name="get_data",
            path="/data",
            method="GET",
            description="Get data from API"
        )
        
        documentation = self.builder.generate_documentation(spec)
        
        assert "# Test API Connector" in documentation
        assert "A test API connector" in documentation
        assert "## Configuration" in documentation
        assert "## Endpoints" in documentation
        assert "### get_data" in documentation
        assert "## Usage Example" in documentation
    
    def test_save_files(self):
        """Test saving connector files"""
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com"
        )
        
        code = self.builder.generate_connector_code(spec)
        documentation = self.builder.generate_documentation(spec)
        
        # Save files
        spec_file = self.builder.save_connector_spec(spec)
        code_file = self.builder.save_connector_code(code)
        doc_file = self.builder.save_documentation(documentation)
        
        # Check files exist
        assert spec_file.exists()
        assert code_file.exists()
        assert doc_file.exists()
        
        # Check file contents
        with open(spec_file, 'r') as f:
            saved_spec = f.read()
            assert "Test API" in saved_spec
        
        with open(code_file, 'r') as f:
            saved_code = f.read()
            assert "TestAPIConnector" in saved_code
        
        with open(doc_file, 'r') as f:
            saved_doc = f.read()
            assert "# Test API Connector" in saved_doc
    
    async def test_test_connector(self):
        """Test connector testing functionality"""
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key"
        )
        
        spec = self.builder.add_endpoint(
            spec,
            name="get_data",
            path="/data",
            method="GET",
            description="Get data from API"
        )
        
        test_results = await self.builder.test_connector(spec)
        
        assert "spec_valid" in test_results
        assert "errors" in test_results
        assert "warnings" in test_results
        assert "endpoint_tests" in test_results
    
    def test_build_complete_connector(self):
        """Test building complete connector"""
        endpoints = [
            {
                "name": "get_data",
                "path": "/data",
                "method": "GET",
                "description": "Get data from API"
            }
        ]
        
        result = self.builder.build_complete_connector(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key",
            endpoints=endpoints,
            test_connector=False  # Skip testing for speed
        )
        
        assert "spec" in result
        assert "spec_file" in result
        assert "code_file" in result
        assert "doc_file" in result
        assert "code" in result
        assert "documentation" in result
        
        # Check files exist
        assert result["spec_file"].exists()
        assert result["code_file"].exists()
        assert result["doc_file"].exists()

class TestConnectorManager:
    """Test connector manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.registry = ConnectorRegistry()
        self.manager = ConnectorManager(self.registry)
    
    def test_connector_manager_initialization(self):
        """Test connector manager initialization"""
        assert self.manager.registry is not None
        assert isinstance(self.manager.registry, ConnectorRegistry)
    
    def test_get_connector_health(self):
        """Test getting connector health"""
        # Test with non-existent connector
        health = self.manager.get_connector_health("non_existent")
        assert health["status"] == "not_found"
    
    def test_get_all_connector_health(self):
        """Test getting all connector health"""
        health_data = self.manager.get_all_connector_health()
        assert isinstance(health_data, dict)
        assert len(health_data) == 0  # No connectors registered

class TestConnectorServer:
    """Test connector server functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.server = ConnectorServer(port=8083)  # Use different port for testing
    
    def test_server_initialization(self):
        """Test server initialization"""
        assert self.server.port == 8083
        assert self.server.registry is not None
        assert self.server.manager is not None
        assert self.server.builder is not None
        assert len(self.server.active_connections) == 0
    
    def test_register_connector_types(self):
        """Test connector type registration"""
        assert "openai" in self.server.registry.connector_types
        assert "slack" in self.server.registry.connector_types
        assert "github" in self.server.registry.connector_types
        assert "custom_rest" in self.server.registry.connector_types
    
    def test_api_models(self):
        """Test API model validation"""
        from connector_server import (
            ConnectorCreateRequest, ConnectorUpdateRequest, ConnectorRequest
        )
        
        # Test ConnectorCreateRequest
        create_req = ConnectorCreateRequest(
            name="Test Connector",
            description="Test description",
            connector_type="openai",
            base_url="https://api.example.com",
            authentication_type="bearer",
            auth_config={"token": "test-token"}
        )
        
        assert create_req.name == "Test Connector"
        assert create_req.connector_type == "openai"
        assert create_req.auth_config["token"] == "test-token"
        
        # Test ConnectorUpdateRequest
        update_req = ConnectorUpdateRequest(
            name="Updated Name",
            timeout=60
        )
        
        assert update_req.name == "Updated Name"
        assert update_req.timeout == 60
        assert update_req.description is None
        
        # Test ConnectorRequest
        request = ConnectorRequest(
            endpoint_name="test_endpoint",
            params={"key": "value"},
            data={"test": "data"}
        )
        
        assert request.endpoint_name == "test_endpoint"
        assert request.params["key"] == "value"
        assert request.data["test"] == "data"

class TestConnectorIntegration:
    """Test integration between connector components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = ConnectorRegistry()
        self.manager = ConnectorManager(self.registry)
        self.builder = ConnectorBuilder(output_dir=Path(self.temp_dir))
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_full_connector_workflow(self):
        """Test complete connector workflow"""
        # Register connector type
        self.registry.register_connector_type("custom_rest", CustomRESTConnector)
        
        # Create connector specification
        spec = self.builder.create_connector_spec(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key"
        )
        
        spec = self.builder.add_endpoint(
            spec,
            name="get_data",
            path="/data",
            method="GET",
            description="Get data from API"
        )
        
        # Generate and save connector
        result = self.builder.build_complete_connector(
            name="Test API",
            description="A test API connector",
            base_url="https://api.test.com",
            authentication_type="api_key",
            endpoints=spec["endpoints"],
            test_connector=False
        )
        
        # Create connector from specification
        config = ConnectorConfig(
            connector_id=spec["connector_id"],
            name=spec["name"],
            description=spec["description"],
            version=spec["version"],
            base_url=spec["base_url"],
            authentication_type=AuthenticationType(spec["authentication_type"]),
            auth_config=spec["auth_config"],
            headers=spec["headers"],
            timeout=spec["timeout"],
            retry_attempts=spec["retry_attempts"],
            data_format=DataFormat(spec["data_format"]),
            custom_config=spec["custom_config"]
        )
        
        connector = self.registry.create_connector(config, "custom_rest")
        
        # Verify connector
        assert connector is not None
        assert connector.config.name == "Test API"
        assert "get_data" in connector.get_endpoints()
        
        # Test manager functionality
        health = self.manager.get_connector_health(spec["connector_id"])
        assert health["status"] != "not_found"
    
    def test_data_transformation_workflow(self):
        """Test data transformation workflow"""
        # Test data
        source_data = {
            "user_id": 123,
            "user_name": "John Doe",
            "user_email": "john@example.com",
            "user_age": 30
        }
        
        # Transformation mapping
        mapping = {
            "user_id": "id",
            "user_name": "name",
            "user_email": "email"
        }
        
        # Transform data
        transformed_data = DataTransformer.transform_data(
            source_data, mapping, "json", "json"
        )
        
        # Verify transformation
        expected_data = {
            "id": 123,
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        assert transformed_data == expected_data
        
        # Validate transformed data
        schema = {
            "type": "object",
            "required": ["id", "name", "email"],
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "email": {"type": "string"}
            }
        }
        
        is_valid = DataTransformer.validate_data(transformed_data, schema)
        assert is_valid

# Performance Tests
class TestConnectorPerformance:
    """Test performance of connector system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = ConnectorRegistry()
        self.manager = ConnectorManager(self.registry)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_connector_creation_performance(self):
        """Test connector creation performance"""
        import time
        
        # Register connector type
        self.registry.register_connector_type("custom_rest", CustomRESTConnector)
        
        # Create many connectors
        num_connectors = 100
        start_time = time.time()
        
        for i in range(num_connectors):
            config = ConnectorConfig(
                connector_id=f"connector_{i}",
                name=f"Connector {i}",
                description=f"Test connector {i}",
                version="1.0.0",
                base_url="https://api.example.com",
                authentication_type=AuthenticationType.NONE,
                custom_config={
                    "endpoints": [
                        {
                            "name": "test",
                            "path": "/test",
                            "method": "GET",
                            "description": "Test endpoint"
                        }
                    ]
                }
            )
            
            self.registry.create_connector(config, "custom_rest")
        
        creation_time = time.time() - start_time
        
        # Should create connectors quickly
        assert creation_time < 5.0  # Less than 5 seconds for 100 connectors
        assert len(self.registry.connectors) == num_connectors
    
    def test_data_transformation_performance(self):
        """Test data transformation performance"""
        import time
        
        # Test data
        data = {
            "user_id": 123,
            "user_name": "John Doe",
            "user_email": "john@example.com"
        }
        
        mapping = {
            "user_id": "id",
            "user_name": "name",
            "user_email": "email"
        }
        
        # Test transformation performance
        num_transformations = 1000
        start_time = time.time()
        
        for _ in range(num_transformations):
            DataTransformer.transform_data(data, mapping, "json", "json")
        
        transformation_time = time.time() - start_time
        
        # Should transform data quickly
        assert transformation_time < 1.0  # Less than 1 second for 1000 transformations
    
    def test_connector_builder_performance(self):
        """Test connector builder performance"""
        import time
        
        builder = ConnectorBuilder(output_dir=Path(self.temp_dir))
        
        # Test building multiple connectors
        num_connectors = 10
        start_time = time.time()
        
        for i in range(num_connectors):
            spec = builder.create_connector_spec(
                name=f"Test API {i}",
                description=f"Test API connector {i}",
                base_url="https://api.test.com"
            )
            
            spec = builder.add_endpoint(
                spec,
                name="get_data",
                path="/data",
                method="GET",
                description="Get data from API"
            )
            
            code = builder.generate_connector_code(spec)
            documentation = builder.generate_documentation(spec)
        
        building_time = time.time() - start_time
        
        # Should build connectors quickly
        assert building_time < 10.0  # Less than 10 seconds for 10 connectors

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])