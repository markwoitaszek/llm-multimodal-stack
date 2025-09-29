"""
Vector Store Operations for Search Engine
"""
import asyncio
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import ResponseHandlingException
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Vector store operations manager"""
    
    def __init__(self):
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self.embedding_dimension = settings.embedding_dimension
    
    async def initialize(self):
        """Initialize Qdrant client and collection"""
        try:
            # Create Qdrant client
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=settings.search_timeout
            )
            
            # Create collection if it doesn't exist
            await self._create_collection_if_not_exists()
            
            logger.info(f"Vector store initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise Exception(f"Vector store initialization failed: {str(e)}")
    
    async def _create_collection_if_not_exists(self):
        """Create collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create new collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    async def close(self):
        """Close vector store connection"""
        if self.client:
            # Qdrant client doesn't need explicit closing
            pass
    
    async def upsert_embedding(self, content_id: str, embedding: List[float], 
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Insert or update embedding in vector store"""
        try:
            # Validate embedding
            if len(embedding) != self.embedding_dimension:
                raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dimension}, got {len(embedding)}")
            
            # Prepare metadata
            point_metadata = {
                "content_id": content_id,
                "timestamp": int(asyncio.get_event_loop().time())
            }
            if metadata:
                point_metadata.update(metadata)
            
            # Create point
            point = PointStruct(
                id=content_id,
                vector=embedding,
                payload=point_metadata
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting embedding: {str(e)}")
            return False
    
    async def search_similar(self, query_embedding: List[float], limit: int = 10,
                           score_threshold: float = 0.0,
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar embeddings"""
        try:
            # Validate query embedding
            if len(query_embedding) != self.embedding_dimension:
                raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dimension}, got {len(query_embedding)}")
            
            # Build filter
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
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "metadata": hit.payload
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {str(e)}")
            return []
    
    async def delete_embedding(self, content_id: str) -> bool:
        """Delete embedding by content ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[content_id]
            )
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embedding: {str(e)}")
            return False
    
    async def get_embedding(self, content_id: str) -> Optional[List[float]]:
        """Get embedding by content ID"""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[content_id],
                with_vectors=True
            )
            
            if result and len(result) > 0:
                return result[0].vector
            return None
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return None
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "name": collection_info.config.params.vectors.size,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "status": collection_info.status,
                "optimizer_status": collection_info.optimizer_status
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {}
    
    async def batch_upsert_embeddings(self, embeddings_data: List[Tuple[str, List[float], Optional[Dict[str, Any]]]]) -> int:
        """Batch upsert multiple embeddings"""
        try:
            points = []
            for content_id, embedding, metadata in embeddings_data:
                # Validate embedding
                if len(embedding) != self.embedding_dimension:
                    logger.warning(f"Skipping embedding with dimension mismatch for {content_id}")
                    continue
                
                # Prepare metadata
                point_metadata = {
                    "content_id": content_id,
                    "timestamp": int(asyncio.get_event_loop().time())
                }
                if metadata:
                    point_metadata.update(metadata)
                
                # Create point
                point = PointStruct(
                    id=content_id,
                    vector=embedding,
                    payload=point_metadata
                )
                points.append(point)
            
            if not points:
                return 0
            
            # Batch upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return len(points)
            
        except Exception as e:
            logger.error(f"Error batch upserting embeddings: {str(e)}")
            return 0
    
    async def batch_delete_embeddings(self, content_ids: List[str]) -> int:
        """Batch delete multiple embeddings"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=content_ids
            )
            return len(content_ids)
            
        except Exception as e:
            logger.error(f"Error batch deleting embeddings: {str(e)}")
            return 0
    
    async def health_check(self) -> bool:
        """Check vector store health"""
        try:
            # Try to get collection info
            collection_info = self.client.get_collection(self.collection_name)
            return collection_info.status == "green"
            
        except Exception as e:
            # Check if it's a Pydantic validation error (version compatibility issue)
            error_str = str(e)
            if "validation errors for ParsingModel" in error_str and "max_optimization_threads" in error_str:
                # This is a known compatibility issue between client and server versions
                # The server is actually healthy, but the client can't parse the response
                logger.warning(f"Vector store health check failed due to version compatibility: {error_str}")
                # Try a simpler health check - just ping the server
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.client._client.url}/health", timeout=5.0)
                        return response.status_code == 200
                except Exception as ping_error:
                    logger.error(f"Vector store ping failed: {str(ping_error)}")
                    return False
            else:
                logger.error(f"Vector store health check failed: {error_str}")
                return False


# Global vector store manager instance
vector_store = VectorStoreManager()