"""
Tool registry for AI agents - integrates with multimodal stack capabilities
"""
import logging
from typing import List, Dict, Any, Optional
import httpx
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from .config import settings

logger = logging.getLogger(__name__)

class ImageAnalysisTool(BaseTool):
    """Tool for analyzing images using the multimodal worker"""
    name: str = "analyze_image"
    description: str = "Analyze an image and generate a detailed caption and features"
    
    class ImageAnalysisInput(BaseModel):
        image_url: str = Field(description="URL or path to the image to analyze")
        
    args_schema: type = ImageAnalysisInput
    
    async def _arun(self, image_url: str) -> str:
        """Analyze image asynchronously"""
        try:
            async with httpx.AsyncClient() as client:
                # Download image if URL
                if image_url.startswith('http'):
                    img_response = await client.get(image_url)
                    img_response.raise_for_status()
                    image_data = img_response.content
                else:
                    with open(image_url, 'rb') as f:
                        image_data = f.read()
                
                # Send to multimodal worker
                files = {'file': ('image.jpg', image_data, 'image/jpeg')}
                data = {'document_name': 'agent_analysis.jpg'}
                
                response = await client.post(
                    f"{settings.multimodal_worker_url}/api/v1/process/image",
                    files=files,
                    data=data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get("success"):
                    return f"Image analysis: {result['data']['caption']}"
                else:
                    return f"Image analysis failed: {result.get('error', 'Unknown error')}"
                    
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    def _run(self, image_url: str) -> str:
        """Synchronous wrapper"""
        import asyncio
        return asyncio.run(self._arun(image_url))

class SearchTool(BaseTool):
    """Tool for searching content using the retrieval proxy"""
    name: str = "search_content"
    description: str = "Search for relevant content across text, images, and videos"
    
    class SearchInput(BaseModel):
        query: str = Field(description="Search query")
        modalities: List[str] = Field(default=["text", "image", "video"], description="Content types to search")
        limit: int = Field(default=5, description="Maximum number of results")
        
    args_schema: type = SearchInput
    
    async def _arun(self, query: str, modalities: List[str] = None, limit: int = 5) -> str:
        """Search content asynchronously"""
        try:
            async with httpx.AsyncClient() as client:
                search_data = {
                    "query": query,
                    "modalities": modalities or ["text", "image", "video"],
                    "limit": limit
                }
                
                response = await client.post(
                    f"{settings.retrieval_proxy_url}/api/v1/search",
                    json=search_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("results"):
                    # Format search results
                    formatted_results = []
                    for item in result["results"][:limit]:
                        formatted_results.append(
                            f"- {item.get('content', 'No content')} "
                            f"(Source: {item.get('filename', 'Unknown')}, "
                            f"Score: {item.get('score', 0):.2f})"
                        )
                    
                    return f"Search results for '{query}':\n" + "\n".join(formatted_results)
                else:
                    return f"No results found for query: {query}"
                    
        except Exception as e:
            return f"Error searching content: {str(e)}"
    
    def _run(self, query: str, modalities: List[str] = None, limit: int = 5) -> str:
        """Synchronous wrapper"""
        import asyncio
        return asyncio.run(self._arun(query, modalities, limit))

class TextGenerationTool(BaseTool):
    """Tool for generating text using the LLM"""
    name: str = "generate_text"
    description: str = "Generate text, summaries, or creative content using the LLM"
    
    class TextGenerationInput(BaseModel):
        prompt: str = Field(description="Text generation prompt")
        max_tokens: int = Field(default=200, description="Maximum tokens to generate")
        
    args_schema: type = TextGenerationInput
    
    async def _arun(self, prompt: str, max_tokens: int = 200) -> str:
        """Generate text asynchronously"""
        try:
            async with httpx.AsyncClient() as client:
                completion_data = {
                    "model": settings.llm_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": settings.llm_temperature
                }
                
                response = await client.post(
                    f"{settings.llm_base_url}/chat/completions",
                    json=completion_data,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("choices"):
                    return result["choices"][0]["message"]["content"]
                else:
                    return "No response generated"
                    
        except Exception as e:
            return f"Error generating text: {str(e)}"
    
    def _run(self, prompt: str, max_tokens: int = 200) -> str:
        """Synchronous wrapper"""
        import asyncio
        return asyncio.run(self._arun(prompt, max_tokens))

class WebSearchTool(BaseTool):
    """Tool for web search (placeholder - would integrate with search API)"""
    name: str = "web_search"
    description: str = "Search the web for current information"
    
    class WebSearchInput(BaseModel):
        query: str = Field(description="Web search query")
        
    args_schema: type = WebSearchInput
    
    def _run(self, query: str) -> str:
        """Web search (placeholder implementation)"""
        # In a real implementation, this would integrate with:
        # - Google Search API
        # - Bing Search API  
        # - DuckDuckGo API
        # - Custom web scraping
        
        return f"Web search for '{query}' - Feature coming soon! Use search_content for local content."
    
    async def _arun(self, query: str) -> str:
        """Async wrapper"""
        return self._run(query)

class ToolRegistry:
    """Registry of available tools for agents"""
    
    def __init__(self):
        self.tools = {}
        
    async def initialize(self):
        """Initialize tool registry"""
        try:
            # Register available tools
            self.tools = {
                "analyze_image": ImageAnalysisTool(),
                "search_content": SearchTool(),
                "generate_text": TextGenerationTool(),
                "web_search": WebSearchTool() if settings.enable_web_search else None
            }
            
            # Remove None tools
            self.tools = {k: v for k, v in self.tools.items() if v is not None}
            
            logger.info(f"Tool registry initialized with {len(self.tools)} tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool registry: {e}")
            raise
    
    async def get_tools(self, tool_names: List[str] = None) -> List[BaseTool]:
        """Get tools by name"""
        if not tool_names:
            return list(self.tools.values())
        
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    async def list_available_tools(self) -> Dict[str, str]:
        """List all available tools with descriptions"""
        return {
            name: tool.description 
            for name, tool in self.tools.items()
        }
