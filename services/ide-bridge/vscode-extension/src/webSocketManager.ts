import * as vscode from 'vscode';
import WebSocket from 'ws';

export class WebSocketManager {
    private ws: WebSocket | null = null;
    private wsUrl: string = '';
    private connected: boolean = false;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private reconnectInterval: number = 5000;

    connect(wsUrl: string): void {
        this.wsUrl = wsUrl;
        this.connectWebSocket();
    }

    private connectWebSocket(): void {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.on('open', () => {
                console.log('WebSocket connected to IDE Bridge');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.sendMessage({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
            });

            this.ws.on('message', (data: WebSocket.Data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            });

            this.ws.on('close', (code: number, reason: string) => {
                console.log(`WebSocket closed: ${code} - ${reason}`);
                this.connected = false;
                this.attemptReconnect();
            });

            this.ws.on('error', (error: Error) => {
                console.error('WebSocket error:', error);
                this.connected = false;
            });

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.attemptReconnect();
        }
    }

    private attemptReconnect(): void {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectInterval);
        } else {
            console.error('Max reconnection attempts reached');
            vscode.window.showErrorMessage('Failed to maintain connection to IDE Bridge WebSocket');
        }
    }

    private handleMessage(message: any): void {
        switch (message.type) {
            case 'pong':
                // Handle pong response
                break;
            
            case 'agent_execution_started':
                vscode.window.showInformationMessage(`Agent execution started: ${message.task}`);
                break;
            
            case 'agent_execution_completed':
                vscode.window.showInformationMessage(`Agent execution completed: ${message.agent_id}`);
                break;
            
            case 'code_analysis_requested':
                // Handle code analysis request
                break;
            
            case 'collaboration_event':
                // Handle collaboration events
                break;
            
            case 'error':
                vscode.window.showErrorMessage(`IDE Bridge error: ${message.message}`);
                break;
            
            default:
                console.log('Unknown WebSocket message type:', message.type);
        }
    }

    sendMessage(message: any): void {
        if (this.ws && this.connected) {
            try {
                this.ws.send(JSON.stringify(message));
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
            }
        }
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
        this.reconnectAttempts = 0;
    }

    isConnected(): boolean {
        return this.connected;
    }

    // Agent execution methods
    executeAgent(agentId: string, task: string, context?: any): void {
        this.sendMessage({
            type: 'agent_execution',
            agent_id: agentId,
            task,
            context,
            timestamp: new Date().toISOString()
        });
    }

    // Code analysis methods
    requestCodeAnalysis(code: string, language: string): void {
        this.sendMessage({
            type: 'code_analysis',
            code,
            language,
            timestamp: new Date().toISOString()
        });
    }

    // Collaboration methods
    sendCollaborationEvent(action: string, workspace: string, data?: any): void {
        this.sendMessage({
            type: 'collaboration',
            action,
            workspace,
            data,
            timestamp: new Date().toISOString()
        });
    }

    // Subscription methods
    subscribe(channel: string): void {
        this.sendMessage({
            type: 'subscribe',
            channel,
            timestamp: new Date().toISOString()
        });
    }

    unsubscribe(channel: string): void {
        this.sendMessage({
            type: 'unsubscribe',
            channel,
            timestamp: new Date().toISOString()
        });
    }
}