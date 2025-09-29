#!/usr/bin/env python3
"""
Advanced Documentation Rendering and Navigation System
Part of Issue #71: Documentation Rendering & Navigation

This module provides a comprehensive documentation system with:
- Markdown to HTML rendering with syntax highlighting
- Advanced navigation and search capabilities
- Content management and organization
- Responsive design and user experience
- Integration with existing documentation structure
"""

import os
import re
import json
import yaml
import markdown
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentationItem:
    """Represents a single documentation item"""
    id: str
    title: str
    content: str
    type: str  # 'page', 'api', 'guide', 'example', 'reference'
    service: str  # 'all', 'litellm', 'multimodal-worker', 'retrieval-proxy', 'ai-agents'
    language: str  # 'all', 'python', 'javascript', 'bash', 'yaml'
    url: str
    last_modified: str
    tags: List[str]
    excerpt: str
    parent_id: Optional[str] = None
    children: List[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

@dataclass
class NavigationNode:
    """Represents a navigation node in the documentation tree"""
    id: str
    title: str
    url: str
    level: int
    children: List['NavigationNode'] = None
    parent: Optional['NavigationNode'] = None
    icon: str = ""
    description: str = ""

    def __post_init__(self):
        if self.children is None:
            self.children = []

class MarkdownRenderer:
    """Enhanced Markdown renderer with syntax highlighting and extensions"""
    
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=[
                'codehilite',
                'fenced_code',
                'tables',
                'toc',
                'attr_list',
                'def_list',
                'footnotes',
                'md_in_html',
                'nl2br',
                'sane_lists',
                'wikilinks',
                'admonition',
                'pymdownx.superfences',
                'pymdownx.tabbed',
                'pymdownx.emoji',
                'pymdownx.critic',
                'pymdownx.details',
                'pymdownx.inlinehilite',
                'pymdownx.keys',
                'pymdownx.magiclink',
                'pymdownx.mark',
                'pymdownx.smartsymbols',
                'pymdownx.superfences',
                'pymdownx.tilde',
                'pymdownx.caret',
                'pymdownx.tabbed',
                'pymdownx.tasklist',
                'pymdownx.tilde',
                'pymdownx.critic',
                'pymdownx.details',
                'pymdownx.inlinehilite',
                'pymdownx.keys',
                'pymdownx.magiclink',
                'pymdownx.mark',
                'pymdownx.smartsymbols',
                'pymdownx.superfences',
                'pymdownx.tilde',
                'pymdownx.caret',
                'pymdownx.tabbed',
                'pymdownx.tasklist'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True,
                    'guess_lang': True,
                    'linenums': True
                },
                'toc': {
                    'permalink': True,
                    'permalink_title': 'Link to this section'
                },
                'pymdownx.superfences': {
                    'custom_fences': [
                        {
                            'name': 'mermaid',
                            'class': 'mermaid',
                            'format': self._format_mermaid
                        }
                    ]
                }
            }
        )
    
    def _format_mermaid(self, source, language, css_class, options, md, **kwargs):
        """Format Mermaid diagrams"""
        return f'<div class="mermaid">{source}</div>'
    
    def render(self, content: str) -> str:
        """Render markdown content to HTML"""
        try:
            html = self.md.convert(content)
            return html
        except Exception as e:
            logger.error(f"Error rendering markdown: {e}")
            return f"<p>Error rendering content: {str(e)}</p>"

class DocumentationIndexer:
    """Indexes and manages documentation content"""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)
        self.items: Dict[str, DocumentationItem] = {}
        self.navigation: List[NavigationNode] = []
        self.search_index: Dict[str, List[str]] = {}
        self.renderer = MarkdownRenderer()
    
    async def build_index(self) -> None:
        """Build comprehensive documentation index"""
        logger.info("Building documentation index...")
        
        # Clear existing index
        self.items.clear()
        self.navigation.clear()
        self.search_index.clear()
        
        # Index all markdown files
        await self._index_markdown_files()
        
        # Index OpenAPI specifications
        await self._index_openapi_specs()
        
        # Build navigation structure
        await self._build_navigation()
        
        # Build search index
        await self._build_search_index()
        
        logger.info(f"Indexed {len(self.items)} documentation items")
    
    async def _index_markdown_files(self) -> None:
        """Index all markdown files in the documentation directory"""
        markdown_files = list(self.docs_dir.rglob("*.md"))
        
        for md_file in markdown_files:
            try:
                async with aiofiles.open(md_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Extract metadata from frontmatter
                metadata, content = self._parse_frontmatter(content)
                
                # Generate item ID
                item_id = str(md_file.relative_to(self.docs_dir)).replace('/', '_').replace('.md', '')
                
                # Determine item type and service
                item_type, service = self._classify_content(md_file, content)
                
                # Generate excerpt
                excerpt = self._generate_excerpt(content)
                
                # Create documentation item
                item = DocumentationItem(
                    id=item_id,
                    title=metadata.get('title', md_file.stem.replace('_', ' ').title()),
                    content=content,
                    type=item_type,
                    service=service,
                    language=metadata.get('language', 'all'),
                    url=str(md_file.relative_to(self.docs_dir)),
                    last_modified=datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
                    tags=metadata.get('tags', []),
                    excerpt=excerpt
                )
                
                self.items[item_id] = item
                
            except Exception as e:
                logger.error(f"Error indexing {md_file}: {e}")
    
    async def _index_openapi_specs(self) -> None:
        """Index OpenAPI specifications"""
        openapi_dir = self.docs_dir / "openapi"
        if not openapi_dir.exists():
            return
        
        for spec_file in openapi_dir.glob("*.yaml"):
            try:
                async with aiofiles.open(spec_file, 'r', encoding='utf-8') as f:
                    spec_content = await f.read()
                
                spec_data = yaml.safe_load(spec_content)
                
                # Extract service name from filename
                service_name = spec_file.stem.replace('-', '_')
                
                # Create documentation item for the spec
                item_id = f"openapi_{service_name}"
                item = DocumentationItem(
                    id=item_id,
                    title=f"{spec_data.get('info', {}).get('title', service_name.title())} API",
                    content=spec_content,
                    type="reference",
                    service=service_name,
                    language="yaml",
                    url=str(spec_file.relative_to(self.docs_dir)),
                    last_modified=datetime.fromtimestamp(spec_file.stat().st_mtime).isoformat(),
                    tags=["api", "openapi", "specification"],
                    excerpt=f"OpenAPI 3.0 specification for {service_name} service"
                )
                
                self.items[item_id] = item
                
            except Exception as e:
                logger.error(f"Error indexing OpenAPI spec {spec_file}: {e}")
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content"""
        metadata = {}
        
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    content = parts[2].strip()
                    metadata = yaml.safe_load(frontmatter) or {}
            except Exception as e:
                logger.warning(f"Error parsing frontmatter: {e}")
        
        return metadata, content
    
    def _classify_content(self, file_path: Path, content: str) -> Tuple[str, str]:
        """Classify content type and service based on file path and content"""
        path_str = str(file_path).lower()
        content_lower = content.lower()
        
        # Determine content type
        if 'api' in path_str or 'openapi' in path_str:
            item_type = "api"
        elif 'guide' in path_str or 'tutorial' in path_str:
            item_type = "guide"
        elif 'example' in path_str or 'demo' in path_str:
            item_type = "example"
        elif 'reference' in path_str or 'spec' in path_str:
            item_type = "reference"
        else:
            item_type = "page"
        
        # Determine service
        if 'litellm' in path_str:
            service = "litellm"
        elif 'multimodal' in path_str:
            service = "multimodal-worker"
        elif 'retrieval' in path_str:
            service = "retrieval-proxy"
        elif 'agent' in path_str:
            service = "ai-agents"
        else:
            service = "all"
        
        return item_type, service
    
    def _generate_excerpt(self, content: str, max_length: int = 200) -> str:
        """Generate excerpt from content"""
        # Remove markdown syntax
        text = re.sub(r'[#*`_\[\]()]', '', content)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove images
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)   # Remove links
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + "..."
        
        return text
    
    async def _build_navigation(self) -> None:
        """Build navigation structure"""
        # Define main navigation structure
        navigation_config = [
            {
                "id": "getting-started",
                "title": "Getting Started",
                "icon": "🚀",
                "description": "Quick start guides and setup",
                "items": ["README", "quick-start", "video-tutorials"]
            },
            {
                "id": "api-documentation",
                "title": "API Documentation",
                "icon": "📚",
                "description": "Complete API reference",
                "items": ["api-reference", "swagger-ui", "openapi"]
            },
            {
                "id": "services",
                "title": "Services",
                "icon": "🏗️",
                "description": "Service-specific documentation",
                "children": [
                    {
                        "id": "litellm-router",
                        "title": "LiteLLM Router",
                        "icon": "🌐",
                        "service": "litellm"
                    },
                    {
                        "id": "multimodal-worker",
                        "title": "Multimodal Worker",
                        "icon": "🖼️",
                        "service": "multimodal-worker"
                    },
                    {
                        "id": "retrieval-proxy",
                        "title": "Retrieval Proxy",
                        "icon": "🔍",
                        "service": "retrieval-proxy"
                    },
                    {
                        "id": "ai-agents",
                        "title": "AI Agents",
                        "icon": "🤖",
                        "service": "ai-agents"
                    }
                ]
            },
            {
                "id": "development",
                "title": "Development",
                "icon": "🛠️",
                "description": "Development guides and tools",
                "items": ["development", "configuration", "troubleshooting"]
            },
            {
                "id": "resources",
                "title": "Resources",
                "icon": "📖",
                "description": "Additional resources and support",
                "items": ["FAQ", "CHANGELOG", "LICENSE"]
            }
        ]
        
        # Build navigation tree
        for nav_config in navigation_config:
            node = await self._create_navigation_node(nav_config)
            self.navigation.append(node)
    
    async def _create_navigation_node(self, config: Dict[str, Any], level: int = 0) -> NavigationNode:
        """Create a navigation node from configuration"""
        node = NavigationNode(
            id=config["id"],
            title=config["title"],
            url=f"#{config['id']}",
            level=level,
            icon=config.get("icon", ""),
            description=config.get("description", "")
        )
        
        # Add children if present
        if "children" in config:
            for child_config in config["children"]:
                child_node = await self._create_navigation_node(child_config, level + 1)
                child_node.parent = node
                node.children.append(child_node)
        
        # Add items if present
        if "items" in config:
            for item_id in config["items"]:
                if item_id in self.items:
                    item = self.items[item_id]
                    child_node = NavigationNode(
                        id=item_id,
                        title=item.title,
                        url=item.url,
                        level=level + 1,
                        parent=node
                    )
                    node.children.append(child_node)
        
        return node
    
    async def _build_search_index(self) -> None:
        """Build search index for fast content retrieval"""
        for item_id, item in self.items.items():
            # Index title
            self._add_to_index(item.title.lower(), item_id)
            
            # Index content
            content_words = re.findall(r'\b\w+\b', item.content.lower())
            for word in content_words:
                if len(word) > 2:  # Skip short words
                    self._add_to_index(word, item_id)
            
            # Index tags
            for tag in item.tags:
                self._add_to_index(tag.lower(), item_id)
    
    def _add_to_index(self, term: str, item_id: str) -> None:
        """Add term to search index"""
        if term not in self.search_index:
            self.search_index[term] = []
        if item_id not in self.search_index[term]:
            self.search_index[term].append(item_id)
    
    async def search(self, query: str, filters: Optional[Dict[str, str]] = None) -> List[DocumentationItem]:
        """Search documentation with optional filters"""
        if not query:
            return []
        
        query_lower = query.lower()
        query_words = re.findall(r'\b\w+\b', query_lower)
        
        # Find matching items
        matching_items = set()
        
        for word in query_words:
            if word in self.search_index:
                matching_items.update(self.search_index[word])
        
        # Convert to DocumentationItem objects
        results = [self.items[item_id] for item_id in matching_items if item_id in self.items]
        
        # Apply filters
        if filters:
            results = self._apply_filters(results, filters)
        
        # Sort by relevance (simple scoring)
        results.sort(key=lambda x: self._calculate_relevance(x, query), reverse=True)
        
        return results
    
    def _apply_filters(self, items: List[DocumentationItem], filters: Dict[str, str]) -> List[DocumentationItem]:
        """Apply filters to search results"""
        filtered_items = items
        
        if "type" in filters and filters["type"] != "all":
            filtered_items = [item for item in filtered_items if item.type == filters["type"]]
        
        if "service" in filters and filters["service"] != "all":
            filtered_items = [item for item in filtered_items if item.service == filters["service"] or item.service == "all"]
        
        if "language" in filters and filters["language"] != "all":
            filtered_items = [item for item in filtered_items if item.language == filters["language"] or item.language == "all"]
        
        return filtered_items
    
    def _calculate_relevance(self, item: DocumentationItem, query: str) -> float:
        """Calculate relevance score for search result"""
        score = 0.0
        query_lower = query.lower()
        
        # Title match (highest weight)
        if query_lower in item.title.lower():
            score += 10.0
        
        # Excerpt match
        if query_lower in item.excerpt.lower():
            score += 5.0
        
        # Content match
        content_lower = item.content.lower()
        query_words = query_lower.split()
        for word in query_words:
            score += content_lower.count(word) * 0.1
        
        # Tag match
        for tag in item.tags:
            if query_lower in tag.lower():
                score += 2.0
        
        return score

class DocumentationServer:
    """FastAPI server for documentation system"""
    
    def __init__(self, docs_dir: Path, port: int = 8080):
        self.docs_dir = Path(docs_dir)
        self.port = port
        self.indexer = DocumentationIndexer(docs_dir)
        self.app = None
    
    async def initialize(self) -> None:
        """Initialize the documentation server"""
        try:
            from fastapi import FastAPI, Request, HTTPException
            from fastapi.responses import HTMLResponse, JSONResponse
            from fastapi.staticfiles import StaticFiles
            from fastapi.templating import Jinja2Templates
            import uvicorn
            
            # Build documentation index
            await self.indexer.build_index()
            
            # Create FastAPI app
            self.app = FastAPI(
                title="Multimodal LLM Stack Documentation",
                description="Comprehensive documentation system with advanced search and navigation",
                version="1.0.0"
            )
            
            # Mount static files
            self.app.mount("/static", StaticFiles(directory=self.docs_dir), name="static")
            
            # Setup templates
            templates = Jinja2Templates(directory=str(self.docs_dir))
            
            # Define routes
            @self.app.get("/", response_class=HTMLResponse)
            async def home(request: Request):
                return templates.TemplateResponse("index.html", {"request": request})
            
            @self.app.get("/search", response_class=HTMLResponse)
            async def search_page(request: Request):
                return templates.TemplateResponse("search.html", {"request": request})
            
            @self.app.get("/api/search")
            async def api_search(q: str = "", type: str = "all", service: str = "all", language: str = "all"):
                filters = {"type": type, "service": service, "language": language}
                results = await self.indexer.search(q, filters)
                return {"results": [asdict(item) for item in results]}
            
            @self.app.get("/api/navigation")
            async def api_navigation():
                return {"navigation": [self._serialize_navigation_node(node) for node in self.indexer.navigation]}
            
            @self.app.get("/api/content/{item_id}")
            async def api_content(item_id: str):
                if item_id not in self.indexer.items:
                    raise HTTPException(status_code=404, detail="Content not found")
                
                item = self.indexer.items[item_id]
                rendered_content = self.indexer.renderer.render(item.content)
                
                return {
                    "item": asdict(item),
                    "rendered_content": rendered_content
                }
            
            logger.info("Documentation server initialized successfully")
            
        except ImportError as e:
            logger.error(f"Missing dependencies for FastAPI server: {e}")
            logger.info("Install with: pip install fastapi uvicorn jinja2")
        except Exception as e:
            logger.error(f"Error initializing documentation server: {e}")
    
    def _serialize_navigation_node(self, node: NavigationNode) -> Dict[str, Any]:
        """Serialize navigation node for JSON response"""
        return {
            "id": node.id,
            "title": node.title,
            "url": node.url,
            "level": node.level,
            "icon": node.icon,
            "description": node.description,
            "children": [self._serialize_navigation_node(child) for child in node.children]
        }
    
    async def start(self) -> None:
        """Start the documentation server"""
        if not self.app:
            await self.initialize()
        
        if self.app:
            import uvicorn
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=self.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()

async def main():
    """Main function to run the documentation system"""
    docs_dir = Path(__file__).parent
    server = DocumentationServer(docs_dir)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Documentation server stopped by user")
    except Exception as e:
        logger.error(f"Error running documentation server: {e}")

if __name__ == "__main__":
    asyncio.run(main())