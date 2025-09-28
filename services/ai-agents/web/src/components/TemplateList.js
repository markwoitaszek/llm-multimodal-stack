import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
    FileText,
    Plus,
    Search,
    Filter,
    Bot,
    MessageSquare,
    Zap,
    BookOpen,
    Users,
    BarChart3,
    Lightbulb
} from 'lucide-react';

const TemplateList = ({ templates, onCreateFromTemplate, compact = false }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');

    const categories = ['all', ...new Set(templates.map(t => t.category))];

    const filteredTemplates = templates.filter(template => {
        const matchesSearch = template.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            template.goal.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;

        return matchesSearch && matchesCategory;
    });

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'research': return <BookOpen className="h-5 w-5" />;
            case 'analysis': return <BarChart3 className="h-5 w-5" />;
            case 'creative': return <Lightbulb className="h-5 w-5" />;
            case 'support': return <Users className="h-5 w-5" />;
            case 'data': return <BarChart3 className="h-5 w-5" />;
            case 'education': return <BookOpen className="h-5 w-5" />;
            case 'productivity': return <Zap className="h-5 w-5" />;
            default: return <FileText className="h-5 w-5" />;
        }
    };

    const getCategoryColor = (category) => {
        switch (category) {
            case 'research': return 'bg-blue-100 text-blue-800';
            case 'analysis': return 'bg-green-100 text-green-800';
            case 'creative': return 'bg-purple-100 text-purple-800';
            case 'support': return 'bg-orange-100 text-orange-800';
            case 'data': return 'bg-indigo-100 text-indigo-800';
            case 'education': return 'bg-yellow-100 text-yellow-800';
            case 'productivity': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const handleCreateFromTemplate = async (templateName, templateDisplayName) => {
        if (onCreateFromTemplate) {
            const agentName = prompt(`Enter a name for your new agent based on "${templateDisplayName}":`);
            if (agentName && agentName.trim()) {
                try {
                    await onCreateFromTemplate(templateName, agentName.trim());
                    alert('Agent created successfully!');
                } catch (error) {
                    alert(`Failed to create agent: ${error.message}`);
                }
            }
        }
    };

    if (compact) {
        return (
            <div className="space-y-3">
                {templates.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">No templates available</p>
                ) : (
                    templates.map((template) => (
                        <div
                            key={template.name}
                            className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <div className={`p-2 rounded-lg ${getCategoryColor(template.category)}`}>
                                        {getCategoryIcon(template.category)}
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-gray-900">{template.display_name}</h4>
                                        <p className="text-sm text-gray-500">{template.description}</p>
                                    </div>
                                </div>
                                {onCreateFromTemplate && (
                                    <button
                                        onClick={() => handleCreateFromTemplate(template.name, template.display_name)}
                                        className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                                        title="Create from template"
                                    >
                                        <Plus className="h-4 w-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        );
    }

    return (
        <div>
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Agent Templates</h1>
                <p className="text-gray-600">Choose from pre-built templates to quickly create agents</p>
            </div>

            {/* Search and Filter */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search templates..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>

                <div className="flex items-center space-x-2">
                    <Filter className="h-4 w-4 text-gray-400" />
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                        {categories.map(category => (
                            <option key={category} value={category}>
                                {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {filteredTemplates.length === 0 ? (
                <div className="text-center py-12">
                    <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
                    <p className="text-gray-500">Try adjusting your search or filter criteria</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredTemplates.map((template) => (
                        <div key={template.name} className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
                            <div className="p-6">
                                <div className="flex items-start justify-between mb-4">
                                    <div className={`p-3 rounded-lg ${getCategoryColor(template.category)}`}>
                                        {getCategoryIcon(template.category)}
                                    </div>
                                    <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(template.category)}`}>
                                        {template.category}
                                    </span>
                                </div>

                                <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.display_name}</h3>
                                <p className="text-gray-600 mb-4">{template.description}</p>

                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">Goal:</h4>
                                    <p className="text-sm text-gray-600">{template.goal}</p>
                                </div>

                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">Tools:</h4>
                                    <div className="flex flex-wrap gap-1">
                                        {template.tools.map((tool) => (
                                            <span
                                                key={tool}
                                                className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                                            >
                                                {tool.replace('_', ' ')}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">Use Cases:</h4>
                                    <ul className="text-sm text-gray-600 space-y-1">
                                        {template.use_cases.slice(0, 3).map((useCase, index) => (
                                            <li key={index} className="flex items-center space-x-1">
                                                <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                                                <span>{useCase}</span>
                                            </li>
                                        ))}
                                        {template.use_cases.length > 3 && (
                                            <li className="text-gray-500">+{template.use_cases.length - 3} more</li>
                                        )}
                                    </ul>
                                </div>

                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-1 text-sm text-gray-500">
                                        <MessageSquare className="h-4 w-4" />
                                        <span>{template.memory_window} messages</span>
                                    </div>

                                    {onCreateFromTemplate ? (
                                        <button
                                            onClick={() => handleCreateFromTemplate(template.name, template.display_name)}
                                            className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                                        >
                                            <Plus className="h-4 w-4" />
                                            <span>Create Agent</span>
                                        </button>
                                    ) : (
                                        <Link
                                            to={`/create?template=${template.name}`}
                                            className="flex items-center space-x-1 px-3 py-1 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                                        >
                                            <Plus className="h-4 w-4" />
                                            <span>Create Agent</span>
                                        </Link>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default TemplateList;
