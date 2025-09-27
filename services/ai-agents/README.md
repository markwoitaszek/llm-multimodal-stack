# AI Agents Service

A comprehensive LangChain-based autonomous agent framework with multimodal capabilities for the Multimodal LLM Stack.

## 🚀 Features

- **Autonomous Agents**: Create and manage AI agents with custom goals and capabilities
- **Multimodal Tools**: Image analysis, content search, text generation, and web search
- **Persistent Memory**: Conversation history and execution tracking
- **Pre-built Templates**: 7+ ready-to-use agent templates for common use cases
- **Web Interface**: React-based management interface for easy agent creation and monitoring
- **Performance Tracking**: Execution time monitoring and success rate analytics
- **RESTful API**: Complete API for programmatic agent management

## 📋 Quick Start

### 1. Start the Service

```bash
# Start with the main stack
docker-compose -f docker-compose.yml -f docker-compose.ai-agents.yml up -d

# Or start just the AI agents service
docker-compose -f docker-compose.ai-agents.yml up -d
```

### 2. Access the Web Interface

- **Web UI**: http://localhost:3001
- **API Documentation**: http://localhost:8003/docs
- **Health Check**: http://localhost:8003/health

### 3. Create Your First Agent

```python
import requests

# Create an agent from template
response = requests.post("http://localhost:8003/api/v1/agents/from-template", 
    params={
        "template_name": "research_assistant",
        "agent_name": "My Research Bot"
    }
)
agent_id = response.json()["agent_id"]

# Execute a task
response = requests.post(f"http://localhost:8003/api/v1/agents/{agent_id}/execute", 
    json={"task": "Research the latest trends in AI"})
result = response.json()
print(result["result"])
```

## 🏗️ Architecture

```
AI Agents Service
├── Agent Manager (LangChain integration)
├── Tool Registry (Multimodal tools)
├── Memory Manager (PostgreSQL persistence)
├── Templates (Pre-built configurations)
├── Web Interface (React frontend)
└── REST API (FastAPI backend)
```

## 🛠️ Available Tools

### 1. Image Analysis Tool
- **Purpose**: Analyze images and generate detailed captions
- **Integration**: Uses multimodal-worker service
- **Use Cases**: Image understanding, content moderation, visual search

### 2. Content Search Tool
- **Purpose**: Search through stored text, images, and videos
- **Integration**: Uses retrieval-proxy service
- **Use Cases**: Knowledge retrieval, content discovery, research

### 3. Text Generation Tool
- **Purpose**: Generate text, summaries, and creative content
- **Integration**: Uses vLLM inference service
- **Use Cases**: Content creation, summarization, creative writing

### 4. Web Search Tool
- **Purpose**: Search the web for current information
- **Integration**: Placeholder for web search APIs
- **Use Cases**: Real-time information, fact checking, news updates

## 📚 Agent Templates

### Research Assistant
- **Goal**: Help users research topics by searching and analyzing information
- **Tools**: search_content, generate_text, web_search
- **Best For**: Academic research, market analysis, competitive intelligence

### Content Analyzer
- **Goal**: Analyze various content types to extract insights
- **Tools**: analyze_image, search_content, generate_text
- **Best For**: Image analysis, video understanding, document summarization

### Creative Writer
- **Goal**: Help create engaging written content
- **Tools**: generate_text, search_content
- **Best For**: Story writing, marketing copy, blog posts

### Customer Service Agent
- **Goal**: Provide helpful customer service and resolve issues
- **Tools**: search_content, generate_text
- **Best For**: FAQ responses, issue resolution, product information

### Data Researcher
- **Goal**: Find and analyze data from various sources
- **Tools**: search_content, generate_text, web_search
- **Best For**: Data discovery, trend analysis, statistical insights

### Learning Tutor
- **Goal**: Help users learn by explaining concepts and answering questions
- **Tools**: search_content, generate_text
- **Best For**: Concept explanation, homework help, study guidance

### Project Manager
- **Goal**: Assist with project planning and coordination
- **Tools**: search_content, generate_text
- **Best For**: Task planning, progress tracking, resource coordination

## 🔧 API Reference

### Agent Management

#### Create Agent
```http
POST /api/v1/agents
Content-Type: application/json

{
  "name": "My Agent",
  "goal": "Help users with their tasks",
  "tools": ["search_content", "generate_text"],
  "memory_window": 10,
  "user_id": "default"
}
```

#### List Agents
```http
GET /api/v1/agents?user_id=default
```

#### Get Agent Details
```http
GET /api/v1/agents/{agent_id}
```

#### Execute Agent Task
```http
POST /api/v1/agents/{agent_id}/execute
Content-Type: application/json

{
  "task": "Your task description",
  "user_id": "default"
}
```

#### Delete Agent
```http
DELETE /api/v1/agents/{agent_id}?user_id=default
```

### Template Management

#### List Templates
```http
GET /api/v1/templates
GET /api/v1/templates?category=research
GET /api/v1/templates?search=assistant
```

#### Get Template Details
```http
GET /api/v1/templates/{template_name}
```

#### Create Agent from Template
```http
POST /api/v1/agents/from-template
Content-Type: application/json

{
  "template_name": "research_assistant",
  "agent_name": "My Research Bot",
  "user_id": "default"
}
```

### Monitoring

#### Get Agent History
```http
GET /api/v1/agents/{agent_id}/history?limit=20
```

#### Get Agent Statistics
```http
GET /api/v1/agents/{agent_id}/stats
```

#### List Available Tools
```http
GET /api/v1/tools
```

## 🎯 Use Cases

### 1. Content Analysis Pipeline
```python
# Create content analyzer agent
agent = create_agent_from_template("content_analyzer", "Content Bot")

# Analyze uploaded content
result = execute_agent(agent, "Analyze this image and provide insights")
```

### 2. Research Workflow
```python
# Create research assistant
agent = create_agent_from_template("research_assistant", "Research Bot")

# Research a topic
result = execute_agent(agent, "Research the latest developments in quantum computing")
```

### 3. Customer Support
```python
# Create customer service agent
agent = create_agent_from_template("customer_service", "Support Bot")

# Handle customer inquiry
result = execute_agent(agent, "Customer is asking about product pricing")
```

## 🔍 Monitoring & Analytics

### Performance Metrics
- **Execution Time**: Track how long tasks take to complete
- **Success Rate**: Monitor agent performance and reliability
- **Tool Usage**: Understand which tools are most effective
- **User Engagement**: Track agent usage patterns

### Logging
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Execution Tracking**: Detailed logs of agent actions and decisions
- **Error Handling**: Comprehensive error logging and debugging info

### Health Monitoring
- **Service Health**: Regular health checks and status monitoring
- **Dependency Status**: Monitor connections to other services
- **Performance Alerts**: Automatic alerts for performance issues

## 🚀 Deployment

### Development
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.ai-agents.yml up -d

# View logs
docker-compose logs -f ai-agents
```

### Production
```bash
# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ai-agents.yml up -d
```

### Environment Variables
```env
# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Service URLs
MULTIMODAL_WORKER_URL=http://multimodal-worker:8001
RETRIEVAL_PROXY_URL=http://retrieval-proxy:8002
LLM_BASE_URL=http://vllm:8000/v1

# Agent Configuration
MAX_AGENTS_PER_USER=10
AGENT_EXECUTION_TIMEOUT=300
MAX_TOOL_CALLS_PER_EXECUTION=50
```

## 🧪 Testing

### Unit Tests
```bash
cd services/ai-agents
python -m pytest tests/
```

### Integration Tests
```bash
# Test agent creation and execution
python tests/test_integration.py
```

### Load Testing
```bash
# Test concurrent agent executions
python tests/test_load.py
```

## 📖 Examples

See the `examples/` directory for:
- Basic agent creation and execution
- Template usage examples
- API integration samples
- Web interface usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is part of the Multimodal LLM Stack and follows the same licensing terms.

## 🆘 Support

- **Documentation**: Check the `/docs` directory for detailed guides
- **Issues**: Report bugs and feature requests via GitHub issues
- **Community**: Join our Discord for discussions and support

---

**Ready to create autonomous AI agents? Start with our [Quick Start Guide](#-quick-start) or explore the [Web Interface](http://localhost:3001)!**
