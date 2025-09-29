import React, { useState, useEffect } from 'react';
import { 
    BarChart3, 
    TrendingUp, 
    Users, 
    Clock, 
    CheckCircle, 
    XCircle,
    Activity,
    Zap,
    Calendar,
    Download
} from 'lucide-react';
import axios from 'axios';

const AnalyticsDashboard = ({ agentId = null, period = '7d' }) => {
    const [analytics, setAnalytics] = useState({
        overview: {
            totalExecutions: 0,
            successRate: 0,
            averageResponseTime: 0,
            totalAgents: 0,
            activeAgents: 0
        },
        trends: {
            executionsOverTime: [],
            successRateOverTime: [],
            responseTimeOverTime: []
        },
        agentStats: [],
        toolUsage: [],
        performanceMetrics: {
            p50: 0,
            p95: 0,
            p99: 0,
            errorRate: 0
        }
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedPeriod, setSelectedPeriod] = useState(period);

    useEffect(() => {
        fetchAnalytics();
    }, [agentId, selectedPeriod]);

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            setError(null);

            const baseUrl = process.env.REACT_APP_API_BASE || '/api/v1';
            const params = { period: selectedPeriod };
            if (agentId) params.agent_id = agentId;

            const [overviewRes, trendsRes, agentStatsRes, toolUsageRes, performanceRes] = await Promise.all([
                axios.get(`${baseUrl}/analytics/overview`, { params }),
                axios.get(`${baseUrl}/analytics/trends`, { params }),
                axios.get(`${baseUrl}/analytics/agent-stats`, { params }),
                axios.get(`${baseUrl}/analytics/tool-usage`, { params }),
                axios.get(`${baseUrl}/analytics/performance`, { params })
            ]);

            setAnalytics({
                overview: overviewRes.data,
                trends: trendsRes.data,
                agentStats: agentStatsRes.data.agents || [],
                toolUsage: toolUsageRes.data.tools || [],
                performanceMetrics: performanceRes.data
            });
        } catch (err) {
            console.error('Error fetching analytics:', err);
            setError('Failed to load analytics data');
        } finally {
            setLoading(false);
        }
    };

    const exportAnalytics = async () => {
        try {
            const baseUrl = process.env.REACT_APP_API_BASE || '/api/v1';
            const params = { period: selectedPeriod, format: 'csv' };
            if (agentId) params.agent_id = agentId;

            const response = await axios.get(`${baseUrl}/analytics/export`, { 
                params,
                responseType: 'blob'
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `analytics-${selectedPeriod}-${new Date().toISOString().split('T')[0]}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error('Error exporting analytics:', err);
        }
    };

    const formatTime = (ms) => {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    const formatNumber = (num) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-pulse" />
                    <p className="text-gray-600">Loading analytics...</p>
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
                        onClick={fetchAnalytics}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Analytics Dashboard</h2>
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
                        onClick={exportAnalytics}
                        className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                    >
                        <Download className="h-4 w-4" />
                        <span>Export</span>
                    </button>
                </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <Activity className="h-8 w-8 text-blue-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Total Executions</p>
                            <p className="text-2xl font-bold text-gray-900">{formatNumber(analytics.overview.totalExecutions)}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <CheckCircle className="h-8 w-8 text-green-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Success Rate</p>
                            <p className="text-2xl font-bold text-gray-900">{analytics.overview.successRate.toFixed(1)}%</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <Clock className="h-8 w-8 text-purple-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Avg Response</p>
                            <p className="text-2xl font-bold text-gray-900">{formatTime(analytics.overview.averageResponseTime)}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <Users className="h-8 w-8 text-indigo-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Total Agents</p>
                            <p className="text-2xl font-bold text-gray-900">{analytics.overview.totalAgents}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <Zap className="h-8 w-8 text-yellow-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Active Agents</p>
                            <p className="text-2xl font-bold text-gray-900">{analytics.overview.activeAgents}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold text-gray-900">Performance Metrics</h3>
                </div>
                <div className="p-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <p className="text-sm text-gray-600">P50 Response Time</p>
                            <p className="text-xl font-bold text-gray-900">{formatTime(analytics.performanceMetrics.p50)}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-gray-600">P95 Response Time</p>
                            <p className="text-xl font-bold text-gray-900">{formatTime(analytics.performanceMetrics.p95)}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-gray-600">P99 Response Time</p>
                            <p className="text-xl font-bold text-gray-900">{formatTime(analytics.performanceMetrics.p99)}</p>
                        </div>
                        <div className="text-center">
                            <p className="text-sm text-gray-600">Error Rate</p>
                            <p className="text-xl font-bold text-gray-900">{analytics.performanceMetrics.errorRate.toFixed(2)}%</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts and Tables */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Agent Statistics */}
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Top Performing Agents</h3>
                    </div>
                    <div className="p-4">
                        {analytics.agentStats.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No agent data available</p>
                        ) : (
                            <div className="space-y-3">
                                {analytics.agentStats.slice(0, 5).map((agent, index) => (
                                    <div key={agent.agent_id} className="flex items-center justify-between">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                <span className="text-sm font-medium text-blue-600">#{index + 1}</span>
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                                                <p className="text-xs text-gray-500">{agent.executions} executions</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-sm font-medium text-gray-900">{agent.success_rate.toFixed(1)}%</p>
                                            <p className="text-xs text-gray-500">{formatTime(agent.avg_response_time)}</p>
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
                        {analytics.toolUsage.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No tool usage data available</p>
                        ) : (
                            <div className="space-y-3">
                                {analytics.toolUsage.slice(0, 5).map((tool) => (
                                    <div key={tool.tool_name} className="flex items-center justify-between">
                                        <div>
                                            <p className="text-sm font-medium text-gray-900">{tool.tool_name}</p>
                                            <p className="text-xs text-gray-500">{tool.usage_count} uses</p>
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

            {/* Trends Chart Placeholder */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-4 border-b">
                    <h3 className="text-lg font-semibold text-gray-900">Execution Trends</h3>
                </div>
                <div className="p-4">
                    <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                        <div className="text-center">
                            <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                            <p className="text-gray-500">Chart visualization would be implemented here</p>
                            <p className="text-sm text-gray-400">Using libraries like Chart.js or Recharts</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AnalyticsDashboard;