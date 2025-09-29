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
    Loader,
    BarChart3,
    Activity,
    Settings,
    Eye,
    EyeOff
} from 'lucide-react';
import RealTimeMonitor from './RealTimeMonitor';
import AgentPerformance from './AgentPerformance';

const EnhancedAgentDetail = ({ agents, onExecute }) => {
    const { agentId } = useParams();
    const [agent, setAgent] = useState(null);
    const [task, setTask] = useState('');
    const [isExecuting, setIsExecuting] = useState(false);
    const [executionHistory, setExecutionHistory] = useState([]);
    const [activeTab, setActiveTab] = useState('execute');
    const [showRealTimeMonitor, setShowRealTimeMonitor] = useState(true);
    const [showPerformance, setShowPerformance] = useState(false);

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

                    {/* Monitoring Controls */}
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={() => setShowRealTimeMonitor(!showRealTimeMonitor)}
                            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm ${
                                showRealTimeMonitor 
                                    ? 'bg-green-100 text-green-700' 
                                    : 'bg-gray-100 text-gray-700'
                            }`}
                        >
                            {showRealTimeMonitor ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                            <span>Monitor</span>
                        </button>
                        <button
                            onClick={() => setShowPerformance(!showPerformance)}
                            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm ${
                                showPerformance 
                                    ? 'bg-blue-100 text-blue-700' 
                                    : 'bg-gray-100 text-gray-700'
                            }`}
                        >
                            <BarChart3 className="h-4 w-4" />
                            <span>Analytics</span>
                        </button>
                    </div>
                </div>
            </div>

            {/* Real-time Monitor */}
            {showRealTimeMonitor && (
                <div className="mb-6">
                    <RealTimeMonitor agentId={agentId} />
                </div>
            )}

            {/* Performance Analytics */}
            {showPerformance && (
                <div className="mb-6">
                    <AgentPerformance agentId={agentId} agentName={agent.name} />
                </div>
            )}

            {/* Tab Navigation */}
            <div className="mb-6">
                <nav className="flex space-x-8">
                    <button
                        onClick={() => setActiveTab('execute')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'execute'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Execute Tasks
                    </button>
                    <button
                        onClick={() => setActiveTab('history')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'history'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Execution History
                    </button>
                    <button
                        onClick={() => setActiveTab('details')}
                        className={`py-2 px-1 border-b-2 font-medium text-sm ${
                            activeTab === 'details'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Agent Details
                    </button>
                </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'execute' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Agent Info */}
                    <div className="lg:col-span-1">
                        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Info</h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="text-sm font-medium text-gray-700">Status</label>
                                    <p className="text-sm text-gray-600 capitalize">{agent.status}</p>
                                </div>

                                <div>
                                    <label className="text-sm font-medium text-gray-700">Tools Available</label>
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

                                <div>
                                    <label className="text-sm font-medium text-gray-700">Created</label>
                                    <p className="text-sm text-gray-600">{formatDate(agent.created_at)}</p>
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
                                            rows={4}
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
                    </div>
                </div>
            )}

            {activeTab === 'history' && (
                <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
                    <div className="p-6 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Execution History</h3>
                        <p className="text-sm text-gray-600 mt-1">
                            Recent task executions and their results
                        </p>
                    </div>

                    <div className="p-6">
                        {executionHistory.length === 0 ? (
                            <div className="text-center py-8">
                                <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                <p className="text-gray-500">No execution history yet</p>
                                <p className="text-sm text-gray-400 mt-1">Execute a task to see the history here</p>
                            </div>
                        ) : (
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
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'details' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Configuration</h3>
                        
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium text-gray-700">Agent ID</label>
                                <p className="text-sm text-gray-600 font-mono">{agent.agent_id}</p>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-gray-700">Name</label>
                                <p className="text-sm text-gray-600">{agent.name}</p>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-gray-700">Goal</label>
                                <p className="text-sm text-gray-600">{agent.goal}</p>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-gray-700">Status</label>
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                                    {agent.status}
                                </span>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-gray-700">Created</label>
                                <p className="text-sm text-gray-600">{formatDate(agent.created_at)}</p>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-gray-700">Last Updated</label>
                                <p className="text-sm text-gray-600">{formatDate(agent.updated_at)}</p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Tools</h3>
                        
                        <div className="space-y-3">
                            {agent.tools.map((tool) => (
                                <div key={tool} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <div className="flex items-center space-x-3">
                                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                            <Settings className="h-4 w-4 text-blue-600" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">
                                                {tool.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                            </p>
                                            <p className="text-xs text-gray-500">Tool</p>
                                        </div>
                                    </div>
                                    <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                                        Available
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EnhancedAgentDetail;