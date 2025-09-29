import React, { useState, useEffect } from 'react';
import { 
    TrendingUp, 
    TrendingDown, 
    Clock, 
    CheckCircle, 
    XCircle, 
    Activity,
    Zap,
    Target,
    BarChart3,
    RefreshCw
} from 'lucide-react';
import axios from 'axios';

const AgentPerformance = ({ agentId, agentName }) => {
    const [performance, setPerformance] = useState({
        overview: {
            totalExecutions: 0,
            successRate: 0,
            averageResponseTime: 0,
            lastExecution: null,
            status: 'inactive'
        },
        trends: {
            executionsOverTime: [],
            successRateOverTime: [],
            responseTimeOverTime: []
        },
        recentExecutions: [],
        toolUsage: [],
        performanceHistory: []
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedPeriod, setSelectedPeriod] = useState('7d');

    useEffect(() => {
        if (agentId) {
            fetchPerformance();
        }
    }, [agentId, selectedPeriod]);

    const fetchPerformance = async () => {
        try {
            setLoading(true);
            setError(null);

            const baseUrl = process.env.REACT_APP_API_BASE || '/api/v1';
            const params = { period: selectedPeriod };

            const [overviewRes, trendsRes, executionsRes, toolUsageRes, historyRes] = await Promise.all([
                axios.get(`${baseUrl}/agents/${agentId}/performance`, { params }),
                axios.get(`${baseUrl}/agents/${agentId}/trends`, { params }),
                axios.get(`${baseUrl}/agents/${agentId}/history`, { params: { limit: 10 } }),
                axios.get(`${baseUrl}/agents/${agentId}/tool-usage`, { params }),
                axios.get(`${baseUrl}/agents/${agentId}/performance-history`, { params })
            ]);

            setPerformance({
                overview: overviewRes.data,
                trends: trendsRes.data,
                recentExecutions: executionsRes.data.executions || [],
                toolUsage: toolUsageRes.data.tools || [],
                performanceHistory: historyRes.data.history || []
            });
        } catch (err) {
            console.error('Error fetching performance data:', err);
            setError('Failed to load performance data');
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (ms) => {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active':
                return 'text-green-600 bg-green-100';
            case 'inactive':
                return 'text-gray-600 bg-gray-100';
            case 'error':
                return 'text-red-600 bg-red-100';
            default:
                return 'text-gray-600 bg-gray-100';
        }
    };

    const getTrendIcon = (trend) => {
        if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
        if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
        return <Activity className="h-4 w-4 text-gray-500" />;
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-pulse" />
                    <p className="text-gray-600">Loading performance data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <XCircle className="h-12 w-12 text-red-600 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">{error}</p>
                    <button
                        onClick={fetchPerformance}
                        className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        <RefreshCw className="h-4 w-4" />
                        <span>Retry</span>
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-gray-900">Performance Analytics</h2>
                    <p className="text-sm text-gray-600">{agentName}</p>
                </div>
                <div className="flex items-center space-x-4">
                    <select
                        value={selectedPeriod}
                        onChange={(e) => setSelectedPeriod(e.target.value)}
                        className="border border-gray-300 rounded-md px-3 py-2 text-sm"
                    >
                        <option value="24h">Last 24 hours</option>
                        <option value="7d">Last 7 days</option>
                        <option value="30d">Last 30 days</option>
                        <option value="90d">Last 90 days</option>
                    </select>
                    <button
                        onClick={fetchPerformance}
                        className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        <RefreshCw className="h-4 w-4" />
                        <span>Refresh</span>
                    </button>
                </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Total Executions</p>
                            <p className="text-2xl font-bold text-gray-900">{performance.overview.totalExecutions}</p>
                        </div>
                        <Activity className="h-8 w-8 text-blue-500" />
                    </div>
                    {performance.trends.executionsOverTime.length > 1 && (
                        <div className="flex items-center mt-2">
                            {getTrendIcon(performance.trends.executionsOverTime[performance.trends.executionsOverTime.length - 1] - performance.trends.executionsOverTime[0])}
                            <span className="text-sm text-gray-600 ml-1">
                                {Math.abs(performance.trends.executionsOverTime[performance.trends.executionsOverTime.length - 1] - performance.trends.executionsOverTime[0])} vs last period
                            </span>
                        </div>
                    )}
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Success Rate</p>
                            <p className="text-2xl font-bold text-gray-900">{performance.overview.successRate.toFixed(1)}%</p>
                        </div>
                        <CheckCircle className="h-8 w-8 text-green-500" />
                    </div>
                    {performance.trends.successRateOverTime.length > 1 && (
                        <div className="flex items-center mt-2">
                            {getTrendIcon(performance.trends.successRateOverTime[performance.trends.successRateOverTime.length - 1] - performance.trends.successRateOverTime[0])}
                            <span className="text-sm text-gray-600 ml-1">
                                {Math.abs(performance.trends.successRateOverTime[performance.trends.successRateOverTime.length - 1] - performance.trends.successRateOverTime[0]).toFixed(1)}% vs last period
                            </span>
                        </div>
                    )}
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
                            <p className="text-2xl font-bold text-gray-900">{formatTime(performance.overview.averageResponseTime)}</p>
                        </div>
                        <Clock className="h-8 w-8 text-purple-500" />
                    </div>
                    {performance.trends.responseTimeOverTime.length > 1 && (
                        <div className="flex items-center mt-2">
                            {getTrendIcon(performance.trends.responseTimeOverTime[0] - performance.trends.responseTimeOverTime[performance.trends.responseTimeOverTime.length - 1])}
                            <span className="text-sm text-gray-600 ml-1">
                                {formatTime(Math.abs(performance.trends.responseTimeOverTime[performance.trends.responseTimeOverTime.length - 1] - performance.trends.responseTimeOverTime[0]))} vs last period
                            </span>
                        </div>
                    )}
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-600">Status</p>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(performance.overview.status)}`}>
                                {performance.overview.status}
                            </span>
                        </div>
                        <Zap className="h-8 w-8 text-yellow-500" />
                    </div>
                    {performance.overview.lastExecution && (
                        <p className="text-sm text-gray-600 mt-2">
                            Last: {formatDate(performance.overview.lastExecution)}
                        </p>
                    )}
                </div>
            </div>

            {/* Recent Executions and Tool Usage */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Executions */}
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Recent Executions</h3>
                    </div>
                    <div className="p-4">
                        {performance.recentExecutions.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No recent executions</p>
                        ) : (
                            <div className="space-y-3">
                                {performance.recentExecutions.map((execution) => (
                                    <div key={execution.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center space-x-3">
                                            {execution.success ? (
                                                <CheckCircle className="h-5 w-5 text-green-500" />
                                            ) : (
                                                <XCircle className="h-5 w-5 text-red-500" />
                                            )}
                                            <div>
                                                <p className="text-sm font-medium text-gray-900">
                                                    {execution.task.substring(0, 50)}...
                                                </p>
                                                <p className="text-xs text-gray-500">
                                                    {formatDate(execution.executed_at)}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-sm font-medium text-gray-900">
                                                {formatTime(execution.execution_time_ms)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Tool Usage */}
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Tool Usage</h3>
                    </div>
                    <div className="p-4">
                        {performance.toolUsage.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No tool usage data</p>
                        ) : (
                            <div className="space-y-3">
                                {performance.toolUsage.map((tool) => (
                                    <div key={tool.tool_name} className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            <Target className="h-5 w-5 text-blue-500" />
                                            <div>
                                                <p className="text-sm font-medium text-gray-900">{tool.tool_name}</p>
                                                <p className="text-xs text-gray-500">{tool.usage_count} uses</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-sm font-medium text-gray-900">{tool.success_rate.toFixed(1)}%</p>
                                            <p className="text-xs text-gray-500">{formatTime(tool.avg_execution_time)}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Performance History Chart Placeholder */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold text-gray-900">Performance History</h3>
                </div>
                <div className="p-4">
                    <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                        <div className="text-center">
                            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                            <p className="text-gray-500">Performance trend chart would be implemented here</p>
                            <p className="text-sm text-gray-400">Showing execution count, success rate, and response time over time</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AgentPerformance;