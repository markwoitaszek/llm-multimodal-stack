# LLM Multimodal Stack - Operations & Maintenance Guide

## 🎯 Overview

This guide provides comprehensive instructions for operating and maintaining the LLM Multimodal Stack in production environments. It covers daily operations, maintenance procedures, troubleshooting, and best practices.

## 📋 Daily Operations

### Morning Checklist
```bash
# 1. Check system status
make system-status

# 2. Verify all stacks are running
make status-core
make status-inference
make status-ai
make status-ui
make status-monitoring

# 3. Check network health
make check-network-health

# 4. Review overnight logs
make logs-monitoring | tail -100
```

### Evening Checklist
```bash
# 1. Run backup verification
make backup-status ENVIRONMENT=production

# 2. Check retention cleanup status
make retention-status ENVIRONMENT=production

# 3. Verify network conflicts
make check-network-conflicts

# 4. Review system metrics
make logs-monitoring | grep -i "error\|warning" | tail -50
```

## 🔧 Stack Management Operations

### Starting Stacks
```bash
# Start stacks in dependency order
make start-core
make start-inference
make start-ai
make start-ui
make start-monitoring

# Or start all at once (development only)
make start-dev
```

### Stopping Stacks
```bash
# Stop stacks in reverse dependency order
make stop-ui
make stop-ai
make stop-inference
make stop-monitoring
make stop-core

# Or stop all at once
make wipe
```

### Restarting Stacks
```bash
# Restart specific stack
make restart-ai

# Restart with dependency check
make restart-ai && make restart-ui
```

### Stack Status Monitoring
```bash
# Check individual stack status
make status-core
make status-inference
make status-ai
make status-ui
make status-testing
make status-monitoring

# Check all stacks
make system-status
```

## 🌐 Network Operations

### Network Health Checks
```bash
# Check for network conflicts
make check-network-conflicts

# Validate network configuration
make validate-networks

# Check network health
make check-network-health

# Cleanup orphaned networks
make cleanup-networks
```

### Network Troubleshooting
```bash
# Check network connectivity
docker network ls | grep multimodal

# Inspect specific network
docker network inspect multimodal-core-net

# Check network IP ranges
docker network inspect multimodal-core-net | grep -A 5 "IPAM"
```

## 💾 Data Management Operations

### Backup Operations
```bash
# Check backup status
make backup-status ENVIRONMENT=production

# Run full backup
make backup-full ENVIRONMENT=production

# Backup specific service
make backup-service SERVICE=postgres ENVIRONMENT=production BACKUP_TYPE=full

# List available backups
make backup-list ENVIRONMENT=production

# Verify backup integrity
make backup-verify ENVIRONMENT=production
```

### Retention Management
```bash
# Check retention status
make retention-status ENVIRONMENT=production

# Run retention cleanup
make retention-cleanup ENVIRONMENT=production

# Test retention cleanup (dry run)
make retention-test ENVIRONMENT=production

# Cleanup specific service
make retention-cleanup-service SERVICE=postgres ENVIRONMENT=production

# Show retention schedules
make retention-schedule
```

### Data Wipe Operations
```bash
# Wipe specific stack
make wipe-ai

# Wipe specific data type
make wipe-db
make wipe-cache
make wipe-models
make wipe-logs

# Wipe entire environment
make wipe-prod
```

## 🔒 Security Operations

### Credential Validation
```bash
# Validate all credentials
make validate-credentials

# Validate environment-specific credentials
make validate-credentials-dev
make validate-credentials-staging
make validate-credentials-prod

# Validate security configuration
make validate-security
```

### Security Monitoring
```bash
# Check for hardcoded credentials
make validate-security

# Review security logs
make logs-monitoring | grep -i "security\|auth\|credential"

# Check service authentication
docker logs multimodal-postgres | grep -i "auth"
```

## 🧪 Testing Operations

### Test Environment Management
```bash
# Start testing stack
make start-testing

# Run test suites
make test-allure
make test-jmeter
make test-unit
make test-integration
make test-performance
make test-api

# Generate test reports
make generate-allure-report
make serve-allure-report
```

### Test Data Management
```bash
# Clean test results
make wipe-test-results

# Backup test results
make backup-service SERVICE=test-results ENVIRONMENT=testing

# Check test environment status
make status-testing
```

## 📊 Monitoring Operations

### Monitoring Stack Management
```bash
# Start monitoring stack
make start-monitoring

# Check monitoring services
make status-monitoring

# View monitoring logs
make logs-monitoring

# Access monitoring dashboards
# Grafana: http://localhost:3000
# Kibana: http://localhost:5601
# Prometheus: http://localhost:9090
```

### Log Management
```bash
# View service logs
make logs-core
make logs-inference
make logs-ai
make logs-ui
make logs-testing
make logs-monitoring

# Search logs
make logs-monitoring | grep -i "error"
make logs-ai | grep -i "warning"

# Archive old logs
make wipe-logs
```

## 🔄 Maintenance Procedures

### Weekly Maintenance
```bash
# 1. Full system backup
make backup-full ENVIRONMENT=production

# 2. Network health check
make check-network-health

# 3. Security validation
make validate-security

# 4. Retention cleanup
make retention-cleanup ENVIRONMENT=production

# 5. Test environment refresh
make wipe-testing
make start-testing
```

### Monthly Maintenance
```bash
# 1. Comprehensive system check
make system-status
make check-network-conflicts
make validate-networks

# 2. Backup verification
make backup-verify ENVIRONMENT=production

# 3. Security audit
make validate-credentials
make validate-security

# 4. Performance review
make logs-monitoring | grep -i "performance\|slow"

# 5. Update documentation
# Review and update operational procedures
```

### Quarterly Maintenance
```bash
# 1. Full system reset (if needed)
make reset

# 2. Network reconfiguration
make cleanup-networks
make validate-networks

# 3. Backup strategy review
make backup-schedule
make retention-schedule

# 4. Security policy review
# Review and update security policies

# 5. Performance optimization
# Review resource usage and optimize
```

## 🚨 Emergency Procedures

### Service Outage Response
```bash
# 1. Check system status
make system-status

# 2. Identify affected stack
make status-core
make status-inference
make status-ai
make status-ui

# 3. Restart affected services
make restart-{affected-stack}

# 4. Check logs for errors
make logs-{affected-stack} | tail -100

# 5. Verify recovery
make status-{affected-stack}
```

### Data Recovery Procedures
```bash
# 1. Stop affected services
make stop-{affected-stack}

# 2. Restore from backup
make backup-restore SERVICE={service} ENVIRONMENT={env} FILE={backup-file}

# 3. Restart services
make start-{affected-stack}

# 4. Verify data integrity
make backup-verify ENVIRONMENT={env}
```

### Network Issues Response
```bash
# 1. Check network conflicts
make check-network-conflicts

# 2. Validate network configuration
make validate-networks

# 3. Cleanup problematic networks
make cleanup-networks

# 4. Restart affected stacks
make restart-{affected-stack}
```

## 📈 Performance Monitoring

### Resource Monitoring
```bash
# Check container resource usage
docker stats

# Check disk usage
df -h

# Check memory usage
free -h

# Check network usage
netstat -i
```

### Service Performance
```bash
# Check service response times
make logs-monitoring | grep -i "response\|latency"

# Check error rates
make logs-monitoring | grep -i "error" | wc -l

# Check throughput
make logs-monitoring | grep -i "throughput\|requests"
```

## 🔧 Configuration Management

### Environment Configuration
```bash
# Update environment variables
# Edit .env files or environment templates

# Regenerate compose files
make generate-compose

# Restart affected services
make restart-{affected-stack}
```

### Schema Updates
```bash
# Update schema
# Edit schemas/compose-schema.yaml

# Validate schema
make validate-schema

# Regenerate compose files
make generate-compose

# Restart services
make restart-{affected-stack}
```

## 📋 Operational Checklists

### Pre-Deployment Checklist
- [ ] Validate schema: `make validate-schema`
- [ ] Check network conflicts: `make check-network-conflicts`
- [ ] Validate credentials: `make validate-credentials-{env}`
- [ ] Run security checks: `make validate-security`
- [ ] Test backup procedures: `make backup-test`
- [ ] Verify monitoring: `make status-monitoring`

### Post-Deployment Checklist
- [ ] Verify all stacks: `make system-status`
- [ ] Check network health: `make check-network-health`
- [ ] Validate services: `make status-{all-stacks}`
- [ ] Test functionality: `make test-integration`
- [ ] Monitor logs: `make logs-monitoring`
- [ ] Update documentation

### Maintenance Checklist
- [ ] Run backups: `make backup-full`
- [ ] Cleanup retention: `make retention-cleanup`
- [ ] Check network health: `make check-network-health`
- [ ] Validate security: `make validate-security`
- [ ] Review logs: `make logs-monitoring`
- [ ] Update monitoring: `make status-monitoring`

## 🛠️ Troubleshooting Guide

### Common Issues and Solutions

#### Stack Won't Start
```bash
# Check dependencies
make status-core
make status-inference

# Check logs
make logs-{stack-name}

# Check network
make check-network-conflicts

# Restart dependencies
make restart-core
make restart-{stack-name}
```

#### Network Conflicts
```bash
# Check conflicts
make check-network-conflicts

# Cleanup networks
make cleanup-networks

# Restart stacks
make restart-{affected-stack}
```

#### Backup Failures
```bash
# Check backup status
make backup-status ENVIRONMENT={env}

# Check service status
make status-{service}

# Retry backup
make backup-service SERVICE={service} ENVIRONMENT={env}
```

#### Credential Issues
```bash
# Validate credentials
make validate-credentials-{env}

# Check security
make validate-security

# Regenerate secrets
make setup-secrets-{env}
```

## 📚 Best Practices

### Operational Best Practices
1. **Always check dependencies** before starting stacks
2. **Validate configuration** before deployment
3. **Monitor logs regularly** for early issue detection
4. **Run backups before** major changes
5. **Test in staging** before production changes
6. **Document all changes** and procedures

### Security Best Practices
1. **Validate credentials regularly**
2. **Check for hardcoded secrets**
3. **Monitor authentication logs**
4. **Keep security policies updated**
5. **Use least privilege principles**
6. **Regular security audits**

### Performance Best Practices
1. **Monitor resource usage**
2. **Optimize based on metrics**
3. **Scale services as needed**
4. **Clean up old data regularly**
5. **Use appropriate retention policies**
6. **Monitor network performance**

---

**Document Version**: 1.0  
**Last Updated**: October 1, 2025  
**Compatible With**: LLM Multimodal Stack v3.0
