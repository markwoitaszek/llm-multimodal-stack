#!/usr/bin/env python3
"""
FastAPI Documentation Server
Part of Issue #71: Documentation Rendering & Navigation

This module provides a comprehensive FastAPI server for the documentation system with:
- RESTful API endpoints for documentation
- Real-time search capabilities
- Content management endpoints
- Analytics and reporting
- WebSocket support for real-time updates
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError as e:
    logger.error(f"Missing dependencies: {e}")
    logger.info("Install with: pip install fastapi uvicorn jinja2 python-multipart")
    raise

# Import our custom modules
from documentation_system import DocumentationIndexer, MarkdownRenderer
from content_manager import ContentManager, ContentMetadata, SearchFilters
from advanced_search import AdvancedSearchEngine, SearchResult, SearchSuggestion

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    service: Optional[str] = Field(None, description="Filter by service")
    language: Optional[str] = Field(None, description="Filter by language")
    difficulty: Optional[str] = Field(None, description="Filter by difficulty")
    category: Optional[str] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    max_results: int = Field(50, description="Maximum number of results")

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    query: str
    search_time_ms: int
    suggestions: List[Dict[str, Any]]

class ContentRequest(BaseModel):
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ContentResponse(BaseModel):
    item_id: str
    title: str
    content: str
    rendered_content: str
    metadata: Dict[str, Any]
    validation_result: Dict[str, Any]

class NavigationResponse(BaseModel):
    navigation: List[Dict[str, Any]]
    breadcrumbs: List[Dict[str, Any]]

class AnalyticsResponse(BaseModel):
    total_searches: int
    popular_queries: List[Dict[str, Any]]
    search_patterns: Dict[str, Any]
    content_stats: Dict[str, Any]

class DocumentationServer:
    """FastAPI server for documentation system"""
    
    def __init__(self, docs_dir: Path, port: int = 8080):
        self.docs_dir = Path(docs_dir)
        self.port = port
        
        # Initialize components
        self.indexer = DocumentationIndexer(docs_dir)
        self.content_manager = ContentManager(docs_dir)
        self.search_engine = AdvancedSearchEngine(docs_dir)
        self.renderer = MarkdownRenderer()
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Multimodal LLM Stack Documentation API",
            description="Comprehensive documentation system with advanced search and navigation",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup templates
        self.templates = Jinja2Templates(directory=str(docs_dir))
        
        # Define routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Static files
        self.app.mount("/static", StaticFiles(directory=str(self.docs_dir)), name="static")
        
        # Web interface routes
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})
        
        @self.app.get("/search", response_class=HTMLResponse)
        async def search_page(request: Request):
            return self.templates.TemplateResponse("search.html", {"request": request})
        
        @self.app.get("/navigation", response_class=HTMLResponse)
        async def navigation_page(request: Request):
            return self.templates.TemplateResponse("enhanced_navigation.html", {"request": request})
        
        # API routes
        @self.app.get("/api/health")
        async def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.post("/api/search", response_model=SearchResponse)
        async def search_documentation(request: SearchRequest):
            try:
                # Create search filters
                filters = None
                if any([request.content_type, request.service, request.language, 
                       request.difficulty, request.category, request.tags]):
                    filters = SearchFilters(
                        content_type=request.content_type,
                        service=request.service,
                        language=request.language,
                        difficulty=request.difficulty,
                        category=request.category,
                        tags=request.tags
                    )
                
                # Perform search
                start_time = datetime.now()
                results = await self.search_engine.search(request.query, filters, request.max_results)
                search_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Get suggestions
                suggestions = await self.search_engine.get_suggestions(request.query, max_suggestions=5)
                
                return SearchResponse(
                    results=[self._serialize_search_result(result) for result in results],
                    total_count=len(results),
                    query=request.query,
                    search_time_ms=int(search_time),
                    suggestions=[self._serialize_suggestion(suggestion) for suggestion in suggestions]
                )
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/suggestions")
        async def get_suggestions(q: str = "", max_suggestions: int = 10):
            try:
                suggestions = await self.search_engine.get_suggestions(q, max_suggestions)
                return {"suggestions": [self._serialize_suggestion(s) for s in suggestions]}
            except Exception as e:
                logger.error(f"Suggestions error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/navigation", response_model=NavigationResponse)
        async def get_navigation():
            try:
                # Get navigation structure
                navigation = [self._serialize_navigation_node(node) for node in self.indexer.navigation]
                
                # Generate breadcrumbs (simplified)
                breadcrumbs = [
                    {"title": "Home", "url": "/"},
                    {"title": "Documentation", "url": "/navigation"}
                ]
                
                return NavigationResponse(
                    navigation=navigation,
                    breadcrumbs=breadcrumbs
                )
            except Exception as e:
                logger.error(f"Navigation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/content/{item_id}", response_model=ContentResponse)
        async def get_content(item_id: str):
            try:
                if item_id not in self.indexer.items:
                    raise HTTPException(status_code=404, detail="Content not found")
                
                item = self.indexer.items[item_id]
                rendered_content = self.renderer.render(item.content)
                
                # Get validation result if available
                validation_result = {}
                if item_id in self.content_manager.content_index:
                    from content_manager import ContentValidator
                    validator = ContentValidator()
                    metadata = self.content_manager.content_index[item_id]
                    validation_result = validator.validate_content(item.content, metadata)
                    validation_result = {
                        "is_valid": validation_result.is_valid,
                        "score": validation_result.score,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings,
                        "suggestions": validation_result.suggestions
                    }
                
                return ContentResponse(
                    item_id=item_id,
                    title=item.title,
                    content=item.content,
                    rendered_content=rendered_content,
                    metadata={
                        "type": item.type,
                        "service": item.service,
                        "language": item.language,
                        "url": item.url,
                        "last_modified": item.last_modified,
                        "tags": item.tags,
                        "excerpt": item.excerpt
                    },
                    validation_result=validation_result
                )
            except Exception as e:
                logger.error(f"Content error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/content", response_model=ContentResponse)
        async def create_content(request: ContentRequest):
            try:
                # Generate item ID
                item_id = request.title.lower().replace(' ', '_').replace('-', '_')
                
                # Create content metadata
                metadata = ContentMetadata(
                    title=request.title,
                    description=request.metadata.get('description', '') if request.metadata else '',
                    author=request.metadata.get('author', 'Documentation Team') if request.metadata else 'Documentation Team',
                    created_date=datetime.now().isoformat(),
                    last_modified=datetime.now().isoformat(),
                    version="1.0.0",
                    tags=request.metadata.get('tags', []) if request.metadata else [],
                    category=request.metadata.get('category', 'general') if request.metadata else 'general',
                    service=request.metadata.get('service', 'all') if request.metadata else 'all',
                    language=request.metadata.get('language', 'all') if request.metadata else 'all',
                    difficulty=request.metadata.get('difficulty', 'intermediate') if request.metadata else 'intermediate',
                    estimated_read_time=len(request.content.split()) // 200 + 1,
                    dependencies=request.metadata.get('dependencies', []) if request.metadata else [],
                    related_content=request.metadata.get('related_content', []) if request.metadata else [],
                    status=request.metadata.get('status', 'draft') if request.metadata else 'draft',
                    seo_keywords=request.metadata.get('seo_keywords', []) if request.metadata else []
                )
                
                # Validate content
                from content_manager import ContentValidator
                validator = ContentValidator()
                validation_result = validator.validate_content(request.content, metadata)
                
                # Add to content manager
                self.content_manager.content_index[item_id] = metadata
                
                # Render content
                rendered_content = self.renderer.render(request.content)
                
                return ContentResponse(
                    item_id=item_id,
                    title=request.title,
                    content=request.content,
                    rendered_content=rendered_content,
                    metadata={
                        "type": metadata.category,
                        "service": metadata.service,
                        "language": metadata.language,
                        "url": f"/api/content/{item_id}",
                        "last_modified": metadata.last_modified,
                        "tags": metadata.tags,
                        "excerpt": metadata.description
                    },
                    validation_result={
                        "is_valid": validation_result.is_valid,
                        "score": validation_result.score,
                        "errors": validation_result.errors,
                        "warnings": validation_result.warnings,
                        "suggestions": validation_result.suggestions
                    }
                )
            except Exception as e:
                logger.error(f"Create content error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/analytics", response_model=AnalyticsResponse)
        async def get_analytics():
            try:
                # Get search analytics
                search_analytics = await self.search_engine.get_search_analytics()
                
                # Get content statistics
                content_report = await self.content_manager.generate_content_report()
                
                return AnalyticsResponse(
                    total_searches=search_analytics.get("total_searches", 0),
                    popular_queries=search_analytics.get("popular_queries", []),
                    search_patterns={
                        "average_results": search_analytics.get("average_results_per_search", 0),
                        "success_rate": search_analytics.get("success_rate_percent", 0),
                        "average_search_time": search_analytics.get("average_search_time_ms", 0)
                    },
                    content_stats=content_report
                )
            except Exception as e:
                logger.error(f"Analytics error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/content")
        async def list_content(
            category: Optional[str] = None,
            service: Optional[str] = None,
            difficulty: Optional[str] = None,
            status: Optional[str] = None,
            limit: int = 50
        ):
            try:
                content_items = []
                
                for item_id, metadata in self.content_manager.content_index.items():
                    # Apply filters
                    if category and metadata.category != category:
                        continue
                    if service and metadata.service != service and metadata.service != 'all':
                        continue
                    if difficulty and metadata.difficulty != difficulty:
                        continue
                    if status and metadata.status != status:
                        continue
                    
                    content_items.append({
                        "item_id": item_id,
                        "title": metadata.title,
                        "description": metadata.description,
                        "category": metadata.category,
                        "service": metadata.service,
                        "difficulty": metadata.difficulty,
                        "status": metadata.status,
                        "tags": metadata.tags,
                        "last_modified": metadata.last_modified,
                        "estimated_read_time": metadata.estimated_read_time
                    })
                    
                    if len(content_items) >= limit:
                        break
                
                return {"content": content_items, "total": len(content_items)}
            except Exception as e:
                logger.error(f"List content error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # WebSocket endpoint for real-time updates
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "search":
                        # Handle real-time search
                        query = message.get("query", "")
                        if query:
                            results = await self.search_engine.search(query, max_results=10)
                            response = {
                                "type": "search_results",
                                "results": [self._serialize_search_result(result) for result in results]
                            }
                            await websocket.send_text(json.dumps(response))
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)
    
    def _serialize_search_result(self, result: SearchResult) -> Dict[str, Any]:
        """Serialize search result for JSON response"""
        return {
            "item_id": result.item_id,
            "title": result.title,
            "excerpt": result.excerpt,
            "type": result.type,
            "service": result.service,
            "language": result.language,
            "url": result.url,
            "last_modified": result.last_modified,
            "tags": result.tags,
            "score": result.score,
            "highlights": result.highlights,
            "matched_terms": result.matched_terms
        }
    
    def _serialize_suggestion(self, suggestion: SearchSuggestion) -> Dict[str, Any]:
        """Serialize search suggestion for JSON response"""
        return {
            "text": suggestion.text,
            "type": suggestion.type,
            "frequency": suggestion.frequency,
            "context": suggestion.context
        }
    
    def _serialize_navigation_node(self, node) -> Dict[str, Any]:
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
    
    async def initialize(self) -> None:
        """Initialize the documentation server"""
        try:
            # Build documentation index
            await self.indexer.build_index()
            
            # Load content manager
            await self.content_manager.load_content_index()
            
            # Build search index
            await self.search_engine.build_index()
            
            logger.info("Documentation server initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing documentation server: {e}")
            raise
    
    async def start(self) -> None:
        """Start the documentation server"""
        await self.initialize()
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info",
            reload=False
        )
        
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Main function to run the documentation server"""
    docs_dir = Path(__file__).parent
    server = DocumentationServer(docs_dir, port=8080)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Documentation server stopped by user")
    except Exception as e:
        logger.error(f"Error running documentation server: {e}")

if __name__ == "__main__":
    asyncio.run(main())