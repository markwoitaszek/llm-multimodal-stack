# n8n Workflow Monitoring Service

A comprehensive monitoring and analytics service for n8n workflows integrated with the Multimodal LLM Stack AI agents.

## 🚀 Features

- **Real-time Workflow Monitoring**: Live tracking of workflow executions and performance
- **AI Agent Integration Analytics**: Detailed metrics on AI agent usage within workflows
- **Performance Dashboards**: Visual dashboards for workflow and agent performance
- **Alert System**: Automated alerts for failures, performance issues, and anomalies
- **Historical Analytics**: Long-term trend analysis and reporting
- **Custom Metrics**: Configurable metrics and KPIs for business intelligence

## 📋 Quick Start

### 1. Start the Service

```bash
# Start with the main stack
docker-compose -f docker-compose.yml -f docker-compose.n8n-monitoring.yml up -d

# Or start just the monitoring service
docker-compose -f docker-compose.n8n-monitoring.yml up -d
```

### 2. Access the Dashboard

- **Web Dashboard**: http://localhost:3003
- **API Documentation**: http://localhost:8008/docs
- **Health Check**: http://localhost:8008/health

### 3. Configure n8n Integration

The service automatically connects to n8n and starts monitoring workflows.

## 🏗️ Architecture

```
n8n Monitoring Service
├── Workflow Monitor (Real-time tracking)
├── Agent Analytics (AI agent performance)
├── Performance Metrics (Execution analytics)
├── Alert Manager (Notification system)
├── Dashboard API (Web interface backend)
└── Data Storage (PostgreSQL + Redis)
```

## 🔧 API Reference

### Workflow Monitoring

#### Get Workflow Status
```http
GET /api/v1/workflows/status
```

#### Get Workflow Execution History
```http
GET /api/v1/workflows/{workflow_id}/executions?limit=50&offset=0
```

#### Get Workflow Performance Metrics
```http
GET /api/v1/workflows/{workflow_id}/metrics?period=7d
```

### Agent Analytics

#### Get Agent Usage Statistics
```http
GET /api/v1/agents/analytics?period=30d
```

#### Get Agent Performance Metrics
```http
GET /api/v1/agents/{agent_id}/performance?period=7d
```

#### Get Agent Workflow Integration Stats
```http
GET /api/v1/agents/{agent_id}/workflows
```

### Real-time Monitoring

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8008/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

#### Subscribe to Workflow Events
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'workflow:customer-support-automation'
}));
```

## 🎯 Use Cases

### 1. Workflow Performance Monitoring
- Track execution times and success rates
- Identify bottlenecks and optimization opportunities
- Monitor resource usage and costs

### 2. AI Agent Analytics
- Analyze agent usage patterns across workflows
- Track agent performance and accuracy
- Optimize agent configurations

### 3. Business Intelligence
- Generate reports on automation ROI
- Track business process efficiency
- Monitor compliance and audit trails

### 4. Operational Excellence
- Proactive issue detection and alerting
- Capacity planning and scaling decisions
- Performance optimization recommendations

## 🔍 Monitoring & Analytics

### Key Metrics

#### Workflow Metrics
- **Execution Count**: Number of workflow runs
- **Success Rate**: Percentage of successful executions
- **Average Execution Time**: Mean time to completion
- **Error Rate**: Frequency of failures
- **Resource Usage**: CPU, memory, and network utilization

#### Agent Metrics
- **Agent Usage**: Frequency of agent calls
- **Response Time**: Agent execution duration
- **Accuracy Rate**: Success rate of agent tasks
- **Tool Usage**: Most frequently used tools
- **Cost Analysis**: Resource consumption per agent

#### Business Metrics
- **Process Efficiency**: Time saved through automation
- **Cost Savings**: Reduction in manual work
- **Quality Improvement**: Error reduction rates
- **Scalability Metrics**: Growth in automation usage

### Alerting

#### Alert Types
- **Critical**: Workflow failures, service outages
- **Warning**: Performance degradation, high error rates
- **Info**: Successful completions, milestone achievements

#### Notification Channels
- **Email**: Detailed reports and summaries
- **Slack**: Real-time notifications and updates
- **Webhook**: Custom integrations and systems
- **Dashboard**: In-app notifications and alerts

## 🚀 Deployment

### Development
```bash
# Start development environment
docker-compose -f docker-compose.yml -f docker-compose.n8n-monitoring.yml up -d

# View logs
docker-compose logs -f n8n-monitoring
```

### Production
```bash
# Deploy with production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.n8n-monitoring.yml up -d
```

### Environment Variables
```env
# Service Configuration
N8N_MONITORING_PORT=8008
N8N_MONITORING_HOST=0.0.0.0

# n8n Integration
N8N_URL=http://n8n:5678
N8N_API_KEY=your-n8n-api-key

# AI Agents Integration
AI_AGENTS_URL=http://ai-agents:8003

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=multimodal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=7

# Alert Configuration
ALERT_EMAIL_ENABLED=true
ALERT_SLACK_ENABLED=true
ALERT_WEBHOOK_ENABLED=false

# Performance Configuration
METRICS_RETENTION_DAYS=90
ALERT_THRESHOLD_ERROR_RATE=5.0
ALERT_THRESHOLD_RESPONSE_TIME=30000
```

## 🧪 Testing

### Unit Tests
```bash
cd services/n8n-monitoring
python -m pytest tests/
```

### Integration Tests
```bash
# Test n8n integration
python tests/test_n8n_integration.py

# Test agent analytics
python tests/test_agent_analytics.py
```

### Load Testing
```bash
# Test monitoring performance
python tests/test_monitoring_load.py
```

## 📖 Examples

See the `examples/` directory for:
- Workflow monitoring setup
- Custom dashboard creation
- Alert configuration
- Analytics integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is part of the Multimodal LLM Stack and follows the same licensing terms.

## 🆘 Support

- **Documentation**: Check the `/docs` directory for detailed guides
- **Issues**: Report bugs and feature requests via GitHub issues
- **Community**: Join our Discord for discussions and support

---

**Ready to monitor your n8n workflows with AI-powered analytics? Start with our [Quick Start Guide](#-quick-start) or explore the [Dashboard](http://localhost:3003)!**