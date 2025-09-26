# Cursor IDE Integration Examples

This guide shows how to integrate the Multimodal LLM Stack with Cursor IDE for enhanced development workflows.

## OpenAI API Configuration

Configure Cursor to use your local LiteLLM endpoint:

### Settings Configuration

1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Navigate to "Extensions" → "Cursor"
3. Set the following:

```json
{
  "cursor.cpp.openaiApiBase": "http://localhost:4000/v1",
  "cursor.cpp.openaiApiKey": "sk-your-litellm-master-key",
  "cursor.cpp.model": "gpt-3.5-turbo"
}
```

### Environment Variables

Alternatively, set environment variables:

```bash
export OPENAI_API_BASE="http://localhost:4000/v1"
export OPENAI_API_KEY="sk-your-litellm-master-key"
```

## Code Context with Multimodal Search

### 1. Document Processing Workflow

```python
# scripts/process_codebase.py
import os
import requests
from pathlib import Path

MULTIMODAL_WORKER_URL = "http://localhost:8001"
RETRIEVAL_PROXY_URL = "http://localhost:8002"

def process_codebase_documentation():
    """Process all documentation and images in codebase"""
    
    # Process README files
    for readme in Path(".").glob("**/README.md"):
        with open(readme, 'r') as f:
            content = f.read()
            
        response = requests.post(f"{MULTIMODAL_WORKER_URL}/api/v1/process/text", json={
            "text": content,
            "document_name": str(readme),
            "metadata": {
                "type": "documentation",
                "path": str(readme),
                "language": "markdown"
            }
        })
        print(f"Processed {readme}: {response.json()}")
    
    # Process architecture diagrams
    for img in Path(".").glob("**/*.{png,jpg,jpeg,svg}"):
        if "architecture" in str(img).lower() or "diagram" in str(img).lower():
            with open(img, 'rb') as f:
                files = {'file': f}
                data = {
                    'document_name': str(img),
                    'metadata': '{"type": "architecture", "format": "' + img.suffix + '"}'
                }
                
                response = requests.post(
                    f"{MULTIMODAL_WORKER_URL}/api/v1/process/image",
                    files=files,
                    data=data
                )
                print(f"Processed {img}: {response.json()}")

if __name__ == "__main__":
    process_codebase_documentation()
```

### 2. Intelligent Code Search

```python
# scripts/smart_search.py
import requests
import json

def search_codebase(query, include_docs=True, include_images=True):
    """Search codebase with multimodal context"""
    
    modalities = ["text"]
    if include_images:
        modalities.append("image")
    
    response = requests.post(f"{RETRIEVAL_PROXY_URL}/api/v1/search", json={
        "query": query,
        "modalities": modalities,
        "limit": 10,
        "filters": {
            "file_types": ["md", "py", "ts", "js", "jsx", "tsx"] if include_docs else ["py", "ts", "js"]
        }
    })
    
    result = response.json()
    
    # Get formatted context
    context_response = requests.get(
        f"{RETRIEVAL_PROXY_URL}/api/v1/context/{result['session_id']}?format=markdown"
    )
    
    return {
        "results": result["results"],
        "context": context_response.json()["context"],
        "session_id": result["session_id"]
    }

# Example usage
if __name__ == "__main__":
    # Search for authentication implementation
    results = search_codebase("user authentication login JWT tokens")
    print("Context for Cursor:")
    print("=" * 50)
    print(results["context"])
```

### 3. Cursor Rules Integration

Create `.cursorrules` file in your project root:

```markdown
# Multimodal LLM Stack - Cursor Rules

## Project Context
This is a production-ready multimodal LLM stack with the following components:
- vLLM for high-performance LLM inference
- LiteLLM as OpenAI-compatible router
- Multimodal Worker for image/video/text processing
- Retrieval Proxy for unified search
- PostgreSQL + Qdrant + MinIO for storage

## Code Style
- Python: Follow PEP 8, use type hints, async/await patterns
- FastAPI: Use Pydantic models, proper error handling, dependency injection
- Docker: Multi-stage builds, health checks, proper secrets management

## Architecture Patterns
- Services communicate via HTTP APIs
- Use async/await for I/O operations
- Implement proper error handling and logging
- Use dependency injection for testability

## Key Files
- `docker-compose.yml`: Main service orchestration
- `services/multimodal-worker/`: Image/video/text processing
- `services/retrieval-proxy/`: Search and context bundling
- `sql/init.sql`: Database schema
- `configs/`: Service configurations

## When suggesting changes:
1. Consider GPU memory constraints (RTX 3090 = 24GB)
2. Ensure services can scale horizontally
3. Maintain OpenAI API compatibility
4. Include proper error handling and logging
5. Update health checks if adding new endpoints

## Search Integration
Use the multimodal search when you need context about:
- Architecture decisions
- Implementation patterns
- Configuration examples
- Troubleshooting guides

Search command: `python scripts/smart_search.py "your query here"`
```

## Advanced Workflows

### 1. Context-Aware Code Generation

```python
# scripts/context_aware_generation.py
import requests
import openai

# Configure OpenAI client for local LiteLLM
openai.api_base = "http://localhost:4000/v1"
openai.api_key = "sk-your-litellm-master-key"

def generate_with_context(prompt, search_query=None):
    """Generate code with relevant project context"""
    
    context = ""
    if search_query:
        # Get relevant context from multimodal search
        search_results = search_codebase(search_query)
        context = f"\n\nRelevant project context:\n{search_results['context']}\n"
    
    full_prompt = f"{prompt}{context}"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a senior developer working on a multimodal LLM stack. Use the provided context to generate accurate, consistent code."},
            {"role": "user", "content": full_prompt}
        ],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

# Example usage
code = generate_with_context(
    "Create a new FastAPI endpoint for batch image processing",
    search_query="image processing FastAPI endpoint batch"
)
print(code)
```

### 2. Automated Documentation Updates

```python
# scripts/update_docs.py
import ast
import requests
from pathlib import Path

def extract_api_endpoints(file_path):
    """Extract FastAPI endpoints from Python file"""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())
    
    endpoints = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and hasattr(decorator.func, 'attr'):
                    if decorator.func.attr in ['get', 'post', 'put', 'delete']:
                        endpoints.append({
                            'method': decorator.func.attr.upper(),
                            'path': decorator.args[0].s if decorator.args else '/',
                            'function': node.name,
                            'docstring': ast.get_docstring(node)
                        })
    return endpoints

def update_api_docs():
    """Update API documentation based on code changes"""
    
    # Extract endpoints from services
    worker_endpoints = extract_api_endpoints("services/multimodal-worker/app/api.py")
    proxy_endpoints = extract_api_endpoints("services/retrieval-proxy/app/api.py")
    
    # Generate documentation
    doc_content = "# Auto-Generated API Reference\n\n"
    
    doc_content += "## Multimodal Worker Endpoints\n\n"
    for endpoint in worker_endpoints:
        doc_content += f"### {endpoint['method']} {endpoint['path']}\n"
        doc_content += f"Function: `{endpoint['function']}`\n"
        if endpoint['docstring']:
            doc_content += f"Description: {endpoint['docstring']}\n"
        doc_content += "\n"
    
    doc_content += "## Retrieval Proxy Endpoints\n\n"
    for endpoint in proxy_endpoints:
        doc_content += f"### {endpoint['method']} {endpoint['path']}\n"
        doc_content += f"Function: `{endpoint['function']}`\n"
        if endpoint['docstring']:
            doc_content += f"Description: {endpoint['docstring']}\n"
        doc_content += "\n"
    
    # Save updated documentation
    with open("docs/auto-generated-api.md", "w") as f:
        f.write(doc_content)
    
    # Process with multimodal worker for search indexing
    requests.post("http://localhost:8001/api/v1/process/text", json={
        "text": doc_content,
        "document_name": "auto-generated-api.md",
        "metadata": {"type": "api_documentation", "auto_generated": True}
    })
    
    print("API documentation updated and indexed")

if __name__ == "__main__":
    update_api_docs()
```

### 3. Visual Architecture Analysis

```python
# scripts/analyze_architecture.py
import requests
from PIL import Image, ImageDraw, ImageFont
import io

def create_architecture_diagram():
    """Create and analyze architecture diagram"""
    
    # Create simple architecture diagram
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw components (simplified example)
    components = [
        ("Cursor IDE", 50, 50, 150, 100),
        ("LiteLLM", 250, 50, 350, 100),
        ("vLLM", 450, 50, 550, 100),
        ("Multimodal Worker", 50, 200, 200, 250),
        ("Retrieval Proxy", 250, 200, 400, 250),
        ("PostgreSQL", 50, 350, 150, 400),
        ("Qdrant", 200, 350, 300, 400),
        ("MinIO", 350, 350, 450, 400),
    ]
    
    for name, x1, y1, x2, y2 in components:
        draw.rectangle([x1, y1, x2, y2], outline='black', fill='lightblue')
        draw.text((x1 + 10, y1 + 10), name, fill='black')
    
    # Save diagram
    img.save('architecture_diagram.png')
    
    # Process with multimodal worker
    with open('architecture_diagram.png', 'rb') as f:
        files = {'file': f}
        data = {
            'document_name': 'architecture_diagram.png',
            'metadata': '{"type": "architecture", "generated": true}'
        }
        
        response = requests.post(
            "http://localhost:8001/api/v1/process/image",
            files=files,
            data=data
        )
    
    print("Architecture diagram created and analyzed:", response.json())

if __name__ == "__main__":
    create_architecture_diagram()
```

## Cursor Commands Integration

Add these commands to your Cursor workspace:

### `.vscode/tasks.json`

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Multimodal Stack",
            "type": "shell",
            "command": "docker-compose up -d",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Health Check",
            "type": "shell",
            "command": "./scripts/health-check.sh",
            "group": "test",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Search Codebase",
            "type": "shell",
            "command": "python scripts/smart_search.py '${input:searchQuery}'",
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Process Documentation",
            "type": "shell",
            "command": "python scripts/process_codebase.py",
            "group": "build"
        }
    ],
    "inputs": [
        {
            "id": "searchQuery",
            "description": "Search query for codebase",
            "default": "authentication",
            "type": "promptString"
        }
    ]
}
```

## Usage Examples

### 1. Code Review with Context

```bash
# Search for similar implementations before reviewing
python scripts/smart_search.py "error handling FastAPI async"

# Use the context in Cursor chat:
# "Review this error handling code using the patterns from our codebase"
```

### 2. Feature Development

```bash
# 1. Search for existing patterns
python scripts/smart_search.py "video processing keyframe extraction"

# 2. Generate new feature with context
# Use Cursor chat: "Create a new video thumbnail generation endpoint following our existing patterns"

# 3. Update documentation
python scripts/update_docs.py
```

### 3. Debugging with Visual Context

```bash
# Process error screenshots
curl -X POST http://localhost:8001/api/v1/process/image \
  -F "file=@error_screenshot.png" \
  -F "document_name=debug_error.png"

# Search for similar issues
python scripts/smart_search.py "database connection error timeout"
```

This integration allows Cursor to leverage the full multimodal capabilities of your stack, providing rich context for code generation, debugging, and development workflows.
