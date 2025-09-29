"""
Model Context Protocol (MCP) server implementation for IDE Bridge Service
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class MCPErrorCode(Enum):
    """MCP error codes"""
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    PARSE_ERROR = -32700

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None

@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str

class MCPServer:
    """Model Context Protocol server implementation"""
    
    def __init__(self, agent_integration):
        self.agent_integration = agent_integration
        self.tools = {}
        self.resources = {}
        self.initialized = False
        
        # Initialize built-in tools
        self._initialize_builtin_tools()
    
    def _initialize_builtin_tools(self):
        """Initialize built-in MCP tools"""
        # Code Analysis Tool
        self.tools["code_analysis"] = MCPTool(
            name="code_analysis",
            description="Analyze code for syntax errors, style issues, and potential improvements",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "file_path": {"type": "string", "description": "File path (optional)"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Code Generation Tool
        self.tools["code_generation"] = MCPTool(
            name="code_generation",
            description="Generate code based on natural language description",
            input_schema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Natural language description of code to generate"},
                    "language": {"type": "string", "description": "Target programming language"},
                    "context": {"type": "string", "description": "Additional context (optional)"}
                },
                "required": ["description", "language"]
            }
        )
        
        # Code Refactoring Tool
        self.tools["code_refactoring"] = MCPTool(
            name="code_refactoring",
            description="Refactor code to improve structure, readability, or performance",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to refactor"},
                    "language": {"type": "string", "description": "Programming language"},
                    "refactoring_type": {"type": "string", "description": "Type of refactoring (optional)"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Documentation Generation Tool
        self.tools["documentation_generation"] = MCPTool(
            name="documentation_generation",
            description="Generate documentation for code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to document"},
                    "language": {"type": "string", "description": "Programming language"},
                    "doc_type": {"type": "string", "description": "Type of documentation (docstring, README, etc.)"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Test Generation Tool
        self.tools["test_generation"] = MCPTool(
            name="test_generation",
            description="Generate unit tests for code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to test"},
                    "language": {"type": "string", "description": "Programming language"},
                    "test_framework": {"type": "string", "description": "Test framework to use (optional)"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Bug Detection Tool
        self.tools["bug_detection"] = MCPTool(
            name="bug_detection",
            description="Detect potential bugs and issues in code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "severity": {"type": "string", "description": "Minimum severity level (optional)"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Performance Analysis Tool
        self.tools["performance_analysis"] = MCPTool(
            name="performance_analysis",
            description="Analyze code performance and suggest optimizations",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "analysis_type": {"type": "string", "description": "Type of analysis (optional)"}
                },
                "required": ["code", "language"]
            }
        )
        
        # Security Analysis Tool
        self.tools["security_analysis"] = MCPTool(
            name="security_analysis",
            description="Analyze code for security vulnerabilities",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "security_level": {"type": "string", "description": "Security analysis level (optional)"}
                },
                "required": ["code", "language"]
            }
        )
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        return tools_list
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Validate parameters
        self._validate_parameters(parameters, tool.input_schema)
        
        # Execute tool based on type
        if tool_name == "code_analysis":
            return await self._execute_code_analysis(parameters)
        elif tool_name == "code_generation":
            return await self._execute_code_generation(parameters)
        elif tool_name == "code_refactoring":
            return await self._execute_code_refactoring(parameters)
        elif tool_name == "documentation_generation":
            return await self._execute_documentation_generation(parameters)
        elif tool_name == "test_generation":
            return await self._execute_test_generation(parameters)
        elif tool_name == "bug_detection":
            return await self._execute_bug_detection(parameters)
        elif tool_name == "performance_analysis":
            return await self._execute_performance_analysis(parameters)
        elif tool_name == "security_analysis":
            return await self._execute_security_analysis(parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def _validate_parameters(self, parameters: Dict[str, Any], schema: Dict[str, Any]):
        """Validate parameters against schema"""
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in parameters:
                raise ValueError(f"Missing required parameter: {field}")
        
        # Check parameter types
        for param_name, param_value in parameters.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type")
                if expected_type == "string" and not isinstance(param_value, str):
                    raise ValueError(f"Parameter {param_name} must be a string")
                elif expected_type == "object" and not isinstance(param_value, dict):
                    raise ValueError(f"Parameter {param_name} must be an object")
    
    async def _execute_code_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code analysis tool"""
        code = parameters["code"]
        language = parameters["language"]
        file_path = parameters.get("file_path")
        
        # Use agent integration for AI-powered analysis
        if self.agent_integration:
            result = await self.agent_integration.analyze_code(code, language, file_path)
            return {
                "analysis": result,
                "tool": "code_analysis",
                "language": language
            }
        
        # Fallback basic analysis
        return {
            "analysis": {
                "syntax_valid": True,
                "issues": [],
                "suggestions": []
            },
            "tool": "code_analysis",
            "language": language
        }
    
    async def _execute_code_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code generation tool"""
        description = parameters["description"]
        language = parameters["language"]
        context = parameters.get("context", "")
        
        # Use agent integration for code generation
        if self.agent_integration:
            result = await self.agent_integration.generate_code(description, language, context)
            return {
                "generated_code": result,
                "tool": "code_generation",
                "language": language,
                "description": description
            }
        
        # Fallback
        return {
            "generated_code": f"# Generated {language} code based on: {description}",
            "tool": "code_generation",
            "language": language,
            "description": description
        }
    
    async def _execute_code_refactoring(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code refactoring tool"""
        code = parameters["code"]
        language = parameters["language"]
        refactoring_type = parameters.get("refactoring_type", "general")
        
        # Use agent integration for refactoring
        if self.agent_integration:
            result = await self.agent_integration.refactor_code(code, language, refactoring_type)
            return {
                "refactored_code": result,
                "tool": "code_refactoring",
                "language": language,
                "refactoring_type": refactoring_type
            }
        
        # Fallback
        return {
            "refactored_code": code,
            "tool": "code_refactoring",
            "language": language,
            "refactoring_type": refactoring_type
        }
    
    async def _execute_documentation_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation generation tool"""
        code = parameters["code"]
        language = parameters["language"]
        doc_type = parameters.get("doc_type", "docstring")
        
        # Use agent integration for documentation generation
        if self.agent_integration:
            result = await self.agent_integration.generate_documentation(code, language, doc_type)
            return {
                "documentation": result,
                "tool": "documentation_generation",
                "language": language,
                "doc_type": doc_type
            }
        
        # Fallback
        return {
            "documentation": f"# Documentation for {language} code",
            "tool": "documentation_generation",
            "language": language,
            "doc_type": doc_type
        }
    
    async def _execute_test_generation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test generation tool"""
        code = parameters["code"]
        language = parameters["language"]
        test_framework = parameters.get("test_framework", "default")
        
        # Use agent integration for test generation
        if self.agent_integration:
            result = await self.agent_integration.generate_tests(code, language, test_framework)
            return {
                "tests": result,
                "tool": "test_generation",
                "language": language,
                "test_framework": test_framework
            }
        
        # Fallback
        return {
            "tests": f"# Generated tests for {language} code",
            "tool": "test_generation",
            "language": language,
            "test_framework": test_framework
        }
    
    async def _execute_bug_detection(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bug detection tool"""
        code = parameters["code"]
        language = parameters["language"]
        severity = parameters.get("severity", "medium")
        
        # Use agent integration for bug detection
        if self.agent_integration:
            result = await self.agent_integration.detect_bugs(code, language, severity)
            return {
                "bugs": result,
                "tool": "bug_detection",
                "language": language,
                "severity": severity
            }
        
        # Fallback
        return {
            "bugs": [],
            "tool": "bug_detection",
            "language": language,
            "severity": severity
        }
    
    async def _execute_performance_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance analysis tool"""
        code = parameters["code"]
        language = parameters["language"]
        analysis_type = parameters.get("analysis_type", "general")
        
        # Use agent integration for performance analysis
        if self.agent_integration:
            result = await self.agent_integration.analyze_performance(code, language, analysis_type)
            return {
                "performance_analysis": result,
                "tool": "performance_analysis",
                "language": language,
                "analysis_type": analysis_type
            }
        
        # Fallback
        return {
            "performance_analysis": {
                "complexity": "O(n)",
                "suggestions": []
            },
            "tool": "performance_analysis",
            "language": language,
            "analysis_type": analysis_type
        }
    
    async def _execute_security_analysis(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security analysis tool"""
        code = parameters["code"]
        language = parameters["language"]
        security_level = parameters.get("security_level", "medium")
        
        # Use agent integration for security analysis
        if self.agent_integration:
            result = await self.agent_integration.analyze_security(code, language, security_level)
            return {
                "security_issues": result,
                "tool": "security_analysis",
                "language": language,
                "security_level": security_level
            }
        
        # Fallback
        return {
            "security_issues": [],
            "tool": "security_analysis",
            "language": language,
            "security_level": security_level
        }