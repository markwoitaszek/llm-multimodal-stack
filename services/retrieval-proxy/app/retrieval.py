"""
Retrieval engine for unified multimodal search and context bundling
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import httpx
import numpy as np
from datetime import datetime
import json

from .config import settings
from .database import DatabaseManager
from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)

class RetrievalEngine:
    """Main retrieval engine for multimodal search and context bundling"""
    
    def __init__(self, db_manager: DatabaseManager, vector_manager: VectorStoreManager):
        self.db_manager = db_manager
        self.vector_manager = vector_manager
        self.multimodal_worker_url = settings.multimodal_worker_url
    
    async def search(self, query: str, modalities: List[str] = None,
                    limit: int = None, filters: Dict[str, Any] = None,
                    score_threshold: float = None) -> Dict[str, Any]:
        """Perform unified multimodal search"""
        try:
            limit = limit or settings.default_search_limit
            limit = min(limit, settings.max_search_limit)
            modalities = modalities or ['text', 'image', 'video']
            score_threshold = score_threshold or settings.similarity_threshold
            
            # Generate query embedding
            query_embedding = await self.generate_query_embedding(query)
            
            # Search vector store
            vector_results = self.vector_manager.search_hybrid(
                query_vector=query_embedding,
                query_text=query,
                limit=limit * 2,  # Get more results for filtering
                score_threshold=score_threshold,
                modalities=modalities
            )
            
            # Enrich results with database information
            enriched_results = await self.enrich_search_results(vector_results)
            
            # Apply additional filters
            if filters:
                enriched_results = self.apply_filters(enriched_results, filters)
            
            # Limit final results
            enriched_results = enriched_results[:limit]
            
            # Create context bundle
            context_bundle = await self.create_context_bundle(enriched_results, query)
            
            # Save search session
            session_id = await self.db_manager.create_search_session(
                query=query,
                filters=filters,
                results_count=len(enriched_results),
                context_bundle=context_bundle
            )
            
            return {
                "session_id": session_id,
                "query": query,
                "modalities": modalities,
                "results_count": len(enriched_results),
                "results": enriched_results,
                "context_bundle": context_bundle,
                "metadata": {
                    "search_timestamp": datetime.utcnow().isoformat(),
                    "filters_applied": filters,
                    "score_threshold": score_threshold
                }
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for search query using multimodal worker"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.multimodal_worker_url}/api/v1/embed/text",
                    json={"text": query},
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return np.array(result["embedding"])
                
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            # Fallback: return zero vector (this should be improved in production)
            return np.zeros(384)
    
    async def enrich_search_results(self, vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich vector search results with database information"""
        enriched_results = []
        
        for result in vector_results:
            try:
                # Get content details from database
                embedding_id = result['id']
                content_info = await self.db_manager.get_content_by_embedding_id(embedding_id)
                
                if content_info:
                    enriched_result = {
                        "embedding_id": embedding_id,
                        "score": result['score'],
                        "modality": result['modality'],
                        "content_type": content_info['content_type'],
                        "content": content_info.get('content', ''),
                        "document_id": content_info['document_id'],
                        "filename": content_info['filename'],
                        "file_type": content_info['file_type'],
                        "metadata": result.get('payload', {}),
                        "citations": self.generate_citations(content_info),
                        "artifacts": await self.get_artifact_links(content_info)
                    }
                    
                    # Add type-specific information
                    if content_info['content_type'] == 'image':
                        enriched_result.update({
                            "image_path": content_info.get('image_path'),
                            "dimensions": {
                                "width": content_info.get('width'),
                                "height": content_info.get('height')
                            },
                            "features": content_info.get('features', {})
                        })
                    
                    elif content_info['content_type'] == 'video':
                        enriched_result.update({
                            "video_path": content_info.get('video_path'),
                            "duration": content_info.get('duration_seconds'),
                            "transcription": content_info.get('content')
                        })
                    
                    elif content_info['content_type'] == 'keyframe':
                        enriched_result.update({
                            "keyframe_path": content_info.get('keyframe_path'),
                            "timestamp": content_info.get('timestamp_seconds'),
                            "video_path": content_info.get('video_path')
                        })
                    
                    elif content_info['content_type'] == 'text':
                        enriched_result.update({
                            "chunk_index": content_info.get('chunk_index'),
                            "text_metadata": content_info.get('metadata', {})
                        })
                    
                    enriched_results.append(enriched_result)
                    
            except Exception as e:
                logger.error(f"Failed to enrich result {result.get('id', 'unknown')}: {e}")
                continue
        
        return enriched_results
    
    def apply_filters(self, results: List[Dict[str, Any]], 
                     filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply additional filters to search results"""
        filtered_results = []
        
        for result in results:
            include = True
            
            # Filter by file type
            if 'file_types' in filters:
                if result.get('file_type') not in filters['file_types']:
                    include = False
            
            # Filter by content type
            if 'content_types' in filters:
                if result.get('content_type') not in filters['content_types']:
                    include = False
            
            # Filter by minimum score
            if 'min_score' in filters:
                if result.get('score', 0) < filters['min_score']:
                    include = False
            
            # Filter by date range (would need to add timestamp to results)
            if 'date_range' in filters:
                # Implementation would depend on having timestamps in results
                pass
            
            if include:
                filtered_results.append(result)
        
        return filtered_results
    
    async def create_context_bundle(self, results: List[Dict[str, Any]], 
                                  query: str) -> Dict[str, Any]:
        """Create a unified context bundle for LLM consumption"""
        try:
            # Group results by type
            grouped_results = {
                'text': [],
                'image': [],
                'video': [],
                'keyframe': []
            }
            
            for result in results:
                content_type = result.get('content_type', 'text')
                grouped_results[content_type].append(result)
            
            # Create context sections
            context_sections = []
            
            # Text context
            if grouped_results['text']:
                text_context = self.create_text_context(grouped_results['text'])
                context_sections.append({
                    "type": "text",
                    "title": "Relevant Text Content",
                    "content": text_context,
                    "count": len(grouped_results['text'])
                })
            
            # Image context
            if grouped_results['image']:
                image_context = self.create_image_context(grouped_results['image'])
                context_sections.append({
                    "type": "image", 
                    "title": "Relevant Images",
                    "content": image_context,
                    "count": len(grouped_results['image'])
                })
            
            # Video context
            if grouped_results['video']:
                video_context = self.create_video_context(grouped_results['video'])
                context_sections.append({
                    "type": "video",
                    "title": "Relevant Videos",
                    "content": video_context,
                    "count": len(grouped_results['video'])
                })
            
            # Keyframe context
            if grouped_results['keyframe']:
                keyframe_context = self.create_keyframe_context(grouped_results['keyframe'])
                context_sections.append({
                    "type": "keyframe",
                    "title": "Relevant Video Keyframes", 
                    "content": keyframe_context,
                    "count": len(grouped_results['keyframe'])
                })
            
            # Create unified context
            unified_context = self.create_unified_context(context_sections, query)
            
            return {
                "query": query,
                "sections": context_sections,
                "unified_context": unified_context,
                "total_results": len(results),
                "context_length": len(unified_context),
                "citations": self.extract_all_citations(results)
            }
            
        except Exception as e:
            logger.error(f"Failed to create context bundle: {e}")
            return {"error": str(e)}
    
    def create_text_context(self, text_results: List[Dict[str, Any]]) -> str:
        """Create text context section"""
        context_parts = []
        
        for i, result in enumerate(text_results[:10]):  # Limit to top 10
            citation = f"[{i+1}]"
            content = result.get('content', '')[:500]  # Truncate long content
            source = f"{result.get('filename', 'unknown')} (chunk {result.get('chunk_index', 0)})"
            
            context_parts.append(f"{citation} {content}\nSource: {source}\n")
        
        return "\n".join(context_parts)
    
    def create_image_context(self, image_results: List[Dict[str, Any]]) -> str:
        """Create image context section"""
        context_parts = []
        
        for i, result in enumerate(image_results[:5]):  # Limit to top 5
            citation = f"[IMG-{i+1}]"
            caption = result.get('content', 'No caption available')
            source = result.get('filename', 'unknown')
            dimensions = result.get('dimensions', {})
            
            context_part = f"{citation} Image: {caption}\n"
            context_part += f"Source: {source}\n"
            if dimensions:
                context_part += f"Size: {dimensions.get('width', '?')}x{dimensions.get('height', '?')}\n"
            
            # Add artifact link if available
            artifacts = result.get('artifacts', {})
            if artifacts.get('view_url'):
                context_part += f"View: {artifacts['view_url']}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def create_video_context(self, video_results: List[Dict[str, Any]]) -> str:
        """Create video context section"""
        context_parts = []
        
        for i, result in enumerate(video_results[:3]):  # Limit to top 3
            citation = f"[VID-{i+1}]"
            transcription = result.get('transcription', 'No transcription available')[:300]
            source = result.get('filename', 'unknown')
            duration = result.get('duration', 0)
            
            context_part = f"{citation} Video Transcription: {transcription}\n"
            context_part += f"Source: {source}\n"
            context_part += f"Duration: {duration:.1f} seconds\n"
            
            # Add artifact link if available
            artifacts = result.get('artifacts', {})
            if artifacts.get('view_url'):
                context_part += f"Watch: {artifacts['view_url']}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def create_keyframe_context(self, keyframe_results: List[Dict[str, Any]]) -> str:
        """Create keyframe context section"""
        context_parts = []
        
        for i, result in enumerate(keyframe_results[:5]):  # Limit to top 5
            citation = f"[KF-{i+1}]"
            caption = result.get('content', 'No caption available')
            timestamp = result.get('timestamp', 0)
            source = result.get('filename', 'unknown')
            
            context_part = f"{citation} Video Keyframe ({timestamp:.1f}s): {caption}\n"
            context_part += f"Source: {source}\n"
            
            # Add artifact link if available
            artifacts = result.get('artifacts', {})
            if artifacts.get('view_url'):
                context_part += f"View: {artifacts['view_url']}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def create_unified_context(self, sections: List[Dict[str, Any]], query: str) -> str:
        """Create unified context for LLM consumption"""
        context_parts = [
            f"# Search Results for: {query}",
            f"Found {sum(s['count'] for s in sections)} relevant items across {len(sections)} content types.",
            ""
        ]
        
        for section in sections:
            context_parts.append(f"## {section['title']} ({section['count']} items)")
            context_parts.append(section['content'])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def generate_citations(self, content_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate citations for content"""
        return {
            "source": content_info.get('filename', 'unknown'),
            "type": content_info.get('content_type', 'unknown'),
            "document_id": content_info.get('document_id'),
            "created_at": content_info.get('created_at'),
        }
    
    async def get_artifact_links(self, content_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate artifact links for content"""
        artifacts = {}
        
        # Add view URLs based on content type
        if content_info['content_type'] == 'image':
            image_path = content_info.get('image_path')
            if image_path:
                artifacts['view_url'] = f"/api/v1/artifacts/image/{content_info['document_id']}"
                artifacts['download_url'] = f"/api/v1/artifacts/download/{content_info['document_id']}"
        
        elif content_info['content_type'] == 'video':
            video_path = content_info.get('video_path')
            if video_path:
                artifacts['view_url'] = f"/api/v1/artifacts/video/{content_info['document_id']}"
                artifacts['download_url'] = f"/api/v1/artifacts/download/{content_info['document_id']}"
        
        elif content_info['content_type'] == 'keyframe':
            keyframe_path = content_info.get('keyframe_path')
            if keyframe_path:
                artifacts['view_url'] = f"/api/v1/artifacts/keyframe/{content_info['id']}"
        
        return artifacts
    
    def extract_all_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract all citations from results"""
        citations = []
        for result in results:
            if 'citations' in result:
                citations.append(result['citations'])
        return citations

