import React from 'react';
import { Link } from 'react-router-dom';
import {
    Bot,
    Clock,
    Trash2,
    MessageSquare,
    Play,
    MoreVertical
} from 'lucide-react';

const AgentList = ({ agents, onDelete, compact = false }) => {
    const handleDelete = async (agentId, agentName) => {
        if (window.confirm(`Are you sure you want to delete "${agentName}"?`)) {
            try {
                await onDelete(agentId);
            } catch (error) {
                alert(`Failed to delete agent: ${error.message}`);
            }
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleDateString();
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'bg-green-100 text-green-800';
            case 'inactive': return 'bg-gray-100 text-gray-800';
            default: return 'bg-yellow-100 text-yellow-800';
        }
    };

    if (compact) {
        return (
            <div className="space-y-3">
                {agents.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">No agents found</p>
                ) : (
                    agents.map((agent) => (
                        <Link
                            key={agent.agent_id}
                            to={`/agents/${agent.agent_id}`}
                            className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-3">
                                    <Bot className="h-5 w-5 text-blue-600" />
                                    <div>
                                        <h4 className="font-medium text-gray-900">{agent.name}</h4>
                                        <p className="text-sm text-gray-500">{agent.goal}</p>
                                    </div>
                                </div>
                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(agent.status)}`}>
                                    {agent.status}
                                </span>
                            </div>
                        </Link>
                    ))
                )}
            </div>
        );
    }

    return (
        <div>
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
                <p className="text-gray-600">Manage your autonomous AI agents</p>
            </div>

            {agents.length === 0 ? (
                <div className="text-center py-12">
                    <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No agents yet</h3>
                    <p className="text-gray-500 mb-6">Create your first AI agent to get started</p>
                    <Link
                        to="/create"
                        className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        <Play className="h-4 w-4 mr-2" />
                        Create Agent
                    </Link>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-6">
                    {agents.map((agent) => (
                        <div key={agent.agent_id} className="bg-white border border-gray-200 rounded-lg shadow-sm">
                            <div className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start space-x-4">
                                        <div className="flex-shrink-0">
                                            <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                                <Bot className="h-6 w-6 text-blue-600" />
                                            </div>
                                        </div>

                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center space-x-2 mb-2">
                                                <h3 className="text-lg font-semibold text-gray-900">
                                                    <Link
                                                        to={`/agents/${agent.agent_id}`}
                                                        className="hover:text-blue-600 transition-colors"
                                                    >
                                                        {agent.name}
                                                    </Link>
                                                </h3>
                                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(agent.status)}`}>
                                                    {agent.status}
                                                </span>
                                            </div>

                                            <p className="text-gray-600 mb-3">{agent.goal}</p>

                                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                                                <div className="flex items-center space-x-1">
                                                    <Clock className="h-4 w-4" />
                                                    <span>Created {formatDate(agent.created_at)}</span>
                                                </div>

                                                <div className="flex items-center space-x-1">
                                                    <MessageSquare className="h-4 w-4" />
                                                    <span>{agent.tools.length} tools</span>
                                                </div>
                                            </div>

                                            <div className="mt-3">
                                                <div className="flex flex-wrap gap-2">
                                                    {agent.tools.map((tool) => (
                                                        <span
                                                            key={tool}
                                                            className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                                                        >
                                                            {tool.replace('_', ' ')}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-2">
                                        <Link
                                            to={`/agents/${agent.agent_id}`}
                                            className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                                            title="View Details"
                                        >
                                            <MoreVertical className="h-5 w-5" />
                                        </Link>

                                        {onDelete && (
                                            <button
                                                onClick={() => handleDelete(agent.agent_id, agent.name)}
                                                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                                                title="Delete Agent"
                                            >
                                                <Trash2 className="h-5 w-5" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default AgentList;
