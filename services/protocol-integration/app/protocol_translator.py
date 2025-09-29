"""
Protocol Translator for converting between different protocol formats
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProtocolType(Enum):
    """Supported protocol types"""
    LSP = "lsp"
    MCP = "mcp"
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"

@dataclass
class ProtocolMessage:
    """Generic protocol message structure"""
    protocol_type: ProtocolType
    message_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ProtocolTranslator:
    """Translates between different protocol formats"""
    
    def __init__(self):
        self.translators = {
            (ProtocolType.LSP, ProtocolType.MCP): self._lsp_to_mcp,
            (ProtocolType.MCP, ProtocolType.LSP): self._mcp_to_lsp,
            (ProtocolType.LSP, ProtocolType.REST): self._lsp_to_rest,
            (ProtocolType.REST, ProtocolType.LSP): self._rest_to_lsp,
            (ProtocolType.MCP, ProtocolType.REST): self._mcp_to_rest,
            (ProtocolType.REST, ProtocolType.MCP): self._rest_to_mcp,
            (ProtocolType.LSP, ProtocolType.GRAPHQL): self._lsp_to_graphql,
            (ProtocolType.GRAPHQL, ProtocolType.LSP): self._graphql_to_lsp,
        }
    
    async def initialize(self):
        """Initialize the protocol translator"""
        logger.info("Protocol translator initialized")
    
    async def translate(self, from_protocol: str, to_protocol: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a request from one protocol to another"""
        try:
            from_type = ProtocolType(from_protocol.lower())
            to_type = ProtocolType(to_protocol.lower())
            
            translator_key = (from_type, to_type)
            if translator_key not in self.translators:
                raise ValueError(f"Translation from {from_protocol} to {to_protocol} not supported")
            
            translator = self.translators[translator_key]
            result = await translator(request)
            
            return {
                "success": True,
                "from_protocol": from_protocol,
                "to_protocol": to_protocol,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Protocol translation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "from_protocol": from_protocol,
                "to_protocol": to_protocol
            }
    
    async def _lsp_to_mcp(self, lsp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LSP request to MCP format"""
        method = lsp_request.get("method", "")
        params = lsp_request.get("params", {})
        
        if method == "textDocument/completion":
            return {
                "tool": "code_completion",
                "parameters": {
                    "file_path": params.get("textDocument", {}).get("uri", ""),
                    "line": params.get("position", {}).get("line", 0),
                    "character": params.get("position", {}).get("character", 0)
                }
            }
        elif method == "textDocument/hover":
            return {
                "tool": "code_hover",
                "parameters": {
                    "file_path": params.get("textDocument", {}).get("uri", ""),
                    "line": params.get("position", {}).get("line", 0),
                    "character": params.get("position", {}).get("character", 0)
                }
            }
        elif method == "textDocument/definition":
            return {
                "tool": "code_definition",
                "parameters": {
                    "file_path": params.get("textDocument", {}).get("uri", ""),
                    "line": params.get("position", {}).get("line", 0),
                    "character": params.get("position", {}).get("character", 0)
                }
            }
        else:
            return {
                "tool": "generic_lsp",
                "parameters": {
                    "method": method,
                    "params": params
                }
            }
    
    async def _mcp_to_lsp(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP request to LSP format"""
        tool = mcp_request.get("tool", "")
        parameters = mcp_request.get("parameters", {})
        
        if tool == "code_completion":
            return {
                "jsonrpc": "2.0",
                "method": "textDocument/completion",
                "params": {
                    "textDocument": {
                        "uri": parameters.get("file_path", "")
                    },
                    "position": {
                        "line": parameters.get("line", 0),
                        "character": parameters.get("character", 0)
                    }
                }
            }
        elif tool == "code_hover":
            return {
                "jsonrpc": "2.0",
                "method": "textDocument/hover",
                "params": {
                    "textDocument": {
                        "uri": parameters.get("file_path", "")
                    },
                    "position": {
                        "line": parameters.get("line", 0),
                        "character": parameters.get("character", 0)
                    }
                }
            }
        elif tool == "code_definition":
            return {
                "jsonrpc": "2.0",
                "method": "textDocument/definition",
                "params": {
                    "textDocument": {
                        "uri": parameters.get("file_path", "")
                    },
                    "position": {
                        "line": parameters.get("line", 0),
                        "character": parameters.get("character", 0)
                    }
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "method": "generic_mcp",
                "params": {
                    "tool": tool,
                    "parameters": parameters
                }
            }
    
    async def _lsp_to_rest(self, lsp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LSP request to REST format"""
        method = lsp_request.get("method", "")
        params = lsp_request.get("params", {})
        
        # Map LSP methods to REST endpoints
        method_mapping = {
            "textDocument/completion": "/api/v1/completion",
            "textDocument/hover": "/api/v1/hover",
            "textDocument/definition": "/api/v1/definition",
            "textDocument/references": "/api/v1/references",
            "textDocument/formatting": "/api/v1/formatting"
        }
        
        endpoint = method_mapping.get(method, "/api/v1/generic")
        
        return {
            "endpoint": endpoint,
            "method": "POST",
            "data": params
        }
    
    async def _rest_to_lsp(self, rest_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert REST request to LSP format"""
        endpoint = rest_request.get("endpoint", "")
        data = rest_request.get("data", {})
        
        # Map REST endpoints to LSP methods
        endpoint_mapping = {
            "/api/v1/completion": "textDocument/completion",
            "/api/v1/hover": "textDocument/hover",
            "/api/v1/definition": "textDocument/definition",
            "/api/v1/references": "textDocument/references",
            "/api/v1/formatting": "textDocument/formatting"
        }
        
        method = endpoint_mapping.get(endpoint, "generic_rest")
        
        return {
            "jsonrpc": "2.0",
            "method": method,
            "params": data
        }
    
    async def _mcp_to_rest(self, mcp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MCP request to REST format"""
        tool = mcp_request.get("tool", "")
        parameters = mcp_request.get("parameters", {})
        
        return {
            "endpoint": f"/api/v1/mcp/tools/{tool}",
            "method": "POST",
            "data": parameters
        }
    
    async def _rest_to_mcp(self, rest_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert REST request to MCP format"""
        endpoint = rest_request.get("endpoint", "")
        data = rest_request.get("data", {})
        
        # Extract tool name from endpoint
        if "/mcp/tools/" in endpoint:
            tool = endpoint.split("/mcp/tools/")[-1]
        else:
            tool = "generic_rest"
        
        return {
            "tool": tool,
            "parameters": data
        }
    
    async def _lsp_to_graphql(self, lsp_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert LSP request to GraphQL format"""
        method = lsp_request.get("method", "")
        params = lsp_request.get("params", {})
        
        # Map LSP methods to GraphQL queries
        if method == "textDocument/completion":
            return {
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
                    "filePath": params.get("textDocument", {}).get("uri", ""),
                    "line": params.get("position", {}).get("line", 0),
                    "character": params.get("position", {}).get("character", 0)
                }
            }
        elif method == "textDocument/hover":
            return {
                "query": """
                    query GetHover($filePath: String!, $line: Int!, $character: Int!) {
                        hover(filePath: $filePath, line: $line, character: $character) {
                            contents
                            range
                        }
                    }
                """,
                "variables": {
                    "filePath": params.get("textDocument", {}).get("uri", ""),
                    "line": params.get("position", {}).get("line", 0),
                    "character": params.get("position", {}).get("character", 0)
                }
            }
        else:
            return {
                "query": """
                    query GenericLSP($method: String!, $params: JSON!) {
                        genericLSP(method: $method, params: $params)
                    }
                """,
                "variables": {
                    "method": method,
                    "params": params
                }
            }
    
    async def _graphql_to_lsp(self, graphql_request: Dict[str, Any]) -> Dict[str, Any]:
        """Convert GraphQL request to LSP format"""
        query = graphql_request.get("query", "")
        variables = graphql_request.get("variables", {})
        
        # Map GraphQL queries to LSP methods
        if "completions" in query:
            return {
                "jsonrpc": "2.0",
                "method": "textDocument/completion",
                "params": {
                    "textDocument": {
                        "uri": variables.get("filePath", "")
                    },
                    "position": {
                        "line": variables.get("line", 0),
                        "character": variables.get("character", 0)
                    }
                }
            }
        elif "hover" in query:
            return {
                "jsonrpc": "2.0",
                "method": "textDocument/hover",
                "params": {
                    "textDocument": {
                        "uri": variables.get("filePath", "")
                    },
                    "position": {
                        "line": variables.get("line", 0),
                        "character": variables.get("character", 0)
                    }
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "method": "generic_graphql",
                "params": {
                    "query": query,
                    "variables": variables
                }
            }
    
    def get_supported_translations(self) -> List[Dict[str, str]]:
        """Get list of supported protocol translations"""
        translations = []
        for (from_type, to_type) in self.translators.keys():
            translations.append({
                "from": from_type.value,
                "to": to_type.value
            })
        return translations