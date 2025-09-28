/**
 * Multimodal LLM Stack JavaScript SDK
 * 
 * A comprehensive JavaScript client for the Multimodal LLM Stack services.
 */

const axios = require('axios');

class MultimodalLLMClient {
    /**
     * Initialize the Multimodal LLM Stack client.
     * 
     * @param {Object} config - Configuration object
     * @param {string} config.litellmBaseUrl - Base URL for LiteLLM Router service
     * @param {string} config.multimodalWorkerUrl - Base URL for Multimodal Worker service
     * @param {string} config.retrievalProxyUrl - Base URL for Retrieval Proxy service
     * @param {string} config.aiAgentsUrl - Base URL for AI Agents service
     * @param {string} config.litellmApiKey - API key for LiteLLM Router
     * @param {number} config.timeout - Request timeout in milliseconds
     */
    constructor({
        litellmBaseUrl = 'http://localhost:4000',
        multimodalWorkerUrl = 'http://localhost:8001',
        retrievalProxyUrl = 'http://localhost:8002',
        aiAgentsUrl = 'http://localhost:8003',
        litellmApiKey = null,
        timeout = 30000
    } = {}) {
        this.litellmBaseUrl = litellmBaseUrl.replace(/\/$/, '');
        this.multimodalWorkerUrl = multimodalWorkerUrl.replace(/\/$/, '');
        this.retrievalProxyUrl = retrievalProxyUrl.replace(/\/$/, '');
        this.aiAgentsUrl = aiAgentsUrl.replace(/\/$/, '');
        this.timeout = timeout;

        // Initialize service clients
        this.litellm = new LiteLLMClient(this.litellmBaseUrl, litellmApiKey, timeout);
        this.multimodalWorker = new MultimodalWorkerClient(this.multimodalWorkerUrl, timeout);
        this.retrievalProxy = new RetrievalProxyClient(this.retrievalProxyUrl, timeout);
        this.aiAgents = new AIAgentsClient(this.aiAgentsUrl, timeout);
    }

    /**
     * Check the health status of all services.
     * 
     * @returns {Promise<Object>} Health status of each service
     */
    async healthCheck() {
        const healthStatus = {};
        
        const services = [
            ['litellm', this.litellmBaseUrl],
            ['multimodal_worker', this.multimodalWorkerUrl],
            ['retrieval_proxy', this.retrievalProxyUrl],
            ['ai_agents', this.aiAgentsUrl]
        ];

        for (const [serviceName, baseUrl] of services) {
            try {
                const response = await axios.get(`${baseUrl}/health`, { timeout: this.timeout });
                healthStatus[serviceName] = response.data;
            } catch (error) {
                healthStatus[serviceName] = { 
                    status: 'unhealthy', 
                    error: error.message 
                };
            }
        }

        return healthStatus;
    }
}

class LiteLLMClient {
    constructor(baseUrl, apiKey, timeout) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
        this.timeout = timeout;
        this.headers = apiKey ? { 'Authorization': `Bearer ${apiKey}` } : {};
    }

    /**
     * Create a chat completion.
     * 
     * @param {Array} messages - List of message objects
     * @param {string} model - Model to use for completion
     * @param {number} maxTokens - Maximum tokens to generate
     * @param {number} temperature - Sampling temperature
     * @param {Object} options - Additional parameters
     * @returns {Promise<Object>} Chat completion response
     */
    async chatCompletion(messages, model = 'gpt-3.5-turbo', maxTokens = null, temperature = null, options = {}) {
        const data = {
            model,
            messages,
            ...options
        };

        if (maxTokens !== null) data.max_tokens = maxTokens;
        if (temperature !== null) data.temperature = temperature;

        const response = await axios.post(
            `${this.baseUrl}/v1/chat/completions`,
            data,
            {
                headers: { ...this.headers, 'Content-Type': 'application/json' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * List available models.
     * 
     * @returns {Promise<Object>} List of available models
     */
    async listModels() {
        const response = await axios.get(
            `${this.baseUrl}/v1/models`,
            {
                headers: this.headers,
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Check service health.
     * 
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`, { timeout: this.timeout });
        return response.data;
    }
}

class MultimodalWorkerClient {
    constructor(baseUrl, timeout) {
        this.baseUrl = baseUrl;
        this.timeout = timeout;
    }

    /**
     * Process an image file.
     * 
     * @param {string|File} imagePath - Path to the image file or File object
     * @param {string} documentName - Optional name for the document
     * @param {Object} metadata - Optional metadata object
     * @returns {Promise<Object>} Processing result
     */
    async processImage(imagePath, documentName = null, metadata = null) {
        const formData = new FormData();
        
        // Handle both file paths and File objects
        if (typeof imagePath === 'string') {
            // In Node.js, you would need to use a file stream
            // This is a simplified version for browser usage
            throw new Error('File path processing requires Node.js environment. Use File object instead.');
        } else {
            formData.append('file', imagePath);
        }

        if (documentName) formData.append('document_name', documentName);
        if (metadata) formData.append('metadata', JSON.stringify(metadata));

        const response = await axios.post(
            `${this.baseUrl}/api/v1/process/image`,
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Process a video file.
     * 
     * @param {string|File} videoPath - Path to the video file or File object
     * @param {string} documentName - Optional name for the document
     * @param {Object} metadata - Optional metadata object
     * @returns {Promise<Object>} Processing result
     */
    async processVideo(videoPath, documentName = null, metadata = null) {
        const formData = new FormData();
        
        if (typeof videoPath === 'string') {
            throw new Error('File path processing requires Node.js environment. Use File object instead.');
        } else {
            formData.append('file', videoPath);
        }

        if (documentName) formData.append('document_name', documentName);
        if (metadata) formData.append('metadata', JSON.stringify(metadata));

        const response = await axios.post(
            `${this.baseUrl}/api/v1/process/video`,
            formData,
            {
                headers: { 'Content-Type': 'multipart/form-data' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Process text content.
     * 
     * @param {string} text - Text content to process
     * @param {string} documentName - Optional name for the document
     * @param {Object} metadata - Optional metadata object
     * @returns {Promise<Object>} Processing result
     */
    async processText(text, documentName = null, metadata = null) {
        const data = { text };

        if (documentName) data.document_name = documentName;
        if (metadata) data.metadata = metadata;

        const response = await axios.post(
            `${this.baseUrl}/api/v1/process/text`,
            data,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get status of loaded models.
     * 
     * @returns {Promise<Object>} Model status
     */
    async getModelsStatus() {
        const response = await axios.get(`${this.baseUrl}/api/v1/models/status`, { timeout: this.timeout });
        return response.data;
    }

    /**
     * Get storage system status.
     * 
     * @returns {Promise<Object>} Storage status
     */
    async getStorageStatus() {
        const response = await axios.get(`${this.baseUrl}/api/v1/storage/status`, { timeout: this.timeout });
        return response.data;
    }

    /**
     * Check service health.
     * 
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`, { timeout: this.timeout });
        return response.data;
    }
}

class RetrievalProxyClient {
    constructor(baseUrl, timeout) {
        this.baseUrl = baseUrl;
        this.timeout = timeout;
    }

    /**
     * Perform multimodal search.
     * 
     * @param {string} query - Search query
     * @param {Array} modalities - Content types to search (text, image, video)
     * @param {number} limit - Maximum number of results
     * @param {Object} filters - Additional filters
     * @param {number} scoreThreshold - Minimum similarity score
     * @returns {Promise<Object>} Search results
     */
    async search(query, modalities = null, limit = 10, filters = null, scoreThreshold = null) {
        const data = { query, limit };

        if (modalities) data.modalities = modalities;
        if (filters) data.filters = filters;
        if (scoreThreshold !== null) data.score_threshold = scoreThreshold;

        const response = await axios.post(
            `${this.baseUrl}/api/v1/search`,
            data,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get recent search sessions.
     * 
     * @param {number} limit - Number of sessions to retrieve
     * @returns {Promise<Object>} Search sessions
     */
    async getSearchSessions(limit = 20) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/search/sessions`,
            {
                params: { limit },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get context bundle for a search session.
     * 
     * @param {string} sessionId - Search session ID
     * @param {string} format - Output format (markdown, json, plain)
     * @returns {Promise<Object>} Context bundle
     */
    async getContextBundle(sessionId, format = 'markdown') {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/context/${sessionId}`,
            {
                params: { format },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get image artifact by document ID.
     * 
     * @param {string} documentId - Document ID
     * @returns {Promise<Object>} Image artifact
     */
    async getImageArtifact(documentId) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/artifacts/image/${documentId}`,
            { timeout: this.timeout }
        );

        return response.data;
    }

    /**
     * Get video artifact by document ID.
     * 
     * @param {string} documentId - Document ID
     * @returns {Promise<Object>} Video artifact
     */
    async getVideoArtifact(documentId) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/artifacts/video/${documentId}`,
            { timeout: this.timeout }
        );

        return response.data;
    }

    /**
     * Get keyframe artifact by keyframe ID.
     * 
     * @param {string} keyframeId - Keyframe ID
     * @returns {Promise<Object>} Keyframe artifact
     */
    async getKeyframeArtifact(keyframeId) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/artifacts/keyframe/${keyframeId}`,
            { timeout: this.timeout }
        );

        return response.data;
    }

    /**
     * Get system statistics.
     * 
     * @returns {Promise<Object>} System statistics
     */
    async getSystemStats() {
        const response = await axios.get(`${this.baseUrl}/api/v1/stats`, { timeout: this.timeout });
        return response.data;
    }

    /**
     * Check service health.
     * 
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`, { timeout: this.timeout });
        return response.data;
    }
}

class AIAgentsClient {
    constructor(baseUrl, timeout) {
        this.baseUrl = baseUrl;
        this.timeout = timeout;
    }

    /**
     * Create a new AI agent.
     * 
     * @param {string} name - Agent name
     * @param {string} goal - Agent goal or purpose
     * @param {Array} tools - List of tool names to enable
     * @param {number} memoryWindow - Conversation memory window size
     * @param {string} userId - User ID
     * @returns {Promise<Object>} Agent creation result
     */
    async createAgent(name, goal, tools = null, memoryWindow = 10, userId = 'default') {
        const data = { name, goal, memory_window: memoryWindow, user_id: userId };

        if (tools) data.tools = tools;

        const response = await axios.post(
            `${this.baseUrl}/api/v1/agents`,
            data,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * List all agents for a user.
     * 
     * @param {string} userId - User ID
     * @returns {Promise<Array>} List of agents
     */
    async listAgents(userId = 'default') {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/agents`,
            {
                params: { user_id: userId },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get agent information.
     * 
     * @param {string} agentId - Agent ID
     * @returns {Promise<Object>} Agent information
     */
    async getAgent(agentId) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/agents/${agentId}`,
            { timeout: this.timeout }
        );

        return response.data;
    }

    /**
     * Execute a task with an agent.
     * 
     * @param {string} agentId - Agent ID
     * @param {string} task - Task for the agent to execute
     * @param {string} userId - User ID
     * @returns {Promise<Object>} Task execution result
     */
    async executeAgentTask(agentId, task, userId = 'default') {
        const data = { task, user_id: userId };

        const response = await axios.post(
            `${this.baseUrl}/api/v1/agents/${agentId}/execute`,
            data,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Delete an agent.
     * 
     * @param {string} agentId - Agent ID
     * @param {string} userId - User ID
     * @returns {Promise<Object>} Deletion result
     */
    async deleteAgent(agentId, userId = 'default') {
        const response = await axios.delete(
            `${this.baseUrl}/api/v1/agents/${agentId}`,
            {
                params: { user_id: userId },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * List available tools for agents.
     * 
     * @returns {Promise<Object>} List of tools
     */
    async listTools() {
        const response = await axios.get(`${this.baseUrl}/api/v1/tools`, { timeout: this.timeout });
        return response.data;
    }

    /**
     * List available agent templates.
     * 
     * @param {string} category - Filter by category
     * @param {string} search - Search templates by name or description
     * @returns {Promise<Object>} List of templates
     */
    async listTemplates(category = null, search = null) {
        const params = {};
        if (category) params.category = category;
        if (search) params.search = search;

        const response = await axios.get(
            `${this.baseUrl}/api/v1/templates`,
            {
                params,
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get details for a specific template.
     * 
     * @param {string} templateName - Template name
     * @returns {Promise<Object>} Template details
     */
    async getTemplateDetails(templateName) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/templates/${templateName}`,
            { timeout: this.timeout }
        );

        return response.data;
    }

    /**
     * Create an agent from a template.
     * 
     * @param {string} templateName - Name of the template to use
     * @param {string} agentName - Custom name for the agent
     * @param {string} userId - User ID
     * @returns {Promise<Object>} Agent creation result
     */
    async createAgentFromTemplate(templateName, agentName = null, userId = 'default') {
        const data = { template_name: templateName, user_id: userId };

        if (agentName) data.agent_name = agentName;

        const response = await axios.post(
            `${this.baseUrl}/api/v1/agents/from-template`,
            data,
            {
                headers: { 'Content-Type': 'application/json' },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get conversation history for an agent.
     * 
     * @param {string} agentId - Agent ID
     * @param {number} limit - Number of history entries to retrieve
     * @returns {Promise<Object>} Agent history
     */
    async getAgentHistory(agentId, limit = 20) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/agents/${agentId}/history`,
            {
                params: { limit },
                timeout: this.timeout
            }
        );

        return response.data;
    }

    /**
     * Get statistics for an agent.
     * 
     * @param {string} agentId - Agent ID
     * @returns {Promise<Object>} Agent statistics
     */
    async getAgentStats(agentId) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/agents/${agentId}/stats`,
            { timeout: this.timeout }
        );

        return response.data;
    }

    /**
     * Check service health.
     * 
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`, { timeout: this.timeout });
        return response.data;
    }
}

// Convenience function for creating a client
function createClient(config = {}) {
    return new MultimodalLLMClient(config);
}

// Export for both CommonJS and ES modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        MultimodalLLMClient,
        LiteLLMClient,
        MultimodalWorkerClient,
        RetrievalProxyClient,
        AIAgentsClient,
        createClient
    };
} else if (typeof window !== 'undefined') {
    window.MultimodalLLMClient = MultimodalLLMClient;
    window.LiteLLMClient = LiteLLMClient;
    window.MultimodalWorkerClient = MultimodalWorkerClient;
    window.RetrievalProxyClient = RetrievalProxyClient;
    window.AIAgentsClient = AIAgentsClient;
    window.createClient = createClient;
}

// Example usage
if (typeof require !== 'undefined' && require.main === module) {
    async function example() {
        // Initialize client
        const client = createClient({
            litellmApiKey: 'sk-your-litellm-key'
        });

        try {
            // Check health
            const health = await client.healthCheck();
            console.log('Health Status:', health);

            // Example: Search for content
            const searchResults = await client.retrievalProxy.search(
                'artificial intelligence',
                ['text', 'image'],
                5
            );
            console.log('Search results:', searchResults);

            // Example: Create an agent
            const agent = await client.aiAgents.createAgent(
                'Test Agent',
                'Help with testing and development',
                ['web_search']
            );
            console.log('Created agent:', agent);

            // Example: Chat completion
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

    example();
}