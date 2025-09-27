import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
    Bot,
    Send,
    Clock,
    MessageSquare,
    ArrowLeft,
    Play,
    CheckCircle,
    XCircle,
    Loader
} from 'lucide-react';

const AgentDetail = ({ agents, onExecute }) => {
    const { agentId } = useParams();
    const [agent, setAgent] = useState(null);
    const [task, setTask] = useState('');
    const [isExecuting, setIsExecuting] = useState(false);
    const [executionHistory, setExecutionHistory] = useState([]);

    useEffect(() => {
        const foundAgent = agents.find(a => a.agent_id === agentId);
        setAgent(foundAgent);
    }, [agentId, agents]);

    const handleExecuteTask = async () => {
        if (!task.trim() || !agent) return;

        setIsExecuting(true);
        try {
            const result = await onExecute(agent.agent_id, task);

            setExecutionHistory(prev => [{
                id: Date.now(),
                task,
                result: result.result,
                success: result.success,
                timestamp: new Date().toISOString(),
                intermediateSteps: result.intermediate_steps || []
            }, ...prev]);

            setTask('');
        } catch (error) {
            setExecutionHistory(prev => [{
                id: Date.now(),
                task,
                result: `Error: ${error.message}`,
                success: false,
                timestamp: new Date().toISOString(),
                intermediateSteps: []
            }, ...prev]);
        } finally {
            setIsExecuting(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleExecuteTask();
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleString();
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'bg-green-100 text-green-800';
            case 'inactive': return 'bg-gray-100 text-gray-800';
            default: return 'bg-yellow-100 text-yellow-800';
        }
    };

    if (!agent) {
        return (
            <div className="text-center py-12">
                <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Agent not found</h3>
                <p className="text-gray-500 mb-6">The agent you're looking for doesn't exist</p>
                <Link
                    to="/agents"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Agents
                </Link>
            </div>
        );
    }

    return (
        <div>
            {/* Header */}
            <div className="mb-6">
                <Link
                    to="/agents"
                    className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Agents
                </Link>

                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-4">
                        <div className="h-16 w-16 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Bot className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                            <div className="flex items-center space-x-2 mb-2">
                                <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(agent.status)}`}>
                                    {agent.status}
                                </span>
                            </div>
                            <p className="text-gray-600">{agent.goal}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Agent Info */}
                <div className="lg:col-span-1">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Details</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium text-gray-700">Created</label>
                                <p className="text-sm text-gray-600">{formatDate(agent.created_at)}</p>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-gray-700">Tools</label>
                                <div className="mt-1 flex flex-wrap gap-2">
                                    {agent.tools.map((tool) => (
                                        <span
                                            key={tool}
                                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded"
                                        >
                                            {tool.replace('_', ' ')}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Task Execution */}
                <div className="lg:col-span-2">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
                        <div className="p-6 border-b">
                            <h3 className="text-lg font-semibold text-gray-900">Execute Task</h3>
                            <p className="text-sm text-gray-600 mt-1">
                                Give this agent a task to complete using its available tools
                            </p>
                        </div>

                        <div className="p-6">
                            <div className="space-y-4">
                                <div>
                                    <label htmlFor="task" className="block text-sm font-medium text-gray-700 mb-2">
                                        Task Description
                                    </label>
                                    <textarea
                                        id="task"
                                        rows={3}
                                        value={task}
                                        onChange={(e) => setTask(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="Describe the task you want the agent to perform..."
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        disabled={isExecuting}
                                    />
                                </div>

                                <button
                                    onClick={handleExecuteTask}
                                    disabled={!task.trim() || isExecuting}
                                    className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                                >
                                    {isExecuting ? (
                                        <>
                                            <Loader className="h-4 w-4 mr-2 animate-spin" />
                                            Executing...
                                        </>
                                    ) : (
                                        <>
                                            <Play className="h-4 w-4 mr-2" />
                                            Execute Task
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Execution History */}
                    {executionHistory.length > 0 && (
                        <div className="mt-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                            <div className="p-6 border-b">
                                <h3 className="text-lg font-semibold text-gray-900">Execution History</h3>
                            </div>

                            <div className="p-6">
                                <div className="space-y-4">
                                    {executionHistory.map((execution) => (
                                        <div key={execution.id} className="border border-gray-200 rounded-lg p-4">
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex items-center space-x-2">
                                                    {execution.success ? (
                                                        <CheckCircle className="h-5 w-5 text-green-600" />
                                                    ) : (
                                                        <XCircle className="h-5 w-5 text-red-600" />
                                                    )}
                                                    <span className="text-sm font-medium text-gray-900">
                                                        {execution.success ? 'Success' : 'Failed'}
                                                    </span>
                                                </div>
                                                <span className="text-xs text-gray-500">
                                                    {formatDate(execution.timestamp)}
                                                </span>
                                            </div>

                                            <div className="mb-3">
                                                <label className="text-sm font-medium text-gray-700">Task:</label>
                                                <p className="text-sm text-gray-600 mt-1">{execution.task}</p>
                                            </div>

                                            <div className="mb-3">
                                                <label className="text-sm font-medium text-gray-700">Result:</label>
                                                <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">{execution.result}</p>
                                            </div>

                                            {execution.intermediateSteps.length > 0 && (
                                                <div>
                                                    <label className="text-sm font-medium text-gray-700">Steps:</label>
                                                    <div className="mt-1 space-y-1">
                                                        {execution.intermediateSteps.map((step, index) => (
                                                            <div key={index} className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded">
                                                                <strong>{step.tool}:</strong> {step.action}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AgentDetail;
