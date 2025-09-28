"""
API routes for the multimodal worker service
"""
import logging
import os
import tempfile
from typing import List, Dict, Any, Optional
import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .processors import ImageProcessor, VideoProcessor, TextProcessor
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class ProcessingResult(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TextProcessingRequest(BaseModel):
    text: str
    document_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    modality: str = "all"  # text, image, video, all
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None

# Dependency to get managers from app state
async def get_managers(request):
    """Get managers from FastAPI app state"""
    return {
        'model_manager': request.app.state.model_manager,
        'db_manager': request.app.state.db_manager,
        'storage_manager': request.app.state.storage_manager
    }

@router.post("/process/image", response_model=ProcessingResult)
async def process_image_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """Process an uploaded image"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Check file size
        if file.size > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # Get managers (this would need to be properly injected in a real implementation)
        from fastapi import Request
        # Note: In production, you'd use proper dependency injection
        
        # Create document record
        from .database import DatabaseManager
        from .storage import StorageManager
        from .models import ModelManager
        
        # This is a simplified version - in production you'd get these from DI
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        storage_manager = StorageManager()
        await storage_manager.initialize()
        
        model_manager = ModelManager()
        await model_manager.load_models()
        
        try:
            # Calculate file hash
            file_hash = storage_manager.calculate_file_hash(temp_path)
            
            # Check if document already exists
            existing_doc = await db_manager.get_document_by_hash(file_hash)
            if existing_doc:
                return ProcessingResult(
                    success=True,
                    message="Document already processed",
                    data={"document_id": existing_doc["id"]}
                )
            
            # Create document record
            document_id = await db_manager.create_document(
                filename=document_name or file.filename,
                file_type="image",
                file_size=file.size,
                mime_type=file.content_type,
                content_hash=file_hash,
                metadata={"original_filename": file.filename}
            )
            
            # Process image
            processor = ImageProcessor(model_manager, db_manager, storage_manager)
            result = await processor.process_image(temp_path, document_id)
            
            return ProcessingResult(
                success=True,
                message="Image processed successfully",
                data={
                    "document_id": document_id,
                    "image_id": result["image_id"],
                    "caption": result["caption"],
                    "dimensions": result["dimensions"],
                    "storage_path": result["storage_path"]
                }
            )
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            # Clean up managers
            await db_manager.close()
            await storage_manager.close()
            await model_manager.cleanup()
            
    except Exception as e:
        logger.error(f"Failed to process image: {e}")
        return ProcessingResult(
            success=False,
            message="Failed to process image",
            error=str(e)
        )

@router.post("/process/video", response_model=ProcessingResult)
async def process_video_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """Process an uploaded video"""
    try:
        # Validate file type
        if not file.content_type.startswith('video/'):
            raise HTTPException(status_code=400, detail="File must be a video")
        
        # Check file size
        if file.size > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        # Initialize managers (simplified for this example)
        from .database import DatabaseManager
        from .storage import StorageManager
        from .models import ModelManager
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        storage_manager = StorageManager()
        await storage_manager.initialize()
        
        model_manager = ModelManager()
        await model_manager.load_models()
        
        try:
            # Calculate file hash
            file_hash = storage_manager.calculate_file_hash(temp_path)
            
            # Check if document already exists
            existing_doc = await db_manager.get_document_by_hash(file_hash)
            if existing_doc:
                return ProcessingResult(
                    success=True,
                    message="Document already processed",
                    data={"document_id": existing_doc["id"]}
                )
            
            # Create document record
            document_id = await db_manager.create_document(
                filename=document_name or file.filename,
                file_type="video",
                file_size=file.size,
                mime_type=file.content_type,
                content_hash=file_hash,
                metadata={"original_filename": file.filename}
            )
            
            # Process video
            processor = VideoProcessor(model_manager, db_manager, storage_manager)
            result = await processor.process_video(temp_path, document_id)
            
            return ProcessingResult(
                success=True,
                message="Video processed successfully",
                data={
                    "document_id": document_id,
                    "video_id": result["video_id"],
                    "transcription": result["transcription"],
                    "keyframes_count": len(result["keyframes"]),
                    "duration": result["duration"],
                    "storage_path": result["storage_path"]
                }
            )
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            # Clean up managers
            await db_manager.close()
            await storage_manager.close()
            await model_manager.cleanup()
            
    except Exception as e:
        logger.error(f"Failed to process video: {e}")
        return ProcessingResult(
            success=False,
            message="Failed to process video",
            error=str(e)
        )

@router.post("/process/text", response_model=ProcessingResult)
async def process_text_endpoint(request: TextProcessingRequest):
    """Process text input"""
    try:
        # Initialize managers (simplified)
        from .database import DatabaseManager
        from .storage import StorageManager
        from .models import ModelManager
        
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        storage_manager = StorageManager()
        await storage_manager.initialize()
        
        model_manager = ModelManager()
        await model_manager.load_models()
        
        try:
            # Calculate text hash
            import hashlib
            text_hash = hashlib.sha256(request.text.encode()).hexdigest()
            
            # Check if document already exists
            existing_doc = await db_manager.get_document_by_hash(text_hash)
            if existing_doc:
                return ProcessingResult(
                    success=True,
                    message="Document already processed",
                    data={"document_id": existing_doc["id"]}
                )
            
            # Create document record
            document_id = await db_manager.create_document(
                filename=request.document_name or "text_document",
                file_type="text",
                file_size=len(request.text.encode()),
                mime_type="text/plain",
                content_hash=text_hash,
                metadata=request.metadata or {}
            )
            
            # Process text
            processor = TextProcessor(model_manager, db_manager, storage_manager)
            result = await processor.process_text(request.text, document_id)
            
            return ProcessingResult(
                success=True,
                message="Text processed successfully",
                data={
                    "document_id": document_id,
                    "chunks_count": result["total_chunks"]
                }
            )
            
        finally:
            # Clean up managers
            await db_manager.close()
            await storage_manager.close()
            await model_manager.cleanup()
            
    except Exception as e:
        logger.error(f"Failed to process text: {e}")
        return ProcessingResult(
            success=False,
            message="Failed to process text",
            error=str(e)
        )

@router.get("/models/status")
async def get_models_status():
    """Get status of loaded models"""
    try:
        # This would check the actual model status in production
        return {
            "clip": "loaded",
            "blip": "loaded", 
            "whisper": "loaded",
            "sentence_transformer": "loaded"
        }
    except Exception as e:
        logger.error(f"Failed to get models status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/status")
async def get_storage_status():
    """Get storage system status"""
    try:
        # This would check actual storage status in production
        return {
            "minio": "connected",
            "postgres": "connected",
            "qdrant": "connected"
        }
    except Exception as e:
        logger.error(f"Failed to get storage status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cache management endpoints
@router.get("/cache/stats")
async def get_cache_stats(req):
    """Get cache statistics"""
    try:
        cache_manager = req.app.state.cache_manager
        stats = await cache_manager.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/clear")
async def clear_cache(req):
    """Clear all cache entries"""
    try:
        cache_manager = req.app.state.cache_manager
        success = await cache_manager.clear_all_cache()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/file/{file_hash}")
async def invalidate_file_cache(file_hash: str, req):
    """Invalidate cache entries for a specific file"""
    try:
        cache_manager = req.app.state.cache_manager
        deleted_count = await cache_manager.invalidate_file_cache(file_hash)
        return {
            "message": f"Invalidated {deleted_count} cache entries",
            "file_hash": file_hash
        }
    except Exception as e:
        logger.error(f"Failed to invalidate file cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

