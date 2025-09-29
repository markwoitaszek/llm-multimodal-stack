import * as vscode from 'vscode';
import { IDEBridgeClient } from './ideBridgeClient';

export class AgentIntegration {
    private client: IDEBridgeClient;

    constructor(client: IDEBridgeClient) {
        this.client = client;
    }

    async analyzeCode(code: string, language: string, filePath?: string): Promise<any> {
        try {
            const result = await this.client.executeMCPTool('code_analysis', {
                code,
                language,
                file_path: filePath
            });
            return result;
        } catch (error) {
            throw new Error(`Code analysis failed: ${error}`);
        }
    }

    async generateCode(description: string, language: string, context?: string): Promise<string> {
        try {
            const result = await this.client.executeMCPTool('code_generation', {
                description,
                language,
                context
            });
            return result.generated_code || '';
        } catch (error) {
            throw new Error(`Code generation failed: ${error}`);
        }
    }

    async refactorCode(code: string, language: string, refactoringType: string = 'general'): Promise<string> {
        try {
            const result = await this.client.executeMCPTool('code_refactoring', {
                code,
                language,
                refactoring_type: refactoringType
            });
            return result.refactored_code || code;
        } catch (error) {
            throw new Error(`Code refactoring failed: ${error}`);
        }
    }

    async generateDocumentation(code: string, language: string, docType: string = 'docstring'): Promise<string> {
        try {
            const result = await this.client.executeMCPTool('documentation_generation', {
                code,
                language,
                doc_type: docType
            });
            return result.documentation || '';
        } catch (error) {
            throw new Error(`Documentation generation failed: ${error}`);
        }
    }

    async generateTests(code: string, language: string, testFramework: string = 'default'): Promise<string> {
        try {
            const result = await this.client.executeMCPTool('test_generation', {
                code,
                language,
                test_framework: testFramework
            });
            return result.tests || '';
        } catch (error) {
            throw new Error(`Test generation failed: ${error}`);
        }
    }

    async detectBugs(code: string, language: string, severity: string = 'medium'): Promise<any[]> {
        try {
            const result = await this.client.executeMCPTool('bug_detection', {
                code,
                language,
                severity
            });
            return result.bugs || [];
        } catch (error) {
            throw new Error(`Bug detection failed: ${error}`);
        }
    }

    async analyzePerformance(code: string, language: string, analysisType: string = 'general'): Promise<any> {
        try {
            const result = await this.client.executeMCPTool('performance_analysis', {
                code,
                language,
                analysis_type: analysisType
            });
            return result.performance_analysis || {};
        } catch (error) {
            throw new Error(`Performance analysis failed: ${error}`);
        }
    }

    async analyzeSecurity(code: string, language: string, securityLevel: string = 'medium'): Promise<any[]> {
        try {
            const result = await this.client.executeMCPTool('security_analysis', {
                code,
                language,
                security_level: securityLevel
            });
            return result.security_issues || [];
        } catch (error) {
            throw new Error(`Security analysis failed: ${error}`);
        }
    }

    async executeAgentTask(agentId: string, task: string, context?: any): Promise<any> {
        try {
            const result = await this.client.executeAgentTask(agentId, task, context);
            return result;
        } catch (error) {
            throw new Error(`Agent task execution failed: ${error}`);
        }
    }

    async listAvailableAgents(): Promise<any[]> {
        try {
            const agents = await this.client.listAgents();
            return agents;
        } catch (error) {
            throw new Error(`Failed to list agents: ${error}`);
        }
    }

    async getAgentSuggestions(code: string, language: string, position: vscode.Position): Promise<any[]> {
        try {
            // Get suggestions from available agents
            const agents = await this.listAvailableAgents();
            const suggestions = [];

            for (const agent of agents) {
                try {
                    const task = `Analyze this ${language} code and provide suggestions for improvement at line ${position.line + 1}, character ${position.character + 1}`;
                    const result = await this.executeAgentTask(agent.agent_id, task, {
                        code,
                        language,
                        position: {
                            line: position.line,
                            character: position.character
                        }
                    });

                    if (result.success && result.result) {
                        suggestions.push({
                            agent: agent.name,
                            suggestion: result.result,
                            agent_id: agent.agent_id
                        });
                    }
                } catch (error) {
                    console.warn(`Failed to get suggestion from agent ${agent.name}:`, error);
                }
            }

            return suggestions;
        } catch (error) {
            throw new Error(`Failed to get agent suggestions: ${error}`);
        }
    }

    async getCodeCompletions(code: string, language: string, position: vscode.Position): Promise<any[]> {
        try {
            // Use code generation agent for intelligent completions
            const task = `Provide intelligent code completions for ${language} code at line ${position.line + 1}, character ${position.character + 1}. Consider the surrounding context and suggest relevant completions.`;
            
            const result = await this.executeAgentTask('code_assistant', task, {
                code,
                language,
                position: {
                    line: position.line,
                    character: position.character
                }
            });

            if (result.success && result.result) {
                // Parse the result to extract completions
                const completions = this.parseCompletions(result.result);
                return completions;
            }

            return [];
        } catch (error) {
            console.warn('Failed to get AI completions:', error);
            return [];
        }
    }

    private parseCompletions(result: string): any[] {
        const completions = [];
        const lines = result.split('\n');

        for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('//')) {
                completions.push({
                    label: trimmed,
                    kind: 1, // Text completion
                    detail: 'AI-generated completion',
                    insertText: trimmed
                });
            }
        }

        return completions.slice(0, 10); // Limit to 10 completions
    }
}