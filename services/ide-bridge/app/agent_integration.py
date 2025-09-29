"""
Agent integration for IDE Bridge Service
Provides AI-powered code assistance through the AI agents service
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

class AgentIntegration:
    """Integration with AI agents service for intelligent code assistance"""
    
    def __init__(self):
        self.ai_agents_url = settings.AI_AGENTS_URL
        self.agent_timeout = settings.AGENT_TIMEOUT
        self.session: Optional[aiohttp.ClientSession] = None
        self.available_agents = []
        self.agent_cache = {}
    
    async def initialize(self):
        """Initialize the agent integration"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.agent_timeout)
        )
        
        # Load available agents
        await self._load_available_agents()
        logger.info(f"Agent integration initialized with {len(self.available_agents)} agents")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
    
    async def _load_available_agents(self):
        """Load available agents from the AI agents service"""
        try:
            async with self.session.get(f"{self.ai_agents_url}/api/v1/agents") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_agents = data.get("agents", [])
                else:
                    logger.warning(f"Failed to load agents: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
            # Use fallback agents
            self.available_agents = [
                {
                    "agent_id": "code_assistant",
                    "name": "Code Assistant",
                    "goal": "Help with code analysis, generation, and improvement"
                },
                {
                    "agent_id": "documentation_helper",
                    "name": "Documentation Helper",
                    "goal": "Generate and improve code documentation"
                }
            ]
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List available agents for IDE integration"""
        return self.available_agents
    
    async def execute_task(self, agent_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task using an AI agent"""
        if not self.session:
            raise RuntimeError("Agent integration not initialized")
        
        try:
            # Find the agent
            agent = next((a for a in self.available_agents if a["agent_id"] == agent_id), None)
            if not agent:
                raise ValueError(f"Agent not found: {agent_id}")
            
            # Prepare the task with context
            full_task = self._prepare_task_with_context(task, context)
            
            # Execute the task
            payload = {
                "task": full_task,
                "user_id": context.get("user_id", "ide_bridge") if context else "ide_bridge"
            }
            
            async with self.session.post(
                f"{self.ai_agents_url}/api/v1/agents/{agent_id}/execute",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "result": result.get("result", ""),
                        "agent_id": agent_id,
                        "agent_name": agent["name"],
                        "execution_time": result.get("execution_time_ms", 0),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Agent execution failed: HTTP {response.status} - {error_text}",
                        "agent_id": agent_id,
                        "timestamp": datetime.now().isoformat()
                    }
        
        except Exception as e:
            logger.error(f"Error executing agent task: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _prepare_task_with_context(self, task: str, context: Dict[str, Any] = None) -> str:
        """Prepare task with additional context"""
        if not context:
            return task
        
        context_parts = []
        
        # Add file information
        if "file_path" in context:
            context_parts.append(f"File: {context['file_path']}")
        
        # Add language information
        if "language" in context:
            context_parts.append(f"Language: {context['language']}")
        
        # Add code context
        if "code" in context:
            context_parts.append(f"Code context:\n```{context.get('language', '')}\n{context['code']}\n```")
        
        # Add cursor position
        if "line" in context and "character" in context:
            context_parts.append(f"Cursor position: line {context['line']}, character {context['character']}")
        
        # Add workspace information
        if "workspace" in context:
            context_parts.append(f"Workspace: {context['workspace']}")
        
        if context_parts:
            context_str = "\n".join(context_parts)
            return f"{task}\n\nContext:\n{context_str}"
        
        return task
    
    # Code assistance methods
    async def get_completions(self, code: str, line: int, character: int, file_path: str = None) -> List[Dict[str, Any]]:
        """Get AI-powered code completions"""
        try:
            # Use code assistant agent for completions
            context = {
                "code": code,
                "line": line,
                "character": character,
                "file_path": file_path,
                "task_type": "completion"
            }
            
            task = f"Provide intelligent code completions for the cursor position at line {line}, character {character}. Consider the surrounding code context and suggest relevant completions."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                # Parse the result to extract completions
                completions = self._parse_completions(result["result"])
                return completions
            else:
                logger.warning(f"Failed to get completions: {result['error']}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting completions: {e}")
            return []
    
    async def get_code_actions(self, code: str, range: Dict[str, Any], file_path: str = None) -> List[Dict[str, Any]]:
        """Get AI-powered code actions"""
        try:
            context = {
                "code": code,
                "range": range,
                "file_path": file_path,
                "task_type": "code_actions"
            }
            
            task = f"Analyze the selected code range and suggest relevant code actions like refactoring, optimization, or fixes."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                actions = self._parse_code_actions(result["result"])
                return actions
            else:
                logger.warning(f"Failed to get code actions: {result['error']}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting code actions: {e}")
            return []
    
    # MCP tool implementations
    async def analyze_code(self, code: str, language: str, file_path: str = None) -> Dict[str, Any]:
        """Analyze code for issues and improvements"""
        try:
            context = {
                "code": code,
                "language": language,
                "file_path": file_path,
                "task_type": "analysis"
            }
            
            task = f"Analyze this {language} code for syntax errors, style issues, potential bugs, and improvement opportunities. Provide detailed feedback with specific suggestions."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                return self._parse_analysis_result(result["result"], language)
            else:
                return {
                    "syntax_valid": True,
                    "issues": [],
                    "suggestions": [],
                    "error": result["error"]
                }
        
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {
                "syntax_valid": True,
                "issues": [],
                "suggestions": [],
                "error": str(e)
            }
    
    async def generate_code(self, description: str, language: str, context: str = "") -> str:
        """Generate code based on description"""
        try:
            task_context = {
                "language": language,
                "context": context,
                "task_type": "generation"
            }
            
            task = f"Generate {language} code based on this description: {description}"
            if context:
                task += f"\n\nAdditional context: {context}"
            
            result = await self.execute_task("code_assistant", task, task_context)
            
            if result["success"]:
                return self._extract_code_from_result(result["result"], language)
            else:
                return f"// Error generating code: {result['error']}"
        
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"// Error generating code: {str(e)}"
    
    async def refactor_code(self, code: str, language: str, refactoring_type: str = "general") -> str:
        """Refactor code for better structure and performance"""
        try:
            context = {
                "code": code,
                "language": language,
                "refactoring_type": refactoring_type,
                "task_type": "refactoring"
            }
            
            task = f"Refactor this {language} code for better structure, readability, and performance. Focus on {refactoring_type} improvements."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                return self._extract_code_from_result(result["result"], language)
            else:
                return code  # Return original code if refactoring fails
        
        except Exception as e:
            logger.error(f"Error refactoring code: {e}")
            return code
    
    async def generate_documentation(self, code: str, language: str, doc_type: str = "docstring") -> str:
        """Generate documentation for code"""
        try:
            context = {
                "code": code,
                "language": language,
                "doc_type": doc_type,
                "task_type": "documentation"
            }
            
            task = f"Generate {doc_type} documentation for this {language} code. Make it clear, comprehensive, and follow best practices."
            
            result = await self.execute_task("documentation_helper", task, context)
            
            if result["success"]:
                return result["result"]
            else:
                return f"# Documentation generation failed: {result['error']}"
        
        except Exception as e:
            logger.error(f"Error generating documentation: {e}")
            return f"# Documentation generation failed: {str(e)}"
    
    async def generate_tests(self, code: str, language: str, test_framework: str = "default") -> str:
        """Generate unit tests for code"""
        try:
            context = {
                "code": code,
                "language": language,
                "test_framework": test_framework,
                "task_type": "testing"
            }
            
            task = f"Generate comprehensive unit tests for this {language} code using {test_framework} framework. Include edge cases and error conditions."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                return self._extract_code_from_result(result["result"], language)
            else:
                return f"// Test generation failed: {result['error']}"
        
        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            return f"// Test generation failed: {str(e)}"
    
    async def detect_bugs(self, code: str, language: str, severity: str = "medium") -> List[Dict[str, Any]]:
        """Detect potential bugs in code"""
        try:
            context = {
                "code": code,
                "language": language,
                "severity": severity,
                "task_type": "bug_detection"
            }
            
            task = f"Analyze this {language} code for potential bugs and issues. Focus on {severity} severity issues and provide specific recommendations."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                return self._parse_bug_detection_result(result["result"])
            else:
                return []
        
        except Exception as e:
            logger.error(f"Error detecting bugs: {e}")
            return []
    
    async def analyze_performance(self, code: str, language: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze code performance"""
        try:
            context = {
                "code": code,
                "language": language,
                "analysis_type": analysis_type,
                "task_type": "performance"
            }
            
            task = f"Analyze the performance characteristics of this {language} code. Focus on {analysis_type} analysis and provide optimization suggestions."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                return self._parse_performance_result(result["result"])
            else:
                return {"complexity": "Unknown", "suggestions": []}
        
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {"complexity": "Unknown", "suggestions": []}
    
    async def analyze_security(self, code: str, language: str, security_level: str = "medium") -> List[Dict[str, Any]]:
        """Analyze code for security vulnerabilities"""
        try:
            context = {
                "code": code,
                "language": language,
                "security_level": security_level,
                "task_type": "security"
            }
            
            task = f"Analyze this {language} code for security vulnerabilities. Focus on {security_level} level security issues and provide remediation suggestions."
            
            result = await self.execute_task("code_assistant", task, context)
            
            if result["success"]:
                return self._parse_security_result(result["result"])
            else:
                return []
        
        except Exception as e:
            logger.error(f"Error analyzing security: {e}")
            return []
    
    # Helper methods for parsing results
    def _parse_completions(self, result: str) -> List[Dict[str, Any]]:
        """Parse completion results from agent response"""
        # This is a simplified parser - in practice, you'd want more sophisticated parsing
        completions = []
        lines = result.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                completions.append({
                    "label": line,
                    "kind": 1,  # Text completion
                    "detail": "AI-generated completion",
                    "insertText": line
                })
        
        return completions[:10]  # Limit to 10 completions
    
    def _parse_code_actions(self, result: str) -> List[Dict[str, Any]]:
        """Parse code actions from agent response"""
        actions = []
        
        # Simple parsing - look for action suggestions
        if "refactor" in result.lower():
            actions.append({
                "title": "Refactor Code",
                "kind": "refactor",
                "command": "refactor"
            })
        
        if "optimize" in result.lower():
            actions.append({
                "title": "Optimize Code",
                "kind": "refactor",
                "command": "optimize"
            })
        
        if "fix" in result.lower() or "bug" in result.lower():
            actions.append({
                "title": "Fix Issues",
                "kind": "quickfix",
                "command": "fix"
            })
        
        return actions
    
    def _parse_analysis_result(self, result: str, language: str) -> Dict[str, Any]:
        """Parse analysis result from agent response"""
        return {
            "syntax_valid": True,
            "issues": [],
            "suggestions": [result],
            "language": language,
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_code_from_result(self, result: str, language: str) -> str:
        """Extract code from agent response"""
        # Look for code blocks
        if "```" in result:
            parts = result.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Odd indices are code blocks
                    if language in part or not part.strip().startswith(language):
                        return part.strip()
        
        return result
    
    def _parse_bug_detection_result(self, result: str) -> List[Dict[str, Any]]:
        """Parse bug detection results"""
        bugs = []
        lines = result.split('\n')
        
        for line in lines:
            if "bug" in line.lower() or "issue" in line.lower() or "error" in line.lower():
                bugs.append({
                    "type": "bug",
                    "message": line.strip(),
                    "severity": "medium"
                })
        
        return bugs
    
    def _parse_performance_result(self, result: str) -> Dict[str, Any]:
        """Parse performance analysis results"""
        return {
            "complexity": "O(n)",  # Default
            "suggestions": [result],
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_security_result(self, result: str) -> List[Dict[str, Any]]:
        """Parse security analysis results"""
        issues = []
        lines = result.split('\n')
        
        for line in lines:
            if "security" in line.lower() or "vulnerability" in line.lower():
                issues.append({
                    "type": "security",
                    "message": line.strip(),
                    "severity": "medium"
                })
        
        return issues