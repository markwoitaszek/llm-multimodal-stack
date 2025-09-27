# 🔄 n8n Workflows

This directory contains pre-built workflow templates for common AI automation tasks.

## 📋 Available Workflows

### 1. **Content Processing Pipeline**
- **File**: `content-processing-pipeline.json`
- **Purpose**: Automated content analysis and indexing
- **Flow**: Upload → Extract Text → Generate Embeddings → Store → Notify

### 2. **Social Media Monitoring**
- **File**: `social-media-monitoring.json`
- **Purpose**: Monitor social platforms for mentions and sentiment
- **Flow**: Scrape → Analyze Sentiment → Generate Summary → Alert

### 3. **Document Intelligence**
- **File**: `document-intelligence.json`
- **Purpose**: Intelligent document processing and Q&A
- **Flow**: PDF Upload → Extract → Chunk → Embed → Enable Q&A

### 4. **Video Content Analysis**
- **File**: `video-analysis-pipeline.json`
- **Purpose**: Comprehensive video content processing
- **Flow**: Video Upload → Transcribe → Extract Keyframes → Caption → Index

### 5. **API Integration Hub**
- **File**: `api-integration-hub.json`
- **Purpose**: Connect external APIs with AI processing
- **Flow**: Webhook → Process → AI Analysis → Forward Results

## 🚀 Quick Start

1. **Access n8n**: http://localhost:5678
2. **Login**: admin / admin123 (change in .env)
3. **Import Workflow**: 
   - Click "Import from File"
   - Select a workflow JSON file
   - Configure credentials
   - Activate workflow

## 🔧 Workflow Development

### Creating Custom Workflows

1. **Start with Template**: Use existing workflows as starting points
2. **Add Nodes**: Drag and drop from the node palette
3. **Configure Connections**: Link nodes for data flow
4. **Test Execution**: Use test data to validate
5. **Deploy**: Activate for production use

### Available Nodes for Multimodal Stack

- **HTTP Request**: Call any API endpoint
- **Webhook**: Trigger workflows from external events
- **Code**: Custom JavaScript/Python logic
- **Schedule**: Time-based automation
- **Email**: Send notifications and reports

### Integration Points

**Multimodal Worker API:**
- Endpoint: `http://multimodal-worker:8001/api/v1`
- Authentication: None (internal network)
- Capabilities: Image, video, text processing

**Retrieval Proxy API:**
- Endpoint: `http://retrieval-proxy:8002/api/v1`
- Authentication: None (internal network)
- Capabilities: Search, context bundling

**vLLM API:**
- Endpoint: `http://vllm:8000/v1`
- Authentication: None (internal network)
- Capabilities: Text generation, chat completion

## 📚 Examples

### Simple Text Processing Workflow
```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "process-text",
        "httpMethod": "POST"
      }
    },
    {
      "name": "Process Text",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://multimodal-worker:8001/api/v1/process/text",
        "method": "POST",
        "body": "={{$json}}"
      }
    },
    {
      "name": "Search Content",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://retrieval-proxy:8002/api/v1/search",
        "method": "POST",
        "body": {
          "query": "={{$json.text}}",
          "limit": 5
        }
      }
    }
  ]
}
```

## 🔒 Security Notes

- **Authentication**: Enable basic auth for n8n interface
- **Network**: All API calls use internal Docker network
- **Credentials**: Store sensitive data in n8n credential store
- **Webhooks**: Use HTTPS in production deployments

## 📊 Monitoring

- **Workflow Execution**: Monitor in n8n interface
- **Performance**: Check execution times and success rates
- **Errors**: Review failed executions and logs
- **Resources**: Monitor CPU and memory usage

---

Start building powerful AI automation workflows with visual simplicity! 🎨
