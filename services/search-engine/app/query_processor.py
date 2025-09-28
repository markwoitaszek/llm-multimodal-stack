"""
Query processing and optimization for the search engine service
"""
import logging
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import httpx
from difflib import SequenceMatcher

from .config import settings
from .models import SearchType, ContentType, SearchSuggestion

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Processes and optimizes search queries"""
    
    def __init__(self):
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'would', 'you', 'your'
        }
        
        # Common misspellings and corrections
        self.spell_corrections = {
            'teh': 'the',
            'adn': 'and',
            'recieve': 'receive',
            'seperate': 'separate',
            'occured': 'occurred',
            'definately': 'definitely',
            'accomodate': 'accommodate',
            'begining': 'beginning',
            'calender': 'calendar',
            'cemetary': 'cemetery'
        }
        
        # Query expansion synonyms
        self.synonyms = {
            'car': ['automobile', 'vehicle', 'auto'],
            'house': ['home', 'residence', 'dwelling'],
            'dog': ['canine', 'pet', 'puppy'],
            'cat': ['feline', 'kitten', 'kitty'],
            'computer': ['pc', 'laptop', 'desktop', 'machine'],
            'phone': ['mobile', 'cellphone', 'smartphone'],
            'book': ['novel', 'publication', 'tome'],
            'movie': ['film', 'cinema', 'picture'],
            'music': ['song', 'tune', 'melody'],
            'food': ['meal', 'cuisine', 'dish']
        }
    
    async def process_query(
        self,
        query: str,
        search_type: SearchType = SearchType.SEMANTIC,
        expand_query: bool = True,
        spell_check: bool = True
    ) -> Dict[str, Any]:
        """Process and optimize a search query"""
        start_time = datetime.utcnow()
        
        try:
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Spell check if enabled
            if spell_check and settings.enable_spell_check:
                corrected_query = self._spell_check(cleaned_query)
            else:
                corrected_query = cleaned_query
            
            # Extract query components
            query_components = self._extract_query_components(corrected_query)
            
            # Expand query if enabled
            expanded_terms = []
            if expand_query and settings.enable_query_expansion:
                expanded_terms = self._expand_query(corrected_query)
            
            # Generate query variations
            query_variations = self._generate_query_variations(corrected_query)
            
            # Extract filters and facets
            filters = self._extract_filters(corrected_query)
            
            # Determine search intent
            search_intent = self._determine_search_intent(corrected_query)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                'original_query': query,
                'cleaned_query': cleaned_query,
                'corrected_query': corrected_query,
                'query_components': query_components,
                'expanded_terms': expanded_terms,
                'query_variations': query_variations,
                'filters': filters,
                'search_intent': search_intent,
                'processing_time_ms': processing_time,
                'search_type': search_type
            }
            
        except Exception as e:
            logger.error(f"Failed to process query '{query}': {e}")
            return {
                'original_query': query,
                'cleaned_query': query,
                'corrected_query': query,
                'query_components': {'terms': query.split()},
                'expanded_terms': [],
                'query_variations': [query],
                'filters': {},
                'search_intent': 'general',
                'processing_time_ms': 0,
                'search_type': search_type,
                'error': str(e)
            }
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Remove special characters but keep alphanumeric, spaces, and basic punctuation
        query = re.sub(r'[^\w\s\-\.]', ' ', query)
        
        # Remove multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        return query.lower()
    
    def _spell_check(self, query: str) -> str:
        """Basic spell checking using predefined corrections"""
        words = query.split()
        corrected_words = []
        
        for word in words:
            if word in self.spell_corrections:
                corrected_words.append(self.spell_corrections[word])
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _extract_query_components(self, query: str) -> Dict[str, Any]:
        """Extract components from the query"""
        words = query.split()
        
        # Remove stop words
        content_words = [word for word in words if word not in self.stop_words]
        
        # Extract phrases (2-3 word combinations)
        phrases = []
        for i in range(len(words) - 1):
            phrase = ' '.join(words[i:i+2])
            phrases.append(phrase)
        
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            phrases.append(phrase)
        
        # Extract potential entities (capitalized words, numbers, etc.)
        entities = []
        for word in words:
            if word.isdigit() or (word[0].isupper() and len(word) > 2):
                entities.append(word)
        
        return {
            'terms': words,
            'content_words': content_words,
            'phrases': phrases,
            'entities': entities,
            'stop_words': [word for word in words if word in self.stop_words]
        }
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms"""
        expanded_terms = []
        words = query.split()
        
        for word in words:
            if word in self.synonyms:
                expanded_terms.extend(self.synonyms[word])
        
        return list(set(expanded_terms))  # Remove duplicates
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate variations of the query"""
        variations = [query]
        
        # Add version without stop words
        words = query.split()
        content_words = [word for word in words if word not in self.stop_words]
        if len(content_words) != len(words):
            variations.append(' '.join(content_words))
        
        # Add version with expanded terms
        expanded_terms = self._expand_query(query)
        if expanded_terms:
            variations.append(f"{query} {' '.join(expanded_terms[:3])}")
        
        return list(set(variations))
    
    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters from the query"""
        filters = {}
        
        # Date filters
        date_patterns = [
            r'(\d{4})',  # Year
            r'(\d{1,2}/\d{1,2}/\d{4})',  # Date
            r'(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                filters['date'] = matches
        
        # Content type filters
        content_type_keywords = {
            'image': ['image', 'picture', 'photo', 'jpg', 'png', 'gif'],
            'video': ['video', 'movie', 'film', 'mp4', 'avi', 'mov'],
            'text': ['text', 'document', 'pdf', 'doc', 'txt'],
            'audio': ['audio', 'sound', 'music', 'mp3', 'wav']
        }
        
        for content_type, keywords in content_type_keywords.items():
            if any(keyword in query.lower() for keyword in keywords):
                filters['content_type'] = content_type
                break
        
        # Size filters
        size_patterns = [
            r'(\d+)\s*(mb|gb|kb)',  # File size
            r'(\d+)\s*(pixels?|px)',  # Image size
            r'(\d+)\s*(minutes?|hours?)'  # Duration
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                filters['size'] = matches
        
        return filters
    
    def _determine_search_intent(self, query: str) -> str:
        """Determine the search intent from the query"""
        query_lower = query.lower()
        
        # Question intent
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        if any(word in query_lower for word in question_words) or query.endswith('?'):
            return 'question'
        
        # Navigational intent (looking for specific site/page)
        navigational_words = ['site:', 'url:', 'www.', 'http']
        if any(word in query_lower for word in navigational_words):
            return 'navigational'
        
        # Informational intent
        informational_words = ['information', 'about', 'explain', 'define', 'meaning']
        if any(word in query_lower for word in informational_words):
            return 'informational'
        
        # Transactional intent
        transactional_words = ['buy', 'purchase', 'download', 'order', 'price', 'cost']
        if any(word in query_lower for word in transactional_words):
            return 'transactional'
        
        # Default to general search
        return 'general'
    
    async def generate_autocomplete_suggestions(
        self,
        partial_query: str,
        limit: int = 10
    ) -> List[str]:
        """Generate autocomplete suggestions for partial query"""
        if len(partial_query) < 2:
            return []
        
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Add common completions
        common_queries = [
            'how to', 'what is', 'best', 'top', 'latest', 'new',
            'tutorial', 'guide', 'example', 'review', 'comparison'
        ]
        
        for common in common_queries:
            if common.startswith(partial_lower):
                suggestions.append(common)
        
        # Add query variations
        words = partial_query.split()
        if len(words) > 0:
            last_word = words[-1]
            
            # Find words that start with the last word
            for word_list in self.synonyms.values():
                for word in word_list:
                    if word.startswith(last_word.lower()):
                        suggestion = ' '.join(words[:-1] + [word])
                        suggestions.append(suggestion)
        
        # Remove duplicates and limit results
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:limit]
    
    async def generate_search_suggestions(
        self,
        query: str,
        limit: int = 10
    ) -> List[SearchSuggestion]:
        """Generate search suggestions for a query"""
        suggestions = []
        
        # Query corrections
        corrected_query = self._spell_check(query)
        if corrected_query != query:
            suggestions.append(SearchSuggestion(
                text=corrected_query,
                type='correction',
                score=0.9,
                metadata={'original': query}
            ))
        
        # Query expansions
        expanded_terms = self._expand_query(query)
        for term in expanded_terms[:3]:
            expanded_query = f"{query} {term}"
            suggestions.append(SearchSuggestion(
                text=expanded_query,
                type='expansion',
                score=0.7,
                metadata={'added_term': term}
            ))
        
        # Related queries
        query_variations = self._generate_query_variations(query)
        for variation in query_variations[1:4]:  # Skip the original
            suggestions.append(SearchSuggestion(
                text=variation,
                type='related',
                score=0.6,
                metadata={'variation_type': 'query_variation'}
            ))
        
        # Sort by score and return top results
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:limit]
    
    def calculate_query_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries"""
        return SequenceMatcher(None, query1.lower(), query2.lower()).ratio()
    
    def extract_keywords(self, query: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from query"""
        words = query.split()
        
        # Remove stop words and short words
        keywords = [
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        ]
        
        # Sort by length (longer words are often more specific)
        keywords.sort(key=len, reverse=True)
        
        return keywords[:max_keywords]
    
    def is_valid_query(self, query: str) -> Tuple[bool, str]:
        """Validate query and return validation result"""
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        if len(query) > settings.max_query_length:
            return False, f"Query too long (max {settings.max_query_length} characters)"
        
        # Check for potentially malicious patterns
        malicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'onload=',
            r'onerror='
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Query contains potentially malicious content"
        
        return True, "Valid query"
    
    async def optimize_query_for_search_type(
        self,
        query: str,
        search_type: SearchType
    ) -> str:
        """Optimize query based on search type"""
        if search_type == SearchType.SEMANTIC:
            # For semantic search, keep the full query
            return query
        
        elif search_type == SearchType.KEYWORD:
            # For keyword search, focus on content words
            words = query.split()
            content_words = [word for word in words if word not in self.stop_words]
            return ' '.join(content_words)
        
        elif search_type == SearchType.HYBRID:
            # For hybrid search, balance between full query and keywords
            words = query.split()
            if len(words) > 5:
                # If query is long, focus on key terms
                content_words = [word for word in words if word not in self.stop_words]
                return ' '.join(content_words[:5])
            return query
        
        return query

# Global query processor instance
query_processor = QueryProcessor()