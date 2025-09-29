import * as vscode from 'vscode';
import { IDEBridgeClient } from './ideBridgeClient';

export class CodeAnalyzer {
    private client: IDEBridgeClient;

    constructor(client: IDEBridgeClient) {
        this.client = client;
    }

    async getCompletions(document: vscode.TextDocument, position: vscode.Position): Promise<vscode.CompletionItem[]> {
        try {
            const code = document.getText();
            const line = position.line;
            const character = position.character;
            const language = document.languageId;

            // Get completions from IDE Bridge server
            const response = await this.client.analyzeCode(code, language, document.uri.fsPath);
            
            if (response.analysis && response.analysis.completions) {
                return response.analysis.completions.map((comp: any) => {
                    const item = new vscode.CompletionItem(comp.label, this.getCompletionKind(comp.kind));
                    item.detail = comp.detail;
                    item.documentation = comp.documentation;
                    item.insertText = comp.insertText || comp.label;
                    return item;
                });
            }

            return [];
        } catch (error) {
            console.error('Error getting completions:', error);
            return [];
        }
    }

    async getHoverInfo(document: vscode.TextDocument, position: vscode.Position): Promise<string | null> {
        try {
            const code = document.getText();
            const line = position.line;
            const character = position.character;
            const language = document.languageId;

            // Get hover info from IDE Bridge server
            const response = await this.client.analyzeCode(code, language, document.uri.fsPath);
            
            if (response.analysis && response.analysis.hover_info) {
                return response.analysis.hover_info;
            }

            return null;
        } catch (error) {
            console.error('Error getting hover info:', error);
            return null;
        }
    }

    async getCodeActions(document: vscode.TextDocument, range: vscode.Range, context: vscode.CodeActionContext): Promise<vscode.CodeAction[]> {
        try {
            const code = document.getText();
            const language = document.languageId;

            // Get code actions from IDE Bridge server
            const response = await this.client.analyzeCode(code, language, document.uri.fsPath);
            
            if (response.analysis && response.analysis.code_actions) {
                return response.analysis.code_actions.map((action: any) => {
                    const codeAction = new vscode.CodeAction(action.title, this.getCodeActionKind(action.kind));
                    codeAction.command = {
                        title: action.title,
                        command: action.command,
                        arguments: action.arguments
                    };
                    return codeAction;
                });
            }

            return [];
        } catch (error) {
            console.error('Error getting code actions:', error);
            return [];
        }
    }

    async getDefinition(document: vscode.TextDocument, position: vscode.Position): Promise<vscode.Definition | null> {
        try {
            const code = document.getText();
            const line = position.line;
            const character = position.character;
            const language = document.languageId;

            // Get definition from IDE Bridge server
            const response = await this.client.analyzeCode(code, language, document.uri.fsPath);
            
            if (response.analysis && response.analysis.definition) {
                const def = response.analysis.definition;
                return new vscode.Location(
                    vscode.Uri.file(def.uri),
                    new vscode.Range(
                        new vscode.Position(def.range.start.line, def.range.start.character),
                        new vscode.Position(def.range.end.line, def.range.end.character)
                    )
                );
            }

            return null;
        } catch (error) {
            console.error('Error getting definition:', error);
            return null;
        }
    }

    async getReferences(document: vscode.TextDocument, position: vscode.Position, context: vscode.ReferenceContext): Promise<vscode.Location[]> {
        try {
            const code = document.getText();
            const line = position.line;
            const character = position.character;
            const language = document.languageId;

            // Get references from IDE Bridge server
            const response = await this.client.analyzeCode(code, language, document.uri.fsPath);
            
            if (response.analysis && response.analysis.references) {
                return response.analysis.references.map((ref: any) => {
                    return new vscode.Location(
                        vscode.Uri.file(ref.uri),
                        new vscode.Range(
                            new vscode.Position(ref.range.start.line, ref.range.start.character),
                            new vscode.Position(ref.range.end.line, ref.range.end.character)
                        )
                    );
                });
            }

            return [];
        } catch (error) {
            console.error('Error getting references:', error);
            return [];
        }
    }

    async getDocumentSymbols(document: vscode.TextDocument): Promise<vscode.DocumentSymbol[]> {
        try {
            const code = document.getText();
            const language = document.languageId;

            // Get document symbols from IDE Bridge server
            const response = await this.client.analyzeCode(code, language, document.uri.fsPath);
            
            if (response.analysis && response.analysis.symbols) {
                return response.analysis.symbols.map((symbol: any) => {
                    return new vscode.DocumentSymbol(
                        symbol.name,
                        symbol.detail || '',
                        this.getSymbolKind(symbol.kind),
                        new vscode.Range(
                            new vscode.Position(symbol.range.start.line, symbol.range.start.character),
                            new vscode.Position(symbol.range.end.line, symbol.range.end.character)
                        ),
                        new vscode.Range(
                            new vscode.Position(symbol.range.start.line, symbol.range.start.character),
                            new vscode.Position(symbol.range.end.line, symbol.range.end.character)
                        )
                    );
                });
            }

            return [];
        } catch (error) {
            console.error('Error getting document symbols:', error);
            return [];
        }
    }

    private getCompletionKind(kind: number): vscode.CompletionItemKind {
        switch (kind) {
            case 1: return vscode.CompletionItemKind.Text;
            case 2: return vscode.CompletionItemKind.Method;
            case 3: return vscode.CompletionItemKind.Function;
            case 4: return vscode.CompletionItemKind.Constructor;
            case 5: return vscode.CompletionItemKind.Field;
            case 6: return vscode.CompletionItemKind.Variable;
            case 7: return vscode.CompletionItemKind.Class;
            case 8: return vscode.CompletionItemKind.Interface;
            case 9: return vscode.CompletionItemKind.Module;
            case 10: return vscode.CompletionItemKind.Property;
            case 11: return vscode.CompletionItemKind.Unit;
            case 12: return vscode.CompletionItemKind.Value;
            case 13: return vscode.CompletionItemKind.Enum;
            case 14: return vscode.CompletionItemKind.Keyword;
            case 15: return vscode.CompletionItemKind.Snippet;
            case 16: return vscode.CompletionItemKind.Color;
            case 17: return vscode.CompletionItemKind.File;
            case 18: return vscode.CompletionItemKind.Reference;
            case 19: return vscode.CompletionItemKind.Folder;
            case 20: return vscode.CompletionItemKind.EnumMember;
            case 21: return vscode.CompletionItemKind.Constant;
            case 22: return vscode.CompletionItemKind.Struct;
            case 23: return vscode.CompletionItemKind.Event;
            case 24: return vscode.CompletionItemKind.Operator;
            case 25: return vscode.CompletionItemKind.TypeParameter;
            default: return vscode.CompletionItemKind.Text;
        }
    }

    private getCodeActionKind(kind: string): vscode.CodeActionKind {
        switch (kind) {
            case 'quickfix': return vscode.CodeActionKind.QuickFix;
            case 'refactor': return vscode.CodeActionKind.Refactor;
            case 'refactor.extract': return vscode.CodeActionKind.RefactorExtract;
            case 'refactor.inline': return vscode.CodeActionKind.RefactorInline;
            case 'refactor.rewrite': return vscode.CodeActionKind.RefactorRewrite;
            case 'source': return vscode.CodeActionKind.Source;
            case 'source.organizeImports': return vscode.CodeActionKind.SourceOrganizeImports;
            default: return vscode.CodeActionKind.Empty;
        }
    }

    private getSymbolKind(kind: number): vscode.SymbolKind {
        switch (kind) {
            case 1: return vscode.SymbolKind.File;
            case 2: return vscode.SymbolKind.Module;
            case 3: return vscode.SymbolKind.Namespace;
            case 4: return vscode.SymbolKind.Package;
            case 5: return vscode.SymbolKind.Class;
            case 6: return vscode.SymbolKind.Method;
            case 7: return vscode.SymbolKind.Property;
            case 8: return vscode.SymbolKind.Field;
            case 9: return vscode.SymbolKind.Constructor;
            case 10: return vscode.SymbolKind.Enum;
            case 11: return vscode.SymbolKind.Interface;
            case 12: return vscode.SymbolKind.Function;
            case 13: return vscode.SymbolKind.Variable;
            case 14: return vscode.SymbolKind.Constant;
            case 15: return vscode.SymbolKind.String;
            case 16: return vscode.SymbolKind.Number;
            case 17: return vscode.SymbolKind.Boolean;
            case 18: return vscode.SymbolKind.Array;
            case 19: return vscode.SymbolKind.Object;
            case 20: return vscode.SymbolKind.Key;
            case 21: return vscode.SymbolKind.Null;
            case 22: return vscode.SymbolKind.EnumMember;
            case 23: return vscode.SymbolKind.Struct;
            case 24: return vscode.SymbolKind.Event;
            case 25: return vscode.SymbolKind.Operator;
            case 26: return vscode.SymbolKind.TypeParameter;
            default: return vscode.SymbolKind.Variable;
        }
    }
}