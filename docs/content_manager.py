#!/usr/bin/env python3
"""
Content Management System for Documentation
Part of Issue #71: Documentation Rendering & Navigation

This module provides content management capabilities including:
- Content organization and categorization
- Metadata management
- Content validation and quality checks
- Cross-referencing and linking
- Content versioning and history
"""

import os
import re
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentMetadata:
    """Metadata for documentation content"""
    title: str
    description: str
    author: str
    created_date: str
    last_modified: str
    version: str
    tags: List[str]
    category: str
    service: str
    language: str
    difficulty: str  # 'beginner', 'intermediate', 'advanced'
    estimated_read_time: int  # in minutes
    dependencies: List[str]  # IDs of content this depends on
    related_content: List[str]  # IDs of related content
    status: str  # 'draft', 'review', 'published', 'archived'
    seo_keywords: List[str]
    custom_fields: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_fields is None:
            self.custom_fields = {}

@dataclass
class ContentValidationResult:
    """Result of content validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    score: float  # 0-100 quality score

@dataclass
class ContentLink:
    """Represents a link between content items"""
    source_id: str
    target_id: str
    link_type: str  # 'reference', 'dependency', 'related', 'example'
    context: str  # Description of the relationship

class ContentValidator:
    """Validates documentation content for quality and consistency"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules from configuration"""
        return {
            "min_title_length": 10,
            "max_title_length": 100,
            "min_description_length": 50,
            "max_description_length": 500,
            "required_tags": ["documentation"],
            "max_tags": 10,
            "min_content_length": 100,
            "max_content_length": 50000,
            "required_sections": ["overview", "examples"],
            "code_block_languages": ["python", "javascript", "bash", "yaml", "json"],
            "link_patterns": [
                r"\[([^\]]+)\]\(([^)]+)\)",  # Markdown links
                r"https?://[^\s]+",  # HTTP links
                r"#[\w-]+"  # Anchor links
            ]
        }
    
    def validate_content(self, content: str, metadata: ContentMetadata) -> ContentValidationResult:
        """Validate content and metadata"""
        errors = []
        warnings = []
        suggestions = []
        
        # Validate metadata
        self._validate_metadata(metadata, errors, warnings, suggestions)
        
        # Validate content
        self._validate_content_structure(content, errors, warnings, suggestions)
        
        # Validate links
        self._validate_links(content, errors, warnings, suggestions)
        
        # Validate code blocks
        self._validate_code_blocks(content, errors, warnings, suggestions)
        
        # Calculate quality score
        score = self._calculate_quality_score(content, metadata, errors, warnings)
        
        return ContentValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            score=score
        )
    
    def _validate_metadata(self, metadata: ContentMetadata, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate content metadata"""
        rules = self.validation_rules
        
        # Title validation
        if len(metadata.title) < rules["min_title_length"]:
            errors.append(f"Title too short (minimum {rules['min_title_length']} characters)")
        elif len(metadata.title) > rules["max_title_length"]:
            errors.append(f"Title too long (maximum {rules['max_title_length']} characters)")
        
        # Description validation
        if len(metadata.description) < rules["min_description_length"]:
            errors.append(f"Description too short (minimum {rules['min_description_length']} characters)")
        elif len(metadata.description) > rules["max_description_length"]:
            warnings.append(f"Description quite long (maximum {rules['max_description_length']} characters)")
        
        # Tags validation
        if len(metadata.tags) == 0:
            warnings.append("No tags specified")
        elif len(metadata.tags) > rules["max_tags"]:
            warnings.append(f"Too many tags (maximum {rules['max_tags']})")
        
        # Required fields
        if not metadata.author:
            errors.append("Author is required")
        if not metadata.category:
            errors.append("Category is required")
        if not metadata.service:
            errors.append("Service is required")
        
        # Status validation
        valid_statuses = ["draft", "review", "published", "archived"]
        if metadata.status not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Difficulty validation
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if metadata.difficulty not in valid_difficulties:
            errors.append(f"Invalid difficulty. Must be one of: {', '.join(valid_difficulties)}")
    
    def _validate_content_structure(self, content: str, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate content structure"""
        rules = self.validation_rules
        
        # Content length
        if len(content) < rules["min_content_length"]:
            errors.append(f"Content too short (minimum {rules['min_content_length']} characters)")
        elif len(content) > rules["max_content_length"]:
            warnings.append(f"Content very long (maximum {rules['max_content_length']} characters)")
        
        # Required sections
        for section in rules["required_sections"]:
            if f"## {section.title()}" not in content and f"# {section.title()}" not in content:
                suggestions.append(f"Consider adding a '{section.title()}' section")
        
        # Headings structure
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        if not headings:
            errors.append("No headings found in content")
        elif len(headings) < 2:
            warnings.append("Consider adding more headings for better structure")
        
        # Check for orphaned content (content without headings)
        lines = content.split('\n')
        has_heading = False
        orphaned_lines = 0
        
        for line in lines:
            if line.strip().startswith('#'):
                has_heading = True
            elif has_heading and line.strip() and not line.strip().startswith('#'):
                orphaned_lines += 1
        
        if orphaned_lines > 10:
            warnings.append("Consider organizing content under proper headings")
    
    def _validate_links(self, content: str, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate links in content"""
        # Find all links
        markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        http_links = re.findall(r'https?://[^\s]+', content)
        
        # Validate markdown links
        for link_text, link_url in markdown_links:
            if not link_text.strip():
                errors.append("Empty link text found")
            if not link_url.strip():
                errors.append("Empty link URL found")
            elif link_url.startswith('http') and not self._is_valid_url(link_url):
                warnings.append(f"Potentially invalid URL: {link_url}")
        
        # Check for broken internal links
        internal_links = [url for _, url in markdown_links if not url.startswith('http')]
        if internal_links:
            suggestions.append("Verify that all internal links are working")
        
        # Check for external links without descriptions
        external_links = [url for url in http_links if not any(url in link for _, link in markdown_links)]
        if external_links:
            suggestions.append("Consider adding descriptive text for external links")
    
    def _validate_code_blocks(self, content: str, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate code blocks in content"""
        # Find code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        
        for language, code in code_blocks:
            # Check if language is specified
            if not language:
                warnings.append("Code block without language specification")
            elif language not in self.validation_rules["code_block_languages"]:
                suggestions.append(f"Consider using a supported language for code block: {language}")
            
            # Check code quality
            if len(code.strip()) < 10:
                warnings.append("Very short code block - consider adding more context")
            
            # Check for syntax issues (basic)
            if language == "python":
                self._validate_python_code(code, errors, warnings)
            elif language == "javascript":
                self._validate_javascript_code(code, errors, warnings)
    
    def _validate_python_code(self, code: str, errors: List[str], warnings: List[str]):
        """Basic Python code validation"""
        lines = code.split('\n')
        
        # Check for common issues
        for i, line in enumerate(lines, 1):
            if line.strip() and not line.startswith('#') and not line.startswith(' '):
                # Check for missing imports
                if 'import' not in line and any(keyword in line for keyword in ['requests', 'json', 'yaml', 'pandas']):
                    warnings.append(f"Line {i}: Consider adding import statement")
    
    def _validate_javascript_code(self, code: str, errors: List[str], warnings: List[str]):
        """Basic JavaScript code validation"""
        # Check for common issues
        if 'console.log' in code and '//' not in code:
            suggestions.append("Consider adding comments to JavaScript code")
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return pattern.match(url) is not None
    
    def _calculate_quality_score(self, content: str, metadata: ContentMetadata, errors: List[str], warnings: List[str]) -> float:
        """Calculate content quality score (0-100)"""
        score = 100.0
        
        # Deduct points for errors
        score -= len(errors) * 10
        
        # Deduct points for warnings
        score -= len(warnings) * 5
        
        # Bonus points for good practices
        if len(metadata.tags) >= 3:
            score += 5
        if metadata.estimated_read_time > 0:
            score += 5
        if len(metadata.related_content) > 0:
            score += 5
        if len(content.split('\n')) > 20:  # Substantial content
            score += 5
        
        return max(0.0, min(100.0, score))

class ContentManager:
    """Manages documentation content and metadata"""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)
        self.content_index: Dict[str, ContentMetadata] = {}
        self.content_links: List[ContentLink] = []
        self.validator = ContentValidator()
        self.metadata_file = self.docs_dir / "content_metadata.json"
        self.links_file = self.docs_dir / "content_links.json"
    
    async def load_content_index(self) -> None:
        """Load content index from metadata file"""
        try:
            if self.metadata_file.exists():
                async with aiofiles.open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.loads(await f.read())
                    self.content_index = {
                        item_id: ContentMetadata(**item_data)
                        for item_id, item_data in data.items()
                    }
                logger.info(f"Loaded {len(self.content_index)} content items from index")
        except Exception as e:
            logger.error(f"Error loading content index: {e}")
    
    async def save_content_index(self) -> None:
        """Save content index to metadata file"""
        try:
            data = {
                item_id: asdict(metadata)
                for item_id, metadata in self.content_index.items()
            }
            async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"Saved {len(self.content_index)} content items to index")
        except Exception as e:
            logger.error(f"Error saving content index: {e}")
    
    async def index_content_file(self, file_path: Path) -> Optional[ContentMetadata]:
        """Index a content file and extract metadata"""
        try:
            # Read file content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Parse frontmatter
            metadata_dict, content_body = self._parse_frontmatter(content)
            
            # Generate file ID
            file_id = str(file_path.relative_to(self.docs_dir)).replace('/', '_').replace('.md', '')
            
            # Create metadata object
            metadata = ContentMetadata(
                title=metadata_dict.get('title', file_path.stem.replace('_', ' ').title()),
                description=metadata_dict.get('description', self._generate_description(content_body)),
                author=metadata_dict.get('author', 'Documentation Team'),
                created_date=metadata_dict.get('created_date', datetime.now().isoformat()),
                last_modified=datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                version=metadata_dict.get('version', '1.0.0'),
                tags=metadata_dict.get('tags', []),
                category=metadata_dict.get('category', 'general'),
                service=metadata_dict.get('service', 'all'),
                language=metadata_dict.get('language', 'all'),
                difficulty=metadata_dict.get('difficulty', 'intermediate'),
                estimated_read_time=self._estimate_read_time(content_body),
                dependencies=metadata_dict.get('dependencies', []),
                related_content=metadata_dict.get('related_content', []),
                status=metadata_dict.get('status', 'published'),
                seo_keywords=metadata_dict.get('seo_keywords', []),
                custom_fields=metadata_dict.get('custom_fields', {})
            )
            
            # Validate content
            validation_result = self.validator.validate_content(content_body, metadata)
            
            if not validation_result.is_valid:
                logger.warning(f"Content validation failed for {file_id}: {validation_result.errors}")
            
            # Store metadata
            self.content_index[file_id] = metadata
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error indexing content file {file_path}: {e}")
            return None
    
    async def build_content_links(self) -> None:
        """Build content links from dependencies and references"""
        self.content_links.clear()
        
        for item_id, metadata in self.content_index.items():
            # Add dependency links
            for dep_id in metadata.dependencies:
                if dep_id in self.content_index:
                    link = ContentLink(
                        source_id=item_id,
                        target_id=dep_id,
                        link_type="dependency",
                        context=f"{metadata.title} depends on {self.content_index[dep_id].title}"
                    )
                    self.content_links.append(link)
            
            # Add related content links
            for related_id in metadata.related_content:
                if related_id in self.content_index:
                    link = ContentLink(
                        source_id=item_id,
                        target_id=related_id,
                        link_type="related",
                        context=f"Related to {self.content_index[related_id].title}"
                    )
                    self.content_links.append(link)
    
    async def save_content_links(self) -> None:
        """Save content links to file"""
        try:
            data = [asdict(link) for link in self.content_links]
            async with aiofiles.open(self.links_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"Saved {len(self.content_links)} content links")
        except Exception as e:
            logger.error(f"Error saving content links: {e}")
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from content"""
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
    
    def _generate_description(self, content: str, max_length: int = 200) -> str:
        """Generate description from content"""
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
    
    def _estimate_read_time(self, content: str) -> int:
        """Estimate reading time in minutes"""
        # Average reading speed: 200 words per minute
        words = len(content.split())
        return max(1, words // 200)
    
    async def get_content_by_category(self, category: str) -> List[ContentMetadata]:
        """Get all content in a specific category"""
        return [metadata for metadata in self.content_index.values() if metadata.category == category]
    
    async def get_content_by_service(self, service: str) -> List[ContentMetadata]:
        """Get all content for a specific service"""
        return [metadata for metadata in self.content_index.values() if metadata.service == service or metadata.service == 'all']
    
    async def get_content_by_difficulty(self, difficulty: str) -> List[ContentMetadata]:
        """Get all content for a specific difficulty level"""
        return [metadata for metadata in self.content_index.values() if metadata.difficulty == difficulty]
    
    async def get_related_content(self, item_id: str) -> List[ContentMetadata]:
        """Get content related to a specific item"""
        if item_id not in self.content_index:
            return []
        
        related_ids = self.content_index[item_id].related_content
        return [self.content_index[rid] for rid in related_ids if rid in self.content_index]
    
    async def get_content_dependencies(self, item_id: str) -> List[ContentMetadata]:
        """Get content dependencies for a specific item"""
        if item_id not in self.content_index:
            return []
        
        dep_ids = self.content_index[item_id].dependencies
        return [self.content_index[did] for did in dep_ids if did in self.content_index]
    
    async def validate_all_content(self) -> Dict[str, ContentValidationResult]:
        """Validate all content in the index"""
        results = {}
        
        for item_id, metadata in self.content_index.items():
            # Read content file
            file_path = self.docs_dir / metadata.title.replace(' ', '_').lower() + '.md'
            if file_path.exists():
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Validate content
                result = self.validator.validate_content(content, metadata)
                results[item_id] = result
        
        return results
    
    async def generate_content_report(self) -> Dict[str, Any]:
        """Generate comprehensive content report"""
        total_items = len(self.content_index)
        
        # Count by category
        categories = {}
        for metadata in self.content_index.values():
            categories[metadata.category] = categories.get(metadata.category, 0) + 1
        
        # Count by service
        services = {}
        for metadata in self.content_index.values():
            services[metadata.service] = services.get(metadata.service, 0) + 1
        
        # Count by difficulty
        difficulties = {}
        for metadata in self.content_index.values():
            difficulties[metadata.difficulty] = difficulties.get(metadata.difficulty, 0) + 1
        
        # Count by status
        statuses = {}
        for metadata in self.content_index.values():
            statuses[metadata.status] = statuses.get(metadata.status, 0) + 1
        
        # Calculate average quality score
        validation_results = await self.validate_all_content()
        avg_quality_score = sum(result.score for result in validation_results.values()) / len(validation_results) if validation_results else 0
        
        return {
            "total_items": total_items,
            "categories": categories,
            "services": services,
            "difficulties": difficulties,
            "statuses": statuses,
            "average_quality_score": round(avg_quality_score, 2),
            "total_links": len(self.content_links),
            "last_updated": datetime.now().isoformat()
        }

# Import aiofiles for async file operations
try:
    import aiofiles
except ImportError:
    logger.warning("aiofiles not available. Install with: pip install aiofiles")
    # Fallback to synchronous file operations
    import aiofiles
    aiofiles.open = open

async def main():
    """Main function to demonstrate content management"""
    docs_dir = Path(__file__).parent
    content_manager = ContentManager(docs_dir)
    
    # Load existing index
    await content_manager.load_content_index()
    
    # Index all markdown files
    markdown_files = list(docs_dir.rglob("*.md"))
    for md_file in markdown_files:
        await content_manager.index_content_file(md_file)
    
    # Build content links
    await content_manager.build_content_links()
    
    # Save index and links
    await content_manager.save_content_index()
    await content_manager.save_content_links()
    
    # Generate report
    report = await content_manager.generate_content_report()
    print("Content Management Report:")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())