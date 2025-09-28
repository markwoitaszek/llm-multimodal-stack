# Frequently Asked Questions (FAQ)

## 🚀 Getting Started

### Q: How do I get started with the Multimodal LLM Stack?

**A:** The easiest way to get started is:

1. **Clone the repository** and follow the setup instructions in the README
2. **Start the services** using Docker Compose: `docker-compose up -d`
3. **Check service health** at `http://localhost:8080/swagger-ui.html`
4. **Try the interactive API docs** to test endpoints
5. **Use the SDKs** for your preferred language (Python/JavaScript)

### Q: What are the system requirements?

**A:** Minimum requirements:
- **CPU**: 4 cores, 2.4GHz
- **RAM**: 8GB (16GB recommended for GPU acceleration)
- **Storage**: 20GB free space
- **GPU**: Optional but recommended (NVIDIA with CUDA support)
- **Docker**: 20.10+ and Docker Compose 2.0+

### Q: Do I need a GPU to run the stack?

**A:** No, but it's highly recommended. The stack can run on CPU-only, but:
- **With GPU**: Much faster model inference and processing
- **Without GPU**: Slower but functional for development and testing
- **Recommended**: NVIDIA GPU with 8GB+ VRAM for optimal performance

## 🔧 Installation & Setup

### Q: How do I install the stack?

**A:** There are several installation methods:

**Docker Compose (Recommended):**
```bash
git clone https://github.com/your-org/llm-multimodal-stack.git
cd llm-multimodal-stack
docker-compose up -d
```

**Manual Installation:**
```bash
# Install dependencies
pip install -r requirements.txt

# Start each service individually
python services/multimodal-worker/main.py
python services/retrieval-proxy/main.py
python services/ai-agents/main.py
```

### Q: How do I configure the services?

**A:** Configuration is done through environment variables:

```bash
# Copy the example environment file
cp env.example .env

# Edit the configuration
nano .env
```

Key configuration options:
- `LITELLM_MASTER_KEY`: API key for LiteLLM Router
- `POSTGRES_PASSWORD`: Database password
- `MINIO_ROOT_PASSWORD`: Storage password
- `VLLM_MODEL`: Model to use for inference

### Q: How do I update the stack?

**A:** To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔑 Authentication & Security

### Q: How does authentication work?

**A:** Currently, the stack uses:
- **LiteLLM Router**: Bearer token authentication (`Authorization: Bearer sk-your-key`)
- **Other Services**: No authentication (internal services)
- **Future**: JWT tokens, API keys, and OAuth 2.0 support planned

### Q: How do I secure the services for production?

**A:** For production deployment:

1. **Use HTTPS** with proper SSL certificates
2. **Implement authentication** for all services
3. **Use environment variables** for sensitive configuration
4. **Enable firewall rules** to restrict access
5. **Regular security updates** and monitoring
6. **Use secrets management** (e.g., HashiCorp Vault)

### Q: Can I use my own API keys?

**A:** Yes! You can configure the stack to use:
- **OpenAI API keys** for GPT models
- **Anthropic API keys** for Claude models
- **Local models** via vLLM or Ollama
- **Custom model endpoints** through LiteLLM configuration

## 📊 API Usage

### Q: How do I make API calls?

**A:** You can use the APIs in several ways:

**Python SDK:**
```python
from multimodal_llm_client import createClient

client = createClient(litellm_api_key="sk-your-key")
result = client.multimodal_worker.process_image("image.jpg")
```

**JavaScript SDK:**
```javascript
const { createClient } = require('./multimodal-llm-client');
const client = createClient({ litellmApiKey: 'sk-your-key' });
const result = await client.multimodalWorker.processImage(file);
```

**Direct HTTP calls:**
```bash
curl -X POST http://localhost:8001/api/v1/process/image \
  -F "file=@image.jpg" \
  -F "document_name=my_image.jpg"
```

### Q: What file formats are supported?

**A:** The stack supports:

**Images**: JPG, PNG, GIF, WebP, BMP, TIFF
**Videos**: MP4, AVI, MOV, WebM, MKV
**Text**: TXT, PDF, DOCX, MD, HTML
**Audio**: MP3, WAV, FLAC (for transcription)

### Q: What are the file size limits?

**A:** Default limits (configurable):
- **Images**: 100MB
- **Videos**: 500MB
- **Text**: 10MB
- **Rate limits**: 60 requests/minute (LiteLLM), 30 uploads/minute (Multimodal Worker)

### Q: How do I handle rate limits?

**A:** Rate limits are enforced per service:
- **LiteLLM Router**: 60 requests/minute per API key
- **Multimodal Worker**: 30 uploads/minute per IP
- **Retrieval Proxy**: 120 searches/minute per IP

To handle rate limits:
```python
import time
import requests

def make_request_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=data)
            if response.status_code == 429:
                time.sleep(60)  # Wait 1 minute
                continue
            return response
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

## 🤖 AI Models & Processing

### Q: What AI models are included?

**A:** The stack includes several pre-configured models:

**Text Processing:**
- **CLIP**: Image-text understanding
- **BLIP**: Image captioning
- **Whisper**: Speech-to-text transcription
- **Sentence Transformers**: Text embeddings

**Language Models:**
- **vLLM**: Local LLM inference
- **OpenAI Models**: GPT-3.5, GPT-4 (via API)
- **Anthropic Models**: Claude (via API)

### Q: How do I add custom models?

**A:** You can add custom models by:

1. **Modifying the configuration** in `configs/litellm_config.yaml`
2. **Adding model files** to the `models/` directory
3. **Updating the model manager** in each service
4. **Restarting the services** to load new models

### Q: How do I improve processing speed?

**A:** To optimize performance:

1. **Use GPU acceleration** when available
2. **Increase batch sizes** for processing multiple files
3. **Enable caching** for repeated operations
4. **Use appropriate model sizes** (smaller models for faster inference)
5. **Optimize image/video resolution** before processing

## 🔍 Search & Retrieval

### Q: How does the search work?

**A:** The search system uses:

1. **Vector embeddings** for semantic similarity
2. **Multimodal indexing** (text, image, video)
3. **Hybrid search** combining vector and keyword search
4. **Context bundling** for comprehensive results
5. **Caching** for improved performance

### Q: How do I improve search results?

**A:** To get better search results:

1. **Use specific keywords** and phrases
2. **Combine multiple modalities** (text + image + video)
3. **Adjust score thresholds** for relevance
4. **Use filters** to narrow results
5. **Process more content** to increase the search index

### Q: Can I search across my own documents?

**A:** Yes! You can:

1. **Upload your documents** via the Multimodal Worker
2. **Process them** for indexing and embedding generation
3. **Search across them** using the Retrieval Proxy
4. **Get context bundles** for comprehensive results

## 🤖 AI Agents

### Q: What are AI agents and how do they work?

**A:** AI agents are autonomous systems that can:

1. **Execute complex tasks** using multiple tools
2. **Maintain conversation memory** across interactions
3. **Use various tools** (web search, document analysis, etc.)
4. **Learn from interactions** and improve over time
5. **Work autonomously** without constant supervision

### Q: How do I create an AI agent?

**A:** You can create agents in several ways:

**Using the API:**
```python
agent = client.ai_agents.create_agent(
    name="Research Assistant",
    goal="Help with research tasks",
    tools=["web_search", "document_analysis"],
    memory_window=15
)
```

**Using templates:**
```python
agent = client.ai_agents.create_agent_from_template(
    template_name="research_assistant",
    agent_name="My Research Bot"
)
```

### Q: What tools are available for agents?

**A:** Available tools include:
- **Web Search**: Search the internet for information
- **Document Analysis**: Analyze uploaded documents
- **Image Analysis**: Process and understand images
- **Text Analysis**: Analyze and summarize text
- **Trend Analysis**: Identify patterns and trends
- **Custom Tools**: Add your own tools via the API

## 🐛 Troubleshooting

### Q: Services won't start - what should I check?

**A:** Common issues and solutions:

1. **Port conflicts**: Check if ports 4000, 8001, 8002, 8003 are available
2. **Docker issues**: Ensure Docker is running and has enough resources
3. **GPU problems**: Check NVIDIA drivers and CUDA installation
4. **Memory issues**: Increase Docker memory limits
5. **Network issues**: Check firewall and network connectivity

### Q: I'm getting "Model not loaded" errors - how do I fix this?

**A:** This usually means:

1. **Models are still loading**: Wait a few minutes for models to load
2. **Insufficient memory**: Increase available RAM/VRAM
3. **Model files missing**: Check if model files are in the correct directory
4. **Configuration issues**: Verify model configuration in the config files

### Q: Search results are empty - what's wrong?

**A:** Empty search results can be caused by:

1. **No content processed**: Upload and process some documents first
2. **Vector store issues**: Check if Qdrant is running and accessible
3. **Indexing problems**: Verify that embeddings were generated correctly
4. **Search query issues**: Try different search terms or lower score thresholds

### Q: How do I debug API errors?

**A:** To debug API issues:

1. **Check service logs**: `docker-compose logs service-name`
2. **Verify endpoints**: Use the Swagger UI to test endpoints
3. **Check health status**: Visit `/health` endpoints
4. **Review error responses**: Look at the error codes and messages
5. **Test with curl**: Use simple curl commands to isolate issues

## 📈 Performance & Scaling

### Q: How do I scale the stack for production?

**A:** For production scaling:

1. **Use load balancers** for multiple service instances
2. **Implement horizontal scaling** with multiple containers
3. **Use managed databases** (PostgreSQL, Redis, Qdrant Cloud)
4. **Implement caching layers** (Redis, CDN)
5. **Monitor performance** with metrics and logging
6. **Use container orchestration** (Kubernetes, Docker Swarm)

### Q: How do I monitor the stack?

**A:** Monitoring options:

1. **Health endpoints**: Check `/health` on each service
2. **Metrics endpoints**: Use `/api/v1/stats` for system statistics
3. **Log aggregation**: Use ELK stack or similar
4. **APM tools**: Integrate with New Relic, DataDog, etc.
5. **Custom dashboards**: Build with Grafana and Prometheus

### Q: What's the expected performance?

**A:** Performance depends on your hardware:

**CPU-only (4 cores, 8GB RAM):**
- Image processing: 2-5 seconds per image
- Text processing: 1-2 seconds per document
- Search: 100-500ms per query

**With GPU (RTX 3080, 16GB RAM):**
- Image processing: 0.5-1 second per image
- Text processing: 0.2-0.5 seconds per document
- Search: 50-200ms per query

## 🔄 Integration & Customization

### Q: How do I integrate with my existing system?

**A:** Integration options:

1. **REST APIs**: Use the HTTP endpoints directly
2. **SDKs**: Use Python or JavaScript SDKs
3. **Webhooks**: Set up webhooks for event notifications
4. **Batch processing**: Use batch endpoints for bulk operations
5. **Custom clients**: Build your own client using the OpenAPI specs

### Q: Can I customize the models and processing?

**A:** Yes! You can:

1. **Add custom models** to the model directory
2. **Modify processing pipelines** in the service code
3. **Create custom tools** for AI agents
4. **Extend the API** with additional endpoints
5. **Customize the UI** and documentation

### Q: How do I contribute to the project?

**A:** We welcome contributions! To contribute:

1. **Fork the repository** on GitHub
2. **Create a feature branch** for your changes
3. **Follow the coding standards** and add tests
4. **Submit a pull request** with a clear description
5. **Join the community** discussions and help others

## 📞 Support & Community

### Q: Where can I get help?

**A:** Support channels:

1. **Documentation**: Check the comprehensive docs first
2. **GitHub Issues**: Report bugs and request features
3. **Community Forum**: Join discussions and ask questions
4. **Discord/Slack**: Real-time chat with the community
5. **Email Support**: For enterprise customers

### Q: How do I report bugs?

**A:** To report bugs effectively:

1. **Check existing issues** to avoid duplicates
2. **Provide detailed information**:
   - OS and version
   - Docker version
   - Error messages and logs
   - Steps to reproduce
   - Expected vs actual behavior
3. **Include relevant files** (configs, logs, etc.)
4. **Use the bug report template** on GitHub

### Q: How do I request new features?

**A:** Feature requests should include:

1. **Clear description** of the feature
2. **Use case and motivation** for why it's needed
3. **Proposed implementation** (if you have ideas)
4. **Priority level** and timeline
5. **Community support** (upvotes, comments)

---

## 📝 Still Have Questions?

If you can't find the answer to your question in this FAQ, please:

1. **Search the documentation** using our search interface
2. **Check the GitHub issues** for similar problems
3. **Join our community** for real-time help
4. **Submit a new issue** with your question

We're here to help you succeed with the Multimodal LLM Stack! 🚀