import * as vscode from 'vscode';
import { IDEBridgeClient } from './ideBridgeClient';
import { WebSocketManager } from './webSocketManager';
import { CodeAnalyzer } from './codeAnalyzer';
import { AgentIntegration } from './agentIntegration';

let ideBridgeClient: IDEBridgeClient;
let webSocketManager: WebSocketManager;
let codeAnalyzer: CodeAnalyzer;
let agentIntegration: AgentIntegration;

export function activate(context: vscode.ExtensionContext) {
    console.log('IDE Bridge extension is now active!');

    // Initialize components
    ideBridgeClient = new IDEBridgeClient();
    webSocketManager = new WebSocketManager();
    codeAnalyzer = new CodeAnalyzer(ideBridgeClient);
    agentIntegration = new AgentIntegration(ideBridgeClient);

    // Register commands
    const commands = [
        vscode.commands.registerCommand('ide-bridge.connect', connectToIDEBridge),
        vscode.commands.registerCommand('ide-bridge.disconnect', disconnectFromIDEBridge),
        vscode.commands.registerCommand('ide-bridge.showStatus', showConnectionStatus),
        vscode.commands.registerCommand('ide-bridge.analyzeCode', analyzeCode),
        vscode.commands.registerCommand('ide-bridge.generateCode', generateCode),
        vscode.commands.registerCommand('ide-bridge.refactorCode', refactorCode),
        vscode.commands.registerCommand('ide-bridge.generateDocumentation', generateDocumentation),
        vscode.commands.registerCommand('ide-bridge.generateTests', generateTests),
        vscode.commands.registerCommand('ide-bridge.detectBugs', detectBugs),
        vscode.commands.registerCommand('ide-bridge.analyzePerformance', analyzePerformance),
        vscode.commands.registerCommand('ide-bridge.analyzeSecurity', analyzeSecurity)
    ];

    // Add commands to context
    commands.forEach(command => context.subscriptions.push(command));

    // Register completion provider
    const completionProvider = vscode.languages.registerCompletionItemProvider(
        { scheme: 'file' },
        {
            async provideCompletionItems(document, position, token, context) {
                if (!ideBridgeClient.isConnected()) {
                    return [];
                }

                try {
                    const completions = await codeAnalyzer.getCompletions(document, position);
                    return completions;
                } catch (error) {
                    console.error('Error getting completions:', error);
                    return [];
                }
            }
        },
        '.', ':', ' ', '('
    );

    context.subscriptions.push(completionProvider);

    // Register hover provider
    const hoverProvider = vscode.languages.registerHoverProvider(
        { scheme: 'file' },
        {
            async provideHover(document, position, token) {
                if (!ideBridgeClient.isConnected()) {
                    return null;
                }

                try {
                    const hoverInfo = await codeAnalyzer.getHoverInfo(document, position);
                    if (hoverInfo) {
                        return new vscode.Hover(hoverInfo);
                    }
                } catch (error) {
                    console.error('Error getting hover info:', error);
                }

                return null;
            }
        }
    );

    context.subscriptions.push(hoverProvider);

    // Register code action provider
    const codeActionProvider = vscode.languages.registerCodeActionsProvider(
        { scheme: 'file' },
        {
            async provideCodeActions(document, range, context, token) {
                if (!ideBridgeClient.isConnected()) {
                    return [];
                }

                try {
                    const actions = await codeAnalyzer.getCodeActions(document, range, context);
                    return actions;
                } catch (error) {
                    console.error('Error getting code actions:', error);
                    return [];
                }
            }
        }
    );

    context.subscriptions.push(codeActionProvider);

    // Register definition provider
    const definitionProvider = vscode.languages.registerDefinitionProvider(
        { scheme: 'file' },
        {
            async provideDefinition(document, position, token) {
                if (!ideBridgeClient.isConnected()) {
                    return null;
                }

                try {
                    const definition = await codeAnalyzer.getDefinition(document, position);
                    return definition;
                } catch (error) {
                    console.error('Error getting definition:', error);
                    return null;
                }
            }
        }
    );

    context.subscriptions.push(definitionProvider);

    // Register references provider
    const referencesProvider = vscode.languages.registerReferenceProvider(
        { scheme: 'file' },
        {
            async provideReferences(document, position, context, token) {
                if (!ideBridgeClient.isConnected()) {
                    return [];
                }

                try {
                    const references = await codeAnalyzer.getReferences(document, position, context);
                    return references;
                } catch (error) {
                    console.error('Error getting references:', error);
                    return [];
                }
            }
        }
    );

    context.subscriptions.push(referencesProvider);

    // Register document symbol provider
    const documentSymbolProvider = vscode.languages.registerDocumentSymbolProvider(
        { scheme: 'file' },
        {
            async provideDocumentSymbols(document, token) {
                if (!ideBridgeClient.isConnected()) {
                    return [];
                }

                try {
                    const symbols = await codeAnalyzer.getDocumentSymbols(document);
                    return symbols;
                } catch (error) {
                    console.error('Error getting document symbols:', error);
                    return [];
                }
            }
        }
    );

    context.subscriptions.push(documentSymbolProvider);

    // Auto-connect if enabled
    const config = vscode.workspace.getConfiguration('ide-bridge');
    if (config.get('autoConnect', true)) {
        connectToIDEBridge();
    }

    // Setup status bar
    setupStatusBar();

    // Setup WebSocket connection
    setupWebSocket();
}

export function deactivate() {
    if (ideBridgeClient) {
        ideBridgeClient.disconnect();
    }
    if (webSocketManager) {
        webSocketManager.disconnect();
    }
}

async function connectToIDEBridge() {
    try {
        const config = vscode.workspace.getConfiguration('ide-bridge');
        const serverUrl = config.get('serverUrl', 'http://localhost:8007');
        
        await ideBridgeClient.connect(serverUrl);
        vscode.window.showInformationMessage('Connected to IDE Bridge server');
        updateStatusBar(true);
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to connect to IDE Bridge: ${error}`);
        updateStatusBar(false);
    }
}

async function disconnectFromIDEBridge() {
    try {
        await ideBridgeClient.disconnect();
        vscode.window.showInformationMessage('Disconnected from IDE Bridge server');
        updateStatusBar(false);
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to disconnect: ${error}`);
    }
}

function showConnectionStatus() {
    const isConnected = ideBridgeClient.isConnected();
    const status = isConnected ? 'Connected' : 'Disconnected';
    vscode.window.showInformationMessage(`IDE Bridge Status: ${status}`);
}

async function analyzeCode() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);
    const language = editor.document.languageId;
    const filePath = editor.document.uri.fsPath;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing code with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.analyzeCode(code, language, filePath);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Show results in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(result, null, 2),
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Code analysis failed: ${error}`);
    }
}

async function generateCode() {
    const input = await vscode.window.showInputBox({
        prompt: 'Describe the code you want to generate',
        placeHolder: 'e.g., Create a function that sorts an array of numbers'
    });

    if (!input) {
        return;
    }

    const editor = vscode.window.activeTextEditor;
    const language = editor?.document.languageId || 'python';

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating code with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.generateCode(input, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Insert generated code at cursor position
            if (editor) {
                const position = editor.selection.active;
                await editor.edit(editBuilder => {
                    editBuilder.insert(position, result);
                });
            } else {
                // Show in new document
                const doc = await vscode.workspace.openTextDocument({
                    content: result,
                    language: language
                });
                await vscode.window.showTextDocument(doc);
            }
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Code generation failed: ${error}`);
    }
}

async function refactorCode() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    if (selection.isEmpty) {
        vscode.window.showWarningMessage('Please select code to refactor');
        return;
    }

    const code = editor.document.getText(selection);
    const language = editor.document.languageId;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Refactoring code with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.refactorCode(code, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Replace selected code with refactored version
            await editor.edit(editBuilder => {
                editBuilder.replace(selection, result);
            });
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Code refactoring failed: ${error}`);
    }
}

async function generateDocumentation() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);
    const language = editor.document.languageId;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating documentation with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.generateDocumentation(code, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Show documentation in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: result,
                language: 'markdown'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Documentation generation failed: ${error}`);
    }
}

async function generateTests() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);
    const language = editor.document.languageId;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Generating tests with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.generateTests(code, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Show tests in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: result,
                language: language
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Test generation failed: ${error}`);
    }
}

async function detectBugs() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);
    const language = editor.document.languageId;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Detecting bugs with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.detectBugs(code, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Show bugs in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(result, null, 2),
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Bug detection failed: ${error}`);
    }
}

async function analyzePerformance() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);
    const language = editor.document.languageId;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing performance with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.analyzePerformance(code, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Show performance analysis in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(result, null, 2),
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Performance analysis failed: ${error}`);
    }
}

async function analyzeSecurity() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage('No active editor');
        return;
    }

    const selection = editor.selection;
    const code = selection.isEmpty ? editor.document.getText() : editor.document.getText(selection);
    const language = editor.document.languageId;

    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Analyzing security with AI...",
            cancellable: true
        }, async (progress, token) => {
            const result = await agentIntegration.analyzeSecurity(code, language);
            
            if (token.isCancellationRequested) {
                return;
            }

            // Show security analysis in a new document
            const doc = await vscode.workspace.openTextDocument({
                content: JSON.stringify(result, null, 2),
                language: 'json'
            });
            await vscode.window.showTextDocument(doc);
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Security analysis failed: ${error}`);
    }
}

let statusBarItem: vscode.StatusBarItem;

function setupStatusBar() {
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'ide-bridge.showStatus';
    statusBarItem.show();
    updateStatusBar(false);
}

function updateStatusBar(connected: boolean) {
    if (statusBarItem) {
        statusBarItem.text = connected ? '$(check) IDE Bridge' : '$(x) IDE Bridge';
        statusBarItem.tooltip = connected ? 'Connected to IDE Bridge' : 'Disconnected from IDE Bridge';
    }
}

function setupWebSocket() {
    const config = vscode.workspace.getConfiguration('ide-bridge');
    const wsUrl = config.get('wsUrl', 'ws://localhost:8007/ws');
    
    webSocketManager.connect(wsUrl);
}