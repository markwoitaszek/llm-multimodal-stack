# Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the Multimodal LLM Stack. The guide is organized by problem type and includes step-by-step solutions, diagnostic commands, and preventive measures.

## Quick Diagnostic Commands

### Service Health Check
```bash
# Check all services
curl http://localhost:3000/health  # AI Agents
curl http://localhost:3004/health  # IDE Bridge
curl http://localhost:3005/health  # Protocol Integration
curl http://localhost:3006/health  # Real-Time Collaboration
curl http://localhost:3007/health  # n8n Monitoring
curl http://localhost:5678/healthz # n8n

# Check Docker services
docker-compose ps
docker-compose logs --tail=50
```

### System Resources
```bash
# Check system resources
docker stats
df -h
free -h
top
```

### Network Connectivity
```bash
# Test internal connectivity
docker-compose exec ai-agents curl http://ide-bridge:3004/health
docker-compose exec ai-agents curl http://postgres:5432
docker-compose exec ai-agents curl http://redis:6379
```

## Common Issues

### 1. Service Startup Issues

#### Problem: Services fail to start
**Symptoms:**
- Docker containers exit immediately
- Health checks fail
- Services are not accessible

**Diagnosis:**
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs <service-name>

# Check resource usage
docker stats
```

**Solutions:**

1. **Insufficient Resources**
   ```bash
   # Check available memory
   free -h
   
   # Increase Docker memory limit
   # In Docker Desktop: Settings > Resources > Memory
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :3000
   
   # Change ports in docker-compose.yml
   ports:
     - "3001:3000"  # Change external port
   ```

3. **Dependency Issues**
   ```bash
   # Start services in order
   docker-compose up -d postgres redis
   sleep 10
   docker-compose up -d ai-agents
   ```

4. **Configuration Errors**
   ```bash
   # Validate configuration
   docker-compose config
   
   # Check environment variables
   docker-compose exec <service> env
   ```

#### Problem: Database connection failures
**Symptoms:**
- "Connection refused" errors
- Database timeout errors
- Service startup failures

**Diagnosis:**
```bash
# Check database status
docker-compose exec postgres pg_isready

# Test connection
docker-compose exec ai-agents psql -h postgres -U user -d ai_agents
```

**Solutions:**

1. **Database Not Ready**
   ```bash
   # Wait for database to be ready
   docker-compose up -d postgres
   sleep 30
   docker-compose up -d ai-agents
   ```

2. **Connection String Issues**
   ```bash
   # Check environment variables
   echo $DATABASE_URL
   
   # Verify connection string format
   # postgresql://user:password@host:port/database
   ```

3. **Database Permissions**
   ```bash
   # Check database permissions
   docker-compose exec postgres psql -U postgres -c "\du"
   
   # Create user if needed
   docker-compose exec postgres psql -U postgres -c "CREATE USER user WITH PASSWORD 'password';"
   ```

### 2. API Issues

#### Problem: API requests fail
**Symptoms:**
- 404 Not Found errors
- 500 Internal Server Error
- Connection timeout

**Diagnosis:**
```bash
# Test API endpoints
curl -v http://localhost:3000/health
curl -v http://localhost:3000/agents

# Check service logs
docker-compose logs ai-agents
```

**Solutions:**

1. **Service Not Running**
   ```bash
   # Restart service
   docker-compose restart ai-agents
   
   # Check service status
   docker-compose ps ai-agents
   ```

2. **Authentication Issues**
   ```bash
   # Check API key
   curl -H "Authorization: Bearer <your-token>" http://localhost:3000/agents
   
   # Verify JWT secret
   echo $JWT_SECRET
   ```

3. **Rate Limiting**
   ```bash
   # Check rate limit headers
   curl -I http://localhost:3000/agents
   
   # Wait for rate limit reset
   # Or increase rate limits in configuration
   ```

#### Problem: Agent execution failures
**Symptoms:**
- Agents fail to execute tasks
- Execution timeouts
- Invalid response errors

**Diagnosis:**
```bash
# Check execution logs
docker-compose logs ai-agents | grep "execution"

# Test agent execution
curl -X POST http://localhost:3000/agents/<agent-id>/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "test task", "user_id": "test"}'
```

**Solutions:**

1. **Model Configuration Issues**
   ```bash
   # Check model configuration
   curl http://localhost:3000/agents/<agent-id>
   
   # Verify model availability
   # Check API keys for model providers
   ```

2. **Tool Execution Failures**
   ```bash
   # Check tool configuration
   # Verify tool dependencies
   # Test tool execution manually
   ```

3. **Resource Constraints**
   ```bash
   # Check system resources
   docker stats
   
   # Increase memory limits
   # Optimize agent configuration
   ```

### 3. IDE Integration Issues

#### Problem: VS Code extension not working
**Symptoms:**
- Extension fails to load
- Code completion not working
- Connection errors

**Diagnosis:**
```bash
# Check IDE Bridge service
curl http://localhost:3004/health

# Check extension logs
# In VS Code: Help > Toggle Developer Tools > Console
```

**Solutions:**

1. **Extension Installation**
   ```bash
   # Install extension manually
   code --install-extension multimodal-llm-stack.ide-bridge
   
   # Check extension status
   code --list-extensions | grep multimodal
   ```

2. **Configuration Issues**
   ```bash
   # Check VS Code settings
   # Verify API endpoints
   # Check authentication
   ```

3. **Network Connectivity**
   ```bash
   # Test connection from VS Code
   # Check firewall settings
   # Verify proxy configuration
   ```

### 4. Real-Time Collaboration Issues

#### Problem: WebSocket connections fail
**Symptoms:**
- Real-time updates not working
- Connection drops frequently
- Authentication errors

**Diagnosis:**
```bash
# Check WebSocket service
curl http://localhost:3006/health

# Test WebSocket connection
wscat -c ws://localhost:3006/ws
```

**Solutions:**

1. **Connection Limits**
   ```bash
   # Check connection count
   curl http://localhost:3006/connections
   
   # Increase connection limits
   # Restart service to clear connections
   ```

2. **Authentication Issues**
   ```bash
   # Check JWT token
   # Verify token expiration
   # Test authentication endpoint
   ```

3. **Network Issues**
   ```bash
   # Check firewall settings
   # Verify WebSocket support
   # Test from different network
   ```

### 5. Performance Issues

#### Problem: Slow response times
**Symptoms:**
- API requests take too long
- High memory usage
- CPU spikes

**Diagnosis:**
```bash
# Check system resources
docker stats

# Check service performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:3000/health

# Check database performance
docker-compose exec postgres psql -U user -d ai_agents -c "SELECT * FROM pg_stat_activity;"
```

**Solutions:**

1. **Resource Optimization**
   ```bash
   # Increase memory limits
   # Optimize database queries
   # Enable caching
   ```

2. **Database Optimization**
   ```bash
   # Check database indexes
   # Analyze query performance
   # Optimize connection pooling
   ```

3. **Service Scaling**
   ```bash
   # Scale services horizontally
   # Use load balancing
   # Implement caching
   ```

### 6. Data Issues

#### Problem: Data corruption or loss
**Symptoms:**
- Missing data
- Inconsistent state
- Database errors

**Diagnosis:**
```bash
# Check database integrity
docker-compose exec postgres psql -U user -d ai_agents -c "VACUUM ANALYZE;"

# Check data consistency
docker-compose exec postgres psql -U user -d ai_agents -c "SELECT COUNT(*) FROM agents;"
```

**Solutions:**

1. **Database Recovery**
   ```bash
   # Restore from backup
   # Check transaction logs
   # Rebuild indexes
   ```

2. **Data Validation**
   ```bash
   # Validate data integrity
   # Check foreign key constraints
   # Verify data relationships
   ```

3. **Backup and Restore**
   ```bash
   # Create backup
   docker-compose exec postgres pg_dump -U user ai_agents > backup.sql
   
   # Restore backup
   docker-compose exec postgres psql -U user ai_agents < backup.sql
   ```

## Advanced Troubleshooting

### 1. Log Analysis

#### Centralized Logging
```bash
# Collect all logs
docker-compose logs --tail=1000 > system-logs.txt

# Filter by service
docker-compose logs ai-agents --tail=100

# Filter by time
docker-compose logs --since="2024-01-01T00:00:00"
```

#### Log Patterns
```bash
# Search for errors
docker-compose logs | grep -i error

# Search for specific patterns
docker-compose logs | grep "execution failed"

# Monitor logs in real-time
docker-compose logs -f
```

### 2. Network Diagnostics

#### Internal Network
```bash
# Test service-to-service communication
docker-compose exec ai-agents ping ide-bridge
docker-compose exec ai-agents nslookup postgres

# Check network configuration
docker network ls
docker network inspect multimodal-llm-stack_default
```

#### External Network
```bash
# Test external connectivity
curl -I https://api.openai.com
curl -I https://api.anthropic.com

# Check DNS resolution
nslookup api.openai.com
```

### 3. Performance Profiling

#### System Metrics
```bash
# Monitor system resources
htop
iotop
nethogs

# Check Docker resource usage
docker system df
docker system prune
```

#### Application Metrics
```bash
# Check service metrics
curl http://localhost:3000/metrics
curl http://localhost:3004/metrics

# Monitor database performance
docker-compose exec postgres psql -U user -d ai_agents -c "SELECT * FROM pg_stat_database;"
```

## Preventive Measures

### 1. Monitoring Setup

#### Health Checks
```bash
# Set up monitoring
# Use tools like Prometheus, Grafana
# Configure alerts for critical metrics
```

#### Log Monitoring
```bash
# Set up log aggregation
# Use tools like ELK stack
# Configure log-based alerts
```

### 2. Backup Strategy

#### Database Backups
```bash
# Automated backups
#!/bin/bash
docker-compose exec postgres pg_dump -U user ai_agents > backup-$(date +%Y%m%d).sql
```

#### Configuration Backups
```bash
# Backup configuration files
tar -czf config-backup-$(date +%Y%m%d).tar.gz docker-compose.yml .env
```

### 3. Security Measures

#### Regular Updates
```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Update system packages
apt update && apt upgrade
```

#### Security Scanning
```bash
# Scan for vulnerabilities
docker scan <image-name>

# Check for security issues
bandit -r services/
```

## Getting Help

### 1. Documentation
- [API Documentation](../api/README.md)
- [User Guides](../user-guides/README.md)
- [Developer Documentation](../developer/README.md)

### 2. Community Support
- [GitHub Issues](https://github.com/your-org/multimodal-llm-stack/issues)
- [Discord Community](https://discord.gg/your-community)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/multimodal-llm-stack)

### 3. Professional Support
- [Enterprise Support](https://your-company.com/support)
- [Consulting Services](https://your-company.com/consulting)
- [Training Programs](https://your-company.com/training)

## Conclusion

This troubleshooting guide provides comprehensive solutions for common issues. For issues not covered here:

1. **Check the logs** for error messages
2. **Search existing issues** on GitHub
3. **Create a new issue** with detailed information
4. **Contact support** for critical issues

Remember to:
- **Document your environment** and configuration
- **Include relevant logs** and error messages
- **Describe steps to reproduce** the issue
- **Provide system information** and versions