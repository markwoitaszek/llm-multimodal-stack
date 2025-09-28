# Multimodal LLM Stack JavaScript SDK

A comprehensive JavaScript client for the Multimodal LLM Stack services.

## Installation

```bash
npm install axios
```

Or with yarn:

```bash
yarn add axios
```

## Quick Start

### Node.js

```javascript
const { createClient } = require('./multimodal-llm-client');

// Initialize client
const client = createClient({
    litellmApiKey: 'sk-your-litellm-key'
});

async function main() {
    try {
        // Check service health
        const health = await client.healthCheck();
        console.log('Health Status:', health);

        // Process text content
        const textResult = await client.multimodalWorker.processText(
            'This is a sample document about artificial intelligence...',
            'ai_document.txt',
            { category: 'tutorial', tags: ['AI', 'machine learning'] }
        );
        console.log('Text processing result:', textResult);

        // Search for content
        const searchResults = await client.retrievalProxy.search(
            'artificial intelligence',
            ['text', 'image'],
            5
        );
        console.log('Search results:', searchResults);

        // Create an AI agent
        const agent = await client.aiAgents.createAgent(
            'Research Assistant',
            'Help with research tasks',
            ['web_search', 'document_analysis']
        );
        console.log('Created agent:', agent);

        // Chat with LiteLLM
        const chatResponse = await client.litellm.chatCompletion(
            [{ role: 'user', content: 'Hello, how are you?' }],
            'gpt-3.5-turbo',
            100
        );
        console.log('Chat response:', chatResponse);

    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

### Browser

```html
<!DOCTYPE html>
<html>
<head>
    <title>Multimodal LLM Client Example</title>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
    <script src="multimodal-llm-client.js"></script>
</head>
<body>
    <script>
        // Initialize client
        const client = createClient({
            litellmApiKey: 'sk-your-litellm-key'
        });

        async function processFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Please select a file');
                return;
            }

            try {
                // Process image
                const result = await client.multimodalWorker.processImage(
                    file,
                    file.name,
                    { category: 'upload', source: 'browser' }
                );
                
                console.log('Processing result:', result);
                document.getElementById('result').innerHTML = 
                    `<pre>${JSON.stringify(result, null, 2)}</pre>`;
                    
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('result').innerHTML = 
                    `<p style="color: red;">Error: ${error.message}</p>`;
            }
        }

        // Search function
        async function searchContent() {
            const query = document.getElementById('searchQuery').value;
            
            if (!query) {
                alert('Please enter a search query');
                return;
            }

            try {
                const results = await client.retrievalProxy.search(
                    query,
                    ['text', 'image', 'video'],
                    10
                );
                
                console.log('Search results:', results);
                document.getElementById('searchResults').innerHTML = 
                    `<pre>${JSON.stringify(results, null, 2)}</pre>`;
                    
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('searchResults').innerHTML = 
                    `<p style="color: red;">Error: ${error.message}</p>`;
            }
        }
    </script>

    <h1>Multimodal LLM Client Example</h1>
    
    <h2>File Processing</h2>
    <input type="file" id="fileInput" accept="image/*">
    <button onclick="processFile()">Process Image</button>
    <div id="result"></div>

    <h2>Search</h2>
    <input type="text" id="searchQuery" placeholder="Enter search query">
    <button onclick="searchContent()">Search</button>
    <div id="searchResults"></div>
</body>
</html>
```

## API Reference

### MultimodalLLMClient

Main client class that provides access to all services.

#### Constructor

```javascript
new MultimodalLLMClient({
    litellmBaseUrl: 'http://localhost:4000',
    multimodalWorkerUrl: 'http://localhost:8001',
    retrievalProxyUrl: 'http://localhost:8002',
    aiAgentsUrl: 'http://localhost:8003',
    litellmApiKey: null,
    timeout: 30000
})
```

#### Methods

- `healthCheck()` - Check health status of all services

### LiteLLMClient

Client for the LiteLLM Router service.

#### Methods

- `chatCompletion(messages, model, maxTokens, temperature, options)` - Create chat completion
- `listModels()` - List available models
- `healthCheck()` - Check service health

### MultimodalWorkerClient

Client for the Multimodal Worker service.

#### Methods

- `processImage(imagePath, documentName, metadata)` - Process image file
- `processVideo(videoPath, documentName, metadata)` - Process video file
- `processText(text, documentName, metadata)` - Process text content
- `getModelsStatus()` - Get model status
- `getStorageStatus()` - Get storage status
- `healthCheck()` - Check service health

### RetrievalProxyClient

Client for the Retrieval Proxy service.

#### Methods

- `search(query, modalities, limit, filters, scoreThreshold)` - Perform search
- `getSearchSessions(limit)` - Get search sessions
- `getContextBundle(sessionId, format)` - Get context bundle
- `getImageArtifact(documentId)` - Get image artifact
- `getVideoArtifact(documentId)` - Get video artifact
- `getKeyframeArtifact(keyframeId)` - Get keyframe artifact
- `getSystemStats()` - Get system statistics
- `healthCheck()` - Check service health

### AIAgentsClient

Client for the AI Agents service.

#### Methods

- `createAgent(name, goal, tools, memoryWindow, userId)` - Create agent
- `listAgents(userId)` - List agents
- `getAgent(agentId)` - Get agent details
- `executeAgentTask(agentId, task, userId)` - Execute agent task
- `deleteAgent(agentId, userId)` - Delete agent
- `listTools()` - List available tools
- `listTemplates(category, search)` - List templates
- `getTemplateDetails(templateName)` - Get template details
- `createAgentFromTemplate(templateName, agentName, userId)` - Create from template
- `getAgentHistory(agentId, limit)` - Get agent history
- `getAgentStats(agentId)` - Get agent statistics
- `healthCheck()` - Check service health

## Examples

### Complete Workflow

```javascript
const { createClient } = require('./multimodal-llm-client');

async function completeWorkflow() {
    const client = createClient({
        litellmApiKey: 'sk-your-key'
    });

    try {
        // 1. Process text content
        const textResult = await client.multimodalWorker.processText(
            'Machine learning is a subset of artificial intelligence...',
            'ml_introduction.txt',
            { category: 'tutorial', tags: ['AI', 'machine learning'] }
        );
        console.log('Text processing result:', textResult);

        // 2. Search for related content
        const searchResults = await client.retrievalProxy.search(
            'machine learning algorithms',
            ['text', 'image'],
            5,
            { file_types: ['txt', 'pdf', 'jpg'] },
            0.8
        );
        console.log('Search results:', searchResults);

        // 3. Create an AI agent to analyze the results
        const agent = await client.aiAgents.createAgent(
            'ML Content Analyzer',
            'Analyze machine learning content and provide insights',
            ['document_analysis', 'text_analysis'],
            15
        );
        console.log('Created agent:', agent);

        // 4. Execute analysis task
        const analysisResult = await client.aiAgents.executeAgentTask(
            agent.agent_id,
            'Analyze the machine learning content and identify key concepts'
        );
        console.log('Analysis result:', analysisResult);

        // 5. Chat about the results
        const chatResponse = await client.litellm.chatCompletion(
            [
                { role: 'system', content: 'You are an AI expert.' },
                { role: 'user', content: `Based on this analysis: ${analysisResult.result}, what are the key insights?` }
            ],
            'gpt-3.5-turbo',
            200
        );
        console.log('Chat response:', chatResponse);

    } catch (error) {
        console.error('Error in workflow:', error.message);
    }
}

completeWorkflow();
```

### Error Handling

```javascript
const { createClient } = require('./multimodal-llm-client');

async function handleErrors() {
    const client = createClient();

    try {
        const result = await client.multimodalWorker.processImage('nonexistent.jpg');
    } catch (error) {
        if (error.response) {
            // Server responded with error status
            const status = error.response.status;
            const data = error.response.data;
            
            switch (status) {
                case 404:
                    console.log('File not found');
                    break;
                case 413:
                    console.log('File too large');
                    break;
                case 422:
                    console.log('Validation error:', data.detail);
                    break;
                default:
                    console.log('HTTP error:', status, data);
            }
        } else if (error.request) {
            // Request was made but no response received
            console.log('Network error:', error.message);
        } else {
            // Something else happened
            console.log('Error:', error.message);
        }
    }
}

handleErrors();
```

### Async/Await with Promise.all

```javascript
const { createClient } = require('./multimodal-llm-client');

async function parallelOperations() {
    const client = createClient();

    try {
        // Run multiple operations in parallel
        const [health, models, stats] = await Promise.all([
            client.healthCheck(),
            client.litellm.listModels(),
            client.retrievalProxy.getSystemStats()
        ]);

        console.log('Health:', health);
        console.log('Models:', models);
        console.log('Stats:', stats);

    } catch (error) {
        console.error('Error in parallel operations:', error.message);
    }
}

parallelOperations();
```

### File Upload with Progress

```javascript
const { createClient } = require('./multimodal-llm-client');
const fs = require('fs');

async function uploadWithProgress() {
    const client = createClient();

    try {
        // For large files, you might want to show progress
        const filePath = 'large_video.mp4';
        const fileSize = fs.statSync(filePath).size;
        
        console.log(`Uploading file: ${filePath} (${fileSize} bytes)`);
        
        const result = await client.multimodalWorker.processVideo(
            filePath,
            'large_video.mp4',
            { 
                category: 'presentation',
                size: fileSize,
                uploaded_at: new Date().toISOString()
            }
        );
        
        console.log('Upload completed:', result);

    } catch (error) {
        console.error('Upload error:', error.message);
    }
}

uploadWithProgress();
```

## Configuration

### Environment Variables

You can configure the client using environment variables:

```bash
export LITELLM_API_KEY="sk-your-litellm-key"
export LITELLM_BASE_URL="http://localhost:4000"
export MULTIMODAL_WORKER_URL="http://localhost:8001"
export RETRIEVAL_PROXY_URL="http://localhost:8002"
export AI_AGENTS_URL="http://localhost:8003"
```

### Custom Configuration

```javascript
const client = createClient({
    litellmBaseUrl: 'https://api.your-domain.com',
    multimodalWorkerUrl: 'https://worker.your-domain.com',
    retrievalProxyUrl: 'https://search.your-domain.com',
    aiAgentsUrl: 'https://agents.your-domain.com',
    litellmApiKey: 'sk-your-production-key',
    timeout: 60000
});
```

## Testing

```bash
npm test
```

## License

MIT License - see LICENSE file for details.