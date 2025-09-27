import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
    Plus,
    Bot,
    Save,
    ArrowLeft,
    FileText,
    Settings,
    MessageSquare,
    Zap
} from 'lucide-react';

const CreateAgent = ({ templates, onCreate, onCreateFromTemplate }) => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [formData, setFormData] = useState({
        name: '',
        goal: '',
        tools: [],
        memory_window: 10
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [showTemplates, setShowTemplates] = useState(false);

    const availableTools = [
        { id: 'analyze_image', name: 'Analyze Image', description: 'Analyze images and generate captions' },
        { id: 'search_content', name: 'Search Content', description: 'Search through stored content' },
        { id: 'generate_text', name: 'Generate Text', description: 'Generate text and creative content' },
        { id: 'web_search', name: 'Web Search', description: 'Search the web for information' }
    ];

    useEffect(() => {
        const templateName = searchParams.get('template');
        if (templateName && templates.length > 0) {
            const template = templates.find(t => t.name === templateName);
            if (template) {
                setSelectedTemplate(template);
                setFormData({
                    name: template.display_name,
                    goal: template.goal,
                    tools: template.tools,
                    memory_window: template.memory_window
                });
            }
        }
    }, [searchParams, templates]);

    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleToolToggle = (toolId) => {
        setFormData(prev => ({
            ...prev,
            tools: prev.tools.includes(toolId)
                ? prev.tools.filter(t => t !== toolId)
                : [...prev.tools, toolId]
        }));
    };

    const handleTemplateSelect = (template) => {
        setSelectedTemplate(template);
        setFormData({
            name: template.display_name,
            goal: template.goal,
            tools: template.tools,
            memory_window: template.memory_window
        });
        setShowTemplates(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.name.trim() || !formData.goal.trim()) {
            alert('Please fill in all required fields');
            return;
        }

        if (formData.tools.length === 0) {
            alert('Please select at least one tool');
            return;
        }

        setIsSubmitting(true);
        try {
            await onCreate(formData);
            navigate('/agents');
        } catch (error) {
            alert(`Failed to create agent: ${error.message}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div>
            <div className="mb-6">
                <button
                    onClick={() => navigate('/agents')}
                    className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Agents
                </button>

                <h1 className="text-2xl font-bold text-gray-900">Create New Agent</h1>
                <p className="text-gray-600">Set up a new AI agent with custom goals and tools</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Template Selection */}
                <div className="lg:col-span-1">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Start from Template</h3>
                        <p className="text-sm text-gray-600 mb-4">
                            Choose a pre-built template to get started quickly
                        </p>

                        <button
                            onClick={() => setShowTemplates(!showTemplates)}
                            className="w-full flex items-center justify-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                            <FileText className="h-4 w-4" />
                            <span>Browse Templates</span>
                        </button>

                        {selectedTemplate && (
                            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                                <h4 className="font-medium text-blue-900">{selectedTemplate.display_name}</h4>
                                <p className="text-sm text-blue-700">{selectedTemplate.description}</p>
                                <button
                                    onClick={() => setSelectedTemplate(null)}
                                    className="text-xs text-blue-600 hover:text-blue-800 mt-2"
                                >
                                    Clear template
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Agent Configuration */}
                <div className="lg:col-span-2">
                    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg shadow-sm">
                        <div className="p-6 border-b">
                            <h3 className="text-lg font-semibold text-gray-900">Agent Configuration</h3>
                            <p className="text-sm text-gray-600 mt-1">
                                Configure your agent's name, goal, and capabilities
                            </p>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Agent Name */}
                            <div>
                                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                                    Agent Name *
                                </label>
                                <input
                                    type="text"
                                    id="name"
                                    value={formData.name}
                                    onChange={(e) => handleInputChange('name', e.target.value)}
                                    placeholder="Enter agent name..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    required
                                />
                            </div>

                            {/* Agent Goal */}
                            <div>
                                <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-2">
                                    Agent Goal *
                                </label>
                                <textarea
                                    id="goal"
                                    rows={4}
                                    value={formData.goal}
                                    onChange={(e) => handleInputChange('goal', e.target.value)}
                                    placeholder="Describe what this agent should accomplish..."
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    required
                                />
                                <p className="text-sm text-gray-500 mt-1">
                                    Be specific about what tasks this agent should perform
                                </p>
                            </div>

                            {/* Tools Selection */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Available Tools *
                                </label>
                                <p className="text-sm text-gray-500 mb-3">
                                    Select the tools this agent can use to accomplish its goal
                                </p>

                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {availableTools.map((tool) => (
                                        <label
                                            key={tool.id}
                                            className={`relative flex items-start p-3 border rounded-lg cursor-pointer transition-colors ${formData.tools.includes(tool.id)
                                                ? 'border-blue-500 bg-blue-50'
                                                : 'border-gray-300 hover:border-gray-400'
                                                }`}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={formData.tools.includes(tool.id)}
                                                onChange={() => handleToolToggle(tool.id)}
                                                className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                            />
                                            <div className="ml-3">
                                                <div className="text-sm font-medium text-gray-900">{tool.name}</div>
                                                <div className="text-sm text-gray-500">{tool.description}</div>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {/* Memory Window */}
                            <div>
                                <label htmlFor="memory_window" className="block text-sm font-medium text-gray-700 mb-2">
                                    Memory Window
                                </label>
                                <div className="flex items-center space-x-4">
                                    <input
                                        type="range"
                                        id="memory_window"
                                        min="5"
                                        max="50"
                                        value={formData.memory_window}
                                        onChange={(e) => handleInputChange('memory_window', parseInt(e.target.value))}
                                        className="flex-1"
                                    />
                                    <div className="flex items-center space-x-1 text-sm text-gray-600">
                                        <MessageSquare className="h-4 w-4" />
                                        <span>{formData.memory_window} messages</span>
                                    </div>
                                </div>
                                <p className="text-sm text-gray-500 mt-1">
                                    Number of conversation messages the agent will remember
                                </p>
                            </div>

                            {/* Submit Button */}
                            <div className="flex items-center justify-end space-x-3 pt-4 border-t">
                                <button
                                    type="button"
                                    onClick={() => navigate('/agents')}
                                    className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                                >
                                    {isSubmitting ? (
                                        <>
                                            <Zap className="h-4 w-4 animate-pulse" />
                                            <span>Creating...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Plus className="h-4 w-4" />
                                            <span>Create Agent</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>

            {/* Template Modal */}
            {showTemplates && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
                        <div className="p-6 border-b">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-gray-900">Choose a Template</h3>
                                <button
                                    onClick={() => setShowTemplates(false)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    ×
                                </button>
                            </div>
                        </div>

                        <div className="p-6 overflow-y-auto max-h-[60vh]">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {templates.map((template) => (
                                    <div
                                        key={template.name}
                                        onClick={() => handleTemplateSelect(template)}
                                        className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 cursor-pointer transition-colors"
                                    >
                                        <h4 className="font-medium text-gray-900">{template.display_name}</h4>
                                        <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                                        <div className="mt-2 flex flex-wrap gap-1">
                                            {template.tools.slice(0, 3).map((tool) => (
                                                <span
                                                    key={tool}
                                                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                                                >
                                                    {tool.replace('_', ' ')}
                                                </span>
                                            ))}
                                            {template.tools.length > 3 && (
                                                <span className="text-xs text-gray-500">+{template.tools.length - 3} more</span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CreateAgent;
