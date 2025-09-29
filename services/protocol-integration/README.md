# Protocol Integration Service

A comprehensive protocol integration service that provides universal IDE compatibility through multiple protocol implementations including LSP, MCP, and custom protocols.

## 🚀 Features

- **Language Server Protocol (LSP)**: Full LSP 3.17 implementation for universal IDE support
- **Model Context Protocol (MCP)**: Complete MCP implementation for AI coding assistants
- **Custom Protocol Support**: Extensible protocol framework for custom integrations
- **Multi-IDE Compatibility**: Support for VS Code, IntelliJ, Vim, Emacs, and more
- **Real-time Communication**: WebSocket and SSE support for live updates
- **Protocol Translation**: Automatic translation between different protocols
- **Plugin System**: Extensible plugin architecture for custom protocol handlers

## 📋 Quick Start

### 1. Start the Service

```bash
# Start with the main stack
docker-compose -f docker-compose.yml -f docker-compose.protocol-integration.yml up -d

# Or start just the protocol integration service
docker-compose -f docker-compose.protocol-integration.yml up -d
```

### 2. Configure Your IDE

The service automatically provides protocol endpoints that can be configured in your IDE settings.

### 3. Test Protocol Integration

```bash
# Test LSP protocol
curl -X POST http://localhost:8009/lsp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"capabilities": {}}}'

# Test MCP protocol
curl -X GET http://localhost:8009/mcp/tools
```

## 🏗️ Architecture

```
Protocol Integration Service
├── LSP Server (Language Server Protocol)
├── MCP Server (Model Context Protocol)
├── Custom Protocol Handler
├── Protocol Translator
├── Plugin Manager
├── WebSocket Manager
└── Configuration Manager
```

## 🔧 Supported Protocols

### Language Server Protocol (LSP)
- **Version**: 3.17
- **Features**: Completion, hover, definition, references, formatting, diagnostics
- **IDEs**: VS Code, IntelliJ, Vim, Emacs, Sublime Text, Atom

### Model Context Protocol (MCP)
- **Version**: Latest
- **Features**: Tool execution, resource management, prompt templates
- **Clients**: Claude Desktop, Cursor, Continue, and other AI coding assistants

### Custom Protocols
- **WebSocket Protocol**: Real-time bidirectional communication
- **REST API Protocol**: Standard HTTP API endpoints
- **GraphQL Protocol**: GraphQL query interface
- **gRPC Protocol**: High-performance RPC communication

## 🎯 Use Cases

### 1. Universal IDE Support
- Single service supporting multiple IDEs
- Consistent experience across different editors
- Automatic protocol translation

### 2. AI Coding Assistant Integration
- Seamless integration with AI coding tools
- Tool execution and resource management
- Context-aware assistance

### 3. Custom Development Tools
- Plugin architecture for custom protocols
- Extensible framework for new integrations
- Protocol translation and bridging

### 4. Enterprise Integration
- Multi-protocol support for different teams
- Centralized protocol management
- Security and access control

## 🔍 API Reference

### LSP Endpoints

#### Initialize
```http
POST /lsp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "processId": 12345,
    "rootUri": "file:///path/to/project",
    "capabilities": {
      "textDocument": {
        "completion": true,
        "hover": true,
        "diagnostics": true
      }
    }
  }
}
```

#### Text Document Completion
```http
POST /lsp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "textDocument/completion",
  "params": {
    "textDocument": {
      "uri": "file:///path/to/file.py"
    },
    "position": {
      "line": 10,
      "character": 5
    }
  }
}
```

### MCP Endpoints

#### List Tools
```http
GET /mcp/tools
```

#### Execute Tool
```http
POST /mcp/tools/execute
Content-Type: application/json

{
  "tool": "code_analysis",
  "parameters": {
    "file_path": "/path/to/file.py",
    "analysis_type": "syntax"
  }
}
```

#### List Resources
```http
GET /mcp/resources
```

#### Read Resource
```http
GET /mcp/resources/{resource_id}
```

### Custom Protocol Endpoints

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8009/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Protocol message:', data);
};
```

#### GraphQL Query
```graphql
query {
  agents {
    id
    name
    status
    tools
  }
}
```

## 🚀 Deployment

### Development
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.protocol-integration.yml up -d

# View logs
docker-compose logs -f protocol-integration
```

### Production
```bash
# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.protocol-integration.yml up -d
```

### Environment Variables
```env
# Service Configuration
PROTOCOL_INTEGRATION_PORT=8009
PROTOCOL_INTEGRATION_HOST=0.0.0.0

# Protocol Configuration
LSP_ENABLED=true
MCP_ENABLED=true
CUSTOM_PROTOCOLS_ENABLED=true

# IDE Integration
AI_AGENTS_URL=http://ai-agents:8003
IDE_BRIDGE_URL=http://ide-bridge:8007

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=8

# Security
SECRET_KEY=protocol-integration-secret-key
ALLOWED_ORIGINS=*
```

## 🧪 Testing

### Unit Tests
```bash
cd services/protocol-integration
python -m pytest tests/
```

### Protocol Tests
```bash
# Test LSP protocol compliance
python tests/test_lsp_compliance.py

# Test MCP protocol compliance
python tests/test_mcp_compliance.py

# Test custom protocols
python tests/test_custom_protocols.py
```

### Integration Tests
```bash
# Test IDE integration
python tests/test_ide_integration.py

# Test protocol translation
python tests/test_protocol_translation.py
```

## 📖 Examples

See the `examples/` directory for:
- IDE configuration examples
- Protocol implementation samples
- Custom protocol development
- Integration patterns

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

**Ready to integrate with any IDE or AI coding assistant? Start with our [Quick Start Guide](#-quick-start) or explore the [Protocol Examples](examples/)!**