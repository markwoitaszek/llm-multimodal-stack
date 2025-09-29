#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 3 Documentation System
Part of Issue #71: Documentation Rendering & Navigation

This test suite validates:
- Documentation rendering and navigation
- Content management system
- Advanced search capabilities
- API endpoints and functionality
- Integration with existing system
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Import the modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "docs"))

from documentation_system import DocumentationIndexer, MarkdownRenderer, DocumentationItem
from content_manager import ContentManager, ContentMetadata, ContentValidator
from advanced_search import AdvancedSearchEngine, SearchFilters, SearchResult
from documentation_server import DocumentationServer

class TestMarkdownRenderer:
    """Test markdown rendering functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.renderer = MarkdownRenderer()
    
    def test_basic_markdown_rendering(self):
        """Test basic markdown rendering"""
        markdown_content = """
# Test Title

This is a **bold** text and this is *italic*.

## Code Example

```python
def hello_world():
    print("Hello, World!")
```

- List item 1
- List item 2
"""
        
        html = self.renderer.render(markdown_content)
        
        assert "<h1>Test Title</h1>" in html
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html
        assert "<h2>Code Example</h2>" in html
        assert "<code>" in html
        assert "<ul>" in html
        assert "<li>List item 1</li>" in html
    
    def test_code_highlighting(self):
        """Test code syntax highlighting"""
        markdown_content = """
```python
import os
from pathlib import Path

def test_function():
    return "Hello, World!"
```
"""
        
        html = self.renderer.render(markdown_content)
        
        assert "highlight" in html
        assert "python" in html.lower()
    
    def test_table_rendering(self):
        """Test table rendering"""
        markdown_content = """
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
"""
        
        html = self.renderer.render(markdown_content)
        
        assert "<table>" in html
        assert "<th>Column 1</th>" in html
        assert "<td>Value 1</td>" in html
    
    def test_link_rendering(self):
        """Test link rendering"""
        markdown_content = """
[External Link](https://example.com)
[Internal Link](../docs/README.md)
"""
        
        html = self.renderer.render(markdown_content)
        
        assert 'href="https://example.com"' in html
        assert 'href="../docs/README.md"' in html

class TestContentValidator:
    """Test content validation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = ContentValidator()
    
    def test_valid_content_validation(self):
        """Test validation of valid content"""
        content = """
# Test Documentation

This is a comprehensive test documentation with proper structure.

## Overview

The system provides excellent functionality.

## Examples

Here are some examples:

```python
def example_function():
    return "Hello, World!"
```

## Conclusion

This documentation is well-structured and informative.
"""
        
        metadata = ContentMetadata(
            title="Test Documentation",
            description="A comprehensive test documentation with proper structure and examples",
            author="Test Author",
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            version="1.0.0",
            tags=["test", "documentation", "example"],
            category="testing",
            service="all",
            language="all",
            difficulty="intermediate",
            estimated_read_time=5,
            dependencies=[],
            related_content=[],
            status="published",
            seo_keywords=["test", "documentation"]
        )
        
        result = self.validator.validate_content(content, metadata)
        
        assert result.is_valid
        assert result.score > 80
        assert len(result.errors) == 0
    
    def test_invalid_content_validation(self):
        """Test validation of invalid content"""
        content = "Short content"
        
        metadata = ContentMetadata(
            title="Short",  # Too short
            description="",  # Empty description
            author="",  # Empty author
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            version="1.0.0",
            tags=[],  # No tags
            category="",  # Empty category
            service="",  # Empty service
            language="all",
            difficulty="invalid",  # Invalid difficulty
            estimated_read_time=0,
            dependencies=[],
            related_content=[],
            status="invalid",  # Invalid status
            seo_keywords=[]
        )
        
        result = self.validator.validate_content(content, metadata)
        
        assert not result.is_valid
        assert result.score < 50
        assert len(result.errors) > 0
    
    def test_content_structure_validation(self):
        """Test content structure validation"""
        content = "This content has no headings or structure."
        
        metadata = ContentMetadata(
            title="Test Content",
            description="Test description",
            author="Test Author",
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            version="1.0.0",
            tags=["test"],
            category="testing",
            service="all",
            language="all",
            difficulty="beginner",
            estimated_read_time=1,
            dependencies=[],
            related_content=[],
            status="published",
            seo_keywords=["test"]
        )
        
        result = self.validator.validate_content(content, metadata)
        
        assert "No headings found" in result.errors
    
    def test_link_validation(self):
        """Test link validation"""
        content = """
# Test Content

[Empty Link]()
[Valid Link](https://example.com)
[Internal Link](../docs/README.md)
"""
        
        metadata = ContentMetadata(
            title="Test Content",
            description="Test description",
            author="Test Author",
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            version="1.0.0",
            tags=["test"],
            category="testing",
            service="all",
            language="all",
            difficulty="beginner",
            estimated_read_time=1,
            dependencies=[],
            related_content=[],
            status="published",
            seo_keywords=["test"]
        )
        
        result = self.validator.validate_content(content, metadata)
        
        assert "Empty link URL found" in result.errors

class TestDocumentationIndexer:
    """Test documentation indexing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir)
        self.indexer = DocumentationIndexer(self.docs_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_build_index(self):
        """Test building documentation index"""
        # Create test markdown files
        test_file1 = self.docs_dir / "test1.md"
        test_file1.write_text("""
---
title: Test Document 1
type: guide
service: litellm
tags: [test, guide]
---

# Test Document 1

This is a test document for the LiteLLM service.
""")
        
        test_file2 = self.docs_dir / "test2.md"
        test_file2.write_text("""
---
title: Test Document 2
type: api
service: multimodal-worker
tags: [test, api]
---

# Test Document 2

This is an API documentation for the Multimodal Worker service.
""")
        
        # Build index
        await self.indexer.build_index()
        
        # Verify index was built
        assert len(self.indexer.items) == 2
        assert "test1" in self.indexer.items
        assert "test2" in self.indexer.items
        
        # Verify item properties
        item1 = self.indexer.items["test1"]
        assert item1.title == "Test Document 1"
        assert item1.type == "guide"
        assert item1.service == "litellm"
        assert "test" in item1.tags
    
    async def test_search_functionality(self):
        """Test search functionality"""
        # Create test content
        test_file = self.docs_dir / "search_test.md"
        test_file.write_text("""
---
title: Search Test Document
type: guide
service: all
tags: [search, test]
---

# Search Test Document

This document contains information about search functionality and testing.
""")
        
        # Build index
        await self.indexer.build_index()
        
        # Test search
        results = await self.indexer.search("search functionality")
        assert len(results) > 0
        
        result = results[0]
        assert result.title == "Search Test Document"
        assert "search" in result.matched_terms
    
    async def test_navigation_building(self):
        """Test navigation structure building"""
        # Create test files
        test_file = self.docs_dir / "navigation_test.md"
        test_file.write_text("""
---
title: Navigation Test
type: page
service: all
tags: [navigation, test]
---

# Navigation Test

This is a test for navigation functionality.
""")
        
        # Build index and navigation
        await self.indexer.build_index()
        
        # Verify navigation was built
        assert len(self.indexer.navigation) > 0
        
        # Check for expected navigation sections
        nav_titles = [node.title for node in self.indexer.navigation]
        assert "Getting Started" in nav_titles or "API Documentation" in nav_titles

class TestContentManager:
    """Test content management functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir)
        self.content_manager = ContentManager(self.docs_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_content_indexing(self):
        """Test content indexing"""
        # Create test markdown file
        test_file = self.docs_dir / "content_test.md"
        test_file.write_text("""
---
title: Content Test
description: A test for content management
author: Test Author
category: testing
service: all
difficulty: beginner
tags: [test, content]
---

# Content Test

This is a test document for content management functionality.
""")
        
        # Index content
        metadata = await self.content_manager.index_content_file(test_file)
        
        assert metadata is not None
        assert metadata.title == "Content Test"
        assert metadata.author == "Test Author"
        assert metadata.category == "testing"
        assert metadata.difficulty == "beginner"
        assert "test" in metadata.tags
    
    async def test_content_filtering(self):
        """Test content filtering by various criteria"""
        # Create test content with different categories
        test_files = [
            ("guide1.md", "Guide 1", "guide", "litellm", "beginner"),
            ("api1.md", "API 1", "api", "multimodal-worker", "intermediate"),
            ("example1.md", "Example 1", "example", "all", "advanced")
        ]
        
        for filename, title, content_type, service, difficulty in test_files:
            test_file = self.docs_dir / filename
            test_file.write_text(f"""
---
title: {title}
type: {content_type}
service: {service}
difficulty: {difficulty}
category: {content_type}
tags: [test]
---

# {title}

This is a {content_type} document.
""")
            await self.content_manager.index_content_file(test_file)
        
        # Test filtering by category
        guide_content = await self.content_manager.get_content_by_category("guide")
        assert len(guide_content) == 1
        assert guide_content[0].title == "Guide 1"
        
        # Test filtering by service
        litellm_content = await self.content_manager.get_content_by_service("litellm")
        assert len(litellm_content) == 1
        assert litellm_content[0].title == "Guide 1"
        
        # Test filtering by difficulty
        beginner_content = await self.content_manager.get_content_by_difficulty("beginner")
        assert len(beginner_content) == 1
        assert beginner_content[0].title == "Guide 1"
    
    async def test_content_links(self):
        """Test content linking functionality"""
        # Create test content with dependencies
        test_file1 = self.docs_dir / "base.md"
        test_file1.write_text("""
---
title: Base Document
type: guide
service: all
tags: [base]
---

# Base Document

This is the base document.
""")
        
        test_file2 = self.docs_dir / "dependent.md"
        test_file2.write_text("""
---
title: Dependent Document
type: guide
service: all
dependencies: [base]
related_content: [base]
tags: [dependent]
---

# Dependent Document

This document depends on the base document.
""")
        
        # Index content
        await self.content_manager.index_content_file(test_file1)
        await self.content_manager.index_content_file(test_file2)
        
        # Build content links
        await self.content_manager.build_content_links()
        
        # Test dependency retrieval
        dependencies = await self.content_manager.get_content_dependencies("dependent")
        assert len(dependencies) == 1
        assert dependencies[0].title == "Base Document"
        
        # Test related content retrieval
        related = await self.content_manager.get_related_content("dependent")
        assert len(related) == 1
        assert related[0].title == "Base Document"
    
    async def test_content_report_generation(self):
        """Test content report generation"""
        # Create test content
        test_file = self.docs_dir / "report_test.md"
        test_file.write_text("""
---
title: Report Test
type: guide
service: all
category: testing
difficulty: intermediate
status: published
tags: [test, report]
---

# Report Test

This is a test for report generation.
""")
        
        # Index content
        await self.content_manager.index_content_file(test_file)
        
        # Generate report
        report = await self.content_manager.generate_content_report()
        
        assert report["total_items"] == 1
        assert "testing" in report["categories"]
        assert "all" in report["services"]
        assert "intermediate" in report["difficulties"]
        assert "published" in report["statuses"]

class TestAdvancedSearchEngine:
    """Test advanced search functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir)
        self.search_engine = AdvancedSearchEngine(self.docs_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_search_index_building(self):
        """Test search index building"""
        # Create test content
        test_file = self.docs_dir / "search_test.md"
        test_file.write_text("""
---
title: Search Test Document
type: guide
service: all
tags: [search, test]
---

# Search Test Document

This document contains information about search functionality and testing.
It includes various terms like API, documentation, and examples.
""")
        
        # Build search index
        await self.search_engine.build_index()
        
        # Verify index was built
        assert self.search_engine.search_index.total_documents == 1
        assert "search" in self.search_engine.search_index.index
        assert "test" in self.search_engine.search_index.index
        assert "api" in self.search_engine.search_index.index
    
    async def test_basic_search(self):
        """Test basic search functionality"""
        # Create test content
        test_file = self.docs_dir / "basic_search.md"
        test_file.write_text("""
---
title: Basic Search Test
type: guide
service: all
tags: [search, basic]
---

# Basic Search Test

This document is about basic search functionality.
It contains information about search algorithms and indexing.
""")
        
        # Build index and search
        await self.search_engine.build_index()
        results = await self.search_engine.search("search functionality")
        
        assert len(results) > 0
        result = results[0]
        assert result.title == "Basic Search Test"
        assert result.score > 0
        assert "search" in result.matched_terms
    
    async def test_filtered_search(self):
        """Test search with filters"""
        # Create test content with different types
        test_files = [
            ("guide_search.md", "Guide Search", "guide", "litellm"),
            ("api_search.md", "API Search", "api", "multimodal-worker"),
            ("example_search.md", "Example Search", "example", "all")
        ]
        
        for filename, title, content_type, service in test_files:
            test_file = self.docs_dir / filename
            test_file.write_text(f"""
---
title: {title}
type: {content_type}
service: {service}
tags: [search, {content_type}]
---

# {title}

This is a {content_type} document about search functionality.
""")
        
        # Build index
        await self.search_engine.build_index()
        
        # Test filtered search
        filters = SearchFilters(content_type="guide", service="litellm")
        results = await self.search_engine.search("search", filters)
        
        assert len(results) == 1
        assert results[0].title == "Guide Search"
        assert results[0].type == "guide"
        assert results[0].service == "litellm"
    
    async def test_search_suggestions(self):
        """Test search suggestions"""
        # Create test content
        test_file = self.docs_dir / "suggestions_test.md"
        test_file.write_text("""
---
title: Suggestions Test
type: guide
service: all
tags: [suggestions, test]
---

# Suggestions Test

This document is about search suggestions and autocomplete functionality.
""")
        
        # Build index
        await self.search_engine.build_index()
        
        # Get suggestions
        suggestions = await self.search_engine.get_suggestions("sug")
        
        assert len(suggestions) > 0
        suggestion_texts = [s.text for s in suggestions]
        assert any("suggestions" in text for text in suggestion_texts)
    
    async def test_search_analytics(self):
        """Test search analytics"""
        # Create test content
        test_file = self.docs_dir / "analytics_test.md"
        test_file.write_text("""
---
title: Analytics Test
type: guide
service: all
tags: [analytics, test]
---

# Analytics Test

This document is about search analytics and reporting.
""")
        
        # Build index
        await self.search_engine.build_index()
        
        # Perform some searches
        await self.search_engine.search("analytics")
        await self.search_engine.search("test")
        await self.search_engine.search("search")
        
        # Get analytics
        analytics = await self.search_engine.get_search_analytics()
        
        assert analytics["total_searches"] >= 3
        assert len(analytics["popular_queries"]) > 0

class TestDocumentationServer:
    """Test documentation server functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir)
        self.server = DocumentationServer(self.docs_dir, port=8081)  # Use different port for testing
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_server_initialization(self):
        """Test server initialization"""
        # Create test content
        test_file = self.docs_dir / "server_test.md"
        test_file.write_text("""
---
title: Server Test
type: guide
service: all
tags: [server, test]
---

# Server Test

This is a test for the documentation server.
""")
        
        # Initialize server
        await self.server.initialize()
        
        # Verify components are initialized
        assert len(self.server.indexer.items) > 0
        assert self.server.search_engine.search_index.total_documents > 0
        assert len(self.server.content_manager.content_index) > 0
    
    def test_api_models(self):
        """Test API model validation"""
        from documentation_server import SearchRequest, SearchResponse, ContentRequest
        
        # Test SearchRequest
        search_req = SearchRequest(
            query="test query",
            content_type="guide",
            max_results=10
        )
        assert search_req.query == "test query"
        assert search_req.content_type == "guide"
        assert search_req.max_results == 10
        
        # Test ContentRequest
        content_req = ContentRequest(
            title="Test Content",
            content="# Test\nThis is test content.",
            metadata={"author": "Test Author"}
        )
        assert content_req.title == "Test Content"
        assert content_req.metadata["author"] == "Test Author"

# Integration Tests
class TestDocumentationSystemIntegration:
    """Test integration between all documentation system components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_full_system_integration(self):
        """Test full system integration"""
        # Create comprehensive test content
        test_files = [
            ("getting_started.md", "Getting Started", "guide", "all", "beginner"),
            ("api_reference.md", "API Reference", "api", "litellm", "intermediate"),
            ("examples.md", "Examples", "example", "multimodal-worker", "advanced"),
            ("troubleshooting.md", "Troubleshooting", "guide", "all", "intermediate")
        ]
        
        for filename, title, content_type, service, difficulty in test_files:
            test_file = self.docs_dir / filename
            test_file.write_text(f"""
---
title: {title}
type: {content_type}
service: {service}
difficulty: {difficulty}
category: {content_type}
tags: [test, {content_type}, {service}]
author: Test Author
description: A comprehensive {content_type} document for {service}
---

# {title}

This is a comprehensive {content_type} document for the {service} service.

## Overview

The {service} service provides excellent functionality for {content_type} operations.

## Examples

Here are some examples:

```python
def example_function():
    return "Hello from {service}!"
```

## Conclusion

This {content_type} document provides comprehensive information about {service}.
""")
        
        # Initialize all components
        indexer = DocumentationIndexer(self.docs_dir)
        content_manager = ContentManager(self.docs_dir)
        search_engine = AdvancedSearchEngine(self.docs_dir)
        
        # Build indexes
        await indexer.build_index()
        await content_manager.load_content_index()
        await search_engine.build_index()
        
        # Test search across all content
        results = await search_engine.search("comprehensive", max_results=10)
        assert len(results) >= 4  # Should find all test files
        
        # Test content filtering
        guide_content = await content_manager.get_content_by_category("guide")
        assert len(guide_content) == 2  # getting_started and troubleshooting
        
        # Test navigation
        assert len(indexer.navigation) > 0
        
        # Test content validation
        validator = ContentValidator()
        for item_id, item in indexer.items.items():
            if item_id in content_manager.content_index:
                metadata = content_manager.content_index[item_id]
                validation_result = validator.validate_content(item.content, metadata)
                assert validation_result.is_valid
                assert validation_result.score > 70  # Should be good quality content

# Performance Tests
class TestDocumentationSystemPerformance:
    """Test performance of documentation system components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir)
    
    async def test_large_content_indexing_performance(self):
        """Test performance with large amount of content"""
        # Create many test files
        num_files = 100
        for i in range(num_files):
            test_file = self.docs_dir / f"test_file_{i}.md"
            test_file.write_text(f"""
---
title: Test File {i}
type: guide
service: all
tags: [test, file{i}]
---

# Test File {i}

This is test file number {i} with some content for performance testing.
It contains various terms like API, documentation, examples, and testing.
""")
        
        # Test indexing performance
        import time
        start_time = time.time()
        
        indexer = DocumentationIndexer(self.docs_dir)
        await indexer.build_index()
        
        indexing_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert indexing_time < 10.0  # 10 seconds for 100 files
        assert len(indexer.items) == num_files
    
    async def test_search_performance(self):
        """Test search performance with large index"""
        # Create test content
        num_files = 50
        for i in range(num_files):
            test_file = self.docs_dir / f"search_test_{i}.md"
            test_file.write_text(f"""
---
title: Search Test {i}
type: guide
service: all
tags: [search, test{i}]
---

# Search Test {i}

This is search test file {i} with content about search functionality.
It includes terms like search, indexing, performance, and testing.
""")
        
        # Build search index
        search_engine = AdvancedSearchEngine(self.docs_dir)
        await search_engine.build_index()
        
        # Test search performance
        import time
        start_time = time.time()
        
        results = await search_engine.search("search functionality", max_results=20)
        
        search_time = time.time() - start_time
        
        # Should complete quickly
        assert search_time < 1.0  # 1 second for search
        assert len(results) > 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])