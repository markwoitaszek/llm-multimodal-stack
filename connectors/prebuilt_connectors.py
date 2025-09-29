#!/usr/bin/env python3
"""
Pre-built Connectors for Popular Services
Part of Issue #10: API Connector Ecosystem

This module provides pre-built connectors for popular services including:
- OpenAI API connector
- Google Cloud services connector
- AWS services connector
- Slack connector
- GitHub connector
- Salesforce connector
- Custom REST API connector
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from connector_framework import (
    BaseConnector, ConnectorConfig, ConnectorEndpoint, ConnectorResponse,
    AuthenticationType, DataFormat, ConnectorError, AuthenticationError
)

logger = logging.getLogger(__name__)

class OpenAIConnector(BaseConnector):
    """OpenAI API connector"""
    
    def _initialize_endpoints(self):
        """Initialize OpenAI API endpoints"""
        self.endpoints = {
            "chat_completions": ConnectorEndpoint(
                name="chat_completions",
                path="/v1/chat/completions",
                method="POST",
                description="Create chat completions",
                request_schema={
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "messages": {"type": "array"},
                        "temperature": {"type": "number"},
                        "max_tokens": {"type": "integer"}
                    },
                    "required": ["model", "messages"]
                },
                response_schema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "object": {"type": "string"},
                        "created": {"type": "integer"},
                        "choices": {"type": "array"}
                    }
                }
            ),
            "completions": ConnectorEndpoint(
                name="completions",
                path="/v1/completions",
                method="POST",
                description="Create text completions",
                request_schema={
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "prompt": {"type": "string"},
                        "temperature": {"type": "number"},
                        "max_tokens": {"type": "integer"}
                    },
                    "required": ["model", "prompt"]
                }
            ),
            "embeddings": ConnectorEndpoint(
                name="embeddings",
                path="/v1/embeddings",
                method="POST",
                description="Create embeddings",
                request_schema={
                    "type": "object",
                    "properties": {
                        "model": {"type": "string"},
                        "input": {"type": "string"}
                    },
                    "required": ["model", "input"]
                }
            ),
            "models": ConnectorEndpoint(
                name="models",
                path="/v1/models",
                method="GET",
                description="List available models",
                authentication_required=True
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with OpenAI API"""
        if self.config.authentication_type != AuthenticationType.BEARER:
            raise AuthenticationError("OpenAI requires Bearer token authentication")
        
        token = self.config.auth_config.get('token')
        if not token:
            raise AuthenticationError("OpenAI API token not provided")
        
        # Test authentication by making a simple request
        try:
            response = await self.make_request("models")
            return response.success
        except Exception as e:
            logger.error(f"OpenAI authentication failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to OpenAI API"""
        try:
            response = await self.make_request("models")
            return response.success and response.status_code == 200
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

class GoogleCloudConnector(BaseConnector):
    """Google Cloud services connector"""
    
    def _initialize_endpoints(self):
        """Initialize Google Cloud endpoints"""
        self.endpoints = {
            "translate": ConnectorEndpoint(
                name="translate",
                path="/v2/translate",
                method="POST",
                description="Translate text using Google Translate API",
                request_schema={
                    "type": "object",
                    "properties": {
                        "q": {"type": "string"},
                        "target": {"type": "string"},
                        "source": {"type": "string"}
                    },
                    "required": ["q", "target"]
                }
            ),
            "vision": ConnectorEndpoint(
                name="vision",
                path="/v1/images:annotate",
                method="POST",
                description="Analyze images using Google Vision API",
                request_schema={
                    "type": "object",
                    "properties": {
                        "requests": {"type": "array"}
                    },
                    "required": ["requests"]
                }
            ),
            "speech": ConnectorEndpoint(
                name="speech",
                path="/v1/speech:recognize",
                method="POST",
                description="Speech recognition using Google Speech API",
                request_schema={
                    "type": "object",
                    "properties": {
                        "config": {"type": "object"},
                        "audio": {"type": "object"}
                    },
                    "required": ["config", "audio"]
                }
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Google Cloud"""
        # Google Cloud supports multiple authentication methods
        if self.config.authentication_type == AuthenticationType.API_KEY:
            api_key = self.config.auth_config.get('api_key')
            if not api_key:
                raise AuthenticationError("Google Cloud API key not provided")
        elif self.config.authentication_type == AuthenticationType.OAUTH2:
            # OAuth2 authentication would be implemented here
            pass
        else:
            raise AuthenticationError("Google Cloud requires API key or OAuth2 authentication")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Google Cloud"""
        try:
            # Test with a simple translate request
            response = await self.make_request("translate", data={
                "q": "Hello",
                "target": "es"
            })
            return response.success
        except Exception as e:
            logger.error(f"Google Cloud connection test failed: {e}")
            return False

class SlackConnector(BaseConnector):
    """Slack API connector"""
    
    def _initialize_endpoints(self):
        """Initialize Slack API endpoints"""
        self.endpoints = {
            "post_message": ConnectorEndpoint(
                name="post_message",
                path="/api/chat.postMessage",
                method="POST",
                description="Post a message to a Slack channel",
                request_schema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "text": {"type": "string"},
                        "blocks": {"type": "array"}
                    },
                    "required": ["channel", "text"]
                }
            ),
            "get_channels": ConnectorEndpoint(
                name="get_channels",
                path="/api/conversations.list",
                method="GET",
                description="Get list of channels",
                parameters={"types": "public_channel,private_channel"}
            ),
            "get_users": ConnectorEndpoint(
                name="get_users",
                path="/api/users.list",
                method="GET",
                description="Get list of users"
            ),
            "upload_file": ConnectorEndpoint(
                name="upload_file",
                path="/api/files.upload",
                method="POST",
                description="Upload a file to Slack",
                request_schema={
                    "type": "object",
                    "properties": {
                        "channels": {"type": "string"},
                        "file": {"type": "string"},
                        "filename": {"type": "string"}
                    },
                    "required": ["channels", "file"]
                }
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Slack"""
        if self.config.authentication_type != AuthenticationType.BEARER:
            raise AuthenticationError("Slack requires Bearer token authentication")
        
        token = self.config.auth_config.get('token')
        if not token:
            raise AuthenticationError("Slack API token not provided")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Slack"""
        try:
            response = await self.make_request("get_users")
            return response.success and response.data.get("ok", False)
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False

class GitHubConnector(BaseConnector):
    """GitHub API connector"""
    
    def _initialize_endpoints(self):
        """Initialize GitHub API endpoints"""
        self.endpoints = {
            "get_repos": ConnectorEndpoint(
                name="get_repos",
                path="/user/repos",
                method="GET",
                description="Get user repositories",
                parameters={"per_page": "100", "sort": "updated"}
            ),
            "get_repo": ConnectorEndpoint(
                name="get_repo",
                path="/repos/{owner}/{repo}",
                method="GET",
                description="Get repository information"
            ),
            "create_issue": ConnectorEndpoint(
                name="create_issue",
                path="/repos/{owner}/{repo}/issues",
                method="POST",
                description="Create an issue",
                request_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "labels": {"type": "array"}
                    },
                    "required": ["title"]
                }
            ),
            "get_commits": ConnectorEndpoint(
                name="get_commits",
                path="/repos/{owner}/{repo}/commits",
                method="GET",
                description="Get repository commits",
                parameters={"per_page": "100"}
            ),
            "search_repos": ConnectorEndpoint(
                name="search_repos",
                path="/search/repositories",
                method="GET",
                description="Search repositories",
                parameters={"q": "language:python"}
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with GitHub"""
        if self.config.authentication_type not in [AuthenticationType.BEARER, AuthenticationType.API_KEY]:
            raise AuthenticationError("GitHub requires Bearer token or API key authentication")
        
        token = self.config.auth_config.get('token') or self.config.auth_config.get('api_key')
        if not token:
            raise AuthenticationError("GitHub API token not provided")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to GitHub"""
        try:
            response = await self.make_request("get_repos")
            return response.success and response.status_code == 200
        except Exception as e:
            logger.error(f"GitHub connection test failed: {e}")
            return False

class SalesforceConnector(BaseConnector):
    """Salesforce API connector"""
    
    def _initialize_endpoints(self):
        """Initialize Salesforce API endpoints"""
        self.endpoints = {
            "query": ConnectorEndpoint(
                name="query",
                path="/services/data/v58.0/query",
                method="GET",
                description="Execute SOQL query",
                parameters={"q": "SELECT Id, Name FROM Account LIMIT 10"}
            ),
            "create_record": ConnectorEndpoint(
                name="create_record",
                path="/services/data/v58.0/sobjects/{sobject}",
                method="POST",
                description="Create a record",
                request_schema={
                    "type": "object",
                    "properties": {
                        "Name": {"type": "string"}
                    }
                }
            ),
            "update_record": ConnectorEndpoint(
                name="update_record",
                path="/services/data/v58.0/sobjects/{sobject}/{id}",
                method="PATCH",
                description="Update a record"
            ),
            "get_record": ConnectorEndpoint(
                name="get_record",
                path="/services/data/v58.0/sobjects/{sobject}/{id}",
                method="GET",
                description="Get a record"
            ),
            "describe_sobject": ConnectorEndpoint(
                name="describe_sobject",
                path="/services/data/v58.0/sobjects/{sobject}/describe",
                method="GET",
                description="Describe an sObject"
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Salesforce"""
        if self.config.authentication_type != AuthenticationType.OAUTH2:
            raise AuthenticationError("Salesforce requires OAuth2 authentication")
        
        # OAuth2 authentication implementation would go here
        access_token = self.config.auth_config.get('access_token')
        if not access_token:
            raise AuthenticationError("Salesforce access token not provided")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to Salesforce"""
        try:
            response = await self.make_request("query")
            return response.success and response.status_code == 200
        except Exception as e:
            logger.error(f"Salesforce connection test failed: {e}")
            return False

class AWSConnector(BaseConnector):
    """AWS services connector"""
    
    def _initialize_endpoints(self):
        """Initialize AWS service endpoints"""
        self.endpoints = {
            "s3_list_buckets": ConnectorEndpoint(
                name="s3_list_buckets",
                path="/",
                method="GET",
                description="List S3 buckets"
            ),
            "s3_get_object": ConnectorEndpoint(
                name="s3_get_object",
                path="/{bucket}/{key}",
                method="GET",
                description="Get S3 object"
            ),
            "lambda_invoke": ConnectorEndpoint(
                name="lambda_invoke",
                path="/2015-03-31/functions/{function_name}/invocations",
                method="POST",
                description="Invoke Lambda function"
            ),
            "dynamodb_query": ConnectorEndpoint(
                name="dynamodb_query",
                path="/",
                method="POST",
                description="Query DynamoDB table"
            )
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with AWS"""
        # AWS authentication using AWS Signature Version 4
        access_key = self.config.auth_config.get('access_key')
        secret_key = self.config.auth_config.get('secret_key')
        region = self.config.auth_config.get('region', 'us-east-1')
        
        if not access_key or not secret_key:
            raise AuthenticationError("AWS access key and secret key required")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to AWS"""
        try:
            response = await self.make_request("s3_list_buckets")
            return response.success
        except Exception as e:
            logger.error(f"AWS connection test failed: {e}")
            return False

class CustomRESTConnector(BaseConnector):
    """Custom REST API connector"""
    
    def _initialize_endpoints(self):
        """Initialize custom REST endpoints"""
        # This connector allows dynamic endpoint configuration
        self.endpoints = {}
        
        # Load endpoints from config if provided
        custom_endpoints = self.config.custom_config.get('endpoints', [])
        
        for endpoint_config in custom_endpoints:
            endpoint = ConnectorEndpoint(
                name=endpoint_config['name'],
                path=endpoint_config['path'],
                method=endpoint_config.get('method', 'GET'),
                description=endpoint_config.get('description', ''),
                parameters=endpoint_config.get('parameters', {}),
                request_schema=endpoint_config.get('request_schema', {}),
                response_schema=endpoint_config.get('response_schema', {}),
                authentication_required=endpoint_config.get('authentication_required', True)
            )
            self.endpoints[endpoint.name] = endpoint
    
    async def authenticate(self) -> bool:
        """Authenticate with custom REST API"""
        # Custom authentication logic based on config
        auth_type = self.config.authentication_type
        
        if auth_type == AuthenticationType.NONE:
            return True
        elif auth_type == AuthenticationType.API_KEY:
            api_key = self.config.auth_config.get('api_key')
            if not api_key:
                raise AuthenticationError("API key not provided")
        elif auth_type == AuthenticationType.BEARER:
            token = self.config.auth_config.get('token')
            if not token:
                raise AuthenticationError("Bearer token not provided")
        elif auth_type == AuthenticationType.BASIC:
            username = self.config.auth_config.get('username')
            password = self.config.auth_config.get('password')
            if not username or not password:
                raise AuthenticationError("Username and password required")
        
        return True
    
    async def test_connection(self) -> bool:
        """Test connection to custom REST API"""
        try:
            # Try to make a request to a test endpoint
            test_endpoint = self.config.custom_config.get('test_endpoint')
            if test_endpoint:
                response = await self.make_request(test_endpoint)
                return response.success
            else:
                # If no test endpoint, assume connection is OK
                return True
        except Exception as e:
            logger.error(f"Custom REST API connection test failed: {e}")
            return False

# Connector factory function
def create_connector(connector_type: str, config: ConnectorConfig) -> BaseConnector:
    """Factory function to create connectors"""
    connector_classes = {
        "openai": OpenAIConnector,
        "google_cloud": GoogleCloudConnector,
        "slack": SlackConnector,
        "github": GitHubConnector,
        "salesforce": SalesforceConnector,
        "aws": AWSConnector,
        "custom_rest": CustomRESTConnector
    }
    
    if connector_type not in connector_classes:
        raise ValueError(f"Unknown connector type: {connector_type}")
    
    connector_class = connector_classes[connector_type]
    return connector_class(config)

# Example configurations
EXAMPLE_CONFIGS = {
    "openai": {
        "connector_id": "openai_connector",
        "name": "OpenAI API",
        "description": "OpenAI API connector for GPT models",
        "version": "1.0.0",
        "base_url": "https://api.openai.com",
        "authentication_type": "bearer",
        "auth_config": {
            "token": "your-openai-api-key"
        },
        "headers": {
            "Content-Type": "application/json"
        },
        "timeout": 30,
        "retry_attempts": 3,
        "data_format": "json"
    },
    "slack": {
        "connector_id": "slack_connector",
        "name": "Slack API",
        "description": "Slack API connector for messaging",
        "version": "1.0.0",
        "base_url": "https://slack.com/api",
        "authentication_type": "bearer",
        "auth_config": {
            "token": "your-slack-bot-token"
        },
        "timeout": 30,
        "data_format": "json"
    },
    "github": {
        "connector_id": "github_connector",
        "name": "GitHub API",
        "description": "GitHub API connector for repository management",
        "version": "1.0.0",
        "base_url": "https://api.github.com",
        "authentication_type": "bearer",
        "auth_config": {
            "token": "your-github-token"
        },
        "headers": {
            "Accept": "application/vnd.github.v3+json"
        },
        "timeout": 30,
        "data_format": "json"
    }
}

async def main():
    """Main function to demonstrate pre-built connectors"""
    from connector_framework import ConnectorRegistry, ConnectorConfig, AuthenticationType, DataFormat
    
    # Create registry
    registry = ConnectorRegistry()
    
    # Register connector types
    registry.register_connector_type("openai", OpenAIConnector)
    registry.register_connector_type("slack", SlackConnector)
    registry.register_connector_type("github", GitHubConnector)
    registry.register_connector_type("custom_rest", CustomRESTConnector)
    
    print("Pre-built connectors registered:")
    for connector_type in registry.connector_types:
        print(f"  - {connector_type}")
    
    # Example: Create OpenAI connector
    openai_config = ConnectorConfig(
        connector_id="openai_demo",
        name="OpenAI Demo",
        description="Demo OpenAI connector",
        version="1.0.0",
        base_url="https://api.openai.com",
        authentication_type=AuthenticationType.BEARER,
        auth_config={"token": "demo-token"},
        data_format=DataFormat.JSON
    )
    
    openai_connector = registry.create_connector(openai_config, "openai")
    print(f"\nCreated connector: {openai_connector.config.name}")
    print(f"Available endpoints: {list(openai_connector.get_endpoints().keys())}")

if __name__ == "__main__":
    asyncio.run(main())