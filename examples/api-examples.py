#!/usr/bin/env python3
"""
API Examples for Multimodal LLM Stack

This script demonstrates how to use all the APIs in the multimodal stack.
Run with: python examples/api-examples.py
"""

import asyncio
import aiohttp
import aiofiles
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import openai

# Configuration
LITELLM_URL = "http://localhost:4000"
MULTIMODAL_WORKER_URL = "http://localhost:8001"
RETRIEVAL_PROXY_URL = "http://localhost:8002"

# API Keys (update with your actual keys)
LITELLM_API_KEY = "sk-your-litellm-master-key"

class MultimodalStackClient:
    """Client for interacting with the Multimodal LLM Stack"""
    
    def __init__(self):
        self.litellm_url = LITELLM_URL
        self.worker_url = MULTIMODAL_WORKER_URL
        self.proxy_url = RETRIEVAL_PROXY_URL
        self.api_key = LITELLM_API_KEY
        
        # Configure OpenAI client for LiteLLM
        openai.api_base = f"{LITELLM_URL}/v1"
        openai.api_key = LITELLM_API_KEY
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        services = {
            "litellm": f"{self.litellm_url}/health",
            "multimodal_worker": f"{self.worker_url}/health",
            "retrieval_proxy": f"{self.proxy_url}/health"
        }
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for service, url in services.items():
                try:
                    async with session.get(url) as response:
                        results[service] = response.status == 200
                except:
                    results[service] = False
        
        return results
    
    async def chat_completion(self, messages: List[Dict], model: str = "gpt-3.5-turbo") -> str:
        """Get chat completion from LiteLLM"""
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {e}"
    
    async def process_text(self, text: str, document_name: str = None) -> Dict[str, Any]:
        """Process text document"""
        async with aiohttp.ClientSession() as session:
            data = {
                "text": text,
                "document_name": document_name or "example_text.txt",
                "metadata": {"source": "api_example", "type": "demo"}
            }
            
            async with session.post(
                f"{self.worker_url}/api/v1/process/text",
                json=data
            ) as response:
                return await response.json()
    
    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process image file"""
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(image_path, 'rb') as f:
                image_data = await f.read()
            
            data = aiohttp.FormData()
            data.add_field('file', image_data, filename=Path(image_path).name)
            data.add_field('document_name', Path(image_path).name)
            data.add_field('metadata', json.dumps({"source": "api_example"}))
            
            async with session.post(
                f"{self.worker_url}/api/v1/process/image",
                data=data
            ) as response:
                return await response.json()
    
    async def search_multimodal(self, query: str, modalities: List[str] = None, limit: int = 5) -> Dict[str, Any]:
        """Search across all modalities"""
        async with aiohttp.ClientSession() as session:
            data = {
                "query": query,
                "modalities": modalities or ["text", "image", "video"],
                "limit": limit,
                "score_threshold": 0.7
            }
            
            async with session.post(
                f"{self.proxy_url}/api/v1/search",
                json=data
            ) as response:
                return await response.json()
    
    async def get_context_bundle(self, session_id: str, format: str = "markdown") -> str:
        """Get formatted context bundle"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.proxy_url}/api/v1/context/{session_id}?format={format}"
            ) as response:
                result = await response.json()
                return result.get("context", "")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.proxy_url}/api/v1/stats") as response:
                return await response.json()

# Example functions
async def example_basic_health_check():
    """Example 1: Basic health check"""
    print("🏥 Example 1: Health Check")
    print("=" * 40)
    
    client = MultimodalStackClient()
    health = await client.health_check()
    
    for service, status in health.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'Healthy' if status else 'Unhealthy'}")
    
    print()

async def example_text_processing():
    """Example 2: Text processing and search"""
    print("📝 Example 2: Text Processing")
    print("=" * 40)
    
    client = MultimodalStackClient()
    
    # Sample text about AI/ML
    sample_text = """
    Artificial Intelligence and Machine Learning have revolutionized how we process and understand data. 
    Deep learning models, particularly transformer architectures, have shown remarkable capabilities in 
    natural language processing, computer vision, and multimodal understanding.
    
    The integration of different modalities - text, images, and videos - allows for more comprehensive 
    AI systems that can understand context across different types of content. This is particularly 
    useful for applications like content analysis, automated documentation, and intelligent search systems.
    """
    
    # Process the text
    print("Processing text document...")
    result = await client.process_text(sample_text, "ai_ml_overview.txt")
    
    if result.get("success"):
        print(f"✅ Text processed successfully!")
        print(f"   Document ID: {result['data']['document_id']}")
        print(f"   Chunks created: {result['data']['chunks_count']}")
    else:
        print(f"❌ Text processing failed: {result.get('error', 'Unknown error')}")
    
    # Wait a moment for indexing
    await asyncio.sleep(2)
    
    # Search for the processed content
    print("\nSearching for 'machine learning transformers'...")
    search_result = await client.search_multimodal(
        "machine learning transformers",
        modalities=["text"],
        limit=3
    )
    
    if search_result.get("results"):
        print(f"✅ Found {len(search_result['results'])} results")
        for i, result in enumerate(search_result['results'][:2]):
            print(f"   Result {i+1}: {result['content'][:100]}...")
            print(f"   Score: {result['score']:.3f}")
    else:
        print("❌ No search results found")
    
    print()

async def example_image_processing():
    """Example 3: Image processing (if image available)"""
    print("🖼️ Example 3: Image Processing")
    print("=" * 40)
    
    client = MultimodalStackClient()
    
    # Create a simple test image
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create test image
        img = Image.new('RGB', (400, 300), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Add some text
        try:
            font = ImageFont.load_default()
            draw.text((50, 100), "Multimodal LLM Stack", fill='black', font=font)
            draw.text((50, 130), "Test Image for Processing", fill='black', font=font)
            draw.text((50, 160), "Contains: AI, ML, Stack", fill='black', font=font)
        except:
            draw.text((50, 100), "Test Image", fill='black')
        
        # Draw some shapes
        draw.rectangle([50, 200, 150, 250], outline='red', width=2)
        draw.ellipse([200, 200, 300, 250], outline='green', width=2)
        
        # Save test image
        test_image_path = "test_image.png"
        img.save(test_image_path)
        
        print(f"Created test image: {test_image_path}")
        
        # Process the image
        print("Processing image...")
        result = await client.process_image(test_image_path)
        
        if result.get("success"):
            print(f"✅ Image processed successfully!")
            print(f"   Document ID: {result['data']['document_id']}")
            print(f"   Caption: {result['data']['caption']}")
            print(f"   Dimensions: {result['data']['dimensions']}")
        else:
            print(f"❌ Image processing failed: {result.get('error', 'Unknown error')}")
        
        # Clean up
        Path(test_image_path).unlink(missing_ok=True)
        
    except ImportError:
        print("❌ PIL not available, skipping image processing example")
        print("   Install with: pip install Pillow")
    except Exception as e:
        print(f"❌ Image processing example failed: {e}")
    
    print()

async def example_multimodal_search():
    """Example 4: Multimodal search with context bundling"""
    print("🔍 Example 4: Multimodal Search")
    print("=" * 40)
    
    client = MultimodalStackClient()
    
    # Search for AI/ML related content
    search_queries = [
        "artificial intelligence machine learning",
        "deep learning neural networks",
        "multimodal AI systems"
    ]
    
    for query in search_queries:
        print(f"Searching for: '{query}'")
        
        search_result = await client.search_multimodal(
            query,
            modalities=["text", "image"],
            limit=5
        )
        
        if search_result.get("results"):
            print(f"✅ Found {len(search_result['results'])} results")
            
            # Get context bundle
            session_id = search_result["session_id"]
            context = await client.get_context_bundle(session_id, "markdown")
            
            if context:
                print("📋 Context Bundle Preview:")
                # Show first 200 characters of context
                preview = context[:200].replace('\n', ' ')
                print(f"   {preview}...")
            
        else:
            print("❌ No results found")
        
        print()

async def example_chat_with_context():
    """Example 5: Chat completion with retrieved context"""
    print("💬 Example 5: Chat with Context")
    print("=" * 40)
    
    client = MultimodalStackClient()
    
    # Search for relevant context
    query = "machine learning deep learning AI"
    print(f"Searching for context about: {query}")
    
    search_result = await client.search_multimodal(query, limit=3)
    
    context = ""
    if search_result.get("results"):
        session_id = search_result["session_id"]
        context = await client.get_context_bundle(session_id, "markdown")
    
    # Create chat messages with context
    messages = [
        {
            "role": "system", 
            "content": "You are an AI assistant with access to a multimodal knowledge base. Use the provided context to answer questions accurately."
        }
    ]
    
    if context:
        messages.append({
            "role": "user", 
            "content": f"Based on this context:\n\n{context[:1000]}\n\nQuestion: What are the key advantages of multimodal AI systems?"
        })
    else:
        messages.append({
            "role": "user", 
            "content": "What are the key advantages of multimodal AI systems?"
        })
    
    print("Generating response with context...")
    response = await client.chat_completion(messages)
    
    print("🤖 AI Response:")
    print(response)
    print()

async def example_system_monitoring():
    """Example 6: System monitoring and stats"""
    print("📊 Example 6: System Monitoring")
    print("=" * 40)
    
    client = MultimodalStackClient()
    
    try:
        stats = await client.get_system_stats()
        
        print("System Statistics:")
        
        # Database stats
        if "database" in stats:
            db_stats = stats["database"]
            print(f"📊 Database:")
            if "totals" in db_stats:
                totals = db_stats["totals"]
                print(f"   Documents: {totals.get('documents', 0)}")
                print(f"   Text chunks: {totals.get('text_chunks', 0)}")
                print(f"   Images: {totals.get('images', 0)}")
                print(f"   Videos: {totals.get('videos', 0)}")
        
        # Vector store stats
        if "vector_store" in stats:
            vs_stats = stats["vector_store"]
            print(f"🔍 Vector Store:")
            for collection, info in vs_stats.items():
                if isinstance(info, dict) and "vectors_count" in info:
                    print(f"   {collection}: {info['vectors_count']} vectors")
        
    except Exception as e:
        print(f"❌ Failed to get system stats: {e}")
    
    print()

async def example_workflow_automation():
    """Example 7: Complete workflow automation"""
    print("🔄 Example 7: Workflow Automation")
    print("=" * 40)
    
    client = MultimodalStackClient()
    
    # Simulate a complete workflow
    print("Starting automated workflow...")
    
    # Step 1: Process some content
    workflow_text = """
    This document describes the workflow automation capabilities of our multimodal LLM stack.
    The system can automatically process documents, extract insights, and provide intelligent responses.
    Key features include: automated content analysis, intelligent search, and context-aware generation.
    """
    
    print("Step 1: Processing workflow documentation...")
    text_result = await client.process_text(workflow_text, "workflow_guide.txt")
    
    if not text_result.get("success"):
        print("❌ Workflow failed at text processing step")
        return
    
    # Step 2: Wait for indexing
    print("Step 2: Waiting for content indexing...")
    await asyncio.sleep(3)
    
    # Step 3: Search for processed content
    print("Step 3: Searching processed content...")
    search_result = await client.search_multimodal(
        "workflow automation capabilities",
        modalities=["text"],
        limit=2
    )
    
    if not search_result.get("results"):
        print("❌ Workflow failed at search step")
        return
    
    # Step 4: Generate summary with context
    print("Step 4: Generating intelligent summary...")
    session_id = search_result["session_id"]
    context = await client.get_context_bundle(session_id)
    
    messages = [
        {"role": "system", "content": "You are a technical documentation assistant."},
        {"role": "user", "content": f"Based on this context:\n\n{context}\n\nProvide a brief summary of the workflow automation capabilities."}
    ]
    
    summary = await client.chat_completion(messages)
    
    print("✅ Workflow completed successfully!")
    print("\n📋 Generated Summary:")
    print(summary)
    print()

async def main():
    """Run all examples"""
    print("🚀 Multimodal LLM Stack - API Examples")
    print("=" * 50)
    print()
    
    # Run all examples
    examples = [
        example_basic_health_check,
        example_text_processing,
        example_image_processing,
        example_multimodal_search,
        example_chat_with_context,
        example_system_monitoring,
        example_workflow_automation
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
            print()
        
        # Small delay between examples
        await asyncio.sleep(1)
    
    print("🎉 All examples completed!")
    print("\n💡 Next steps:")
    print("1. Explore the web interface at http://localhost:3000")
    print("2. Check the API documentation at http://localhost:8001/docs")
    print("3. Try the search interface at http://localhost:8002/docs")
    print("4. Integrate with your own applications using these patterns")

if __name__ == "__main__":
    asyncio.run(main())
