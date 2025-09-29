#!/usr/bin/env python3
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
