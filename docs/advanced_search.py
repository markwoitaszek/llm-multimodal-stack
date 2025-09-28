#!/usr/bin/env python3
"""
Advanced Search System for Documentation
Part of Issue #71: Documentation Rendering & Navigation

This module provides advanced search capabilities including:
- Full-text search with relevance scoring
- Faceted search with filters
- Search suggestions and autocomplete
- Search analytics and optimization
- Real-time search with debouncing
"""

import re
import json
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from collections import defaultdict, Counter
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a search result"""
    item_id: str
    title: str
    excerpt: str
    content: str
    type: str
    service: str
    language: str
    url: str
    last_modified: str
    tags: List[str]
    score: float
    highlights: List[str]
    matched_terms: List[str]

@dataclass
class SearchFilters:
    """Search filters for faceted search"""
    content_type: Optional[str] = None
    service: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    date_range: Optional[Tuple[str, str]] = None
    author: Optional[str] = None

@dataclass
class SearchSuggestion:
    """Search suggestion for autocomplete"""
    text: str
    type: str  # 'term', 'phrase', 'content'
    frequency: int
    context: str

@dataclass
class SearchAnalytics:
    """Search analytics data"""
    query: str
    timestamp: str
    results_count: int
    clicked_result: Optional[str] = None
    filters_applied: Optional[Dict[str, str]] = None
    search_time_ms: Optional[int] = None

class SearchIndex:
    """Inverted index for fast text search"""
    
    def __init__(self):
        self.index: Dict[str, Set[str]] = defaultdict(set)
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.term_frequencies: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.document_frequencies: Dict[str, int] = {}
        self.total_documents = 0
    
    def add_document(self, doc_id: str, content: Dict[str, Any]) -> None:
        """Add a document to the index"""
        self.documents[doc_id] = content
        self.total_documents += 1
        
        # Index all text fields
        text_fields = ['title', 'content', 'excerpt', 'tags']
        all_text = []
        
        for field in text_fields:
            if field in content:
                if isinstance(content[field], list):
                    all_text.extend(content[field])
                else:
                    all_text.append(str(content[field]))
        
        # Tokenize and index
        tokens = self._tokenize(' '.join(all_text))
        term_counts = Counter(tokens)
        
        for term, count in term_counts.items():
            self.index[term].add(doc_id)
            self.term_frequencies[term][doc_id] = count
        
        # Update document frequencies
        for term in term_counts.keys():
            self.document_frequencies[term] = len(self.index[term])
    
    def remove_document(self, doc_id: str) -> None:
        """Remove a document from the index"""
        if doc_id not in self.documents:
            return
        
        # Remove from term frequencies
        for term, doc_freqs in self.term_frequencies.items():
            if doc_id in doc_freqs:
                del doc_freqs[doc_id]
        
        # Remove from index
        for term, docs in self.index.items():
            docs.discard(doc_id)
            if not docs:
                del self.index[term]
                del self.document_frequencies[term]
        
        del self.documents[doc_id]
        self.total_documents -= 1
    
    def search(self, query: str, filters: Optional[SearchFilters] = None) -> List[SearchResult]:
        """Search the index with optional filters"""
        if not query.strip():
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # Find matching documents
        matching_docs = self._find_matching_documents(query_tokens)
        
        # Apply filters
        if filters:
            matching_docs = self._apply_filters(matching_docs, filters)
        
        # Calculate relevance scores
        results = []
        for doc_id in matching_docs:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                score = self._calculate_relevance_score(query_tokens, doc_id)
                highlights = self._generate_highlights(query_tokens, doc)
                matched_terms = self._find_matched_terms(query_tokens, doc_id)
                
                result = SearchResult(
                    item_id=doc_id,
                    title=doc.get('title', ''),
                    excerpt=doc.get('excerpt', ''),
                    content=doc.get('content', ''),
                    type=doc.get('type', ''),
                    service=doc.get('service', ''),
                    language=doc.get('language', ''),
                    url=doc.get('url', ''),
                    last_modified=doc.get('last_modified', ''),
                    tags=doc.get('tags', []),
                    score=score,
                    highlights=highlights,
                    matched_terms=matched_terms
                )
                results.append(result)
        
        # Sort by relevance score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable terms"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Filter out stop words and short words
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'this', 'these', 'they', 'them',
            'their', 'there', 'then', 'than', 'or', 'but', 'not', 'no',
            'so', 'if', 'when', 'where', 'why', 'how', 'what', 'which',
            'who', 'whom', 'whose', 'can', 'could', 'should', 'would',
            'may', 'might', 'must', 'shall', 'do', 'does', 'did', 'have',
            'had', 'has', 'been', 'being', 'am', 'are', 'is', 'was', 'were'
        }
        
        # Filter words
        filtered_words = []
        for word in words:
            if len(word) > 2 and word not in stop_words:
                filtered_words.append(word)
        
        return filtered_words
    
    def _find_matching_documents(self, query_tokens: List[str]) -> Set[str]:
        """Find documents that match the query tokens"""
        if not query_tokens:
            return set()
        
        # Start with documents containing the first token
        matching_docs = set(self.index.get(query_tokens[0], []))
        
        # Intersect with documents containing other tokens
        for token in query_tokens[1:]:
            token_docs = set(self.index.get(token, []))
            matching_docs = matching_docs.intersection(token_docs)
        
        # If no documents match all tokens, try union
        if not matching_docs:
            matching_docs = set()
            for token in query_tokens:
                matching_docs.update(self.index.get(token, []))
        
        return matching_docs
    
    def _apply_filters(self, doc_ids: Set[str], filters: SearchFilters) -> Set[str]:
        """Apply filters to document IDs"""
        filtered_docs = set(doc_ids)
        
        for doc_id in doc_ids:
            if doc_id not in self.documents:
                filtered_docs.discard(doc_id)
                continue
            
            doc = self.documents[doc_id]
            
            # Apply content type filter
            if filters.content_type and doc.get('type') != filters.content_type:
                filtered_docs.discard(doc_id)
                continue
            
            # Apply service filter
            if filters.service and doc.get('service') != filters.service and doc.get('service') != 'all':
                filtered_docs.discard(doc_id)
                continue
            
            # Apply language filter
            if filters.language and doc.get('language') != filters.language and doc.get('language') != 'all':
                filtered_docs.discard(doc_id)
                continue
            
            # Apply difficulty filter
            if filters.difficulty and doc.get('difficulty') != filters.difficulty:
                filtered_docs.discard(doc_id)
                continue
            
            # Apply category filter
            if filters.category and doc.get('category') != filters.category:
                filtered_docs.discard(doc_id)
                continue
            
            # Apply tags filter
            if filters.tags:
                doc_tags = doc.get('tags', [])
                if not any(tag in doc_tags for tag in filters.tags):
                    filtered_docs.discard(doc_id)
                    continue
            
            # Apply author filter
            if filters.author and doc.get('author') != filters.author:
                filtered_docs.discard(doc_id)
                continue
        
        return filtered_docs
    
    def _calculate_relevance_score(self, query_tokens: List[str], doc_id: str) -> float:
        """Calculate TF-IDF relevance score"""
        score = 0.0
        
        for token in query_tokens:
            if token in self.term_frequencies and doc_id in self.term_frequencies[token]:
                # Term frequency in document
                tf = self.term_frequencies[token][doc_id]
                
                # Inverse document frequency
                idf = math.log(self.total_documents / self.document_frequencies[token])
                
                # TF-IDF score
                score += tf * idf
        
        # Boost score for title matches
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            title_tokens = self._tokenize(doc.get('title', ''))
            for token in query_tokens:
                if token in title_tokens:
                    score += 2.0  # Boost for title matches
        
        return score
    
    def _generate_highlights(self, query_tokens: List[str], doc: Dict[str, Any]) -> List[str]:
        """Generate highlighted excerpts"""
        highlights = []
        
        # Highlight in title
        title = doc.get('title', '')
        if title:
            highlighted_title = self._highlight_text(title, query_tokens)
            if highlighted_title != title:
                highlights.append(f"Title: {highlighted_title}")
        
        # Highlight in excerpt
        excerpt = doc.get('excerpt', '')
        if excerpt:
            highlighted_excerpt = self._highlight_text(excerpt, query_tokens)
            if highlighted_excerpt != excerpt:
                highlights.append(f"Excerpt: {highlighted_excerpt}")
        
        # Highlight in content (first few matches)
        content = doc.get('content', '')
        if content:
            content_highlights = self._highlight_content_snippets(content, query_tokens, max_snippets=3)
            highlights.extend(content_highlights)
        
        return highlights
    
    def _highlight_text(self, text: str, query_tokens: List[str]) -> str:
        """Highlight query terms in text"""
        highlighted_text = text
        
        for token in query_tokens:
            # Case-insensitive replacement
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            highlighted_text = pattern.sub(f'<mark>{token}</mark>', highlighted_text)
        
        return highlighted_text
    
    def _highlight_content_snippets(self, content: str, query_tokens: List[str], max_snippets: int = 3) -> List[str]:
        """Generate highlighted content snippets"""
        snippets = []
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            if any(token.lower() in sentence.lower() for token in query_tokens):
                highlighted_sentence = self._highlight_text(sentence.strip(), query_tokens)
                if highlighted_sentence != sentence.strip():
                    snippets.append(f"Content: {highlighted_sentence}")
                    if len(snippets) >= max_snippets:
                        break
        
        return snippets
    
    def _find_matched_terms(self, query_tokens: List[str], doc_id: str) -> List[str]:
        """Find which query terms matched in the document"""
        matched_terms = []
        
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            doc_text = ' '.join([
                doc.get('title', ''),
                doc.get('content', ''),
                doc.get('excerpt', ''),
                ' '.join(doc.get('tags', []))
            ]).lower()
            
            for token in query_tokens:
                if token in doc_text:
                    matched_terms.append(token)
        
        return matched_terms

class SearchSuggester:
    """Provides search suggestions and autocomplete"""
    
    def __init__(self, search_index: SearchIndex):
        self.search_index = search_index
        self.suggestion_cache: Dict[str, List[SearchSuggestion]] = {}
        self.popular_queries: Counter = Counter()
    
    def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[SearchSuggestion]:
        """Get search suggestions for a query"""
        if not query.strip():
            return self._get_popular_suggestions(max_suggestions)
        
        # Check cache first
        cache_key = query.lower()
        if cache_key in self.suggestion_cache:
            return self.suggestion_cache[cache_key][:max_suggestions]
        
        suggestions = []
        
        # Get term-based suggestions
        term_suggestions = self._get_term_suggestions(query)
        suggestions.extend(term_suggestions)
        
        # Get phrase suggestions
        phrase_suggestions = self._get_phrase_suggestions(query)
        suggestions.extend(phrase_suggestions)
        
        # Get content-based suggestions
        content_suggestions = self._get_content_suggestions(query)
        suggestions.extend(content_suggestions)
        
        # Sort by frequency and relevance
        suggestions.sort(key=lambda x: x.frequency, reverse=True)
        
        # Cache results
        self.suggestion_cache[cache_key] = suggestions
        
        return suggestions[:max_suggestions]
    
    def _get_popular_suggestions(self, max_suggestions: int) -> List[SearchSuggestion]:
        """Get popular search suggestions"""
        suggestions = []
        
        # Get popular terms from index
        popular_terms = sorted(
            self.search_index.document_frequencies.items(),
            key=lambda x: x[1],
            reverse=True
        )[:max_suggestions]
        
        for term, frequency in popular_terms:
            suggestions.append(SearchSuggestion(
                text=term,
                type='term',
                frequency=frequency,
                context=f'Popular search term'
            ))
        
        return suggestions
    
    def _get_term_suggestions(self, query: str) -> List[SearchSuggestion]:
        """Get term-based suggestions"""
        suggestions = []
        query_lower = query.lower()
        
        # Find terms that start with the query
        for term in self.search_index.index.keys():
            if term.startswith(query_lower) and term != query_lower:
                frequency = self.search_index.document_frequencies[term]
                suggestions.append(SearchSuggestion(
                    text=term,
                    type='term',
                    frequency=frequency,
                    context=f'Term starting with "{query}"'
                ))
        
        return suggestions
    
    def _get_phrase_suggestions(self, query: str) -> List[SearchSuggestion]:
        """Get phrase-based suggestions"""
        suggestions = []
        
        # This would typically use a phrase index
        # For now, we'll generate simple phrase suggestions
        query_words = query.split()
        if len(query_words) > 1:
            # Try to complete the last word
            last_word = query_words[-1]
            prefix = ' '.join(query_words[:-1])
            
            for term in self.search_index.index.keys():
                if term.startswith(last_word.lower()):
                    phrase = f"{prefix} {term}"
                    frequency = self.search_index.document_frequencies[term]
                    suggestions.append(SearchSuggestion(
                        text=phrase,
                        type='phrase',
                        frequency=frequency,
                        context=f'Phrase completion'
                    ))
        
        return suggestions
    
    def _get_content_suggestions(self, query: str) -> List[SearchSuggestion]:
        """Get content-based suggestions"""
        suggestions = []
        
        # Find documents that match the query
        results = self.search_index.search(query)
        
        for result in results[:5]:  # Top 5 results
            # Extract key terms from the result
            title_tokens = self.search_index._tokenize(result.title)
            for token in title_tokens:
                if token not in query.lower():
                    frequency = self.search_index.document_frequencies.get(token, 0)
                    suggestions.append(SearchSuggestion(
                        text=token,
                        type='content',
                        frequency=frequency,
                        context=f'From "{result.title}"'
                    ))
        
        return suggestions
    
    def record_query(self, query: str) -> None:
        """Record a search query for analytics"""
        self.popular_queries[query.lower()] += 1

class AdvancedSearchEngine:
    """Main search engine with advanced features"""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)
        self.search_index = SearchIndex()
        self.suggester = SearchSuggester(self.search_index)
        self.analytics: List[SearchAnalytics] = []
        self.analytics_file = self.docs_dir / "search_analytics.json"
    
    async def build_index(self) -> None:
        """Build search index from documentation"""
        logger.info("Building search index...")
        
        # Clear existing index
        self.search_index = SearchIndex()
        self.suggester = SearchSuggester(self.search_index)
        
        # Index all markdown files
        markdown_files = list(self.docs_dir.rglob("*.md"))
        
        for md_file in markdown_files:
            try:
                async with aiofiles.open(md_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Parse frontmatter
                metadata, content_body = self._parse_frontmatter(content)
                
                # Generate document ID
                doc_id = str(md_file.relative_to(self.docs_dir)).replace('/', '_').replace('.md', '')
                
                # Create document
                doc = {
                    'title': metadata.get('title', md_file.stem.replace('_', ' ').title()),
                    'content': content_body,
                    'excerpt': self._generate_excerpt(content_body),
                    'type': metadata.get('type', 'page'),
                    'service': metadata.get('service', 'all'),
                    'language': metadata.get('language', 'all'),
                    'url': str(md_file.relative_to(self.docs_dir)),
                    'last_modified': datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
                    'tags': metadata.get('tags', []),
                    'difficulty': metadata.get('difficulty', 'intermediate'),
                    'category': metadata.get('category', 'general'),
                    'author': metadata.get('author', 'Documentation Team')
                }
                
                # Add to index
                self.search_index.add_document(doc_id, doc)
                
            except Exception as e:
                logger.error(f"Error indexing {md_file}: {e}")
        
        logger.info(f"Indexed {self.search_index.total_documents} documents")
    
    async def search(self, query: str, filters: Optional[SearchFilters] = None, max_results: int = 50) -> List[SearchResult]:
        """Perform advanced search"""
        start_time = datetime.now()
        
        # Record query for analytics
        self.suggester.record_query(query)
        
        # Perform search
        results = self.search_index.search(query, filters)
        
        # Limit results
        results = results[:max_results]
        
        # Record analytics
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        analytics = SearchAnalytics(
            query=query,
            timestamp=start_time.isoformat(),
            results_count=len(results),
            search_time_ms=int(search_time),
            filters_applied=asdict(filters) if filters else None
        )
        self.analytics.append(analytics)
        
        return results
    
    async def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[SearchSuggestion]:
        """Get search suggestions"""
        return self.suggester.get_suggestions(query, max_suggestions)
    
    async def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics"""
        if not self.analytics:
            return {"message": "No search analytics available"}
        
        # Calculate statistics
        total_searches = len(self.analytics)
        avg_results = sum(a.results_count for a in self.analytics) / total_searches
        avg_search_time = sum(a.search_time_ms for a in self.analytics if a.search_time_ms) / total_searches
        
        # Most popular queries
        query_counts = Counter(a.query for a in self.analytics)
        popular_queries = query_counts.most_common(10)
        
        # Search patterns
        queries_with_results = sum(1 for a in self.analytics if a.results_count > 0)
        success_rate = queries_with_results / total_searches * 100
        
        return {
            "total_searches": total_searches,
            "average_results_per_search": round(avg_results, 2),
            "average_search_time_ms": round(avg_search_time, 2),
            "success_rate_percent": round(success_rate, 2),
            "popular_queries": popular_queries,
            "last_updated": datetime.now().isoformat()
        }
    
    async def save_analytics(self) -> None:
        """Save search analytics to file"""
        try:
            data = [asdict(analytics) for analytics in self.analytics]
            async with aiofiles.open(self.analytics_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"Saved {len(self.analytics)} search analytics records")
        except Exception as e:
            logger.error(f"Error saving search analytics: {e}")
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from content"""
        metadata = {}
        
        if content.startswith('---'):
            try:
                import yaml
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    content = parts[2].strip()
                    metadata = yaml.safe_load(frontmatter) or {}
            except Exception as e:
                logger.warning(f"Error parsing frontmatter: {e}")
        
        return metadata, content
    
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

async def main():
    """Main function to demonstrate advanced search"""
    docs_dir = Path(__file__).parent
    search_engine = AdvancedSearchEngine(docs_dir)
    
    # Build search index
    await search_engine.build_index()
    
    # Example searches
    test_queries = [
        "API documentation",
        "multimodal worker",
        "authentication",
        "python examples"
    ]
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        results = await search_engine.search(query, max_results=5)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.title} (Score: {result.score:.2f})")
            print(f"   {result.excerpt[:100]}...")
            print(f"   Type: {result.type}, Service: {result.service}")
            print()
    
    # Get suggestions
    print("Search suggestions for 'API':")
    suggestions = await search_engine.get_suggestions("API", max_suggestions=5)
    for suggestion in suggestions:
        print(f"- {suggestion.text} ({suggestion.type}, freq: {suggestion.frequency})")
    
    # Get analytics
    analytics = await search_engine.get_search_analytics()
    print(f"\nSearch Analytics:")
    print(json.dumps(analytics, indent=2))

if __name__ == "__main__":
    asyncio.run(main())