#!/usr/bin/env python3
"""
Production Deployment Script
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class ProductionDeployer:
    """Production deployment orchestrator"""
    
    def __init__(self):
        self.workspace_path = Path(__file__).parent.parent
        self.environments = ['development', 'staging', 'production']
    
    async def deploy(self, environment: str, version: str = None):
        """Deploy to specified environment"""
        print(f"Deploying to {environment} environment...")
        
        if version:
            print(f"Deploying version: {version}")
        
        # Build images
        await self._build_images(version)
        
        # Deploy to environment
        await self._deploy_environment(environment)
        
        # Health check
        await self._health_check(environment)
        
        print(f"✅ Deployment to {environment} completed successfully")
    
    async def _build_images(self, version: str = None):
        """Build Docker images"""
        print("Building Docker images...")
        
        tag = version or "latest"
        
        # Build multimodal-worker
        cmd = [
            "docker", "build",
            "-t", f"multimodal-worker:{tag}",
            "-f", "services/multimodal-worker/Dockerfile",
            "services/multimodal-worker/"
        ]
        
        result = subprocess.run(cmd, cwd=self.workspace_path)
        if result.returncode != 0:
            raise Exception("Failed to build multimodal-worker image")
        
        # Tag as latest
        if version:
            subprocess.run([
                "docker", "tag",
                f"multimodal-worker:{tag}",
                "multimodal-worker:latest"
            ])
        
        print("✅ Docker images built successfully")
    
    async def _deploy_environment(self, environment: str):
        """Deploy to specific environment"""
        print(f"Deploying to {environment}...")
        
        compose_file = f"docker-compose.{environment}.yml"
        if not (self.workspace_path / compose_file).exists():
            compose_file = "docker-compose.yml"
        
        cmd = [
            "docker-compose",
            "-f", compose_file,
            "up", "-d", "--force-recreate"
        ]
        
        result = subprocess.run(cmd, cwd=self.workspace_path)
        if result.returncode != 0:
            raise Exception(f"Failed to deploy to {environment}")
        
        print(f"✅ Deployed to {environment} successfully")
    
    async def _health_check(self, environment: str):
        """Perform health check after deployment"""
        print("Performing health check...")
        
        # Wait for services to start
        await asyncio.sleep(30)
        
        # Run health check script
        cmd = ["python3", "scripts/health_check.py"]
        result = subprocess.run(cmd, cwd=self.workspace_path)
        
        if result.returncode != 0:
            raise Exception("Health check failed")
        
        print("✅ Health check passed")

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy to production")
    parser.add_argument("--environment", choices=["development", "staging", "production"],
                       required=True, help="Target environment")
    parser.add_argument("--version", help="Version to deploy")
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer()
    
    try:
        await deployer.deploy(args.environment, args.version)
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
