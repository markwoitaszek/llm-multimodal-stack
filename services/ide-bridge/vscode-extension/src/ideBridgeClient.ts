import * as vscode from 'vscode';
import axios, { AxiosInstance } from 'axios';

export class IDEBridgeClient {
    private client: AxiosInstance;
    private connected: boolean = false;
    private serverUrl: string = '';

    constructor() {
        this.client = axios.create({
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async connect(serverUrl: string): Promise<void> {
        this.serverUrl = serverUrl;
        
        try {
            // Test connection with health check
            const response = await this.client.get(`${serverUrl}/health`);
            if (response.status === 200) {
                this.connected = true;
                console.log('Connected to IDE Bridge server');
            } else {
                throw new Error(`Health check failed: ${response.status}`);
            }
        } catch (error) {
            this.connected = false;
            throw new Error(`Failed to connect to IDE Bridge server: ${error}`);
        }
    }

    async disconnect(): Promise<void> {
        this.connected = false;
        this.serverUrl = '';
        console.log('Disconnected from IDE Bridge server');
    }

    isConnected(): boolean {
        return this.connected;
    }

    async analyzeCode(code: string, language: string, filePath?: string): Promise<any> {
        if (!this.connected) {
            throw new Error('Not connected to IDE Bridge server');
        }

        try {
            const response = await this.client.post(`${this.serverUrl}/analyze`, {
                code,
                language,
                file_path: filePath
            });
            return response.data;
        } catch (error) {
            throw new Error(`Code analysis failed: ${error}`);
        }
    }

    async executeAgentTask(agentId: string, task: string, context?: any): Promise<any> {
        if (!this.connected) {
            throw new Error('Not connected to IDE Bridge server');
        }

        try {
            const response = await this.client.post(`${this.serverUrl}/agents/execute`, {
                agent_id: agentId,
                task,
                context
            });
            return response.data;
        } catch (error) {
            throw new Error(`Agent task execution failed: ${error}`);
        }
    }

    async listAgents(): Promise<any[]> {
        if (!this.connected) {
            throw new Error('Not connected to IDE Bridge server');
        }

        try {
            const response = await this.client.get(`${this.serverUrl}/agents`);
            return response.data.agents || [];
        } catch (error) {
            throw new Error(`Failed to list agents: ${error}`);
        }
    }

    async executeMCPTool(toolName: string, parameters: any): Promise<any> {
        if (!this.connected) {
            throw new Error('Not connected to IDE Bridge server');
        }

        try {
            const response = await this.client.post(`${this.serverUrl}/mcp/tools/execute`, {
                tool: toolName,
                parameters
            });
            return response.data;
        } catch (error) {
            throw new Error(`MCP tool execution failed: ${error}`);
        }
    }

    async listMCPTools(): Promise<any[]> {
        if (!this.connected) {
            throw new Error('Not connected to IDE Bridge server');
        }

        try {
            const response = await this.client.get(`${this.serverUrl}/mcp/tools`);
            return response.data.tools || [];
        } catch (error) {
            throw new Error(`Failed to list MCP tools: ${error}`);
        }
    }
}