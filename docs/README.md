# Multimodal LLM Stack API Documentation

This directory contains comprehensive API documentation for the Multimodal LLM Stack, including OpenAPI 3.0 specifications and an enhanced Swagger UI interface.

## 📁 Directory Structure

```
docs/
├── openapi/                    # OpenAPI 3.0 specifications
│   ├── combined.yaml          # All services combined
│   ├── litellm-router.yaml    # LiteLLM Router API
│   ├── multimodal-worker.yaml # Multimodal Worker API
│   ├── retrieval-proxy.yaml   # Retrieval Proxy API
│   └── ai-agents.yaml         # AI Agents API
├── swagger-ui.html            # Enhanced Swagger UI interface
├── serve-docs.py              # HTTP server for documentation
├── api-reference.md           # Enhanced API reference
└── README.md                  # This file
```

## 🚀 Quick Start

### Option 1: Use the Integrated Documentation (RECOMMENDED)

The documentation is now integrated with the AI Agents Web Interface for a seamless experience.

1. **Start the full stack:**
   ```bash
   docker-compose up -d
   ```

2. **Access the documentation through the web interface:**
   - **Main Interface**: http://localhost:3001
   - **Documentation**: http://localhost:3001/docs/
   - **API Documentation (Swagger UI)**: http://localhost:3001/api-docs/
   - **Combined OpenAPI Spec**: http://localhost:3001/docs/openapi/combined.yaml

### Option 2: Use the Standalone Documentation Server

1. **Start the documentation server:**
   ```bash
   cd docs
   python3 serve-docs.py
   ```

2. **Open your browser and navigate to:**
   - **Interactive Swagger UI**: http://localhost:8080/swagger-ui.html
   - **Combined OpenAPI Spec**: http://localhost:8080/openapi/combined.yaml

### Option 3: Use Any HTTP Server

1. **Serve the docs directory with any HTTP server:**
   ```bash
   cd docs
   python3 -m http.server 8080
   # or
   npx serve .
   # or
   php -S localhost:8080
   ```

2. **Open**: http://localhost:8080/swagger-ui.html

## 📚 API Services

### 1. LiteLLM Router (Port 4000)
- **Purpose**: OpenAI-compatible API router
- **Key Endpoints**:
  - `POST /v1/chat/completions` - Create chat completions
  - `GET /v1/models` - List available models
- **Authentication**: Bearer token (LiteLLM master key)
- **OpenAPI Spec**: [litellm-router.yaml](./openapi/litellm-router.yaml)

### 2. Multimodal Worker (Port 8001)
- **Purpose**: Image, video, and text processing with AI models
- **Key Endpoints**:
  - `POST /api/v1/process/image` - Process images for captioning
  - `POST /api/v1/process/video` - Process videos for transcription
  - `POST /api/v1/process/text` - Process text for chunking
  - `GET /api/v1/models/status` - Check model status
- **Authentication**: None (internal service)
- **OpenAPI Spec**: [multimodal-worker.yaml](./openapi/multimodal-worker.yaml)

### 3. Retrieval Proxy (Port 8002)
- **Purpose**: Unified search and context bundling
- **Key Endpoints**:
  - `POST /api/v1/search` - Multimodal search
  - `GET /api/v1/search/sessions` - Get search sessions
  - `GET /api/v1/context/{session_id}` - Get context bundle
  - `GET /api/v1/artifacts/{type}/{id}` - Get artifacts
- **Authentication**: None (internal service)
- **OpenAPI Spec**: [retrieval-proxy.yaml](./openapi/retrieval-proxy.yaml)

### 4. AI Agents (Port 8003)
- **Purpose**: LangChain-based autonomous agents
- **Key Endpoints**:
  - `POST /api/v1/agents` - Create agents
  - `GET /api/v1/agents` - List agents
  - `POST /api/v1/agents/{id}/execute` - Execute agent tasks
  - `GET /api/v1/templates` - List agent templates
- **Authentication**: None (internal service)
- **OpenAPI Spec**: [ai-agents.yaml](./openapi/ai-agents.yaml)

## 🎨 Enhanced Swagger UI Features

The enhanced Swagger UI includes:

- **Service Selection**: Switch between individual services or view all combined
- **Interactive Testing**: Try out API endpoints directly from the browser
- **Quick Start Examples**: Pre-built curl commands for common operations
- **Service Overview Cards**: Visual representation of each service
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices
- **CORS Support**: Configured for local development and testing

## 📖 API Reference

For detailed API documentation, see:
- [Enhanced API Reference](./api-reference.md) - Comprehensive endpoint documentation
- [OpenAPI Specifications](./openapi/) - Machine-readable API specs

## 🔧 Development

### Adding New Endpoints

1. **Update the service's OpenAPI spec** in `openapi/{service}.yaml`
2. **Update the combined spec** in `openapi/combined.yaml`
3. **Test the changes** by refreshing the Swagger UI

### Customizing Swagger UI

Edit `swagger-ui.html` to:
- Add new service cards
- Modify the color scheme
- Add custom JavaScript functionality
- Include additional examples

### Generating SDKs

The OpenAPI specs can be used to generate client SDKs:

```bash
# Python SDK
openapi-generator generate -i openapi/combined.yaml -g python -o ../sdk/python

# JavaScript SDK
openapi-generator generate -i openapi/combined.yaml -g javascript -o ../sdk/javascript

# Go SDK
openapi-generator generate -i openapi/combined.yaml -g go -o ../sdk/go
```

## 🌐 Production Deployment

For production deployment:

1. **Use a proper web server** (nginx, Apache, etc.)
2. **Configure HTTPS** for security
3. **Set up authentication** if needed
4. **Enable caching** for better performance
5. **Monitor usage** with analytics

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name api-docs.your-domain.com;
    
    location / {
        root /path/to/docs;
        index swagger-ui.html;
        
        # Enable CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # Cache OpenAPI specs
    location ~* \.(yaml|yml|json)$ {
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
}
```

## 📝 Contributing

1. **Follow OpenAPI 3.0 standards**
2. **Include comprehensive examples** for all endpoints
3. **Document error responses** with proper HTTP status codes
4. **Test all changes** in the Swagger UI
5. **Update both individual and combined specs**

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure the server includes CORS headers
2. **YAML Parsing Errors**: Validate YAML syntax with online tools
3. **Missing Examples**: Ensure all endpoints have request/response examples
4. **Authentication Issues**: Check bearer token format and validity

### Validation Tools

- **OpenAPI Validator**: https://editor.swagger.io/
- **YAML Linter**: https://www.yamllint.com/
- **JSON Schema Validator**: https://www.jsonschemavalidator.net/

## 📞 Support

For issues with the API documentation:
1. Check the [troubleshooting section](#-troubleshooting)
2. Validate your OpenAPI specs
3. Test with the interactive Swagger UI
4. Review the service logs for errors

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**OpenAPI Version**: 3.0.3