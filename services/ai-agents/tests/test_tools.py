"""
Unit tests for Tools in ai-agents service
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import httpx

from app.tools import (
    ImageAnalysisTool, SearchTool, TextGenerationTool, 
    WebSearchTool, ToolRegistry
)


class TestImageAnalysisTool:
    """Test cases for ImageAnalysisTool"""

    @pytest.fixture
    def tool(self):
        """Create tool instance"""
        return ImageAnalysisTool()

    def test_tool_properties(self, tool):
        """Test tool basic properties"""
        assert tool.name == "analyze_image"
        assert "image" in tool.description.lower()
        assert tool.args_schema == tool.ImageAnalysisInput

    def test_input_schema(self, tool):
        """Test input schema validation"""
        # Test valid input
        valid_input = tool.ImageAnalysisInput(image_url="https://example.com/image.jpg")
        assert valid_input.image_url == "https://example.com/image.jpg"

        # Test required field
        with pytest.raises(ValueError):
            tool.ImageAnalysisInput()

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_analyze_image_from_url_success(self, mock_client_class, tool):
        """Test successful image analysis from URL"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock image download
        mock_img_response = Mock()
        mock_img_response.content = b"fake_image_data"
        mock_client.get.return_value = mock_img_response
        
        # Mock multimodal worker response
        mock_analysis_response = Mock()
        mock_analysis_response.json.return_value = {
            "success": True,
            "data": {
                "caption": "A beautiful landscape with mountains and trees"
            }
        }
        mock_client.post.return_value = mock_analysis_response

        # Test image analysis
        result = await tool._arun("https://example.com/image.jpg")

        # Verify result
        assert "Image analysis: A beautiful landscape with mountains and trees" in result

        # Verify HTTP calls
        mock_client.get.assert_called_once_with("https://example.com/image.jpg")
        mock_client.post.assert_called_once()
        post_call_args = mock_client.post.call_args
        assert "/api/v1/process/image" in post_call_args[0][0]

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    @patch('builtins.open', create=True)
    async def test_analyze_image_from_file_success(self, mock_open, mock_client_class, tool):
        """Test successful image analysis from file"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock file reading
        mock_file = Mock()
        mock_file.read.return_value = b"fake_image_data"
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Mock multimodal worker response
        mock_analysis_response = Mock()
        mock_analysis_response.json.return_value = {
            "success": True,
            "data": {
                "caption": "A portrait of a person"
            }
        }
        mock_client.post.return_value = mock_analysis_response

        # Test image analysis
        result = await tool._arun("/path/to/image.jpg")

        # Verify result
        assert "Image analysis: A portrait of a person" in result

        # Verify file was read
        mock_open.assert_called_once_with("/path/to/image.jpg", 'rb')

        # Verify HTTP call
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_analyze_image_failure(self, mock_client_class, tool):
        """Test image analysis failure"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock image download
        mock_img_response = Mock()
        mock_img_response.content = b"fake_image_data"
        mock_client.get.return_value = mock_img_response
        
        # Mock multimodal worker failure
        mock_analysis_response = Mock()
        mock_analysis_response.json.return_value = {
            "success": False,
            "error": "Image processing failed"
        }
        mock_client.post.return_value = mock_analysis_response

        # Test image analysis
        result = await tool._arun("https://example.com/image.jpg")

        # Verify error result
        assert "Image analysis failed: Image processing failed" in result

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_analyze_image_http_error(self, mock_client_class, tool):
        """Test image analysis with HTTP error"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock HTTP error
        mock_client.get.side_effect = httpx.HTTPError("Network error")

        # Test image analysis
        result = await tool._arun("https://example.com/image.jpg")

        # Verify error result
        assert "Error analyzing image: Network error" in result

    def test_sync_wrapper(self, tool):
        """Test synchronous wrapper"""
        with patch.object(tool, '_arun', return_value="Test result") as mock_arun:
            result = tool._run("https://example.com/image.jpg")
            assert result == "Test result"
            mock_arun.assert_called_once_with("https://example.com/image.jpg")


class TestSearchTool:
    """Test cases for SearchTool"""

    @pytest.fixture
    def tool(self):
        """Create tool instance"""
        return SearchTool()

    def test_tool_properties(self, tool):
        """Test tool basic properties"""
        assert tool.name == "search_content"
        assert "search" in tool.description.lower()
        assert tool.args_schema == tool.SearchInput

    def test_input_schema(self, tool):
        """Test input schema validation"""
        # Test valid input with defaults
        valid_input = tool.SearchInput(query="test query")
        assert valid_input.query == "test query"
        assert valid_input.modalities == ["text", "image", "video"]
        assert valid_input.limit == 5

        # Test custom input
        custom_input = tool.SearchInput(
            query="test query",
            modalities=["text"],
            limit=10
        )
        assert custom_input.query == "test query"
        assert custom_input.modalities == ["text"]
        assert custom_input.limit == 10

        # Test required field
        with pytest.raises(ValueError):
            tool.SearchInput()

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_search_content_success(self, mock_client_class, tool):
        """Test successful content search"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock search response
        mock_search_response = Mock()
        mock_search_response.json.return_value = {
            "results": [
                {
                    "content": "First search result",
                    "filename": "doc1.txt",
                    "score": 0.95
                },
                {
                    "content": "Second search result",
                    "filename": "doc2.txt",
                    "score": 0.87
                }
            ]
        }
        mock_client.post.return_value = mock_search_response

        # Test content search
        result = await tool._arun("test query", ["text"], 5)

        # Verify result
        assert "Search results for 'test query':" in result
        assert "First search result" in result
        assert "Second search result" in result
        assert "doc1.txt" in result
        assert "doc2.txt" in result
        assert "0.95" in result
        assert "0.87" in result

        # Verify HTTP call
        mock_client.post.assert_called_once()
        post_call_args = mock_client.post.call_args
        assert "/api/v1/search" in post_call_args[0][0]
        assert post_call_args[1]["json"]["query"] == "test query"
        assert post_call_args[1]["json"]["modalities"] == ["text"]
        assert post_call_args[1]["json"]["limit"] == 5

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_search_content_no_results(self, mock_client_class, tool):
        """Test content search with no results"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock empty search response
        mock_search_response = Mock()
        mock_search_response.json.return_value = {"results": []}
        mock_client.post.return_value = mock_search_response

        # Test content search
        result = await tool._arun("test query")

        # Verify result
        assert "No results found for query: test query" in result

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_search_content_with_defaults(self, mock_client_class, tool):
        """Test content search with default parameters"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock search response
        mock_search_response = Mock()
        mock_search_response.json.return_value = {"results": []}
        mock_client.post.return_value = mock_search_response

        # Test content search with minimal parameters
        result = await tool._arun("test query")

        # Verify HTTP call with defaults
        mock_client.post.assert_called_once()
        post_call_args = mock_client.post.call_args
        assert post_call_args[1]["json"]["modalities"] == ["text", "image", "video"]
        assert post_call_args[1]["json"]["limit"] == 5

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_search_content_http_error(self, mock_client_class, tool):
        """Test content search with HTTP error"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock HTTP error
        mock_client.post.side_effect = httpx.HTTPError("Network error")

        # Test content search
        result = await tool._arun("test query")

        # Verify error result
        assert "Error searching content: Network error" in result

    def test_sync_wrapper(self, tool):
        """Test synchronous wrapper"""
        with patch.object(tool, '_arun', return_value="Search results") as mock_arun:
            result = tool._run("test query", ["text"], 5)
            assert result == "Search results"
            mock_arun.assert_called_once_with("test query", ["text"], 5)


class TestTextGenerationTool:
    """Test cases for TextGenerationTool"""

    @pytest.fixture
    def tool(self):
        """Create tool instance"""
        return TextGenerationTool()

    def test_tool_properties(self, tool):
        """Test tool basic properties"""
        assert tool.name == "generate_text"
        assert "generate" in tool.description.lower()
        assert tool.args_schema == tool.TextGenerationInput

    def test_input_schema(self, tool):
        """Test input schema validation"""
        # Test valid input with defaults
        valid_input = tool.TextGenerationInput(prompt="Generate text")
        assert valid_input.prompt == "Generate text"
        assert valid_input.max_tokens == 200

        # Test custom input
        custom_input = tool.TextGenerationInput(
            prompt="Generate text",
            max_tokens=500
        )
        assert custom_input.prompt == "Generate text"
        assert custom_input.max_tokens == 500

        # Test required field
        with pytest.raises(ValueError):
            tool.TextGenerationInput()

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_generate_text_success(self, mock_client_class, tool):
        """Test successful text generation"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is the generated text response."
                    }
                }
            ]
        }
        mock_client.post.return_value = mock_llm_response

        # Test text generation
        result = await tool._arun("Generate a story about a cat", 300)

        # Verify result
        assert result == "This is the generated text response."

        # Verify HTTP call
        mock_client.post.assert_called_once()
        post_call_args = mock_client.post.call_args
        assert "/chat/completions" in post_call_args[0][0]
        assert post_call_args[1]["json"]["messages"][0]["content"] == "Generate a story about a cat"
        assert post_call_args[1]["json"]["max_tokens"] == 300

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_generate_text_no_response(self, mock_client_class, tool):
        """Test text generation with no response"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock LLM response with no choices
        mock_llm_response = Mock()
        mock_llm_response.json.return_value = {"choices": []}
        mock_client.post.return_value = mock_llm_response

        # Test text generation
        result = await tool._arun("Generate text")

        # Verify result
        assert result == "No response generated"

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_generate_text_with_defaults(self, mock_client_class, tool):
        """Test text generation with default parameters"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text"}}]
        }
        mock_client.post.return_value = mock_llm_response

        # Test text generation with minimal parameters
        result = await tool._arun("Generate text")

        # Verify HTTP call with defaults
        mock_client.post.assert_called_once()
        post_call_args = mock_client.post.call_args
        assert post_call_args[1]["json"]["max_tokens"] == 200

    @pytest.mark.asyncio
    @patch('app.tools.httpx.AsyncClient')
    async def test_generate_text_http_error(self, mock_client_class, tool):
        """Test text generation with HTTP error"""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock HTTP error
        mock_client.post.side_effect = httpx.HTTPError("LLM service error")

        # Test text generation
        result = await tool._arun("Generate text")

        # Verify error result
        assert "Error generating text: LLM service error" in result

    def test_sync_wrapper(self, tool):
        """Test synchronous wrapper"""
        with patch.object(tool, '_arun', return_value="Generated text") as mock_arun:
            result = tool._run("Generate text", 200)
            assert result == "Generated text"
            mock_arun.assert_called_once_with("Generate text", 200)


class TestWebSearchTool:
    """Test cases for WebSearchTool"""

    @pytest.fixture
    def tool(self):
        """Create tool instance"""
        return WebSearchTool()

    def test_tool_properties(self, tool):
        """Test tool basic properties"""
        assert tool.name == "web_search"
        assert "web" in tool.description.lower()
        assert tool.args_schema == tool.WebSearchInput

    def test_input_schema(self, tool):
        """Test input schema validation"""
        # Test valid input
        valid_input = tool.WebSearchInput(query="test query")
        assert valid_input.query == "test query"

        # Test required field
        with pytest.raises(ValueError):
            tool.WebSearchInput()

    def test_web_search_placeholder(self, tool):
        """Test web search placeholder implementation"""
        result = tool._run("test query")
        
        # Verify placeholder response
        assert "Web search for 'test query'" in result
        assert "Feature coming soon!" in result
        assert "search_content" in result

    @pytest.mark.asyncio
    async def test_web_search_async_wrapper(self, tool):
        """Test web search async wrapper"""
        result = await tool._arun("test query")
        
        # Verify same result as sync version
        assert "Web search for 'test query'" in result
        assert "Feature coming soon!" in result


class TestToolRegistry:
    """Test cases for ToolRegistry"""

    @pytest.fixture
    def registry(self):
        """Create tool registry instance"""
        return ToolRegistry()

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_initialize_success(self, mock_settings, registry):
        """Test successful tool registry initialization"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Test initialization
        await registry.initialize()

        # Verify tools were registered
        assert "analyze_image" in registry.tools
        assert "search_content" in registry.tools
        assert "generate_text" in registry.tools
        assert "web_search" in registry.tools

        # Verify tool types
        assert isinstance(registry.tools["analyze_image"], ImageAnalysisTool)
        assert isinstance(registry.tools["search_content"], SearchTool)
        assert isinstance(registry.tools["generate_text"], TextGenerationTool)
        assert isinstance(registry.tools["web_search"], WebSearchTool)

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_initialize_without_web_search(self, mock_settings, registry):
        """Test tool registry initialization without web search"""
        # Setup settings
        mock_settings.enable_web_search = False

        # Test initialization
        await registry.initialize()

        # Verify tools were registered
        assert "analyze_image" in registry.tools
        assert "search_content" in registry.tools
        assert "generate_text" in registry.tools
        assert "web_search" not in registry.tools

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_initialize_failure(self, mock_settings, registry):
        """Test tool registry initialization failure"""
        # Setup settings to raise exception
        mock_settings.enable_web_search = True
        mock_settings.side_effect = Exception("Settings error")

        # Test initialization should raise exception
        with pytest.raises(Exception, match="Settings error"):
            await registry.initialize()

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_get_tools_all(self, mock_settings, registry):
        """Test getting all tools"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Initialize registry
        await registry.initialize()

        # Test getting all tools
        tools = await registry.get_tools()

        # Verify all tools returned
        assert len(tools) == 4
        tool_names = [tool.name for tool in tools]
        assert "analyze_image" in tool_names
        assert "search_content" in tool_names
        assert "generate_text" in tool_names
        assert "web_search" in tool_names

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_get_tools_specific(self, mock_settings, registry):
        """Test getting specific tools"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Initialize registry
        await registry.initialize()

        # Test getting specific tools
        tools = await registry.get_tools(["analyze_image", "search_content"])

        # Verify specific tools returned
        assert len(tools) == 2
        tool_names = [tool.name for tool in tools]
        assert "analyze_image" in tool_names
        assert "search_content" in tool_names
        assert "generate_text" not in tool_names

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_get_tools_nonexistent(self, mock_settings, registry):
        """Test getting non-existent tools"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Initialize registry
        await registry.initialize()

        # Test getting non-existent tools
        tools = await registry.get_tools(["nonexistent_tool"])

        # Verify empty list returned
        assert tools == []

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_list_available_tools(self, mock_settings, registry):
        """Test listing available tools"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Initialize registry
        await registry.initialize()

        # Test listing tools
        tools = await registry.list_available_tools()

        # Verify tools listed
        assert "analyze_image" in tools
        assert "search_content" in tools
        assert "generate_text" in tools
        assert "web_search" in tools

        # Verify descriptions
        assert "image" in tools["analyze_image"].lower()
        assert "search" in tools["search_content"].lower()
        assert "generate" in tools["generate_text"].lower()
        assert "web" in tools["web_search"].lower()

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_get_tools_empty_list(self, mock_settings, registry):
        """Test getting tools with empty list"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Initialize registry
        await registry.initialize()

        # Test getting tools with empty list
        tools = await registry.get_tools([])

        # Verify empty list returned
        assert tools == []

    @pytest.mark.asyncio
    @patch('app.tools.settings')
    async def test_get_tools_mixed_existent_nonexistent(self, mock_settings, registry):
        """Test getting mix of existent and non-existent tools"""
        # Setup settings
        mock_settings.enable_web_search = True

        # Initialize registry
        await registry.initialize()

        # Test getting mixed tools
        tools = await registry.get_tools(["analyze_image", "nonexistent_tool", "search_content"])

        # Verify only existent tools returned
        assert len(tools) == 2
        tool_names = [tool.name for tool in tools]
        assert "analyze_image" in tool_names
        assert "search_content" in tool_names
        assert "nonexistent_tool" not in tool_names