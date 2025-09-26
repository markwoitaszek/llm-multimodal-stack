"""
Vector store manager for Qdrant operations
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, 
    FieldCondition, Range, MatchValue
)
import uuid

from .config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages Qdrant vector database operations"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collections = {
            "text": settings.qdrant_collection_text,
            "image": settings.qdrant_collection_image,
            "video": settings.qdrant_collection_video
        }
        self.vector_size = 384  # Default for sentence-transformers/all-MiniLM-L6-v2
    
    async def initialize(self):
        """Initialize Qdrant client and create collections"""
        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            
            # Test connection
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant, found {len(collections.collections)} collections")
            
            # Create collections if they don't exist
            for collection_type, collection_name in self.collections.items():
                if not self.client.collection_exists(collection_name):
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=self.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created collection: {collection_name}")
                else:
                    logger.info(f"Collection exists: {collection_name}")
            
            logger.info("Vector store manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def close(self):
        """Close vector store connections"""
        if self.client:
            self.client.close()
            logger.info("Vector store connections closed")
    
    def add_vectors(self, collection_name: str, vectors: List[np.ndarray], 
                   metadata_list: List[Dict[str, Any]]) -> List[str]:
        """Add vectors to a collection"""
        try:
            points = []
            ids = []
            
            for i, (vector, metadata) in enumerate(zip(vectors, metadata_list)):
                point_id = str(uuid.uuid4())
                ids.append(point_id)
                
                points.append(PointStruct(
                    id=point_id,
                    vector=vector.tolist() if isinstance(vector, np.ndarray) else vector,
                    payload=metadata
                ))
            
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} vectors to {collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise
    
    def search_vectors(self, collection_name: str, query_vector: np.ndarray,
                      limit: int = 10, score_threshold: float = None,
                      filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            # Build filter if provided
            search_filter = None
            if filters:
                conditions = []
                
                if 'document_id' in filters:
                    conditions.append(FieldCondition(
                        key="document_id",
                        match=MatchValue(value=filters['document_id'])
                    ))
                
                if 'content_type' in filters:
                    conditions.append(FieldCondition(
                        key="content_type", 
                        match=MatchValue(value=filters['content_type'])
                    ))
                
                if 'date_range' in filters:
                    date_range = filters['date_range']
                    conditions.append(FieldCondition(
                        key="created_at",
                        range=Range(
                            gte=date_range.get('gte'),
                            lte=date_range.get('lte')
                        )
                    ))
                
                if conditions:
                    search_filter = Filter(must=conditions)
            
            # Perform search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector.tolist() if isinstance(query_vector, np.ndarray) else query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            # Format results
            results = []
            for result in search_results:
                results.append({
                    'id': result.id,
                    'score': result.score,
                    'payload': result.payload
                })
            
            logger.info(f"Found {len(results)} similar vectors in {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors: {e}")
            raise
    
    def get_vector(self, collection_name: str, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific vector by ID"""
        try:
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[vector_id],
                with_vectors=True,
                with_payload=True
            )
            
            if points:
                point = points[0]
                return {
                    'id': point.id,
                    'vector': point.vector,
                    'payload': point.payload
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get vector: {e}")
            return None
    
    def delete_vectors(self, collection_name: str, vector_ids: List[str]) -> bool:
        """Delete vectors by IDs"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=vector_ids
            )
            
            logger.info(f"Deleted {len(vector_ids)} vectors from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False
    
    def update_vector_payload(self, collection_name: str, vector_id: str,
                            payload: Dict[str, Any]) -> bool:
        """Update vector payload/metadata"""
        try:
            self.client.set_payload(
                collection_name=collection_name,
                payload=payload,
                points=[vector_id]
            )
            
            logger.info(f"Updated payload for vector {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update vector payload: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'vectors_count': info.vectors_count,
                'indexed_vectors_count': info.indexed_vectors_count,
                'points_count': info.points_count,
                'segments_count': info.segments_count,
                'config': {
                    'vector_size': info.config.params.vectors.size,
                    'distance': info.config.params.vectors.distance.value
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def search_hybrid(self, query_vector: np.ndarray, query_text: str = None,
                     limit: int = 10, score_threshold: float = None,
                     modalities: List[str] = None) -> List[Dict[str, Any]]:
        """Search across multiple modalities and combine results"""
        try:
            all_results = []
            modalities = modalities or ['text', 'image', 'video']
            
            # Search each modality
            for modality in modalities:
                if modality in self.collections:
                    collection_name = self.collections[modality]
                    results = self.search_vectors(
                        collection_name=collection_name,
                        query_vector=query_vector,
                        limit=limit,
                        score_threshold=score_threshold
                    )
                    
                    # Add modality info to results
                    for result in results:
                        result['modality'] = modality
                        result['collection'] = collection_name
                    
                    all_results.extend(results)
            
            # Sort by score (descending) and limit
            all_results.sort(key=lambda x: x['score'], reverse=True)
            return all_results[:limit]
            
        except Exception as e:
            logger.error(f"Failed to perform hybrid search: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        try:
            stats = {}
            
            for collection_type, collection_name in self.collections.items():
                if self.client.collection_exists(collection_name):
                    info = self.get_collection_info(collection_name)
                    stats[collection_type] = info
                else:
                    stats[collection_type] = {"status": "not_found"}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

