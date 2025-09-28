#!/usr/bin/env node

/**
 * Example usage of the Multimodal LLM Stack JavaScript SDK
 */

const { createClient } = require('./multimodal-llm-client');

async function main() {
    console.log('🚀 Multimodal LLM Stack JavaScript SDK Example\n');

    // Initialize client
    const client = createClient({
        litellmApiKey: process.env.LITELLM_API_KEY || 'sk-your-litellm-key'
    });

    try {
        // 1. Check service health
        console.log('1. Checking service health...');
        const health = await client.healthCheck();
        console.log('Health Status:', JSON.stringify(health, null, 2));
        console.log('');

        // 2. Process text content
        console.log('2. Processing text content...');
        const textResult = await client.multimodalWorker.processText(
            'Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data without being explicitly programmed. It has applications in image recognition, natural language processing, and predictive analytics.',
            'ml_introduction.txt',
            { 
                category: 'tutorial', 
                tags: ['AI', 'machine learning', 'introduction'],
                author: 'AI Expert',
                created_at: new Date().toISOString()
            }
        );
        console.log('Text processing result:', JSON.stringify(textResult, null, 2));
        console.log('');

        // 3. Search for content
        console.log('3. Searching for content...');
        const searchResults = await client.retrievalProxy.search(
            'machine learning algorithms',
            ['text', 'image'],
            5,
            { 
                file_types: ['txt', 'pdf', 'jpg'],
                min_score: 0.7
            },
            0.8
        );
        console.log('Search results:', JSON.stringify(searchResults, null, 2));
        console.log('');

        // 4. Create an AI agent
        console.log('4. Creating AI agent...');
        const agent = await client.aiAgents.createAgent(
            'ML Content Analyzer',
            'Analyze machine learning content and provide insights about algorithms, applications, and best practices',
            ['document_analysis', 'text_analysis', 'web_search'],
            15,
            'example_user'
        );
        console.log('Created agent:', JSON.stringify(agent, null, 2));
        console.log('');

        // 5. Execute agent task
        console.log('5. Executing agent task...');
        const analysisResult = await client.aiAgents.executeAgentTask(
            agent.agent_id,
            'Analyze the machine learning content and identify the key concepts, applications, and provide recommendations for further learning',
            'example_user'
        );
        console.log('Analysis result:', JSON.stringify(analysisResult, null, 2));
        console.log('');

        // 6. Chat with LiteLLM
        console.log('6. Chatting with LiteLLM...');
        const chatResponse = await client.litellm.chatCompletion(
            [
                { role: 'system', content: 'You are an AI expert specializing in machine learning and artificial intelligence.' },
                { role: 'user', content: 'Based on the analysis of machine learning content, what are the most important concepts that beginners should understand?' }
            ],
            'gpt-3.5-turbo',
            200,
            0.7
        );
        console.log('Chat response:', JSON.stringify(chatResponse, null, 2));
        console.log('');

        // 7. Get agent statistics
        console.log('7. Getting agent statistics...');
        const agentStats = await client.aiAgents.getAgentStats(agent.agent_id);
        console.log('Agent stats:', JSON.stringify(agentStats, null, 2));
        console.log('');

        // 8. List available tools
        console.log('8. Listing available tools...');
        const tools = await client.aiAgents.listTools();
        console.log('Available tools:', JSON.stringify(tools, null, 2));
        console.log('');

        // 9. List agent templates
        console.log('9. Listing agent templates...');
        const templates = await client.aiAgents.listTemplates('research');
        console.log('Research templates:', JSON.stringify(templates, null, 2));
        console.log('');

        // 10. Get system statistics
        console.log('10. Getting system statistics...');
        const systemStats = await client.retrievalProxy.getSystemStats();
        console.log('System stats:', JSON.stringify(systemStats, null, 2));
        console.log('');

        console.log('✅ Example completed successfully!');

    } catch (error) {
        console.error('❌ Error in example:', error.message);
        if (error.response) {
            console.error('Response status:', error.response.status);
            console.error('Response data:', error.response.data);
        }
    }
}

// Run the example
if (require.main === module) {
    main().catch(console.error);
}

module.exports = { main };