"""
Processing modules for different media types
"""
import logging
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch
from PIL import Image
import cv2
import whisper
from moviepy.editor import VideoFileClip
import librosa

from .config import settings

logger = logging.getLogger(__name__)

class BaseProcessor:
    """Base class for all processors"""
    
    def __init__(self, model_manager, db_manager, storage_manager):
        self.model_manager = model_manager
        self.db_manager = db_manager
        self.storage_manager = storage_manager

class ImageProcessor(BaseProcessor):
    """Handles image processing, embedding generation, and captioning"""
    
    async def process_image(self, image_path: str, document_id: str) -> Dict[str, Any]:
        """Process an image: generate embeddings, caption, and extract features"""
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Resize if too large
            if image.size[0] > settings.image_max_size[0] or image.size[1] > settings.image_max_size[1]:
                image.thumbnail(settings.image_max_size, Image.Resampling.LANCZOS)
            
            # Generate image embedding using CLIP
            embedding = await self.generate_image_embedding(image)
            
            # Generate caption using BLIP
            caption = await self.generate_image_caption(image)
            
            # Extract basic features
            features = self.extract_image_features(image)
            
            # Store image in MinIO
            image_filename = os.path.basename(image_path)
            file_hash = self.storage_manager.calculate_file_hash(image_path)
            object_path = self.storage_manager.generate_object_path(
                file_hash, image_filename, "images"
            )
            
            self.storage_manager.upload_file(
                settings.minio_bucket_images,
                object_path,
                image_path,
                content_type="image/jpeg"
            )
            
            # Create database record
            image_id = await self.db_manager.create_image(
                document_id=document_id,
                image_path=object_path,
                width=image.size[0],
                height=image.size[1],
                format=image.format,
                caption=caption,
                embedding_id=None,  # Will be set after storing in Qdrant
                features=features
            )
            
            return {
                "image_id": image_id,
                "embedding": embedding,
                "caption": caption,
                "features": features,
                "storage_path": object_path,
                "dimensions": image.size
            }
            
        except Exception as e:
            logger.error(f"Failed to process image {image_path}: {e}")
            raise
    
    async def generate_image_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate CLIP embedding for an image"""
        try:
            clip_model = self.model_manager.get_model('clip')
            clip_processor = self.model_manager.get_processor('clip')
            
            # Process image
            inputs = clip_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(clip_model.device) for k, v in inputs.items()}
            
            # Generate embedding
            with torch.no_grad():
                image_features = clip_model.get_image_features(**inputs)
                embedding = image_features.cpu().numpy().flatten()
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            raise
    
    async def generate_image_caption(self, image: Image.Image) -> str:
        """Generate caption for an image using BLIP"""
        try:
            blip_model = self.model_manager.get_model('blip')
            blip_processor = self.model_manager.get_processor('blip')
            
            # Process image
            inputs = blip_processor(image, return_tensors="pt")
            inputs = {k: v.to(blip_model.device) for k, v in inputs.items()}
            
            # Generate caption
            with torch.no_grad():
                out = blip_model.generate(**inputs, max_length=50, num_beams=5)
                caption = blip_processor.decode(out[0], skip_special_tokens=True)
            
            return caption
            
        except Exception as e:
            logger.error(f"Failed to generate image caption: {e}")
            return "Caption generation failed"
    
    def extract_image_features(self, image: Image.Image) -> Dict[str, Any]:
        """Extract basic image features"""
        try:
            # Convert to numpy array for analysis
            img_array = np.array(image)
            
            # Calculate basic statistics
            features = {
                "mean_brightness": float(np.mean(img_array)),
                "std_brightness": float(np.std(img_array)),
                "dominant_colors": self.get_dominant_colors(img_array),
                "aspect_ratio": float(image.size[0] / image.size[1]),
                "file_size": len(image.tobytes())
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract image features: {e}")
            return {}
    
    def get_dominant_colors(self, img_array: np.ndarray, k: int = 5) -> List[List[int]]:
        """Get dominant colors using k-means clustering"""
        try:
            from sklearn.cluster import KMeans
            
            # Reshape image to be a list of pixels
            pixels = img_array.reshape(-1, 3)
            
            # Apply k-means clustering
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            # Get dominant colors
            colors = kmeans.cluster_centers_.astype(int)
            return colors.tolist()
            
        except Exception as e:
            logger.error(f"Failed to get dominant colors: {e}")
            return []

class VideoProcessor(BaseProcessor):
    """Handles video processing, transcription, and keyframe extraction"""
    
    async def process_video(self, video_path: str, document_id: str) -> Dict[str, Any]:
        """Process a video: extract keyframes, transcribe audio, generate embeddings"""
        try:
            # Load video
            video_clip = VideoFileClip(video_path)
            duration = video_clip.duration
            fps = video_clip.fps
            size = video_clip.size
            
            # Extract audio and transcribe
            transcription = await self.transcribe_video_audio(video_path)
            
            # Generate text embedding for transcription
            text_embedding = None
            if transcription:
                text_embedding = await self.generate_text_embedding(transcription)
            
            # Extract keyframes
            keyframes = await self.extract_keyframes(video_path, duration)
            
            # Store video in MinIO
            video_filename = os.path.basename(video_path)
            file_hash = self.storage_manager.calculate_file_hash(video_path)
            object_path = self.storage_manager.generate_object_path(
                file_hash, video_filename, "videos"
            )
            
            self.storage_manager.upload_file(
                settings.minio_bucket_videos,
                object_path,
                video_path,
                content_type="video/mp4"
            )
            
            # Create database record
            video_id = await self.db_manager.create_video(
                document_id=document_id,
                video_path=object_path,
                duration=duration,
                width=size[0] if size else None,
                height=size[1] if size else None,
                fps=fps,
                format=os.path.splitext(video_filename)[1][1:],
                transcription=transcription,
                embedding_id=None,  # Will be set after storing in Qdrant
                metadata={"keyframe_count": len(keyframes)}
            )
            
            # Process keyframes
            processed_keyframes = []
            for i, (timestamp, keyframe_path) in enumerate(keyframes):
                keyframe_result = await self.process_keyframe(
                    video_id, keyframe_path, timestamp
                )
                processed_keyframes.append(keyframe_result)
            
            video_clip.close()
            
            return {
                "video_id": video_id,
                "transcription": transcription,
                "text_embedding": text_embedding,
                "keyframes": processed_keyframes,
                "storage_path": object_path,
                "duration": duration,
                "dimensions": size
            }
            
        except Exception as e:
            logger.error(f"Failed to process video {video_path}: {e}")
            raise
    
    async def transcribe_video_audio(self, video_path: str) -> str:
        """Transcribe audio from video using Whisper"""
        try:
            whisper_model = self.model_manager.get_model('whisper')
            
            # Extract audio from video
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            try:
                video_clip = VideoFileClip(video_path)
                audio_clip = video_clip.audio
                if audio_clip is None:
                    return "No audio track found"
                
                audio_clip.write_audiofile(temp_audio_path, verbose=False, logger=None)
                video_clip.close()
                
                # Transcribe using Whisper
                result = whisper_model.transcribe(temp_audio_path)
                transcription = result["text"].strip()
                
                return transcription
                
            finally:
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
            
        except Exception as e:
            logger.error(f"Failed to transcribe video audio: {e}")
            return "Transcription failed"
    
    async def extract_keyframes(self, video_path: str, duration: float) -> List[Tuple[float, str]]:
        """Extract keyframes from video at regular intervals"""
        try:
            keyframes = []
            interval = settings.keyframe_interval
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            timestamps = np.arange(0, duration, interval)
            
            for timestamp in timestamps:
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Save keyframe
                keyframe_filename = f"keyframe_{timestamp:.1f}s.jpg"
                keyframe_path = os.path.join(settings.temp_dir, keyframe_filename)
                
                cv2.imwrite(keyframe_path, frame)
                keyframes.append((timestamp, keyframe_path))
            
            cap.release()
            return keyframes
            
        except Exception as e:
            logger.error(f"Failed to extract keyframes: {e}")
            return []
    
    async def process_keyframe(self, video_id: str, keyframe_path: str, 
                             timestamp: float) -> Dict[str, Any]:
        """Process a single keyframe"""
        try:
            # Load keyframe as PIL Image
            image = Image.open(keyframe_path).convert('RGB')
            
            # Generate embedding and caption
            embedding = await self.generate_image_embedding(image)
            caption = await self.generate_image_caption(image)
            
            # Store keyframe in MinIO
            keyframe_filename = os.path.basename(keyframe_path)
            file_hash = self.storage_manager.calculate_file_hash(keyframe_path)
            object_path = self.storage_manager.generate_object_path(
                file_hash, keyframe_filename, "keyframes"
            )
            
            self.storage_manager.upload_file(
                settings.minio_bucket_images,
                object_path,
                keyframe_path,
                content_type="image/jpeg"
            )
            
            # Create database record
            keyframe_id = await self.db_manager.create_video_keyframe(
                video_id=video_id,
                keyframe_path=object_path,
                timestamp=timestamp,
                caption=caption,
                embedding_id=None  # Will be set after storing in Qdrant
            )
            
            # Clean up temporary file
            if os.path.exists(keyframe_path):
                os.unlink(keyframe_path)
            
            return {
                "keyframe_id": keyframe_id,
                "timestamp": timestamp,
                "embedding": embedding,
                "caption": caption,
                "storage_path": object_path
            }
            
        except Exception as e:
            logger.error(f"Failed to process keyframe: {e}")
            raise
    
    async def generate_image_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate CLIP embedding for an image (reused from ImageProcessor)"""
        image_processor = ImageProcessor(
            self.model_manager, self.db_manager, self.storage_manager
        )
        return await image_processor.generate_image_embedding(image)
    
    async def generate_image_caption(self, image: Image.Image) -> str:
        """Generate caption for an image (reused from ImageProcessor)"""
        image_processor = ImageProcessor(
            self.model_manager, self.db_manager, self.storage_manager
        )
        return await image_processor.generate_image_caption(image)
    
    async def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using sentence transformer"""
        try:
            model = self.model_manager.get_model('sentence_transformer')
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            raise

class TextProcessor(BaseProcessor):
    """Handles text processing and embedding generation"""
    
    async def process_text(self, text: str, document_id: str) -> Dict[str, Any]:
        """Process text: chunk it and generate embeddings"""
        try:
            # Split text into chunks
            chunks = self.chunk_text(text)
            
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.generate_text_embedding(chunk)
                
                # Create database record
                chunk_id = await self.db_manager.create_text_chunk(
                    document_id=document_id,
                    chunk_text=chunk,
                    chunk_index=i,
                    embedding_id=None  # Will be set after storing in Qdrant
                )
                
                processed_chunks.append({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "text": chunk,
                    "embedding": embedding
                })
            
            return {
                "chunks": processed_chunks,
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Failed to process text: {e}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            
            # Move to next chunk with overlap
            i += chunk_size - overlap
            
            # Stop if we've processed all words
            if i >= len(words):
                break
        
        return chunks
    
    async def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using sentence transformer"""
        try:
            model = self.model_manager.get_model('sentence_transformer')
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            raise

