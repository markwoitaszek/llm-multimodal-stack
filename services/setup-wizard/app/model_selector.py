"""
Model selection for setup wizard
"""

import logging
from typing import List, Dict, Any
from .models import ModelOption

logger = logging.getLogger(__name__)


class ModelSelector:
    """Model selection helper"""
    
    def __init__(self):
        self.available_models = self._get_available_models()
    
    def _get_available_models(self) -> List[ModelOption]:
        """Get list of available models"""
        return [
            # Small/Fast Models
            ModelOption(
                id="microsoft/DialoGPT-medium",
                name="DialoGPT Medium",
                description="Fast conversational model, great for testing and development",
                size_gb=0.35,
                memory_required_gb=1.0,
                recommended=True
            ),
            ModelOption(
                id="distilgpt2",
                name="DistilGPT-2",
                description="Lightweight GPT-2 variant, very fast and efficient",
                size_gb=0.32,
                memory_required_gb=1.0,
                recommended=True
            ),
            ModelOption(
                id="microsoft/DialoGPT-large",
                name="DialoGPT Large",
                description="Larger conversational model with better quality",
                size_gb=0.75,
                memory_required_gb=2.0
            ),
            
            # Medium Models
            ModelOption(
                id="gpt2-medium",
                name="GPT-2 Medium",
                description="Balanced GPT-2 model, good for general text generation",
                size_gb=1.5,
                memory_required_gb=3.0
            ),
            ModelOption(
                id="EleutherAI/gpt-neo-1.3B",
                name="GPT-Neo 1.3B",
                description="High-quality text generation, requires more resources",
                size_gb=5.0,
                memory_required_gb=6.0
            ),
            ModelOption(
                id="gpt2-large",
                name="GPT-2 Large",
                description="Larger GPT-2 model with better performance",
                size_gb=3.0,
                memory_required_gb=4.0
            ),
            
            # Large Models (requires more VRAM)
            ModelOption(
                id="EleutherAI/gpt-neo-2.7B",
                name="GPT-Neo 2.7B",
                description="High-performance model, requires significant GPU memory",
                size_gb=11.0,
                memory_required_gb=12.0
            ),
            ModelOption(
                id="meta-llama/Llama-2-7b-chat-hf",
                name="Llama 2 7B Chat",
                description="Meta's Llama 2 model, requires approval and significant resources",
                size_gb=13.0,
                memory_required_gb=14.0,
                requires_approval=True
            ),
            ModelOption(
                id="mistralai/Mistral-7B-Instruct-v0.1",
                name="Mistral 7B Instruct",
                description="High-quality instruction-following model",
                size_gb=14.0,
                memory_required_gb=15.0
            )
        ]
    
    def get_models_for_memory(self, available_memory_gb: float) -> List[ModelOption]:
        """Get models that fit within available memory"""
        suitable_models = []
        
        for model in self.available_models:
            if model.memory_required_gb <= available_memory_gb:
                suitable_models.append(model)
        
        return suitable_models
    
    def get_recommended_models(self) -> List[ModelOption]:
        """Get recommended models for beginners"""
        return [model for model in self.available_models if model.recommended]
    
    def get_model_by_id(self, model_id: str) -> ModelOption:
        """Get model by ID"""
        for model in self.available_models:
            if model.id == model_id:
                return model
        raise ValueError(f"Model {model_id} not found")
    
    def validate_model_selection(self, model_id: str, system_check: SystemCheckResult) -> Dict[str, Any]:
        """Validate model selection against system capabilities"""
        model = self.get_model_by_id(model_id)
        
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check memory requirements
        if model.memory_required_gb > system_check.memory_gb:
            validation["errors"].append(
                f"Model requires {model.memory_required_gb}GB RAM, "
                f"but only {system_check.memory_gb:.1f}GB available"
            )
            validation["valid"] = False
        
        # Check GPU availability for large models
        if model.memory_required_gb > 4.0 and not system_check.nvidia_gpu_available:
            validation["warnings"].append(
                "Large model selected but no GPU detected. "
                "Performance will be limited on CPU."
            )
        
        # Check disk space
        if model.size_gb > system_check.disk_space_gb:
            validation["errors"].append(
                f"Model requires {model.size_gb}GB disk space, "
                f"but only {system_check.disk_space_gb:.1f}GB available"
            )
            validation["valid"] = False
        
        return validation
