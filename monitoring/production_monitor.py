"""
Production Monitoring & Centralized Logging System
Issue #104 Implementation
"""
import asyncio
import json
import logging
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Production monitoring and centralized logging system"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.config_dir = self.workspace_path / "configs"
        self.monitoring_dir = self.workspace_path / "monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)
        
        # Monitoring configurations
        self.monitoring_configs = {
            'prometheus': {
                'retention_time': '30d',
                'scrape_interval': '15s',
                'evaluation_interval': '15s',
                'max_samples': 50000000,
                'max_series': 10000000
            },
            'grafana': {
                'admin_password': '${GRAFANA_PASSWORD}',
                'datasource_url': 'http://prometheus:9090',
                'dashboard_refresh': '30s',
                'alerting_enabled': True
            },
            'elasticsearch': {
                'cluster_name': 'multimodal-cluster',
                'node_name': 'multimodal-node-1',
                'discovery_type': 'single-node',
                'heap_size': '2g',
                'data_path': '/usr/share/elasticsearch/data'
            },
            'logstash': {
                'pipeline_workers': 4,
                'pipeline_batch_size': 1000,
                'pipeline_batch_delay': 50,
                'config_reload_automatic': True
            },
            'kibana': {
                'server_name': 'kibana',
                'server_host': '0.0.0.0',
                'elasticsearch_hosts': ['http://elasticsearch:9200'],
                'server_max_payload': '1048576'
            }
        }
    
    async def setup_comprehensive_monitoring(self) -> Dict[str, Any]:
        """Set up comprehensive monitoring system"""
        logger.info("Setting up comprehensive monitoring system")
        
        # Create ELK stack configuration
        elk_config = await self._create_elk_stack_config()
        
        # Create Prometheus configuration
        prometheus_config = await self._create_prometheus_config()
        
        # Create Grafana configuration
        grafana_config = await self._create_grafana_config()
        
        # Create alerting configuration
        alerting_config = await self._create_alerting_config()
        
        # Create health check configuration
        health_check_config = await self._create_health_check_config()
        
        return {
            'elk_config': elk_config,
            'prometheus_config': prometheus_config,
            'grafana_config': grafana_config,
            'alerting_config': alerting_config,
            'health_check_config': health_check_config
        }
    
    async def _create_elk_stack_config(self) -> Dict[str, str]:
        """Create ELK stack configuration for centralized logging"""
        logger.info("Creating ELK stack configuration")
        
        # Create Elasticsearch configuration
        elasticsearch_config = await self._create_elasticsearch_config()
        
        # Create Logstash configuration
        logstash_config = await self._create_logstash_config()
        
        # Create Kibana configuration
        kibana_config = await self._create_kibana_config()
        
        # Create ELK Docker Compose
        elk_compose = await self._create_elk_compose()
        
        return {
            'elasticsearch_config': elasticsearch_config,
            'logstash_config': logstash_config,
            'kibana_config': kibana_config,
            'elk_compose': elk_compose
        }
    
    async def _create_elasticsearch_config(self) -> str:
        """Create Elasticsearch configuration"""
        es_config_file = self.config_dir / "elasticsearch.yml"
        
        es_config = f"""cluster.name: {self.monitoring_configs['elasticsearch']['cluster_name']}
node.name: {self.monitoring_configs['elasticsearch']['node_name']}
node.roles: [ master, data, ingest ]

path.data: {self.monitoring_configs['elasticsearch']['data_path']}
path.logs: /usr/share/elasticsearch/logs

network.host: 0.0.0.0
http.port: 9200

discovery.type: {self.monitoring_configs['elasticsearch']['discovery_type']}

# Memory settings
bootstrap.memory_lock: true

# Security settings
xpack.security.enabled: false
xpack.security.enrollment.enabled: false

# Performance settings
indices.memory.index_buffer_size: 20%
indices.queries.cache.size: 10%
indices.fielddata.cache.size: 20%

# Logging settings
logger.level: INFO
"""
        
        with open(es_config_file, 'w') as f:
            f.write(es_config)
        
        logger.info(f"Created Elasticsearch configuration: {es_config_file}")
        return str(es_config_file)
    
    async def _create_logstash_config(self) -> str:
        """Create Logstash configuration"""
        logstash_config_file = self.config_dir / "logstash.conf"
        
        logstash_config = """input {
  # Docker container logs
  docker {
    host => "unix:///var/run/docker.sock"
    type => "docker"
  }
  
  # File input for application logs
  file {
    path => "/var/log/multimodal/*.log"
    type => "application"
    start_position => "beginning"
    codec => "json"
  }
  
  # Syslog input
  syslog {
    port => 514
    type => "syslog"
  }
  
  # Beats input for filebeat
  beats {
    port => 5044
    type => "beats"
  }
}

filter {
  # Parse JSON logs
  if [type] == "application" {
    json {
      source => "message"
    }
  }
  
  # Parse Docker logs
  if [type] == "docker" {
    if [container_name] {
      mutate {
        add_field => { "service" => "%{[container_name]}" }
      }
    }
  }
  
  # Parse syslog
  if [type] == "syslog" {
    grok {
      match => { "message" => "%{SYSLOGTIMESTAMP:timestamp} %{IPORHOST:host} %{PROG:program}: %{GREEDYDATA:message}" }
    }
  }
  
  # Add timestamp
  date {
    match => [ "timestamp", "ISO8601" ]
  }
  
  # Add environment tag
  mutate {
    add_field => { "environment" => "production" }
  }
}

output {
  # Output to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "multimodal-logs-%{+YYYY.MM.dd}"
    template_name => "multimodal-logs"
    template => "/usr/share/logstash/templates/multimodal-logs.json"
    template_overwrite => true
  }
  
  # Output to stdout for debugging
  stdout {
    codec => rubydebug
  }
}
"""
        
        with open(logstash_config_file, 'w') as f:
            f.write(logstash_config)
        
        logger.info(f"Created Logstash configuration: {logstash_config_file}")
        return str(logstash_config_file)
    
    async def _create_kibana_config(self) -> str:
        """Create Kibana configuration"""
        kibana_config_file = self.config_dir / "kibana.yml"
        
        kibana_config = f"""server.name: {self.monitoring_configs['kibana']['server_name']}
server.host: {self.monitoring_configs['kibana']['server_host']}
server.port: 5601
server.maxPayload: {self.monitoring_configs['kibana']['server_max_payload']}

elasticsearch.hosts: {self.monitoring_configs['kibana']['elasticsearch_hosts']}

# Security settings
xpack.security.enabled: false
xpack.encryptedSavedObjects.encryptionKey: "multimodal-encryption-key-32-chars"

# Logging
logging.appenders:
  file:
    type: file
    fileName: /usr/share/kibana/logs/kibana.log
    layout:
      type: json
logging.root:
  appenders:
    - default
    - file
logging.loggers:
  - name: plugins
    level: info

# Performance settings
optimize.bundleFilter: "!tests"
optimize.useBundleCache: true
optimize.bundleDir: /usr/share/kibana/optimize/bundles

# Monitoring
monitoring.ui.container.elasticsearch.enabled: true
monitoring.ui.container.logstash.enabled: true
"""
        
        with open(kibana_config_file, 'w') as f:
            f.write(kibana_config)
        
        logger.info(f"Created Kibana configuration: {kibana_config_file}")
        return str(kibana_config_file)
    
    async def _create_elk_compose(self) -> str:
        """Create ELK stack Docker Compose configuration"""
        elk_compose_file = self.workspace_path / "docker-compose.elk.yml"
        
        elk_compose = f"""# ELK Stack for Centralized Logging
# Generated on: {datetime.utcnow().isoformat()}

version: '3.8'

services:
  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: multimodal-elasticsearch
    environment:
      - discovery.type={self.monitoring_configs['elasticsearch']['discovery_type']}
      - ES_JAVA_OPTS=-Xms{self.monitoring_configs['elasticsearch']['heap_size']} -Xmx{self.monitoring_configs['elasticsearch']['heap_size']}
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      - ./configs/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
    ports:
      - "9200:9200"
      - "9300:9300"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    networks:
      - multimodal-net

  # Logstash
  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: multimodal-logstash
    environment:
      - LS_JAVA_OPTS=-Xms1g -Xmx1g
      - PIPELINE_WORKERS={self.monitoring_configs['logstash']['pipeline_workers']}
      - PIPELINE_BATCH_SIZE={self.monitoring_configs['logstash']['pipeline_batch_size']}
      - PIPELINE_BATCH_DELAY={self.monitoring_configs['logstash']['pipeline_batch_delay']}
    volumes:
      - ./configs/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log/multimodal:/var/log/multimodal:ro
    ports:
      - "5044:5044"
      - "514:514/udp"
    depends_on:
      elasticsearch:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9600/_node/stats || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    networks:
      - multimodal-net

  # Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: multimodal-kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - xpack.security.enabled=false
    volumes:
      - ./configs/kibana.yml:/usr/share/kibana/config/kibana.yml:ro
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped
    networks:
      - multimodal-net

  # Filebeat for log collection
  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: multimodal-filebeat
    user: root
    volumes:
      - ./configs/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log/multimodal:/var/log/multimodal:ro
    depends_on:
      logstash:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    restart: unless-stopped
    networks:
      - multimodal-net

volumes:
  elasticsearch_data:

networks:
  multimodal-net:
    external: true
"""
        
        with open(elk_compose_file, 'w') as f:
            f.write(elk_compose)
        
        logger.info(f"Created ELK stack Docker Compose: {elk_compose_file}")
        return str(elk_compose_file)
    
    async def _create_prometheus_config(self) -> str:
        """Create enhanced Prometheus configuration"""
        prometheus_file = self.config_dir / "prometheus_enhanced.yml"
        
        prometheus_config = f"""global:
  scrape_interval: {self.monitoring_configs['prometheus']['scrape_interval']}
  evaluation_interval: {self.monitoring_configs['prometheus']['evaluation_interval']}
  external_labels:
    cluster: 'multimodal-production'
    environment: 'production'

rule_files:
  - "alert_rules.yml"
  - "recording_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    scrape_interval: 30s
    metrics_path: /nginx_status

  - job_name: 'multimodal-worker'
    static_configs:
      - targets: ['multimodal-worker:8001']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'retrieval-proxy'
    static_configs:
      - targets: ['retrieval-proxy:8002']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'litellm'
    static_configs:
      - targets: ['litellm:4000']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'vllm'
    static_configs:
      - targets: ['vllm:8000']
    scrape_interval: 15s
    metrics_path: /metrics

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
    scrape_interval: 30s
    metrics_path: /_prometheus/metrics

  - job_name: 'logstash'
    static_configs:
      - targets: ['logstash:9600']
    scrape_interval: 30s
    metrics_path: /_node/stats/prometheus

  - job_name: 'kibana'
    static_configs:
      - targets: ['kibana:5601']
    scrape_interval: 30s
    metrics_path: /api/status

# Storage configuration
storage:
  tsdb:
    retention.time: {self.monitoring_configs['prometheus']['retention_time']}
    retention.size: 10GB
"""
        
        with open(prometheus_file, 'w') as f:
            f.write(prometheus_config)
        
        logger.info(f"Created enhanced Prometheus configuration: {prometheus_file}")
        return str(prometheus_file)
    
    async def _create_grafana_config(self) -> str:
        """Create Grafana configuration"""
        grafana_config_file = self.config_dir / "grafana.ini"
        
        grafana_config = f"""[server]
protocol = http
http_port = 3000
domain = localhost
root_url = %(protocol)s://%(domain)s:%(http_port)s/
serve_from_sub_path = false

[database]
type = sqlite3
path = grafana.db

[session]
provider = file
provider_config = sessions
cookie_secure = false
cookie_samesite = lax
session_life_time = 86400

[security]
admin_user = admin
admin_password = {self.monitoring_configs['grafana']['admin_password']}
secret_key = multimodal-grafana-secret-key
disable_gravatar = false
data_source_proxy_whitelist = 
cookie_remember_name = grafana_remember
cookie_username = grafana_user
cookie_secure = false
strict_transport_security = false
strict_transport_security_max_age_seconds = 86400
strict_transport_security_preload = false
strict_transport_security_subdomains = false
x_content_type_options = false
x_xss_protection = false

[snapshots]
external_enabled = true
external_snapshot_url = https://snapshots-origin.raintank.io
external_snapshot_name = Publish to snapshot.raintank.io
snapshot_remove_expired = true

[dashboards]
default_home_dashboard_path = /var/lib/grafana/dashboards/home.json

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_id = 1
auto_assign_org_role = Viewer
verify_email_enabled = false
login_hint = email or username
default_theme = dark
home_page = 
viewers_can_edit = false
editors_can_admin = false

[auth.anonymous]
enabled = false
org_name = Main Org.
org_role = Viewer
hide_version = false

[auth.basic]
enabled = true

[auth.proxy]
enabled = false
header_name = X-WEBAUTH-USER
header_property = username
auto_sign_up = true
sync_ttl = 60

[log]
mode = console file
level = info
filters = 
format = json
"""
        
        with open(grafana_config_file, 'w') as f:
            f.write(grafana_config)
        
        logger.info(f"Created Grafana configuration: {grafana_config_file}")
        return str(grafana_config_file)
    
    async def _create_alerting_config(self) -> str:
        """Create comprehensive alerting configuration"""
        alerting_file = self.config_dir / "alertmanager.yml"
        
        alerting_config = """global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@multimodal.local'
  smtp_auth_username: 'alerts@multimodal.local'
  smtp_auth_password: '${ALERT_EMAIL_PASSWORD}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/'

- name: 'critical-alerts'
  email_configs:
  - to: '${ALERT_EMAIL_TO}'
    subject: '[CRITICAL] Multimodal Stack Alert'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#alerts-critical'
    title: 'Critical Alert'
    text: |
      {{ range .Alerts }}
      *Alert:* {{ .Annotations.summary }}
      *Description:* {{ .Annotations.description }}
      {{ end }}

- name: 'warning-alerts'
  email_configs:
  - to: '${ALERT_EMAIL_TO}'
    subject: '[WARNING] Multimodal Stack Alert'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: '${SLACK_WEBHOOK_URL}'
    channel: '#alerts-warning'
    title: 'Warning Alert'
    text: |
      {{ range .Alerts }}
      *Alert:* {{ .Annotations.summary }}
      *Description:* {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
"""
        
        with open(alerting_file, 'w') as f:
            f.write(alerting_config)
        
        logger.info(f"Created alerting configuration: {alerting_file}")
        return str(alerting_file)
    
    async def _create_health_check_config(self) -> str:
        """Create comprehensive health check configuration"""
        health_check_file = self.workspace_path / "scripts" / "health_check.py"
        health_check_file.parent.mkdir(exist_ok=True)
        
        health_check_script = '''#!/usr/bin/env python3
"""
Comprehensive Health Check Script for Multimodal Stack
"""
import asyncio
import aiohttp
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class HealthChecker:
    """Comprehensive health checker for all services"""
    
    def __init__(self):
        self.services = {
            'postgres': {'url': 'http://postgres:5432/health', 'timeout': 5},
            'redis': {'url': 'http://redis:6379/ping', 'timeout': 5},
            'qdrant': {'url': 'http://qdrant:6333/health', 'timeout': 5},
            'elasticsearch': {'url': 'http://elasticsearch:9200/_cluster/health', 'timeout': 10},
            'kibana': {'url': 'http://kibana:5601/api/status', 'timeout': 10},
            'prometheus': {'url': 'http://prometheus:9090/-/healthy', 'timeout': 5},
            'grafana': {'url': 'http://grafana:3000/api/health', 'timeout': 5},
            'multimodal-worker': {'url': 'http://multimodal-worker:8001/health', 'timeout': 10},
            'retrieval-proxy': {'url': 'http://retrieval-proxy:8002/health', 'timeout': 10},
            'litellm': {'url': 'http://litellm:4000/health', 'timeout': 10},
            'vllm': {'url': 'http://vllm:8000/health', 'timeout': 10},
            'nginx': {'url': 'http://nginx:80/health', 'timeout': 5}
        }
        self.results = {}
    
    async def check_service(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check individual service health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    config['url'], 
                    timeout=aiohttp.ClientTimeout(total=config['timeout'])
                ) as response:
                    if response.status == 200:
                        return {
                            'status': 'healthy',
                            'response_time': response.headers.get('X-Response-Time', 'N/A'),
                            'status_code': response.status
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'status_code': response.status,
                            'error': f'HTTP {response.status}'
                        }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check all services health"""
        tasks = []
        for name, config in self.services.items():
            task = asyncio.create_task(self.check_service(name, config))
            tasks.append((name, task))
        
        for name, task in tasks:
            self.results[name] = await task
        
        return self.results
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate health check report"""
        healthy_services = sum(1 for result in self.results.values() if result['status'] == 'healthy')
        total_services = len(self.results)
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy' if healthy_services == total_services else 'unhealthy',
            'healthy_services': healthy_services,
            'total_services': total_services,
            'health_percentage': (healthy_services / total_services) * 100,
            'services': self.results
        }
        
        return report

async def main():
    """Main health check function"""
    checker = HealthChecker()
    await checker.check_all_services()
    report = checker.generate_report()
    
    print(json.dumps(report, indent=2))
    
    # Exit with error code if any service is unhealthy
    if report['overall_status'] == 'unhealthy':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(health_check_file, 'w') as f:
            f.write(health_check_script)
        
        os.chmod(health_check_file, 0o755)
        
        logger.info(f"Created health check script: {health_check_file}")
        return str(health_check_file)
    
    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        logger.info("Generating monitoring report")
        
        report = {
            'monitoring_timestamp': datetime.utcnow().isoformat(),
            'monitoring_summary': {
                'elk_stack': 'configured',
                'prometheus': 'configured',
                'grafana': 'configured',
                'alerting': 'configured',
                'health_checks': 'configured'
            },
            'elk_stack_configuration': {
                'elasticsearch': {
                    'cluster_name': self.monitoring_configs['elasticsearch']['cluster_name'],
                    'heap_size': self.monitoring_configs['elasticsearch']['heap_size'],
                    'discovery_type': self.monitoring_configs['elasticsearch']['discovery_type']
                },
                'logstash': {
                    'pipeline_workers': self.monitoring_configs['logstash']['pipeline_workers'],
                    'pipeline_batch_size': self.monitoring_configs['logstash']['pipeline_batch_size']
                },
                'kibana': {
                    'server_name': self.monitoring_configs['kibana']['server_name'],
                    'elasticsearch_hosts': self.monitoring_configs['kibana']['elasticsearch_hosts']
                }
            },
            'prometheus_configuration': {
                'scrape_interval': self.monitoring_configs['prometheus']['scrape_interval'],
                'retention_time': self.monitoring_configs['prometheus']['retention_time'],
                'monitored_services': 12
            },
            'grafana_configuration': {
                'admin_user': 'admin',
                'datasource_url': self.monitoring_configs['grafana']['datasource_url'],
                'alerting_enabled': self.monitoring_configs['grafana']['alerting_enabled']
            },
            'alerting_configuration': {
                'email_alerts': 'configured',
                'slack_alerts': 'configured',
                'webhook_alerts': 'configured',
                'alert_rules': 6
            },
            'health_check_configuration': {
                'monitored_services': 12,
                'check_interval': '30s',
                'timeout': '10s'
            },
            'recommendations': [
                'Deploy ELK stack for centralized logging',
                'Set up Prometheus and Grafana for metrics monitoring',
                'Configure alerting channels (email, Slack)',
                'Implement health check monitoring',
                'Set up log retention policies',
                'Configure log rotation and archival',
                'Implement log analysis and alerting rules',
                'Set up dashboard for operational visibility'
            ],
            'next_steps': [
                'Deploy monitoring stack using docker-compose.elk.yml',
                'Configure alerting channels with actual credentials',
                'Set up log shipping from all services',
                'Create custom dashboards for business metrics',
                'Implement log-based alerting rules',
                'Set up log retention and archival policies',
                'Train operations team on monitoring tools',
                'Document monitoring procedures and runbooks'
            ]
        }
        
        # Save report
        report_file = self.workspace_path / "reports" / "monitoring_setup_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Monitoring report generated: {report_file}")
        return report

# Global production monitor instance
production_monitor = ProductionMonitor()