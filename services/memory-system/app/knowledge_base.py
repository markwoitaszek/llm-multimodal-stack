"""
Knowledge base management for the memory system service
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from .database import DatabaseManager
from .cache import CacheManager
from .models import (
    KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse, KnowledgeCategory,
    KnowledgeSearchRequest, KnowledgeSearchResponse
)

logger = logging.getLogger(__name__)

class KnowledgeManager:
    """Manages knowledge base operations and search"""
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        self.db = db_manager
        self.cache = cache_manager
    
    async def create_knowledge(self, knowledge_data: KnowledgeCreate) -> KnowledgeResponse:
        """Create a new knowledge base entry"""
        try:
            knowledge_id = await self.db.create_knowledge(knowledge_data)
            
            # Get the created knowledge entry
            knowledge_dict = await self.db.get_knowledge(knowledge_id)
            if not knowledge_dict:
                raise RuntimeError("Failed to retrieve created knowledge entry")
            
            knowledge = KnowledgeResponse(**knowledge_dict)
            
            # Invalidate agent knowledge cache
            await self.cache.invalidate_agent_knowledge(knowledge_data.agent_id)
            
            logger.info(f"Created knowledge entry {knowledge_id} for agent {knowledge_data.agent_id}")
            return knowledge
            
        except Exception as e:
            logger.error(f"Failed to create knowledge entry: {e}")
            raise
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeResponse]:
        """Get knowledge base entry by ID"""
        try:
            knowledge_dict = await self.db.get_knowledge(knowledge_id)
            if not knowledge_dict:
                return None
            
            return KnowledgeResponse(**knowledge_dict)
            
        except Exception as e:
            logger.error(f"Failed to get knowledge entry {knowledge_id}: {e}")
            return None
    
    async def update_knowledge(self, knowledge_id: str, update_data: KnowledgeUpdate) -> bool:
        """Update knowledge base entry"""
        try:
            # Get current knowledge to find agent_id
            current_knowledge = await self.get_knowledge(knowledge_id)
            if not current_knowledge:
                return False
            
            success = await self.db.update_knowledge(knowledge_id, update_data)
            
            if success:
                # Invalidate agent knowledge cache
                await self.cache.invalidate_agent_knowledge(current_knowledge.agent_id)
                logger.info(f"Updated knowledge entry {knowledge_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update knowledge entry {knowledge_id}: {e}")
            return False
    
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete knowledge base entry"""
        try:
            # Get current knowledge to find agent_id
            current_knowledge = await self.get_knowledge(knowledge_id)
            if not current_knowledge:
                return False
            
            success = await self.db.delete_knowledge(knowledge_id)
            
            if success:
                # Invalidate agent knowledge cache
                await self.cache.invalidate_agent_knowledge(current_knowledge.agent_id)
                logger.info(f"Deleted knowledge entry {knowledge_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge entry {knowledge_id}: {e}")
            return False
    
    async def list_knowledge(self, agent_id: str, category: Optional[KnowledgeCategory] = None,
                           limit: int = 50, offset: int = 0) -> List[KnowledgeResponse]:
        """List knowledge base entries for an agent"""
        try:
            # Try cache first for common requests
            if offset == 0 and category is None and limit <= 50:
                cached_knowledge = await self.cache.get_cached_knowledge_list(agent_id)
                if cached_knowledge:
                    return cached_knowledge[:limit]
            
            # Get from database
            knowledge_dicts = await self.db.list_knowledge(
                agent_id, category.value if category else None, limit, offset
            )
            knowledge_items = [KnowledgeResponse(**kb_dict) for kb_dict in knowledge_dicts]
            
            # Cache common requests
            if offset == 0 and category is None and limit <= 50:
                await self.cache.cache_knowledge_list(agent_id, knowledge_items)
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Failed to list knowledge for agent {agent_id}: {e}")
            return []
    
    async def search_knowledge(self, search_request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        """Search knowledge base entries"""
        try:
            # Try cache first
            cached_results = await self.cache.get_cached_knowledge_search(
                search_request.agent_id, search_request.query
            )
            if cached_results:
                # Apply additional filters if needed
                filtered_results = self._filter_search_results(
                    cached_results, search_request.category, search_request.tags
                )
                return KnowledgeSearchResponse(
                    results=filtered_results[:search_request.limit],
                    total_found=len(filtered_results),
                    query=search_request.query,
                    search_time_ms=0  # Cached result
                )
            
            # Search in database
            start_time = datetime.now()
            knowledge_dicts = await self.db.search_knowledge(
                search_request.agent_id,
                search_request.query,
                search_request.category.value if search_request.category else None,
                search_request.tags
            )
            
            # Convert to response objects
            knowledge_items = [KnowledgeResponse(**kb_dict) for kb_dict in knowledge_dicts]
            
            # Apply relevance threshold
            filtered_items = [
                kb for kb in knowledge_items 
                if hasattr(kb, 'rank') and getattr(kb, 'rank', 0) >= search_request.threshold
            ]
            
            # Cache the results
            await self.cache.cache_knowledge_search(
                search_request.agent_id, search_request.query, knowledge_items
            )
            
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return KnowledgeSearchResponse(
                results=filtered_items[:search_request.limit],
                total_found=len(filtered_items),
                query=search_request.query,
                search_time_ms=int(search_time)
            )
            
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return KnowledgeSearchResponse(
                results=[],
                total_found=0,
                query=search_request.query,
                search_time_ms=0
            )
    
    def _filter_search_results(self, results: List[KnowledgeResponse], 
                             category: Optional[KnowledgeCategory] = None,
                             tags: Optional[List[str]] = None) -> List[KnowledgeResponse]:
        """Filter search results by category and tags"""
        filtered = results
        
        if category:
            filtered = [kb for kb in filtered if kb.category == category]
        
        if tags:
            filtered = [
                kb for kb in filtered 
                if kb.tags and any(tag in kb.tags for tag in tags)
            ]
        
        return filtered
    
    async def extract_knowledge_from_conversation(self, agent_id: str, conv_id: str, 
                                                messages: List[Dict[str, Any]]) -> List[KnowledgeCreate]:
        """Extract knowledge from conversation messages"""
        try:
            extracted_knowledge = []
            
            # Simple extraction logic - look for factual statements, procedures, preferences
            for message in messages:
                if message.get('role') == 'assistant' and len(message.get('content', '')) > 50:
                    content = message['content']
                    
                    # Extract facts (simple heuristic: statements with "is", "are", "has", etc.)
                    if any(indicator in content.lower() for indicator in ['is', 'are', 'has', 'have', 'contains']):
                        knowledge = KnowledgeCreate(
                            agent_id=agent_id,
                            category=KnowledgeCategory.FACT,
                            title=f"Fact from conversation {conv_id[:8]}",
                            content=content,
                            tags=["extracted", "conversation"],
                            metadata={"source": "conversation", "conversation_id": conv_id},
                            source=f"conversation:{conv_id}"
                        )
                        extracted_knowledge.append(knowledge)
                    
                    # Extract procedures (simple heuristic: statements with "how to", "steps", etc.)
                    elif any(indicator in content.lower() for indicator in ['how to', 'steps', 'procedure', 'process']):
                        knowledge = KnowledgeCreate(
                            agent_id=agent_id,
                            category=KnowledgeCategory.PROCEDURE,
                            title=f"Procedure from conversation {conv_id[:8]}",
                            content=content,
                            tags=["extracted", "conversation", "procedure"],
                            metadata={"source": "conversation", "conversation_id": conv_id},
                            source=f"conversation:{conv_id}"
                        )
                        extracted_knowledge.append(knowledge)
                    
                    # Extract preferences (simple heuristic: statements with "prefer", "like", "dislike")
                    elif any(indicator in content.lower() for indicator in ['prefer', 'like', 'dislike', 'favorite']):
                        knowledge = KnowledgeCreate(
                            agent_id=agent_id,
                            category=KnowledgeCategory.PREFERENCE,
                            title=f"Preference from conversation {conv_id[:8]}",
                            content=content,
                            tags=["extracted", "conversation", "preference"],
                            metadata={"source": "conversation", "conversation_id": conv_id},
                            source=f"conversation:{conv_id}"
                        )
                        extracted_knowledge.append(knowledge)
            
            logger.info(f"Extracted {len(extracted_knowledge)} knowledge items from conversation {conv_id}")
            return extracted_knowledge
            
        except Exception as e:
            logger.error(f"Failed to extract knowledge from conversation {conv_id}: {e}")
            return []
    
    async def consolidate_knowledge(self, agent_id: str) -> Dict[str, int]:
        """Consolidate and deduplicate knowledge base entries"""
        try:
            # Get all knowledge for agent
            all_knowledge = await self.list_knowledge(agent_id, limit=10000)
            
            # Group by category and content similarity
            consolidated = {}
            duplicates = []
            
            for knowledge in all_knowledge:
                key = f"{knowledge.category}:{knowledge.title.lower().strip()}"
                
                if key in consolidated:
                    # Check content similarity
                    existing = consolidated[key]
                    if self._is_similar_content(existing.content, knowledge.content):
                        duplicates.append(knowledge.id)
                    else:
                        # Merge similar content
                        existing.content += f"\n\nAdditional: {knowledge.content}"
                        await self.update_knowledge(existing.id, KnowledgeUpdate(content=existing.content))
                        duplicates.append(knowledge.id)
                else:
                    consolidated[key] = knowledge
            
            # Delete duplicates
            deleted_count = 0
            for dup_id in duplicates:
                if await self.delete_knowledge(dup_id):
                    deleted_count += 1
            
            logger.info(f"Consolidated knowledge for agent {agent_id}: {deleted_count} duplicates removed")
            return {
                "total_items": len(all_knowledge),
                "duplicates_found": len(duplicates),
                "duplicates_removed": deleted_count,
                "final_count": len(all_knowledge) - deleted_count
            }
            
        except Exception as e:
            logger.error(f"Failed to consolidate knowledge for agent {agent_id}: {e}")
            return {"error": str(e)}
    
    def _is_similar_content(self, content1: str, content2: str, threshold: float = 0.8) -> bool:
        """Check if two content strings are similar (simple implementation)"""
        # Simple similarity check based on word overlap
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    async def get_knowledge_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get knowledge base statistics for an agent"""
        try:
            all_knowledge = await self.list_knowledge(agent_id, limit=10000)
            
            # Calculate stats
            stats = {
                "total_items": len(all_knowledge),
                "category_distribution": {},
                "average_content_length": 0,
                "total_characters": 0,
                "tag_distribution": {},
                "recent_items": 0
            }
            
            recent_cutoff = datetime.utcnow().timestamp() - (7 * 24 * 3600)  # Last 7 days
            
            for knowledge in all_knowledge:
                # Category distribution
                category = knowledge.category.value
                stats["category_distribution"][category] = stats["category_distribution"].get(category, 0) + 1
                
                # Content length
                content_length = len(knowledge.content)
                stats["total_characters"] += content_length
                
                # Recent items
                if knowledge.created_at.timestamp() > recent_cutoff:
                    stats["recent_items"] += 1
                
                # Tag distribution
                if knowledge.tags:
                    for tag in knowledge.tags:
                        stats["tag_distribution"][tag] = stats["tag_distribution"].get(tag, 0) + 1
            
            if all_knowledge:
                stats["average_content_length"] = stats["total_characters"] / len(all_knowledge)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats for agent {agent_id}: {e}")
            return {}