# LLM Multimodal Stack - Troubleshooting & Debugging Guide

## 🎯 Overview

This guide provides comprehensive troubleshooting procedures for common issues in the LLM Multimodal Stack. It includes diagnostic commands, error resolution steps, and debugging techniques.

## 🔍 Diagnostic Commands

### System Status Diagnostics
```bash
# Overall system status
make system-status

# Individual stack status
make status-core
make status-inference
make status-ai
make status-ui
make status-testing
make status-monitoring

# Service health check
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Network Diagnostics
```bash
# Check network conflicts
make check-network-conflicts

# Validate network configuration
make validate-networks

# Check network health
make check-network-health

# List all networks
docker network ls | grep multimodal

# Inspect specific network
docker network inspect multimodal-core-net
```

### Log Analysis
```bash
# View recent logs
make logs-{stack-name} | tail -50

# Search for errors
make logs-{stack-name} | grep -i "error"

# Search for warnings
make logs-{stack-name} | grep -i "warning"

# Search for specific patterns
make logs-{stack-name} | grep -i "connection\|timeout\|failed"
```

## 🚨 Common Issues and Solutions

### 1. Stack Startup Issues

#### Problem: Stack fails to start
**Symptoms:**
- `make start-{stack}` fails
- Services show as "Exited" status
- Error messages in logs

**Diagnostic Steps:**
```bash
# 1. Check stack status
make status-{stack-name}

# 2. Check dependencies
make status-core
make status-inference

# 3. Check logs
make logs-{stack-name}

# 4. Check network
make check-network-conflicts
```

**Solutions:**
```bash
# Solution 1: Start dependencies first
make start-core
make start-inference
make start-{stack-name}

# Solution 2: Restart dependencies
make restart-core
make restart-{stack-name}

# Solution 3: Check configuration
make validate-schema
make generate-compose
make restart-{stack-name}
```

#### Problem: Service dependency issues
**Symptoms:**
- Services start but fail to connect
- Connection refused errors
- Timeout errors

**Diagnostic Steps:**
```bash
# 1. Check service connectivity
docker exec -it multimodal-postgres psql -U postgres -c "SELECT 1;"

# 2. Check network connectivity
docker exec -it multimodal-{service} ping multimodal-postgres

# 3. Check service logs
make logs-{service-name}
```

**Solutions:**
```bash
# Solution 1: Restart in correct order
make restart-core
sleep 10
make restart-inference
sleep 10
make restart-ai

# Solution 2: Check network configuration
make validate-networks
make restart-{stack-name}
```

### 2. Network Issues

#### Problem: Network conflicts
**Symptoms:**
- `make start-{stack}` fails with network error
- "Pool overlaps with other one" error
- Network creation fails

**Diagnostic Steps:**
```bash
# 1. Check for conflicts
make check-network-conflicts

# 2. List existing networks
docker network ls

# 3. Check network configuration
make validate-networks
```

**Solutions:**
```bash
# Solution 1: Cleanup conflicting networks
make cleanup-networks

# Solution 2: Restart with clean networks
make wipe
make start-{stack-name}

# Solution 3: Manual network cleanup
docker network prune -f
make start-{stack-name}
```

#### Problem: Network connectivity issues
**Symptoms:**
- Services can't communicate
- Connection timeouts
- DNS resolution failures

**Diagnostic Steps:**
```bash
# 1. Check network health
make check-network-health

# 2. Test connectivity
docker exec -it multimodal-{service} ping multimodal-{target-service}

# 3. Check DNS resolution
docker exec -it multimodal-{service} nslookup multimodal-{target-service}
```

**Solutions:**
```bash
# Solution 1: Restart network stack
make restart-{stack-name}

# Solution 2: Recreate networks
make wipe-{stack-name}
make start-{stack-name}

# Solution 3: Check network configuration
make validate-networks
```

### 3. Database Issues

#### Problem: PostgreSQL connection failures
**Symptoms:**
- "Connection refused" errors
- "Authentication failed" errors
- Database startup failures

**Diagnostic Steps:**
```bash
# 1. Check PostgreSQL status
make status-core
docker logs multimodal-postgres

# 2. Test connection
docker exec -it multimodal-postgres psql -U postgres -c "SELECT 1;"

# 3. Check credentials
make validate-credentials-dev
```

**Solutions:**
```bash
# Solution 1: Restart PostgreSQL
make restart-core

# Solution 2: Check credentials
make validate-credentials-dev
make setup-secrets-dev
make restart-core

# Solution 3: Reset database
make wipe-db
make start-core
```

#### Problem: Redis connection issues
**Symptoms:**
- Redis connection timeouts
- Cache failures
- Session storage issues

**Diagnostic Steps:**
```bash
# 1. Check Redis status
docker logs multimodal-redis

# 2. Test Redis connection
docker exec -it multimodal-redis redis-cli ping

# 3. Check Redis configuration
docker exec -it multimodal-redis redis-cli config get "*"
```

**Solutions:**
```bash
# Solution 1: Restart Redis
make restart-core

# Solution 2: Clear Redis cache
make wipe-cache
make restart-core

# Solution 3: Check Redis logs
make logs-core | grep redis
```

### 4. GPU Issues

#### Problem: GPU not detected
**Symptoms:**
- "No CUDA GPUs available" error
- GPU services fail to start
- CUDA_VISIBLE_DEVICES empty

**Diagnostic Steps:**
```bash
# 1. Check GPU detection
make detect-gpu

# 2. Check GPU configuration
make configure-gpu

# 3. Check GPU environment variables
echo $CUDA_VISIBLE_DEVICES
echo $GPU_COUNT
```

**Solutions:**
```bash
# Solution 1: Reconfigure GPU
make configure-gpu
make restart-inference

# Solution 2: Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Solution 3: Manual GPU configuration
export CUDA_VISIBLE_DEVICES=0,1
export GPU_COUNT=2
make restart-inference
```

#### Problem: vLLM startup failures
**Symptoms:**
- vLLM container exits immediately
- GPU memory errors
- Model loading failures

**Diagnostic Steps:**
```bash
# 1. Check vLLM logs
make logs-inference | grep vllm

# 2. Check GPU memory
nvidia-smi

# 3. Check vLLM configuration
docker exec -it multimodal-vllm env | grep VLLM
```

**Solutions:**
```bash
# Solution 1: Adjust GPU memory
export VLLM_GPU_MEMORY_UTILIZATION=0.8
make restart-inference

# Solution 2: Check model path
make logs-inference | grep "model"
make restart-inference

# Solution 3: Reset vLLM cache
make wipe-models
make restart-inference
```

### 5. Backup and Retention Issues

#### Problem: Backup failures
**Symptoms:**
- Backup commands fail
- Backup files not created
- Backup verification failures

**Diagnostic Steps:**
```bash
# 1. Check backup status
make backup-status ENVIRONMENT=development

# 2. Check service status
make status-{service-name}

# 3. Check backup logs
./scripts/manage-backups.sh backup-service postgres development full
```

**Solutions:**
```bash
# Solution 1: Check service availability
make status-core
make backup-service SERVICE=postgres ENVIRONMENT=development

# Solution 2: Check backup directory permissions
ls -la backups/
chmod 755 backups/

# Solution 3: Manual backup
docker exec multimodal-postgres pg_dump -U postgres multimodal > backup.sql
```

#### Problem: Retention cleanup failures
**Symptoms:**
- Retention cleanup fails
- Old data not cleaned up
- Cleanup script errors

**Diagnostic Steps:**
```bash
# 1. Check retention status
make retention-status ENVIRONMENT=development

# 2. Test retention cleanup
make retention-test ENVIRONMENT=development

# 3. Check retention logs
./scripts/manage-retention.sh retention-cleanup development
```

**Solutions:**
```bash
# Solution 1: Check service status
make status-{service-name}
make retention-cleanup ENVIRONMENT=development

# Solution 2: Manual cleanup
make wipe-cache
make wipe-logs

# Solution 3: Check retention policies
cat configs/retention-policies.yaml
```

### 6. Security Issues

#### Problem: Credential validation failures
**Symptoms:**
- "Hardcoded defaults found" error
- Credential validation fails
- Security checks fail

**Diagnostic Steps:**
```bash
# 1. Check security validation
make validate-security

# 2. Check credential validation
make validate-credentials-dev

# 3. Check for hardcoded credentials
grep -r "postgres:postgres" services/
```

**Solutions:**
```bash
# Solution 1: Fix hardcoded credentials
# Edit service configuration files
make validate-security

# Solution 2: Regenerate secrets
make setup-secrets-dev
make validate-credentials-dev

# Solution 3: Check environment variables
make validate-credentials-dev
```

#### Problem: Authentication failures
**Symptoms:**
- "Authentication failed" errors
- Login failures
- Permission denied errors

**Diagnostic Steps:**
```bash
# 1. Check authentication logs
make logs-{service-name} | grep -i "auth\|login\|permission"

# 2. Check credential configuration
make validate-credentials-{env}

# 3. Test authentication
docker exec -it multimodal-postgres psql -U postgres -c "SELECT 1;"
```

**Solutions:**
```bash
# Solution 1: Check credentials
make validate-credentials-{env}
make setup-secrets-{env}

# Solution 2: Restart services
make restart-{stack-name}

# Solution 3: Check user permissions
make logs-{service-name} | grep -i "user\|permission"
```

## 🔧 Advanced Debugging

### Container Debugging
```bash
# Enter container for debugging
docker exec -it multimodal-{service-name} /bin/bash

# Check container environment
docker exec -it multimodal-{service-name} env

# Check container processes
docker exec -it multimodal-{service-name} ps aux

# Check container network
docker exec -it multimodal-{service-name} netstat -tlnp
```

### Service Debugging
```bash
# Check service configuration
docker exec -it multimodal-{service-name} cat /app/config.py

# Check service logs in real-time
docker logs -f multimodal-{service-name}

# Check service health
docker exec -it multimodal-{service-name} curl -f http://localhost:8080/health
```

### Network Debugging
```bash
# Check network connectivity
docker exec -it multimodal-{service-name} ping multimodal-{target-service}

# Check DNS resolution
docker exec -it multimodal-{service-name} nslookup multimodal-{target-service}

# Check port connectivity
docker exec -it multimodal-{service-name} telnet multimodal-{target-service} 5432
```

### Database Debugging
```bash
# Connect to PostgreSQL
docker exec -it multimodal-postgres psql -U postgres -d multimodal

# Check database connections
docker exec -it multimodal-postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Check database size
docker exec -it multimodal-postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('multimodal'));"
```

## 📊 Performance Debugging

### Resource Monitoring
```bash
# Check container resource usage
docker stats

# Check system resources
top
htop
iostat
vmstat

# Check disk usage
df -h
du -sh /var/lib/docker/
```

### Performance Analysis
```bash
# Check service response times
make logs-monitoring | grep -i "response\|latency"

# Check error rates
make logs-monitoring | grep -i "error" | wc -l

# Check throughput
make logs-monitoring | grep -i "throughput\|requests"
```

### Memory Debugging
```bash
# Check memory usage
free -h
docker stats --no-stream

# Check memory leaks
docker exec -it multimodal-{service-name} cat /proc/meminfo

# Check swap usage
swapon -s
```

## 🚨 Emergency Recovery

### Complete System Recovery
```bash
# 1. Stop all services
make wipe

# 2. Clean up everything
docker system prune -a -f
docker volume prune -f
docker network prune -f

# 3. Restart from scratch
make setup
make start-dev
```

### Data Recovery
```bash
# 1. Stop affected services
make stop-{affected-stack}

# 2. Restore from backup
make backup-restore SERVICE={service} ENVIRONMENT={env} FILE={backup-file}

# 3. Restart services
make start-{affected-stack}

# 4. Verify recovery
make status-{affected-stack}
```

### Network Recovery
```bash
# 1. Stop all services
make wipe

# 2. Clean up networks
docker network prune -f

# 3. Restart services
make start-core
make start-inference
make start-ai
make start-ui
```

## 📋 Debugging Checklist

### Pre-Debugging Checklist
- [ ] Document the issue and symptoms
- [ ] Check system status: `make system-status`
- [ ] Review recent changes
- [ ] Check logs for errors: `make logs-{stack-name}`
- [ ] Verify network health: `make check-network-health`

### During Debugging
- [ ] Use diagnostic commands
- [ ] Check service dependencies
- [ ] Verify configuration
- [ ] Test connectivity
- [ ] Monitor resource usage

### Post-Debugging
- [ ] Document the solution
- [ ] Test the fix
- [ ] Monitor for recurrence
- [ ] Update documentation
- [ ] Share knowledge with team

## 🛠️ Debugging Tools

### Built-in Tools
```bash
# System status
make system-status

# Network diagnostics
make check-network-conflicts
make validate-networks
make check-network-health

# Log analysis
make logs-{stack-name}

# Service status
make status-{stack-name}
```

### External Tools
```bash
# Container inspection
docker inspect multimodal-{service-name}

# Network inspection
docker network inspect multimodal-{network-name}

# Volume inspection
docker volume inspect multimodal-{volume-name}

# Image inspection
docker image inspect multimodal-{service-name}
```

### Monitoring Tools
```bash
# Resource monitoring
docker stats
htop
iostat

# Network monitoring
netstat -tlnp
ss -tlnp

# Log monitoring
tail -f logs/backup-$(date +%Y%m%d).log
```

## 📚 Best Practices

### Debugging Best Practices
1. **Start with system status** - Always check overall system health first
2. **Check dependencies** - Verify that all required services are running
3. **Review logs** - Look for error messages and warnings
4. **Test connectivity** - Verify network and service connectivity
5. **Document findings** - Keep track of what you've tried and what worked
6. **Use incremental approach** - Make small changes and test each one

### Prevention Best Practices
1. **Regular monitoring** - Check system health regularly
2. **Proactive maintenance** - Run maintenance procedures before issues occur
3. **Backup verification** - Regularly test backup and restore procedures
4. **Security validation** - Regularly check for security issues
5. **Performance monitoring** - Monitor resource usage and performance
6. **Documentation updates** - Keep troubleshooting guides updated

---

**Document Version**: 1.0  
**Last Updated**: October 1, 2025  
**Compatible With**: LLM Multimodal Stack v3.0
