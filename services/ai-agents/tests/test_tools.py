"""
Unit tests for tools in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from app.tools import ToolManager, SearchContentTool, GenerateTextTool, WebSearchTool, AnalyzeImageTool


class TestToolManager:
    """Test cases for ToolManager"""

    @pytest.fixture
    def tool_manager(self):
        """Create ToolManager instance for testing"""
        return ToolManager()

    @pytest.mark.asyncio
    async def test_tool_manager_initialization(self, tool_manager):
        """Test ToolManager initialization"""
        assert tool_manager is not None
        assert hasattr(tool_manager, 'tools')
        assert hasattr(tool_manager, 'tool_registry')

    @pytest.mark.asyncio
    async def test_register_tool_success(self, tool_manager):
        """Test successful tool registration"""
        # Create mock tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool for unit testing"

        # Test tool registration
        result = await tool_manager.register_tool(mock_tool)

        # Verify result
        assert result["success"] is True
        assert "test_tool" in tool_manager.tools

    @pytest.mark.asyncio
    async def test_get_tool_success(self, tool_manager):
        """Test successful tool retrieval"""
        # Register a tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        tool_manager.tools["test_tool"] = mock_tool

        # Test tool retrieval
        result = await tool_manager.get_tool("test_tool")

        # Verify result
        assert result == mock_tool

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, tool_manager):
        """Test tool retrieval for non-existent tool"""
        # Test tool retrieval
        result = await tool_manager.get_tool("nonexistent_tool")

        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_list_tools_success(self, tool_manager):
        """Test successful tool listing"""
        # Register multiple tools
        tool1 = Mock()
        tool1.name = "tool1"
        tool1.description = "Tool 1"
        tool2 = Mock()
        tool2.name = "tool2"
        tool2.description = "Tool 2"
        
        tool_manager.tools = {"tool1": tool1, "tool2": tool2}

        # Test tool listing
        result = await tool_manager.list_tools()

        # Verify result
        assert len(result) == 2
        assert "tool1" in result
        assert "tool2" in result

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, tool_manager):
        """Test successful tool execution"""
        # Register a tool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.execute.return_value = {"success": True, "result": "Tool executed"}
        tool_manager.tools["test_tool"] = mock_tool

        # Test tool execution
        result = await tool_manager.execute_tool("test_tool", {"param": "value"})

        # Verify result
        assert result["success"] is True
        assert result["result"] == "Tool executed"
        mock_tool.execute.assert_called_once_with({"param": "value"})

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, tool_manager):
        """Test tool execution for non-existent tool"""
        # Test tool execution
        result = await tool_manager.execute_tool("nonexistent_tool", {})

        # Verify result
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_validate_tool_parameters_success(self, tool_manager):
        """Test successful tool parameter validation"""
        # Register a tool with schema
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.parameters_schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            },
            "required": ["param1"]
        }
        tool_manager.tools["test_tool"] = mock_tool

        # Test parameter validation
        result = await tool_manager.validate_tool_parameters(
            "test_tool",
            {"param1": "value", "param2": 123}
        )

        # Verify result
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_tool_parameters_invalid(self, tool_manager):
        """Test tool parameter validation with invalid parameters"""
        # Register a tool with schema
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.parameters_schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            },
            "required": ["param1"]
        }
        tool_manager.tools["test_tool"] = mock_tool

        # Test parameter validation
        result = await tool_manager.validate_tool_parameters(
            "test_tool",
            {"param2": "value"}  # Missing required param1
        )

        # Verify result
        assert result["valid"] is False
        assert len(result["errors"]) > 0


class TestSearchContentTool:
    """Test cases for SearchContentTool"""

    @pytest.fixture
    def search_tool(self, mock_http_client):
        """Create SearchContentTool instance for testing"""
        return SearchContentTool(mock_http_client)

    @pytest.mark.asyncio
    async def test_search_content_tool_initialization(self, search_tool):
        """Test SearchContentTool initialization"""
        assert search_tool is not None
        assert search_tool.name == "search_content"
        assert hasattr(search_tool, 'http_client')

    @pytest.mark.asyncio
    async def test_execute_search_success(self, search_tool, mock_http_client):
        """Test successful search execution"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "results": [
                {"content": "Test result 1", "score": 0.95},
                {"content": "Test result 2", "score": 0.87}
            ]
        }
        mock_http_client.post.return_value = mock_response

        # Test search execution
        result = await search_tool.execute({
            "query": "test query",
            "content_types": ["text"],
            "limit": 10
        })

        # Verify result
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["content"] == "Test result 1"

    @pytest.mark.asyncio
    async def test_execute_search_failure(self, search_tool, mock_http_client):
        """Test search execution failure"""
        # Mock HTTP error
        mock_http_client.post.side_effect = Exception("HTTP error")

        # Test search execution
        result = await search_tool.execute({
            "query": "test query",
            "content_types": ["text"],
            "limit": 10
        })

        # Verify result
        assert result["success"] is False
        assert "error" in result


class TestGenerateTextTool:
    """Test cases for GenerateTextTool"""

    @pytest.fixture
    def generate_tool(self, mock_http_client):
        """Create GenerateTextTool instance for testing"""
        return GenerateTextTool(mock_http_client)

    @pytest.mark.asyncio
    async def test_generate_text_tool_initialization(self, generate_tool):
        """Test GenerateTextTool initialization"""
        assert generate_tool is not None
        assert generate_tool.name == "generate_text"
        assert hasattr(generate_tool, 'http_client')

    @pytest.mark.asyncio
    async def test_execute_generate_success(self, generate_tool, mock_http_client):
        """Test successful text generation"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "generated_text": "This is generated text based on the prompt."
        }
        mock_http_client.post.return_value = mock_response

        # Test text generation
        result = await generate_tool.execute({
            "prompt": "Generate a test response",
            "max_tokens": 100,
            "temperature": 0.7
        })

        # Verify result
        assert result["success"] is True
        assert "generated_text" in result
        assert result["generated_text"] == "This is generated text based on the prompt."

    @pytest.mark.asyncio
    async def test_execute_generate_failure(self, generate_tool, mock_http_client):
        """Test text generation failure"""
        # Mock HTTP error
        mock_http_client.post.side_effect = Exception("HTTP error")

        # Test text generation
        result = await generate_tool.execute({
            "prompt": "Generate a test response",
            "max_tokens": 100
        })

        # Verify result
        assert result["success"] is False
        assert "error" in result


class TestWebSearchTool:
    """Test cases for WebSearchTool"""

    @pytest.fixture
    def web_search_tool(self, mock_http_client):
        """Create WebSearchTool instance for testing"""
        return WebSearchTool(mock_http_client)

    @pytest.mark.asyncio
    async def test_web_search_tool_initialization(self, web_search_tool):
        """Test WebSearchTool initialization"""
        assert web_search_tool is not None
        assert web_search_tool.name == "web_search"
        assert hasattr(web_search_tool, 'http_client')

    @pytest.mark.asyncio
    async def test_execute_web_search_success(self, web_search_tool, mock_http_client):
        """Test successful web search"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "results": [
                {"title": "Test Result 1", "url": "https://example.com/1", "snippet": "Snippet 1"},
                {"title": "Test Result 2", "url": "https://example.com/2", "snippet": "Snippet 2"}
            ]
        }
        mock_http_client.post.return_value = mock_response

        # Test web search
        result = await web_search_tool.execute({
            "query": "test search query",
            "limit": 5
        })

        # Verify result
        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["title"] == "Test Result 1"

    @pytest.mark.asyncio
    async def test_execute_web_search_failure(self, web_search_tool, mock_http_client):
        """Test web search failure"""
        # Mock HTTP error
        mock_http_client.post.side_effect = Exception("HTTP error")

        # Test web search
        result = await web_search_tool.execute({
            "query": "test search query",
            "limit": 5
        })

        # Verify result
        assert result["success"] is False
        assert "error" in result


class TestAnalyzeImageTool:
    """Test cases for AnalyzeImageTool"""

    @pytest.fixture
    def analyze_image_tool(self, mock_http_client):
        """Create AnalyzeImageTool instance for testing"""
        return AnalyzeImageTool(mock_http_client)

    @pytest.mark.asyncio
    async def test_analyze_image_tool_initialization(self, analyze_image_tool):
        """Test AnalyzeImageTool initialization"""
        assert analyze_image_tool is not None
        assert analyze_image_tool.name == "analyze_image"
        assert hasattr(analyze_image_tool, 'http_client')

    @pytest.mark.asyncio
    async def test_execute_analyze_image_success(self, analyze_image_tool, mock_http_client):
        """Test successful image analysis"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "analysis": {
                "caption": "A test image showing various objects",
                "objects": ["object1", "object2"],
                "confidence": 0.95
            }
        }
        mock_http_client.post.return_value = mock_response

        # Test image analysis
        result = await analyze_image_tool.execute({
            "image_data": "base64_encoded_image_data",
            "analysis_type": "full"
        })

        # Verify result
        assert result["success"] is True
        assert "analysis" in result
        assert result["analysis"]["caption"] == "A test image showing various objects"

    @pytest.mark.asyncio
    async def test_execute_analyze_image_failure(self, analyze_image_tool, mock_http_client):
        """Test image analysis failure"""
        # Mock HTTP error
        mock_http_client.post.side_effect = Exception("HTTP error")

        # Test image analysis
        result = await analyze_image_tool.execute({
            "image_data": "base64_encoded_image_data",
            "analysis_type": "full"
        })

        # Verify result
        assert result["success"] is False
        assert "error" in result
