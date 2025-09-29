import React, { useState, useEffect, useRef } from 'react';
import { Activity, Zap, Clock, TrendingUp, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const RealTimeMonitor = ({ agentId = null }) => {
    const [metrics, setMetrics] = useState({
        activeExecutions: 0,
        totalExecutions: 0,
        successRate: 0,
        averageResponseTime: 0,
        recentActivity: []
    });
    const [isConnected, setIsConnected] = useState(false);
    const [alerts, setAlerts] = useState([]);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    useEffect(() => {
        connectWebSocket();
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [agentId]);

    const connectWebSocket = () => {
        const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8003/ws';
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
            console.log('WebSocket connected');
            setIsConnected(true);
            
            // Subscribe to agent-specific updates if agentId is provided
            if (agentId) {
                wsRef.current.send(JSON.stringify({
                    type: 'subscribe',
                    channel: `agent:${agentId}`
                }));
            } else {
                // Subscribe to global updates
                wsRef.current.send(JSON.stringify({
                    type: 'subscribe',
                    channel: 'global'
                }));
            }
        };

        wsRef.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        wsRef.current.onclose = () => {
            console.log('WebSocket disconnected');
            setIsConnected(false);
            
            // Attempt to reconnect after 5 seconds
            reconnectTimeoutRef.current = setTimeout(() => {
                connectWebSocket();
            }, 5000);
        };

        wsRef.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            setIsConnected(false);
        };
    };

    const handleWebSocketMessage = (data) => {
        switch (data.type) {
            case 'agent_execution_started':
                setMetrics(prev => ({
                    ...prev,
                    activeExecutions: prev.activeExecutions + 1,
                    recentActivity: [
                        {
                            id: Date.now(),
                            type: 'execution_started',
                            agentId: data.agent_id,
                            task: data.task,
                            timestamp: new Date(data.timestamp)
                        },
                        ...prev.recentActivity.slice(0, 9)
                    ]
                }));
                break;

            case 'agent_execution_completed':
                setMetrics(prev => ({
                    ...prev,
                    activeExecutions: Math.max(0, prev.activeExecutions - 1),
                    totalExecutions: prev.totalExecutions + 1,
                    recentActivity: [
                        {
                            id: Date.now(),
                            type: 'execution_completed',
                            agentId: data.agent_id,
                            success: data.success,
                            executionTime: data.execution_time_ms,
                            timestamp: new Date(data.timestamp)
                        },
                        ...prev.recentActivity.slice(0, 9)
                    ]
                }));
                break;

            case 'agent_execution_failed':
                setMetrics(prev => ({
                    ...prev,
                    activeExecutions: Math.max(0, prev.activeExecutions - 1),
                    totalExecutions: prev.totalExecutions + 1,
                    recentActivity: [
                        {
                            id: Date.now(),
                            type: 'execution_failed',
                            agentId: data.agent_id,
                            error: data.error,
                            timestamp: new Date(data.timestamp)
                        },
                        ...prev.recentActivity.slice(0, 9)
                    ]
                }));
                
                // Add alert for failed execution
                setAlerts(prev => [
                    {
                        id: Date.now(),
                        type: 'error',
                        message: `Agent ${data.agent_id} execution failed: ${data.error}`,
                        timestamp: new Date(data.timestamp)
                    },
                    ...prev.slice(0, 4)
                ]);
                break;

            case 'metrics_update':
                setMetrics(prev => ({
                    ...prev,
                    successRate: data.success_rate,
                    averageResponseTime: data.average_response_time
                }));
                break;

            case 'alert':
                setAlerts(prev => [
                    {
                        id: Date.now(),
                        type: data.alert_type,
                        message: data.message,
                        timestamp: new Date(data.timestamp)
                    },
                    ...prev.slice(0, 4)
                ]);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    };

    const getActivityIcon = (type) => {
        switch (type) {
            case 'execution_started':
                return <Zap className="h-4 w-4 text-blue-500" />;
            case 'execution_completed':
                return <CheckCircle className="h-4 w-4 text-green-500" />;
            case 'execution_failed':
                return <XCircle className="h-4 w-4 text-red-500" />;
            default:
                return <Activity className="h-4 w-4 text-gray-500" />;
        }
    };

    const getAlertIcon = (type) => {
        switch (type) {
            case 'error':
                return <XCircle className="h-4 w-4 text-red-500" />;
            case 'warning':
                return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
            case 'info':
                return <CheckCircle className="h-4 w-4 text-blue-500" />;
            default:
                return <AlertTriangle className="h-4 w-4 text-gray-500" />;
        }
    };

    const formatTime = (timestamp) => {
        return new Date(timestamp).toLocaleTimeString();
    };

    const formatDuration = (ms) => {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(1)}s`;
    };

    return (
        <div className="space-y-6">
            {/* Connection Status */}
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Real-Time Monitor</h2>
                <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm text-gray-600">
                        {isConnected ? 'Connected' : 'Disconnected'}
                    </span>
                </div>
            </div>

            {/* Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <Activity className="h-8 w-8 text-blue-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Active</p>
                            <p className="text-2xl font-bold text-gray-900">{metrics.activeExecutions}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <TrendingUp className="h-8 w-8 text-green-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Total Executions</p>
                            <p className="text-2xl font-bold text-gray-900">{metrics.totalExecutions}</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <CheckCircle className="h-8 w-8 text-green-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Success Rate</p>
                            <p className="text-2xl font-bold text-gray-900">{metrics.successRate.toFixed(1)}%</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <div className="flex items-center">
                        <Clock className="h-8 w-8 text-purple-500" />
                        <div className="ml-3">
                            <p className="text-sm font-medium text-gray-600">Avg Response</p>
                            <p className="text-2xl font-bold text-gray-900">{formatDuration(metrics.averageResponseTime)}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Activity and Alerts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Activity */}
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
                    </div>
                    <div className="p-4">
                        {metrics.recentActivity.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No recent activity</p>
                        ) : (
                            <div className="space-y-3">
                                {metrics.recentActivity.map((activity) => (
                                    <div key={activity.id} className="flex items-start space-x-3">
                                        {getActivityIcon(activity.type)}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-gray-900">
                                                {activity.type === 'execution_started' && `Started: ${activity.task}`}
                                                {activity.type === 'execution_completed' && `Completed in ${formatDuration(activity.executionTime)}`}
                                                {activity.type === 'execution_failed' && `Failed: ${activity.error}`}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                Agent: {activity.agentId} • {formatTime(activity.timestamp)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Alerts */}
                <div className="bg-white rounded-lg shadow">
                    <div className="p-4 border-b">
                        <h3 className="text-lg font-semibold text-gray-900">Alerts</h3>
                    </div>
                    <div className="p-4">
                        {alerts.length === 0 ? (
                            <p className="text-gray-500 text-center py-4">No alerts</p>
                        ) : (
                            <div className="space-y-3">
                                {alerts.map((alert) => (
                                    <div key={alert.id} className="flex items-start space-x-3">
                                        {getAlertIcon(alert.type)}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-gray-900">{alert.message}</p>
                                            <p className="text-xs text-gray-500">
                                                {formatTime(alert.timestamp)}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RealTimeMonitor;