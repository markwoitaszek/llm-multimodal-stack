"""
Code analyzer for IDE Bridge Service
Provides syntax analysis, symbol resolution, and basic language features
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SymbolKind(Enum):
    """LSP symbol kinds"""
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    OBJECT = 19
    KEY = 20
    NULL = 21
    ENUM_MEMBER = 22
    STRUCT = 23
    EVENT = 24
    OPERATOR = 25
    TYPE_PARAMETER = 26

@dataclass
class Symbol:
    """Code symbol representation"""
    name: str
    kind: SymbolKind
    location: Dict[str, Any]
    detail: Optional[str] = None
    children: Optional[List['Symbol']] = None

@dataclass
class Completion:
    """Code completion item"""
    label: str
    kind: int
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insertText: Optional[str] = None

class CodeAnalyzer:
    """Code analyzer for multiple programming languages"""
    
    def __init__(self):
        self.language_parsers = {
            "python": PythonParser(),
            "javascript": JavaScriptParser(),
            "typescript": TypeScriptParser(),
            "go": GoParser(),
            "rust": RustParser(),
            "java": JavaParser(),
            "cpp": CppParser(),
            "c": CParser()
        }
    
    async def initialize(self):
        """Initialize the code analyzer"""
        logger.info("Code analyzer initialized")
    
    async def analyze(self, code: str, language: str, file_path: str = None) -> Dict[str, Any]:
        """Analyze code for syntax and semantic information"""
        parser = self.language_parsers.get(language.lower())
        if not parser:
            return {
                "syntax_valid": True,
                "language": language,
                "issues": [],
                "suggestions": []
            }
        
        try:
            analysis = await parser.analyze(code, file_path)
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing {language} code: {e}")
            return {
                "syntax_valid": False,
                "language": language,
                "issues": [{"type": "error", "message": str(e)}],
                "suggestions": []
            }
    
    async def get_completions(self, code: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get code completions at the specified position"""
        # Determine language from code context
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return []
        
        try:
            completions = await parser.get_completions(code, line, character)
            return completions
        except Exception as e:
            logger.error(f"Error getting completions: {e}")
            return []
    
    async def get_hover_info(self, code: str, line: int, character: int) -> Optional[str]:
        """Get hover information at the specified position"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return None
        
        try:
            hover_info = await parser.get_hover_info(code, line, character)
            return hover_info
        except Exception as e:
            logger.error(f"Error getting hover info: {e}")
            return None
    
    async def get_definition(self, code: str, line: int, character: int, uri: str) -> Optional[Dict[str, Any]]:
        """Get definition location for symbol at position"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return None
        
        try:
            definition = await parser.get_definition(code, line, character, uri)
            return definition
        except Exception as e:
            logger.error(f"Error getting definition: {e}")
            return None
    
    async def get_references(self, code: str, line: int, character: int, uri: str) -> List[Dict[str, Any]]:
        """Get references for symbol at position"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return []
        
        try:
            references = await parser.get_references(code, line, character, uri)
            return references
        except Exception as e:
            logger.error(f"Error getting references: {e}")
            return []
    
    async def get_document_symbols(self, code: str, uri: str) -> List[Dict[str, Any]]:
        """Get document symbols"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return []
        
        try:
            symbols = await parser.get_document_symbols(code, uri)
            return symbols
        except Exception as e:
            logger.error(f"Error getting document symbols: {e}")
            return []
    
    async def get_code_actions(self, code: str, range: Dict[str, Any], uri: str) -> List[Dict[str, Any]]:
        """Get code actions for the specified range"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return []
        
        try:
            actions = await parser.get_code_actions(code, range, uri)
            return actions
        except Exception as e:
            logger.error(f"Error getting code actions: {e}")
            return []
    
    async def format_document(self, code: str, uri: str) -> List[Dict[str, Any]]:
        """Format document"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return []
        
        try:
            edits = await parser.format_document(code, uri)
            return edits
        except Exception as e:
            logger.error(f"Error formatting document: {e}")
            return []
    
    async def rename_symbol(self, code: str, line: int, character: int, new_name: str, uri: str) -> Dict[str, Any]:
        """Rename symbol and return changes"""
        language = self._detect_language(code)
        parser = self.language_parsers.get(language)
        
        if not parser:
            return {}
        
        try:
            changes = await parser.rename_symbol(code, line, character, new_name, uri)
            return changes
        except Exception as e:
            logger.error(f"Error renaming symbol: {e}")
            return {}
    
    async def get_workspace_symbols(self, query: str) -> List[Dict[str, Any]]:
        """Get workspace symbols matching query"""
        # This would typically search across multiple files
        # For now, return empty list
        return []
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        # Simple language detection based on keywords and patterns
        if re.search(r'\bdef\s+\w+\(', code) or re.search(r'\bclass\s+\w+', code):
            return "python"
        elif re.search(r'\bfunction\s+\w+\(', code) or re.search(r'var\s+\w+\s*=', code):
            return "javascript"
        elif re.search(r'\binterface\s+\w+', code) or re.search(r':\s*\w+', code):
            return "typescript"
        elif re.search(r'\bfunc\s+\w+\(', code) or re.search(r'\bpackage\s+\w+', code):
            return "go"
        elif re.search(r'\bfn\s+\w+\(', code) or re.search(r'\bstruct\s+\w+', code):
            return "rust"
        elif re.search(r'\bpublic\s+class\s+\w+', code) or re.search(r'\bimport\s+java\.', code):
            return "java"
        elif re.search(r'#include\s*<', code) or re.search(r'\bnamespace\s+\w+', code):
            return "cpp"
        elif re.search(r'#include\s*<', code) and not re.search(r'\bnamespace\s+\w+', code):
            return "c"
        else:
            return "python"  # Default fallback

class BaseParser:
    """Base parser for programming languages"""
    
    async def analyze(self, code: str, file_path: str = None) -> Dict[str, Any]:
        """Analyze code for syntax and semantic information"""
        return {
            "syntax_valid": True,
            "language": "unknown",
            "issues": [],
            "suggestions": []
        }
    
    async def get_completions(self, code: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get code completions"""
        return []
    
    async def get_hover_info(self, code: str, line: int, character: int) -> Optional[str]:
        """Get hover information"""
        return None
    
    async def get_definition(self, code: str, line: int, character: int, uri: str) -> Optional[Dict[str, Any]]:
        """Get definition location"""
        return None
    
    async def get_references(self, code: str, line: int, character: int, uri: str) -> List[Dict[str, Any]]:
        """Get references"""
        return []
    
    async def get_document_symbols(self, code: str, uri: str) -> List[Dict[str, Any]]:
        """Get document symbols"""
        return []
    
    async def get_code_actions(self, code: str, range: Dict[str, Any], uri: str) -> List[Dict[str, Any]]:
        """Get code actions"""
        return []
    
    async def format_document(self, code: str, uri: str) -> List[Dict[str, Any]]:
        """Format document"""
        return []
    
    async def rename_symbol(self, code: str, line: int, character: int, new_name: str, uri: str) -> Dict[str, Any]:
        """Rename symbol"""
        return {}

class PythonParser(BaseParser):
    """Python code parser"""
    
    async def analyze(self, code: str, file_path: str = None) -> Dict[str, Any]:
        """Analyze Python code"""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Check for common Python issues
            if line.strip().startswith('import ') and ' as ' not in line:
                # Check for unused imports (simplified)
                pass
            
            # Check for missing docstrings in functions
            if re.match(r'\s*def\s+\w+\(', line):
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""'):
                    suggestions.append({
                        "line": i + 1,
                        "message": "Consider adding a docstring",
                        "type": "suggestion"
                    })
        
        return {
            "syntax_valid": True,
            "language": "python",
            "issues": issues,
            "suggestions": suggestions
        }
    
    async def get_completions(self, code: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get Python completions"""
        completions = []
        
        # Basic Python keywords and built-ins
        python_keywords = [
            "def", "class", "if", "else", "elif", "for", "while", "try", "except",
            "finally", "with", "import", "from", "as", "return", "yield", "lambda",
            "and", "or", "not", "in", "is", "True", "False", "None"
        ]
        
        python_builtins = [
            "print", "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "range", "enumerate", "zip", "map", "filter", "sorted", "reversed",
            "open", "file", "input", "raw_input", "type", "isinstance", "hasattr",
            "getattr", "setattr", "delattr", "dir", "vars", "locals", "globals"
        ]
        
        # Get current line context
        lines = code.split('\n')
        if line < len(lines):
            current_line = lines[line][:character]
            
            # Simple completion based on context
            if current_line.endswith('.'):
                # Object method completion
                completions.extend([
                    {"label": "append", "kind": 2, "detail": "list method"},
                    {"label": "extend", "kind": 2, "detail": "list method"},
                    {"label": "insert", "kind": 2, "detail": "list method"},
                    {"label": "remove", "kind": 2, "detail": "list method"},
                    {"label": "pop", "kind": 2, "detail": "list method"},
                    {"label": "index", "kind": 2, "detail": "list method"},
                    {"label": "count", "kind": 2, "detail": "list method"},
                    {"label": "sort", "kind": 2, "detail": "list method"},
                    {"label": "reverse", "kind": 2, "detail": "list method"}
                ])
            else:
                # General completions
                for keyword in python_keywords:
                    completions.append({
                        "label": keyword,
                        "kind": 14,  # Keyword
                        "detail": "Python keyword"
                    })
                
                for builtin in python_builtins:
                    completions.append({
                        "label": builtin,
                        "kind": 3,  # Function
                        "detail": "Python built-in"
                    })
        
        return completions[:20]  # Limit completions
    
    async def get_document_symbols(self, code: str, uri: str) -> List[Dict[str, Any]]:
        """Get Python document symbols"""
        symbols = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Find function definitions
            func_match = re.match(r'\s*def\s+(\w+)\s*\(', line)
            if func_match:
                symbols.append({
                    "name": func_match.group(1),
                    "kind": 12,  # Function
                    "location": {
                        "uri": uri,
                        "range": {
                            "start": {"line": i, "character": 0},
                            "end": {"line": i, "character": len(line)}
                        }
                    }
                })
            
            # Find class definitions
            class_match = re.match(r'\s*class\s+(\w+)', line)
            if class_match:
                symbols.append({
                    "name": class_match.group(1),
                    "kind": 5,  # Class
                    "location": {
                        "uri": uri,
                        "range": {
                            "start": {"line": i, "character": 0},
                            "end": {"line": i, "character": len(line)}
                        }
                    }
                })
        
        return symbols

class JavaScriptParser(BaseParser):
    """JavaScript code parser"""
    
    async def analyze(self, code: str, file_path: str = None) -> Dict[str, Any]:
        """Analyze JavaScript code"""
        issues = []
        suggestions = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Check for common JavaScript issues
            if '==' in line and '===' not in line:
                suggestions.append({
                    "line": i + 1,
                    "message": "Consider using === instead of ==",
                    "type": "suggestion"
                })
        
        return {
            "syntax_valid": True,
            "language": "javascript",
            "issues": issues,
            "suggestions": suggestions
        }
    
    async def get_completions(self, code: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get JavaScript completions"""
        completions = []
        
        # JavaScript keywords and built-ins
        js_keywords = [
            "function", "var", "let", "const", "if", "else", "for", "while", "do",
            "switch", "case", "default", "break", "continue", "return", "try",
            "catch", "finally", "throw", "new", "this", "typeof", "instanceof",
            "true", "false", "null", "undefined"
        ]
        
        js_builtins = [
            "console", "document", "window", "Array", "Object", "String", "Number",
            "Boolean", "Date", "Math", "JSON", "Promise", "setTimeout", "setInterval"
        ]
        
        for keyword in js_keywords:
            completions.append({
                "label": keyword,
                "kind": 14,  # Keyword
                "detail": "JavaScript keyword"
            })
        
        for builtin in js_builtins:
            completions.append({
                "label": builtin,
                "kind": 3,  # Function
                "detail": "JavaScript built-in"
            })
        
        return completions[:20]
    
    async def get_document_symbols(self, code: str, uri: str) -> List[Dict[str, Any]]:
        """Get JavaScript document symbols"""
        symbols = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            # Find function declarations
            func_match = re.match(r'\s*function\s+(\w+)\s*\(', line)
            if func_match:
                symbols.append({
                    "name": func_match.group(1),
                    "kind": 12,  # Function
                    "location": {
                        "uri": uri,
                        "range": {
                            "start": {"line": i, "character": 0},
                            "end": {"line": i, "character": len(line)}
                        }
                    }
                })
            
            # Find variable declarations
            var_match = re.match(r'\s*(var|let|const)\s+(\w+)', line)
            if var_match:
                symbols.append({
                    "name": var_match.group(2),
                    "kind": 13,  # Variable
                    "location": {
                        "uri": uri,
                        "range": {
                            "start": {"line": i, "character": 0},
                            "end": {"line": i, "character": len(line)}
                        }
                    }
                })
        
        return symbols

# Additional parsers for other languages
class TypeScriptParser(JavaScriptParser):
    """TypeScript parser (extends JavaScript parser)"""
    pass

class GoParser(BaseParser):
    """Go code parser"""
    pass

class RustParser(BaseParser):
    """Rust code parser"""
    pass

class JavaParser(BaseParser):
    """Java code parser"""
    pass

class CppParser(BaseParser):
    """C++ code parser"""
    pass

class CParser(BaseParser):
    """C code parser"""
    pass