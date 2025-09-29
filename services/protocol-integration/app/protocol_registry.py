"""
Protocol Registry for managing protocol definitions and schemas
"""

import json
import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class ProtocolCategory(Enum):
    """Protocol categories"""
    LANGUAGE_SERVER = "language_server"
    MODEL_CONTEXT = "model_context"
    API = "api"
    MESSAGING = "messaging"
    STORAGE = "storage"
    AUTHENTICATION = "authentication"
    MONITORING = "monitoring"

@dataclass
class ProtocolDefinition:
    """Protocol definition structure"""
    id: str
    name: str
    version: str
    category: ProtocolCategory
    description: str
    schema: Dict[str, Any]
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProtocolSchema:
    """Protocol schema structure"""
    protocol_id: str
    message_types: Dict[str, Dict[str, Any]]
    data_types: Dict[str, Dict[str, Any]]
    validation_rules: Dict[str, Any]
    version: str

class ProtocolRegistry:
    """Registry for managing protocol definitions and schemas"""
    
    def __init__(self):
        self.protocols: Dict[str, ProtocolDefinition] = {}
        self.schemas: Dict[str, ProtocolSchema] = {}
        self.capability_index: Dict[str, Set[str]] = {}
        self.category_index: Dict[ProtocolCategory, Set[str]] = {}
    
    async def initialize(self):
        """Initialize the protocol registry"""
        logger.info("Protocol registry initialized")
        
        # Register default protocols
        await self._register_default_protocols()
    
    async def _register_default_protocols(self):
        """Register default protocol definitions"""
        # LSP Protocol
        lsp_protocol = ProtocolDefinition(
            id="lsp-3.17",
            name="Language Server Protocol",
            version="3.17.0",
            category=ProtocolCategory.LANGUAGE_SERVER,
            description="Protocol for language servers to provide language features to editors",
            schema={
                "jsonrpc": "2.0",
                "methods": [
                    "initialize",
                    "textDocument/completion",
                    "textDocument/hover",
                    "textDocument/definition",
                    "textDocument/references",
                    "textDocument/formatting",
                    "textDocument/diagnostic"
                ],
                "notifications": [
                    "textDocument/didOpen",
                    "textDocument/didChange",
                    "textDocument/didClose",
                    "textDocument/didSave"
                ]
            },
            capabilities=[
                "completion",
                "hover",
                "definition",
                "references",
                "formatting",
                "diagnostic",
                "code_action",
                "rename",
                "folding"
            ],
            examples=[
                {
                    "name": "Completion Request",
                    "request": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "textDocument/completion",
                        "params": {
                            "textDocument": {"uri": "file:///path/to/file.py"},
                            "position": {"line": 10, "character": 5}
                        }
                    },
                    "response": {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "result": {
                            "items": [
                                {
                                    "label": "function_name",
                                    "kind": 3,
                                    "detail": "def function_name()",
                                    "insertText": "function_name()"
                                }
                            ]
                        }
                    }
                }
            ]
        )
        await self.register_protocol(lsp_protocol)
        
        # MCP Protocol
        mcp_protocol = ProtocolDefinition(
            id="mcp-1.0",
            name="Model Context Protocol",
            version="1.0.0",
            category=ProtocolCategory.MODEL_CONTEXT,
            description="Protocol for AI model context management and tool integration",
            schema={
                "version": "1.0.0",
                "tools": [
                    "code_completion",
                    "code_hover",
                    "code_definition",
                    "code_analysis",
                    "code_generation",
                    "context_management"
                ],
                "messages": [
                    "tool_call",
                    "tool_result",
                    "context_update",
                    "context_query"
                ]
            },
            capabilities=[
                "code_completion",
                "code_hover",
                "code_definition",
                "code_analysis",
                "code_generation",
                "context_management",
                "tool_execution",
                "context_persistence"
            ],
            examples=[
                {
                    "name": "Tool Call",
                    "request": {
                        "tool": "code_completion",
                        "parameters": {
                            "file_path": "/path/to/file.py",
                            "line": 10,
                            "character": 5,
                            "context": "import numpy as np\nnp."
                        }
                    },
                    "response": {
                        "success": True,
                        "result": {
                            "completions": [
                                {"label": "array", "type": "function"},
                                {"label": "zeros", "type": "function"},
                                {"label": "ones", "type": "function"}
                            ]
                        }
                    }
                }
            ]
        )
        await self.register_protocol(mcp_protocol)
        
        # REST API Protocol
        rest_protocol = ProtocolDefinition(
            id="rest-1.0",
            name="REST API Protocol",
            version="1.0.0",
            category=ProtocolCategory.API,
            description="RESTful API protocol for HTTP-based communication",
            schema={
                "base_url": "http://localhost:3002/api/v1",
                "endpoints": [
                    "/completion",
                    "/hover",
                    "/definition",
                    "/references",
                    "/formatting",
                    "/diagnostic"
                ],
                "methods": ["GET", "POST", "PUT", "DELETE"],
                "authentication": "Bearer token"
            },
            capabilities=[
                "completion",
                "hover",
                "definition",
                "references",
                "formatting",
                "diagnostic",
                "authentication",
                "rate_limiting"
            ],
            examples=[
                {
                    "name": "Completion Request",
                    "request": {
                        "method": "POST",
                        "url": "/api/v1/completion",
                        "headers": {"Authorization": "Bearer token"},
                        "body": {
                            "file_path": "/path/to/file.py",
                            "line": 10,
                            "character": 5
                        }
                    },
                    "response": {
                        "status": 200,
                        "data": {
                            "completions": [
                                {"label": "function_name", "type": "function"}
                            ]
                        }
                    }
                }
            ]
        )
        await self.register_protocol(rest_protocol)
        
        # GraphQL Protocol
        graphql_protocol = ProtocolDefinition(
            id="graphql-1.0",
            name="GraphQL Protocol",
            version="1.0.0",
            category=ProtocolCategory.API,
            description="GraphQL protocol for flexible data querying",
            schema={
                "endpoint": "/graphql",
                "queries": [
                    "GetCompletions",
                    "GetHover",
                    "GetDefinition",
                    "GetReferences"
                ],
                "mutations": [
                    "UpdateContext",
                    "ExecuteTool"
                ],
                "subscriptions": [
                    "CodeChanges",
                    "DiagnosticUpdates"
                ]
            },
            capabilities=[
                "completion",
                "hover",
                "definition",
                "references",
                "context_management",
                "real_time_updates",
                "flexible_querying"
            ],
            examples=[
                {
                    "name": "Completion Query",
                    "request": {
                        "query": """
                            query GetCompletions($filePath: String!, $line: Int!, $character: Int!) {
                                completions(filePath: $filePath, line: $line, character: $character) {
                                    label
                                    kind
                                    detail
                                    insertText
                                }
                            }
                        """,
                        "variables": {
                            "filePath": "/path/to/file.py",
                            "line": 10,
                            "character": 5
                        }
                    },
                    "response": {
                        "data": {
                            "completions": [
                                {
                                    "label": "function_name",
                                    "kind": "function",
                                    "detail": "def function_name()",
                                    "insertText": "function_name()"
                                }
                            ]
                        }
                    }
                }
            ]
        )
        await self.register_protocol(graphql_protocol)
    
    async def register_protocol(self, protocol: ProtocolDefinition) -> bool:
        """Register a new protocol definition"""
        try:
            self.protocols[protocol.id] = protocol
            
            # Update capability index
            for capability in protocol.capabilities:
                if capability not in self.capability_index:
                    self.capability_index[capability] = set()
                self.capability_index[capability].add(protocol.id)
            
            # Update category index
            if protocol.category not in self.category_index:
                self.category_index[protocol.category] = set()
            self.category_index[protocol.category].add(protocol.id)
            
            logger.info(f"Registered protocol: {protocol.name} ({protocol.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register protocol {protocol.name}: {e}")
            return False
    
    async def unregister_protocol(self, protocol_id: str) -> bool:
        """Unregister a protocol definition"""
        try:
            if protocol_id not in self.protocols:
                logger.warning(f"Protocol {protocol_id} not found")
                return False
            
            protocol = self.protocols[protocol_id]
            
            # Remove from capability index
            for capability in protocol.capabilities:
                if capability in self.capability_index:
                    self.capability_index[capability].discard(protocol_id)
                    if not self.capability_index[capability]:
                        del self.capability_index[capability]
            
            # Remove from category index
            if protocol.category in self.category_index:
                self.category_index[protocol.category].discard(protocol_id)
                if not self.category_index[protocol.category]:
                    del self.category_index[protocol.category]
            
            del self.protocols[protocol_id]
            logger.info(f"Unregistered protocol: {protocol_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister protocol {protocol_id}: {e}")
            return False
    
    async def get_protocol(self, protocol_id: str) -> Optional[ProtocolDefinition]:
        """Get a protocol definition by ID"""
        return self.protocols.get(protocol_id)
    
    async def get_all_protocols(self) -> List[ProtocolDefinition]:
        """Get all registered protocols"""
        return list(self.protocols.values())
    
    async def get_protocols_by_category(self, category: ProtocolCategory) -> List[ProtocolDefinition]:
        """Get protocols by category"""
        protocol_ids = self.category_index.get(category, set())
        return [self.protocols[pid] for pid in protocol_ids if pid in self.protocols]
    
    async def get_protocols_by_capability(self, capability: str) -> List[ProtocolDefinition]:
        """Get protocols that support a specific capability"""
        protocol_ids = self.capability_index.get(capability, set())
        return [self.protocols[pid] for pid in protocol_ids if pid in self.protocols]
    
    async def search_protocols(self, query: str) -> List[ProtocolDefinition]:
        """Search protocols by name or description"""
        query_lower = query.lower()
        results = []
        
        for protocol in self.protocols.values():
            if (query_lower in protocol.name.lower() or 
                query_lower in protocol.description.lower() or
                any(query_lower in cap.lower() for cap in protocol.capabilities)):
                results.append(protocol)
        
        return results
    
    async def register_schema(self, schema: ProtocolSchema) -> bool:
        """Register a protocol schema"""
        try:
            self.schemas[schema.protocol_id] = schema
            logger.info(f"Registered schema for protocol: {schema.protocol_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register schema for {schema.protocol_id}: {e}")
            return False
    
    async def get_schema(self, protocol_id: str) -> Optional[ProtocolSchema]:
        """Get a protocol schema by protocol ID"""
        return self.schemas.get(protocol_id)
    
    async def validate_message(self, protocol_id: str, message_type: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a message against a protocol schema"""
        try:
            schema = self.schemas.get(protocol_id)
            if not schema:
                return {
                    "valid": False,
                    "error": f"No schema found for protocol {protocol_id}"
                }
            
            if message_type not in schema.message_types:
                return {
                    "valid": False,
                    "error": f"Unknown message type: {message_type}"
                }
            
            message_schema = schema.message_types[message_type]
            # In a real implementation, this would perform actual JSON schema validation
            # For now, we'll do basic validation
            
            required_fields = message_schema.get("required", [])
            for field in required_fields:
                if field not in message:
                    return {
                        "valid": False,
                        "error": f"Missing required field: {field}"
                    }
            
            return {
                "valid": True,
                "message_type": message_type,
                "protocol_id": protocol_id
            }
            
        except Exception as e:
            logger.error(f"Message validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def get_protocol_statistics(self) -> Dict[str, Any]:
        """Get protocol registry statistics"""
        total_protocols = len(self.protocols)
        total_schemas = len(self.schemas)
        
        category_counts = {}
        for category, protocol_ids in self.category_index.items():
            category_counts[category.value] = len(protocol_ids)
        
        capability_counts = {}
        for capability, protocol_ids in self.capability_index.items():
            capability_counts[capability] = len(protocol_ids)
        
        return {
            "total_protocols": total_protocols,
            "total_schemas": total_schemas,
            "category_distribution": category_counts,
            "capability_distribution": capability_counts,
            "most_common_capabilities": sorted(
                capability_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
        }
    
    async def export_protocol(self, protocol_id: str) -> Optional[Dict[str, Any]]:
        """Export a protocol definition and schema"""
        protocol = self.protocols.get(protocol_id)
        if not protocol:
            return None
        
        schema = self.schemas.get(protocol_id)
        
        export_data = {
            "protocol": {
                "id": protocol.id,
                "name": protocol.name,
                "version": protocol.version,
                "category": protocol.category.value,
                "description": protocol.description,
                "schema": protocol.schema,
                "capabilities": protocol.capabilities,
                "dependencies": protocol.dependencies,
                "examples": protocol.examples,
                "metadata": protocol.metadata
            }
        }
        
        if schema:
            export_data["schema"] = {
                "protocol_id": schema.protocol_id,
                "message_types": schema.message_types,
                "data_types": schema.data_types,
                "validation_rules": schema.validation_rules,
                "version": schema.version
            }
        
        return export_data
    
    async def import_protocol(self, protocol_data: Dict[str, Any]) -> bool:
        """Import a protocol definition and schema"""
        try:
            # Import protocol definition
            protocol_info = protocol_data.get("protocol", {})
            if not protocol_info:
                logger.error("No protocol information found in import data")
                return False
            
            protocol = ProtocolDefinition(
                id=protocol_info["id"],
                name=protocol_info["name"],
                version=protocol_info["version"],
                category=ProtocolCategory(protocol_info["category"]),
                description=protocol_info["description"],
                schema=protocol_info["schema"],
                capabilities=protocol_info.get("capabilities", []),
                dependencies=protocol_info.get("dependencies", []),
                examples=protocol_info.get("examples", []),
                metadata=protocol_info.get("metadata", {})
            )
            
            success = await self.register_protocol(protocol)
            if not success:
                return False
            
            # Import schema if available
            schema_info = protocol_data.get("schema")
            if schema_info:
                schema = ProtocolSchema(
                    protocol_id=schema_info["protocol_id"],
                    message_types=schema_info["message_types"],
                    data_types=schema_info["data_types"],
                    validation_rules=schema_info["validation_rules"],
                    version=schema_info["version"]
                )
                await self.register_schema(schema)
            
            logger.info(f"Successfully imported protocol: {protocol.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import protocol: {e}")
            return False