"""
Language Server Protocol (LSP) implementation for IDE Bridge Service
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LSPErrorCode(Enum):
    """LSP error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000
    SERVER_NOT_INITIALIZED = -32002
    UNKNOWN_ERROR_CODE = -32001
    REQUEST_CANCELLED = -32800
    CONTENT_MODIFIED = -32801

@dataclass
class LSPRequest:
    """LSP request structure"""
    jsonrpc: str
    id: Union[str, int, None]
    method: str
    params: Optional[Dict[str, Any]] = None

@dataclass
class LSPResponse:
    """LSP response structure"""
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class LSPServer:
    """Language Server Protocol server implementation"""
    
    def __init__(self, code_analyzer, agent_integration):
        self.code_analyzer = code_analyzer
        self.agent_integration = agent_integration
        self.initialized = False
        self.client_capabilities = {}
        self.server_capabilities = {
            "textDocumentSync": {
                "openClose": True,
                "change": 1,  # Full document sync
                "willSave": False,
                "willSaveWaitUntil": False,
                "save": True
            },
            "completionProvider": {
                "resolveProvider": True,
                "triggerCharacters": [".", ":", " "]
            },
            "hoverProvider": True,
            "signatureHelpProvider": {
                "triggerCharacters": ["(", ","]
            },
            "definitionProvider": True,
            "referencesProvider": True,
            "documentHighlightProvider": True,
            "documentSymbolProvider": True,
            "workspaceSymbolProvider": True,
            "codeActionProvider": True,
            "codeLensProvider": {
                "resolveProvider": True
            },
            "documentFormattingProvider": True,
            "documentRangeFormattingProvider": True,
            "documentOnTypeFormattingProvider": {
                "firstTriggerCharacter": ";",
                "moreTriggerCharacter": ["}", "\n"]
            },
            "renameProvider": True,
            "diagnosticProvider": {
                "interFileDependencies": True,
                "workspaceDiagnostics": True
            }
        }
        self.documents = {}  # Store document contents
        
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming LSP request"""
        try:
            # Parse request
            request = LSPRequest(
                jsonrpc=request_data.get("jsonrpc", "2.0"),
                id=request_data.get("id"),
                method=request_data.get("method"),
                params=request_data.get("params")
            )
            
            # Route to appropriate handler
            handler = getattr(self, f"handle_{request.method.replace('/', '_')}", None)
            if not handler:
                return self._create_error_response(
                    request.id,
                    LSPErrorCode.METHOD_NOT_FOUND,
                    f"Method not found: {request.method}"
                )
            
            # Execute handler
            result = await handler(request.params)
            return self._create_success_response(request.id, result)
            
        except Exception as e:
            logger.error(f"LSP request handling failed: {e}")
            return self._create_error_response(
                request_data.get("id"),
                LSPErrorCode.INTERNAL_ERROR,
                str(e)
            )
    
    def _create_success_response(self, request_id: Union[str, int, None], result: Any) -> Dict[str, Any]:
        """Create successful LSP response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def _create_error_response(self, request_id: Union[str, int, None], error_code: LSPErrorCode, message: str) -> Dict[str, Any]:
        """Create error LSP response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code.value,
                "message": message
            }
        }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        self.client_capabilities = params.get("capabilities", {})
        
        return {
            "capabilities": self.server_capabilities,
            "serverInfo": {
                "name": "Multimodal LLM Stack IDE Bridge",
                "version": "1.0.0"
            }
        }
    
    async def handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification"""
        self.initialized = True
        logger.info("LSP client initialized")
    
    async def handle_textDocument_didOpen(self, params: Dict[str, Any]) -> None:
        """Handle text document did open notification"""
        document = params.get("textDocument", {})
        uri = document.get("uri")
        text = document.get("text", "")
        
        if uri:
            self.documents[uri] = text
            logger.info(f"Document opened: {uri}")
    
    async def handle_textDocument_didChange(self, params: Dict[str, Any]) -> None:
        """Handle text document did change notification"""
        document = params.get("textDocument", {})
        uri = document.get("uri")
        changes = params.get("contentChanges", [])
        
        if uri and changes:
            # For now, assume full document sync
            if changes and "text" in changes[0]:
                self.documents[uri] = changes[0]["text"]
                logger.info(f"Document changed: {uri}")
    
    async def handle_textDocument_didClose(self, params: Dict[str, Any]) -> None:
        """Handle text document did close notification"""
        document = params.get("textDocument", {})
        uri = document.get("uri")
        
        if uri and uri in self.documents:
            del self.documents[uri]
            logger.info(f"Document closed: {uri}")
    
    async def handle_textDocument_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document completion request"""
        document = params.get("textDocument", {})
        position = params.get("position", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return {"items": []}
        
        # Get document text and position
        text = self.documents[uri]
        line = position.get("line", 0)
        character = position.get("character", 0)
        
        # Get completions from code analyzer and agent integration
        completions = []
        
        # Basic completions from code analyzer
        if self.code_analyzer:
            basic_completions = await self.code_analyzer.get_completions(text, line, character)
            completions.extend(basic_completions)
        
        # AI-powered completions from agent integration
        if self.agent_integration:
            ai_completions = await self.agent_integration.get_completions(text, line, character, uri)
            completions.extend(ai_completions)
        
        return {"items": completions}
    
    async def handle_completionItem_resolve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completion item resolve request"""
        # Return the completion item with additional details
        return params
    
    async def handle_textDocument_hover(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document hover request"""
        document = params.get("textDocument", {})
        position = params.get("position", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return {"contents": {"kind": "markdown", "value": "No information available"}}
        
        text = self.document[uri]
        line = position.get("line", 0)
        character = position.get("character", 0)
        
        # Get hover information from code analyzer
        hover_info = None
        if self.code_analyzer:
            hover_info = await self.code_analyzer.get_hover_info(text, line, character)
        
        if hover_info:
            return {
                "contents": {
                    "kind": "markdown",
                    "value": hover_info
                }
            }
        
        return {"contents": {"kind": "markdown", "value": "No information available"}}
    
    async def handle_textDocument_definition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document definition request"""
        document = params.get("textDocument", {})
        position = params.get("position", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return []
        
        text = self.documents[uri]
        line = position.get("line", 0)
        character = position.get("character", 0)
        
        # Get definition from code analyzer
        definition = None
        if self.code_analyzer:
            definition = await self.code_analyzer.get_definition(text, line, character, uri)
        
        if definition:
            return [definition]
        
        return []
    
    async def handle_textDocument_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document references request"""
        document = params.get("textDocument", {})
        position = params.get("position", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return []
        
        text = self.documents[uri]
        line = position.get("line", 0)
        character = position.get("character", 0)
        
        # Get references from code analyzer
        references = []
        if self.code_analyzer:
            references = await self.code_analyzer.get_references(text, line, character, uri)
        
        return references
    
    async def handle_textDocument_documentSymbol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document document symbol request"""
        document = params.get("textDocument", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return []
        
        text = self.documents[uri]
        
        # Get symbols from code analyzer
        symbols = []
        if self.code_analyzer:
            symbols = await self.code_analyzer.get_document_symbols(text, uri)
        
        return symbols
    
    async def handle_textDocument_codeAction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document code action request"""
        document = params.get("textDocument", {})
        range = params.get("range", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return []
        
        text = self.documents[uri]
        
        # Get code actions from code analyzer and agent integration
        actions = []
        
        if self.code_analyzer:
            basic_actions = await self.code_analyzer.get_code_actions(text, range, uri)
            actions.extend(basic_actions)
        
        if self.agent_integration:
            ai_actions = await self.agent_integration.get_code_actions(text, range, uri)
            actions.extend(ai_actions)
        
        return actions
    
    async def handle_textDocument_formatting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document formatting request"""
        document = params.get("textDocument", {})
        uri = document.get("uri")
        
        if not uri or uri not in self.documents:
            return []
        
        text = self.documents[uri]
        
        # Get formatting from code analyzer
        edits = []
        if self.code_analyzer:
            edits = await self.code_analyzer.format_document(text, uri)
        
        return edits
    
    async def handle_textDocument_rename(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text document rename request"""
        document = params.get("textDocument", {})
        position = params.get("position", {})
        new_name = params.get("newName")
        uri = document.get("uri")
        
        if not uri or uri not in self.documents or not new_name:
            return {"changes": {}}
        
        text = self.documents[uri]
        line = position.get("line", 0)
        character = position.get("character", 0)
        
        # Get rename changes from code analyzer
        changes = {}
        if self.code_analyzer:
            changes = await self.code_analyzer.rename_symbol(text, line, character, new_name, uri)
        
        return {"changes": changes}
    
    async def handle_workspace_symbol(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workspace symbol request"""
        query = params.get("query", "")
        
        # Get workspace symbols from code analyzer
        symbols = []
        if self.code_analyzer:
            symbols = await self.code_analyzer.get_workspace_symbols(query)
        
        return symbols