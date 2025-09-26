"""
Model manager for loading and managing ML models
"""
import os
import logging
from typing import Dict, Any, Optional
import torch
from transformers import (
    CLIPProcessor, CLIPModel,
    BlipProcessor, BlipForConditionalGeneration,
    pipeline
)
from sentence_transformers import SentenceTransformer
import whisper

from .config import settings

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages all ML models used by the service"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.processors: Dict[str, Any] = {}
        self.device = torch.device(settings.device)
        
        # Ensure cache directories exist
        os.makedirs(settings.cache_dir, exist_ok=True)
        os.makedirs(settings.model_cache_dir, exist_ok=True)
    
    async def load_models(self):
        """Load all required models"""
        logger.info("Loading models...")
        
        try:
            # Load CLIP model for image embeddings
            logger.info("Loading CLIP model...")
            self.models['clip'] = CLIPModel.from_pretrained(
                settings.clip_model,
                cache_dir=settings.model_cache_dir
            ).to(self.device)
            self.processors['clip'] = CLIPProcessor.from_pretrained(
                settings.clip_model,
                cache_dir=settings.model_cache_dir
            )
            
            # Load BLIP model for image captioning
            logger.info("Loading BLIP model...")
            self.models['blip'] = BlipForConditionalGeneration.from_pretrained(
                settings.blip_model,
                cache_dir=settings.model_cache_dir
            ).to(self.device)
            self.processors['blip'] = BlipProcessor.from_pretrained(
                settings.blip_model,
                cache_dir=settings.model_cache_dir
            )
            
            # Load Whisper model for audio transcription
            logger.info("Loading Whisper model...")
            self.models['whisper'] = whisper.load_model(
                settings.whisper_model.split('/')[-1],  # Extract model size
                download_root=settings.model_cache_dir
            )
            
            # Load sentence transformer for text embeddings
            logger.info("Loading Sentence Transformer...")
            self.models['sentence_transformer'] = SentenceTransformer(
                settings.sentence_transformer_model,
                cache_folder=settings.model_cache_dir,
                device=self.device
            )
            
            logger.info("All models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def get_model(self, model_name: str) -> Any:
        """Get a loaded model by name"""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        return self.models[model_name]
    
    def get_processor(self, processor_name: str) -> Any:
        """Get a processor by name"""
        if processor_name not in self.processors:
            raise ValueError(f"Processor '{processor_name}' not found")
        return self.processors[processor_name]
    
    async def cleanup(self):
        """Clean up models and free memory"""
        logger.info("Cleaning up models...")
        
        # Clear models from GPU memory
        for model_name, model in self.models.items():
            if hasattr(model, 'cpu'):
                model.cpu()
        
        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.models.clear()
        self.processors.clear()
        
        logger.info("Model cleanup completed")

