# Models Directory

This directory will contain downloaded models for the multimodal stack.

Models are automatically downloaded on first use, but you can pre-download them:

## Text Models
- sentence-transformers/all-MiniLM-L6-v2 (for text embeddings)

## Vision Models  
- openai/clip-vit-base-patch32 (for image embeddings)
- Salesforce/blip-image-captioning-base (for image captioning)

## Audio Models
- openai/whisper-base (for audio transcription)

## LLM Models
Configure your preferred model in the .env file under VLLM_MODEL.
Popular options:
- microsoft/DialoGPT-medium (default, small)
- meta-llama/Llama-2-7b-chat-hf (requires approval)
- mistralai/Mistral-7B-Instruct-v0.1

Models will be cached in this directory after first download.
