"""
Qdrant vector store operations for the search engine service
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import httpx

from .config import settings
from .models import ContentType

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages Qdrant vector store operations"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collections = {
            ContentType.TEXT: settings.qdrant_collection_text,
            ContentType.IMAGE: settings.qdrant_collection_image,
            ContentType.VIDEO: settings.qdrant_collection_video
        }
    
    async def initialize(self):
        """Initialize Qdrant client and verify collections"""
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=30
            )
            
            # Verify connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant. Available collections: {[c.name for c in collections.collections]}")
            
            # Verify required collections exist
            collection_names = [c.name for c in collections.collections]
            for content_type, collection_name in self.collections.items():
                if collection_name not in collection_names:
                    logger.warning(f"Collection {collection_name} for {content_type} not found")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise
    
    async def close(self):
        """Close Qdrant client connection"""
        if self.client:
            # Qdrant client doesn't have explicit close method
            self.client = None
            logger.info("Qdrant client connection closed")
    
    def _get_collection_name(self, content_type: ContentType) -> str:
        """Get collection name for content type"""
        return self.collections.get(content_type, settings.qdrant_collection_text)
    
    async def search_similar(
        self,
        query_vector: List[float],
        content_types: List[ContentType],
        limit: int = 20,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors across multiple collections"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        all_results = []
        
        for content_type in content_types:
            collection_name = self._get_collection_name(content_type)
            
            try:
                # Build filter conditions
                query_filter = None
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        if isinstance(value, list):
                            conditions.append(
                                FieldCondition(
                                    key=key,
                                    match=MatchValue(value=value)
                                )
                            )
                        else:
                            conditions.append(
                                FieldCondition(
                                    key=key,
                                    match=MatchValue(value=value)
                                )
                            )
                    
                    if conditions:
                        query_filter = Filter(must=conditions)
                
                # Perform search
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    score_threshold=score_threshold,
                    with_payload=True,
                    with_vectors=False
                )
                
                # Process results
                for result in search_results:
                    all_results.append({
                        'id': result.id,
                        'score': result.score,
                        'content_type': content_type.value,
                        'payload': result.payload or {},
                        'collection': collection_name
                    })
                
            except Exception as e:
                logger.error(f"Failed to search collection {collection_name}: {e}")
                continue
        
        # Sort by score and return top results
        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:limit]
    
    async def search_semantic(
        self,
        query_vector: List[float],
        content_type: ContentType,
        limit: int = 20,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on a specific content type"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            # Build filter conditions
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                    else:
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Perform search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False
            )
            
            # Process results
            results = []
            for result in search_results:
                results.append({
                    'id': result.id,
                    'score': result.score,
                    'content_type': content_type.value,
                    'payload': result.payload or {},
                    'collection': collection_name
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search on {collection_name}: {e}")
            return []
    
    async def get_collection_info(self, content_type: ContentType) -> Optional[Dict[str, Any]]:
        """Get information about a collection"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            collection_info = self.client.get_collection(collection_name)
            
            return {
                'name': collection_info.config.params.vectors.size,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance,
                'points_count': collection_info.points_count,
                'status': collection_info.status,
                'optimizer_status': collection_info.optimizer_status
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None
    
    async def get_all_collections_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all collections"""
        collections_info = {}
        
        for content_type in ContentType:
            info = await self.get_collection_info(content_type)
            if info:
                collections_info[content_type.value] = info
        
        return collections_info
    
    async def create_collection(
        self,
        content_type: ContentType,
        vector_size: int = 384,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """Create a new collection for a content type"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info(f"Created collection {collection_name} for {content_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    async def delete_collection(self, content_type: ContentType) -> bool:
        """Delete a collection"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    async def upsert_points(
        self,
        content_type: ContentType,
        points: List[Dict[str, Any]]
    ) -> bool:
        """Upsert points to a collection"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            point_structs = []
            for point in points:
                point_structs.append(
                    PointStruct(
                        id=point['id'],
                        vector=point['vector'],
                        payload=point.get('payload', {})
                    )
                )
            
            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            logger.info(f"Upserted {len(point_structs)} points to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert points to {collection_name}: {e}")
            return False
    
    async def delete_points(
        self,
        content_type: ContentType,
        point_ids: List[str]
    ) -> bool:
        """Delete points from a collection"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=point_ids)
            )
            
            logger.info(f"Deleted {len(point_ids)} points from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete points from {collection_name}: {e}")
            return False
    
    async def get_point(
        self,
        content_type: ContentType,
        point_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific point from a collection"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            point = self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
                with_payload=True,
                with_vectors=False
            )
            
            if point:
                return {
                    'id': point[0].id,
                    'payload': point[0].payload or {},
                    'collection': collection_name
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get point {point_id} from {collection_name}: {e}")
            return None
    
    async def scroll_collection(
        self,
        content_type: ContentType,
        limit: int = 100,
        offset: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Scroll through collection points"""
        if not self.client:
            raise RuntimeError("Qdrant client not initialized")
        
        collection_name = self._get_collection_name(content_type)
        
        try:
            # Build filter conditions
            query_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                    else:
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Perform scroll
            scroll_result = self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset,
                scroll_filter=query_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # Process results
            results = []
            for point in scroll_result[0]:
                results.append({
                    'id': point.id,
                    'payload': point.payload or {},
                    'collection': collection_name
                })
            
            return results, scroll_result[1]
            
        except Exception as e:
            logger.error(f"Failed to scroll collection {collection_name}: {e}")
            return [], None
    
    async def get_collection_stats(self, content_type: ContentType) -> Dict[str, Any]:
        """Get collection statistics"""
        collection_info = await self.get_collection_info(content_type)
        
        if not collection_info:
            return {}
        
        return {
            'content_type': content_type.value,
            'collection_name': self._get_collection_name(content_type),
            'points_count': collection_info.get('points_count', 0),
            'vector_size': collection_info.get('vector_size', 0),
            'distance_metric': collection_info.get('distance', 'unknown'),
            'status': collection_info.get('status', 'unknown')
        }
    
    async def health_check(self) -> bool:
        """Check Qdrant health"""
        try:
            if not self.client:
                return False
            
            # Try to get collections
            collections = self.client.get_collections()
            return True
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

# Global vector store manager instance
vector_manager = VectorStoreManager()