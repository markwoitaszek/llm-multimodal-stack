import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import AgentList from './components/AgentList';
import AgentDetail from './components/AgentDetail';
import TemplateList from './components/TemplateList';
import CreateAgent from './components/CreateAgent';
import {
    Bot,
    List,
    Plus,
    FileText,
    Settings,
    Home
} from 'lucide-react';

// API base URL
const API_BASE = process.env.REACT_APP_API_BASE || '/api/v1';

function App() {
    const [agents, setAgents] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [agentsRes, templatesRes] = await Promise.all([
                axios.get(`${API_BASE}/agents`),
                axios.get(`${API_BASE}/templates`)
            ]);

            setAgents(agentsRes.data);
            setTemplates(templatesRes.data.templates);
            setError(null);
        } catch (err) {
            setError('Failed to load data. Please check if the AI Agents service is running.');
            console.error('Error fetching data:', err);
        } finally {
            setLoading(false);
        }
    };

    const createAgent = async (agentData) => {
        try {
            const response = await axios.post(`${API_BASE}/agents`, agentData);
            await fetchData(); // Refresh the list
            return response.data;
        } catch (err) {
            throw new Error(err.response?.data?.detail || 'Failed to create agent');
        }
    };

    const createAgentFromTemplate = async (templateName, agentName) => {
        try {
            const response = await axios.post(`${API_BASE}/agents/from-template`, null, {
                params: { template_name: templateName, agent_name: agentName }
            });
            await fetchData(); // Refresh the list
            return response.data;
        } catch (err) {
            throw new Error(err.response?.data?.detail || 'Failed to create agent from template');
        }
    };

    const executeAgent = async (agentId, task) => {
        try {
            const response = await axios.post(`${API_BASE}/agents/${agentId}/execute`, { task });
            return response.data;
        } catch (err) {
            throw new Error(err.response?.data?.detail || 'Failed to execute agent task');
        }
    };

    const deleteAgent = async (agentId) => {
        try {
            await axios.delete(`${API_BASE}/agents/${agentId}`);
            await fetchData(); // Refresh the list
        } catch (err) {
            throw new Error(err.response?.data?.detail || 'Failed to delete agent');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <Bot className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-pulse" />
                    <p className="text-gray-600">Loading AI Agents...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center max-w-md">
                    <Bot className="h-12 w-12 text-red-600 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">Connection Error</h2>
                    <p className="text-gray-600 mb-4">{error}</p>
                    <button
                        onClick={fetchData}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <Router>
            <div className="min-h-screen bg-gray-50">
                {/* Navigation */}
                <nav className="bg-white shadow-sm border-b">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex justify-between h-16">
                            <div className="flex items-center">
                                <Link to="/" className="flex items-center space-x-2">
                                    <Bot className="h-8 w-8 text-blue-600" />
                                    <span className="text-xl font-bold text-gray-900">AI Agents</span>
                                </Link>
                            </div>

                            <div className="flex items-center space-x-4">
                                <Link
                                    to="/"
                                    className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md"
                                >
                                    <Home className="h-4 w-4" />
                                    <span>Home</span>
                                </Link>
                                <Link
                                    to="/agents"
                                    className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md"
                                >
                                    <List className="h-4 w-4" />
                                    <span>Agents</span>
                                </Link>
                                <Link
                                    to="/templates"
                                    className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md"
                                >
                                    <FileText className="h-4 w-4" />
                                    <span>Templates</span>
                                </Link>
                                <Link
                                    to="/create"
                                    className="flex items-center space-x-1 bg-blue-600 text-white px-3 py-2 rounded-md hover:bg-blue-700"
                                >
                                    <Plus className="h-4 w-4" />
                                    <span>Create Agent</span>
                                </Link>
                            </div>
                        </div>
                    </div>
                </nav>

                {/* Main Content */}
                <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
                    <Routes>
                        <Route
                            path="/"
                            element={
                                <div>
                                    <h1 className="text-3xl font-bold text-gray-900 mb-6">AI Agents Dashboard</h1>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                                        <div className="bg-white p-6 rounded-lg shadow">
                                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Agents</h3>
                                            <p className="text-3xl font-bold text-blue-600">{agents.length}</p>
                                        </div>
                                        <div className="bg-white p-6 rounded-lg shadow">
                                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Templates</h3>
                                            <p className="text-3xl font-bold text-green-600">{templates.length}</p>
                                        </div>
                                        <div className="bg-white p-6 rounded-lg shadow">
                                            <h3 className="text-lg font-semibold text-gray-900 mb-2">Active</h3>
                                            <p className="text-3xl font-bold text-purple-600">
                                                {agents.filter(a => a.status === 'active').length}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                        <div className="bg-white rounded-lg shadow">
                                            <div className="p-6 border-b">
                                                <h2 className="text-xl font-semibold text-gray-900">Recent Agents</h2>
                                            </div>
                                            <div className="p-6">
                                                <AgentList agents={agents.slice(0, 5)} compact />
                                            </div>
                                        </div>

                                        <div className="bg-white rounded-lg shadow">
                                            <div className="p-6 border-b">
                                                <h2 className="text-xl font-semibold text-gray-900">Popular Templates</h2>
                                            </div>
                                            <div className="p-6">
                                                <TemplateList templates={templates.slice(0, 5)} compact />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            }
                        />
                        <Route
                            path="/agents"
                            element={<AgentList agents={agents} onDelete={deleteAgent} />}
                        />
                        <Route
                            path="/agents/:agentId"
                            element={<AgentDetail agents={agents} onExecute={executeAgent} />}
                        />
                        <Route
                            path="/templates"
                            element={<TemplateList templates={templates} />}
                        />
                        <Route
                            path="/create"
                            element={
                                <CreateAgent
                                    templates={templates}
                                    onCreate={createAgent}
                                    onCreateFromTemplate={createAgentFromTemplate}
                                />
                            }
                        />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App;
