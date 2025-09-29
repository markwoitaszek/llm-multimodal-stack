"""
Allure Framework Implementation - Professional Test Reporting & Analytics
Issue #108 Implementation
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
import shutil

logger = logging.getLogger(__name__)

class AllureIntegration:
    """Allure Framework integration for professional test reporting"""
    
    def __init__(self, workspace_path: str = "/workspace"):
        self.workspace_path = Path(workspace_path)
        self.testing_dir = self.workspace_path / "testing"
        self.config_dir = self.workspace_path / "configs"
        self.reports_dir = self.workspace_path / "reports"
        self.allure_dir = self.workspace_path / "allure"
        
        # Create directories
        for dir_path in [self.testing_dir, self.allure_dir, self.reports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Allure configuration
        self.allure_config = {
            'allure': {
                'version': '2.24.0',
                'results_dir': 'allure-results',
                'report_dir': 'allure-report',
                'history_dir': 'allure-history',
                'server_port': 8080,
                'server_host': '0.0.0.0'
            },
            'pytest': {
                'allure_dir': 'allure-results',
                'allure_clean': True,
                'allure_attach': True,
                'allure_links': True
            },
            'reporting': {
                'title': 'LLM Multimodal Stack Test Report',
                'description': 'Comprehensive test reporting for the LLM Multimodal Stack',
                'logo': 'https://example.com/logo.png',
                'theme': 'default',
                'language': 'en'
            }
        }
    
    async def setup_allure_framework(self) -> Dict[str, Any]:
        """Set up Allure Framework for test reporting"""
        logger.info("Setting up Allure Framework for test reporting")
        
        # Create Allure configuration
        allure_config = await self._create_allure_config()
        
        # Update pytest configuration
        pytest_config = await self._update_pytest_config()
        
        # Create Allure Docker setup
        allure_docker = await self._create_allure_docker()
        
        # Create test execution scripts
        test_scripts = await self._create_test_scripts()
        
        # Create CI/CD integration
        cicd_integration = await self._create_cicd_integration()
        
        return {
            'allure_config': allure_config,
            'pytest_config': pytest_config,
            'allure_docker': allure_docker,
            'test_scripts': test_scripts,
            'cicd_integration': cicd_integration
        }
    
    async def _create_allure_config(self) -> str:
        """Create Allure configuration"""
        allure_config_file = self.config_dir / "allure.yml"
        
        allure_config = """# Allure Framework Configuration
# Generated on: {timestamp}

allure:
  version: {version}
  results_dir: {results_dir}
  report_dir: {report_dir}
  history_dir: {history_dir}
  server:
    port: {server_port}
    host: {server_host}

pytest:
  allure_dir: {allure_dir}
  allure_clean: {allure_clean}
  allure_attach: {allure_attach}
  allure_links: {allure_links}

reporting:
  title: "{title}"
  description: "{description}"
  logo: "{logo}"
  theme: "{theme}"
  language: "{language}"

# Test categories
categories:
  - name: "Failed tests"
    matchedStatuses: ["failed", "broken"]
  - name: "Skipped tests"
    matchedStatuses: ["skipped"]
  - name: "Passed tests"
    matchedStatuses: ["passed"]
  - name: "Performance tests"
    matchedStatuses: ["passed", "failed"]
    messageRegex: ".*performance.*"

# Test environment
environment:
  project: "LLM Multimodal Stack"
  version: "1.0.0"
  environment: "production"
  browser: "Docker"
  os: "Linux"
  python: "3.13"

# Links configuration
links:
  - name: "GitHub Issues"
    pattern: "https://github.com/markwoitaszek/llm-multimodal-stack/issues/{{issue}}"
    type: "issue"
  - name: "Test Management"
    pattern: "https://testmanagement.example.com/testcase/{{tms}}"
    type: "tms"
""".format(
            timestamp=datetime.utcnow().isoformat(),
            version=self.allure_config['allure']['version'],
            results_dir=self.allure_config['allure']['results_dir'],
            report_dir=self.allure_config['allure']['report_dir'],
            history_dir=self.allure_config['allure']['history_dir'],
            server_port=self.allure_config['allure']['server_port'],
            server_host=self.allure_config['allure']['server_host'],
            allure_dir=self.allure_config['pytest']['allure_dir'],
            allure_clean=self.allure_config['pytest']['allure_clean'],
            allure_attach=self.allure_config['pytest']['allure_attach'],
            allure_links=self.allure_config['pytest']['allure_links'],
            title=self.allure_config['reporting']['title'],
            description=self.allure_config['reporting']['description'],
            logo=self.allure_config['reporting']['logo'],
            theme=self.allure_config['reporting']['theme'],
            language=self.allure_config['reporting']['language']
        )
        
        with open(allure_config_file, 'w') as f:
            f.write(allure_config)
        
        logger.info(f"Created Allure configuration: {allure_config_file}")
        return str(allure_config_file)
    
    async def _update_pytest_config(self) -> str:
        """Update pytest configuration for Allure integration"""
        pytest_config_file = self.workspace_path / "pytest.ini"
        
        # Read existing pytest.ini
        existing_config = ""
        if pytest_config_file.exists():
            with open(pytest_config_file, 'r') as f:
                existing_config = f.read()
        
        # Add Allure-specific configuration
        allure_additions = """
# Allure Framework Integration
addopts = 
    --alluredir=allure-results
    --allure-clean
    --allure-attach
    --allure-links

# Allure markers
markers =
    allure_epic: Epic for test organization
    allure_feature: Feature being tested
    allure_story: User story being tested
    allure_severity: Test severity (blocker, critical, normal, minor, trivial)
    allure_owner: Test owner
    allure_issue: Related issue number
    allure_tms: Test management system ID
    allure_tag: Additional tags for test categorization
"""
        
        # Update the existing config
        updated_config = existing_config + allure_additions
        
        with open(pytest_config_file, 'w') as f:
            f.write(updated_config)
        
        logger.info(f"Updated pytest configuration: {pytest_config_file}")
        return str(pytest_config_file)
    
    async def _create_allure_docker(self) -> str:
        """Create Allure Docker setup"""
        allure_docker_file = self.workspace_path / "docker-compose.allure.yml"
        
        allure_docker = f"""# Allure Framework Docker Setup
# Generated on: {datetime.utcnow().isoformat()}

version: '3.8'

services:
  # Allure Results Server
  allure-results:
    image: frankescobar/allure-docker-service:latest
    container_name: multimodal-allure-results
    environment:
      - CHECK_RESULTS_EVERY_SECONDS=3
      - KEEP_HISTORY=1
      - KEEP_HISTORY_BY_DAYS=30
      - CLEAN_RESULTS_DIRECTORY=1
    volumes:
      - allure_results:/app/allure-results
      - allure_history:/app/default-reports
    ports:
      - "5050:5050"
    restart: unless-stopped
    networks:
      - multimodal-net

  # Allure Report Server
  allure-report:
    image: frankescobar/allure-docker-service:latest
    container_name: multimodal-allure-report
    environment:
      - CHECK_RESULTS_EVERY_SECONDS=3
      - KEEP_HISTORY=1
      - KEEP_HISTORY_BY_DAYS=30
      - CLEAN_RESULTS_DIRECTORY=1
    volumes:
      - allure_results:/app/allure-results
      - allure_history:/app/default-reports
    ports:
      - "8080:5050"
    restart: unless-stopped
    networks:
      - multimodal-net

  # Allure CLI for report generation
  allure-cli:
    image: frankescobar/allure-docker-service:latest
    container_name: multimodal-allure-cli
    volumes:
      - allure_results:/app/allure-results
      - allure_history:/app/default-reports
      - ./reports:/app/reports
    command: >
      sh -c "
        allure generate /app/allure-results -o /app/reports/allure-report --clean &&
        allure open /app/reports/allure-report --port 8080 --host 0.0.0.0
      "
    ports:
      - "8081:8080"
    depends_on:
      - allure-results
    restart: unless-stopped
    networks:
      - multimodal-net

volumes:
  allure_results:
  allure_history:

networks:
  multimodal-net:
    external: true
"""
        
        with open(allure_docker_file, 'w') as f:
            f.write(allure_docker)
        
        logger.info(f"Created Allure Docker setup: {allure_docker_file}")
        return str(allure_docker_file)
    
    async def _create_test_scripts(self) -> List[str]:
        """Create test execution scripts with Allure integration"""
        scripts_dir = self.workspace_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        created_scripts = []
        
        # Create comprehensive test runner
        test_runner = scripts_dir / "run_tests_with_allure.py"
        test_runner_content = '''#!/usr/bin/env python3
"""
Comprehensive Test Runner with Allure Integration
"""
import asyncio
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class AllureTestRunner:
    """Test runner with Allure integration"""
    
    def __init__(self):
        self.workspace_path = Path(__file__).parent.parent
        self.allure_results_dir = self.workspace_path / "allure-results"
        self.allure_report_dir = self.workspace_path / "allure-report"
        
    async def run_tests(self, test_type: str = "all"):
        """Run tests with Allure integration"""
        print(f"Running {test_type} tests with Allure integration...")
        
        # Clean previous results
        if self.allure_results_dir.exists():
            import shutil
            shutil.rmtree(self.allure_results_dir)
        self.allure_results_dir.mkdir(exist_ok=True)
        
        # Build pytest command
        cmd = [
            "python3", "-m", "pytest",
            "--alluredir=allure-results",
            "--allure-clean",
            "--allure-attach",
            "-v",
            "--tb=short"
        ]
        
        # Add test type specific options
        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "performance":
            cmd.extend(["-m", "performance"])
        elif test_type == "api":
            cmd.extend(["-m", "api"])
        
        # Add test paths
        cmd.append("tests/")
        
        print(f"Executing: {' '.join(cmd)}")
        
        # Run tests
        result = subprocess.run(cmd, cwd=self.workspace_path)
        
        if result.returncode == 0:
            print("✅ Tests completed successfully")
        else:
            print("❌ Tests failed")
        
        return result.returncode
    
    async def generate_report(self):
        """Generate Allure report"""
        print("Generating Allure report...")
        
        # Generate report
        cmd = [
            "allure", "generate",
            str(self.allure_results_dir),
            "-o", str(self.allure_report_dir),
            "--clean"
        ]
        
        result = subprocess.run(cmd, cwd=self.workspace_path)
        
        if result.returncode == 0:
            print("✅ Allure report generated successfully")
            print(f"Report location: {self.allure_report_dir}")
        else:
            print("❌ Failed to generate Allure report")
        
        return result.returncode
    
    async def serve_report(self, port: int = 8080):
        """Serve Allure report"""
        print(f"Serving Allure report on port {port}...")
        
        cmd = [
            "allure", "open",
            str(self.allure_report_dir),
            "--port", str(port),
            "--host", "0.0.0.0"
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        print(f"Report will be available at: http://localhost:{port}")
        
        # Run in background
        subprocess.Popen(cmd, cwd=self.workspace_path)

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests with Allure integration")
    parser.add_argument("--type", choices=["all", "unit", "integration", "performance", "api"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--report-only", action="store_true", help="Generate report only")
    parser.add_argument("--serve", action="store_true", help="Serve report after generation")
    parser.add_argument("--port", type=int, default=8080, help="Port for serving report")
    
    args = parser.parse_args()
    
    runner = AllureTestRunner()
    
    if not args.report_only:
        # Run tests
        exit_code = await runner.run_tests(args.type)
        if exit_code != 0:
            sys.exit(exit_code)
    
    # Generate report
    exit_code = await runner.generate_report()
    if exit_code != 0:
        sys.exit(exit_code)
    
    # Serve report if requested
    if args.serve:
        await runner.serve_report(args.port)
        print("Press Ctrl+C to stop the server")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\\nServer stopped")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(test_runner, 'w') as f:
            f.write(test_runner_content)
        
        os.chmod(test_runner, 0o755)
        created_scripts.append(str(test_runner))
        
        # Create test execution script
        test_executor = scripts_dir / "execute_tests.sh"
        test_executor_content = '''#!/bin/bash
# Test Execution Script with Allure Integration

set -e

echo "🚀 Starting test execution with Allure integration..."

# Configuration
WORKSPACE_PATH="/workspace"
ALLURE_RESULTS_DIR="$WORKSPACE_PATH/allure-results"
ALLURE_REPORT_DIR="$WORKSPACE_PATH/allure-report"
TEST_TYPE="${1:-all}"

# Clean previous results
echo "🧹 Cleaning previous test results..."
rm -rf "$ALLURE_RESULTS_DIR"
mkdir -p "$ALLURE_RESULTS_DIR"

# Run tests
echo "🧪 Running $TEST_TYPE tests..."
case $TEST_TYPE in
    "unit")
        python3 -m pytest tests/ -m unit --alluredir=allure-results --allure-clean -v
        ;;
    "integration")
        python3 -m pytest tests/ -m integration --alluredir=allure-results --allure-clean -v
        ;;
    "performance")
        python3 -m pytest tests/ -m performance --alluredir=allure-results --allure-clean -v
        ;;
    "api")
        python3 -m pytest tests/ -m api --alluredir=allure-results --allure-clean -v
        ;;
    *)
        python3 -m pytest tests/ --alluredir=allure-results --allure-clean -v
        ;;
esac

# Generate Allure report
echo "📊 Generating Allure report..."
allure generate "$ALLURE_RESULTS_DIR" -o "$ALLURE_REPORT_DIR" --clean

# Check if report was generated
if [ -d "$ALLURE_REPORT_DIR" ]; then
    echo "✅ Allure report generated successfully"
    echo "📁 Report location: $ALLURE_REPORT_DIR"
    
    # Serve report if requested
    if [ "$2" = "serve" ]; then
        echo "🌐 Serving Allure report on port 8080..."
        allure open "$ALLURE_REPORT_DIR" --port 8080 --host 0.0.0.0
    fi
else
    echo "❌ Failed to generate Allure report"
    exit 1
fi

echo "🎉 Test execution completed successfully!"
'''
        
        with open(test_executor, 'w') as f:
            f.write(test_executor_content)
        
        os.chmod(test_executor, 0o755)
        created_scripts.append(str(test_executor))
        
        logger.info(f"Created {len(created_scripts)} test execution scripts")
        return created_scripts
    
    async def _create_cicd_integration(self) -> Dict[str, str]:
        """Create CI/CD integration for Allure"""
        logger.info("Creating CI/CD integration for Allure")
        
        # Create GitHub Actions workflow
        github_actions = self.workspace_path / ".github" / "workflows" / "allure-tests.yml"
        github_actions.parent.mkdir(parents=True, exist_ok=True)
        
        github_workflow = f"""name: Allure Test Reports

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        test-type: [unit, integration, performance, api]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        pip install allure-pytest
    
    - name: Install Allure
      run: |
        wget https://github.com/allure-framework/allure2/releases/download/{self.allure_config['allure']['version']}/allure-{self.allure_config['allure']['version']}.tgz
        tar -xzf allure-{self.allure_config['allure']['version']}.tgz
        sudo mv allure-{self.allure_config['allure']['version']} /opt/allure
        sudo ln -s /opt/allure/bin/allure /usr/local/bin/allure
    
    - name: Run ${{{{ matrix.test-type }}}} tests
      run: |
        python -m pytest tests/ -m ${{{{ matrix.test-type }}}} --alluredir=allure-results --allure-clean -v
    
    - name: Generate Allure Report
      if: always()
      run: |
        allure generate allure-results -o allure-report --clean
    
    - name: Upload Allure Report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: allure-report-${{{{ matrix.test-type }}}}
        path: allure-report/
    
    - name: Deploy to Allure Server
      if: always()
      run: |
        # Deploy to Allure server (configure with your server details)
        echo "Deploying report to Allure server..."
        # Add deployment commands here

  deploy-report:
    needs: test
    runs-on: ubuntu-latest
    if: always()
    
    steps:
    - name: Download Allure Reports
      uses: actions/download-artifact@v3
      with:
        path: allure-reports/
    
    - name: Deploy Combined Report
      run: |
        # Combine and deploy all test reports
        echo "Deploying combined Allure report..."
        # Add deployment commands here
"""
        
        with open(github_actions, 'w') as f:
            f.write(github_workflow)
        
        # Create Jenkins pipeline
        jenkins_pipeline = self.workspace_path / "Jenkinsfile"
        
        jenkins_content = f"""pipeline {{
    agent any
    
    environment {{
        ALLURE_RESULTS = 'allure-results'
        ALLURE_REPORT = 'allure-report'
        ALLURE_VERSION = '{self.allure_config['allure']['version']}'
    }}
    
    stages {{
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Setup') {{
            steps {{
                sh '''
                    python3 -m pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r requirements-test.txt
                    pip install allure-pytest
                '''
            }}
        }}
        
        stage('Install Allure') {{
            steps {{
                sh '''
                    wget https://github.com/allure-framework/allure2/releases/download/${{ALLURE_VERSION}}/allure-${{ALLURE_VERSION}}.tgz
                    tar -xzf allure-${{ALLURE_VERSION}}.tgz
                    sudo mv allure-${{ALLURE_VERSION}} /opt/allure
                    sudo ln -s /opt/allure/bin/allure /usr/local/bin/allure
                '''
            }}
        }}
        
        stage('Run Tests') {{
            parallel {{
                stage('Unit Tests') {{
                    steps {{
                        sh 'python3 -m pytest tests/ -m unit --alluredir=${{ALLURE_RESULTS}} --allure-clean -v'
                    }}
                }}
                stage('Integration Tests') {{
                    steps {{
                        sh 'python3 -m pytest tests/ -m integration --alluredir=${{ALLURE_RESULTS}} --allure-clean -v'
                    }}
                }}
                stage('Performance Tests') {{
                    steps {{
                        sh 'python3 -m pytest tests/ -m performance --alluredir=${{ALLURE_RESULTS}} --allure-clean -v'
                    }}
                }}
                stage('API Tests') {{
                    steps {{
                        sh 'python3 -m pytest tests/ -m api --alluredir=${{ALLURE_RESULTS}} --allure-clean -v'
                    }}
                }}
            }}
        }}
        
        stage('Generate Report') {{
            steps {{
                sh 'allure generate ${{ALLURE_RESULTS}} -o ${{ALLURE_REPORT}} --clean'
            }}
        }}
        
        stage('Publish Report') {{
            steps {{
                allure([
                    includeProperties: false,
                    jdk: '',
                    properties: [],
                    reportBuildPolicy: 'ALWAYS',
                    results: [[path: '${{ALLURE_RESULTS}}']]
                ])
            }}
        }}
    }}
    
    post {{
        always {{
            archiveArtifacts artifacts: '${{ALLURE_REPORT}}/**/*', fingerprint: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '${{ALLURE_REPORT}}',
                reportFiles: 'index.html',
                reportName: 'Allure Report'
            ])
        }}
    }}
}}
"""
        
        with open(jenkins_pipeline, 'w') as f:
            f.write(jenkins_content)
        
        logger.info("Created CI/CD integration files")
        return {
            'github_actions': str(github_actions),
            'jenkins_pipeline': str(jenkins_pipeline)
        }
    
    async def create_test_management_features(self) -> Dict[str, Any]:
        """Create test management features"""
        logger.info("Creating test management features")
        
        # Create test data management
        test_data_config = await self._create_test_data_config()
        
        # Create test environment management
        test_env_config = await self._create_test_env_config()
        
        # Create test metrics dashboard
        metrics_dashboard = await self._create_metrics_dashboard()
        
        return {
            'test_data_config': test_data_config,
            'test_env_config': test_env_config,
            'metrics_dashboard': metrics_dashboard
        }
    
    async def _create_test_data_config(self) -> str:
        """Create test data management configuration"""
        test_data_file = self.config_dir / "test_data.yaml"
        
        test_data_config = f"""# Test Data Management Configuration
# Generated on: {datetime.utcnow().isoformat()}

test_data:
  # Test datasets
  datasets:
    small_text:
      size: "1KB"
      samples: 100
      description: "Small text samples for unit tests"
    
    medium_text:
      size: "10KB"
      samples: 50
      description: "Medium text samples for integration tests"
    
    large_text:
      size: "100KB"
      samples: 10
      description: "Large text samples for performance tests"
    
    images:
      small: [100, 100]
      medium: [512, 512]
      large: [1024, 1024]
      description: "Image samples for multimodal tests"
  
  # Test data sources
  sources:
    local:
      path: "./test_data/"
      type: "file"
    
    remote:
      url: "https://testdata.example.com/"
      type: "http"
      auth_required: true
  
  # Data management
  management:
    cleanup_after_tests: true
    backup_test_data: true
    version_control: true
    retention_days: 30

# Test environment data
test_environments:
  development:
    database_url: "postgresql://test:test@localhost:5432/test_db"
    redis_url: "redis://localhost:6379/0"
    api_base_url: "http://localhost:8000"
  
  staging:
    database_url: "postgresql://staging:staging@staging-db:5432/staging_db"
    redis_url: "redis://staging-redis:6379/0"
    api_base_url: "http://staging-api:8000"
  
  production:
    database_url: "postgresql://prod:prod@prod-db:5432/prod_db"
    redis_url: "redis://prod-redis:6379/0"
    api_base_url: "http://prod-api:8000"

# Test fixtures
fixtures:
  users:
    admin:
      username: "admin"
      password: "admin123"
      role: "admin"
    
    user:
      username: "testuser"
      password: "test123"
      role: "user"
  
  models:
    default:
      name: "test-model"
      version: "1.0.0"
      type: "text"
  
  agents:
    test_agent:
      name: "Test Agent"
      goal: "Execute test tasks"
      tools: ["test_tool"]
"""
        
        with open(test_data_file, 'w') as f:
            f.write(test_data_config)
        
        logger.info(f"Created test data configuration: {test_data_file}")
        return str(test_data_file)
    
    async def _create_test_env_config(self) -> str:
        """Create test environment management configuration"""
        test_env_file = self.config_dir / "test_environments.yaml"
        
        test_env_config = f"""# Test Environment Management
# Generated on: {datetime.utcnow().isoformat()}

environments:
  # Local development environment
  local:
    name: "Local Development"
    description: "Local development environment for testing"
    docker_compose: "docker-compose.test.yml"
    services:
      - postgres
      - redis
      - qdrant
      - multimodal-worker
      - retrieval-proxy
    resources:
      cpu: "2.0"
      memory: "4G"
    cleanup: true
  
  # CI/CD environment
  ci:
    name: "CI/CD Environment"
    description: "Continuous integration environment"
    docker_compose: "docker-compose.ci.yml"
    services:
      - postgres
      - redis
      - qdrant
      - multimodal-worker
      - retrieval-proxy
    resources:
      cpu: "4.0"
      memory: "8G"
    cleanup: true
    timeout: "30m"
  
  # Staging environment
  staging:
    name: "Staging Environment"
    description: "Staging environment for pre-production testing"
    docker_compose: "docker-compose.staging.yml"
    services:
      - postgres
      - redis
      - qdrant
      - multimodal-worker
      - retrieval-proxy
      - litellm
      - vllm
    resources:
      cpu: "8.0"
      memory: "16G"
    cleanup: false
    persistent: true

# Environment provisioning
provisioning:
  # Database setup
  database:
    init_script: "./sql/init.sql"
    test_data: "./test_data/database/"
    migrations: "./sql/migrations/"
  
  # Service configuration
  services:
    multimodal-worker:
      config: "./configs/multimodal-worker-test.yaml"
      models: "./models/test/"
    
    retrieval-proxy:
      config: "./configs/retrieval-proxy-test.yaml"
      indexes: "./test_data/indexes/"
  
  # Monitoring setup
  monitoring:
    prometheus: true
    grafana: true
    logs: true

# Test execution configuration
execution:
  # Test categories
  categories:
    unit:
      parallel: true
      timeout: "5m"
      resources:
        cpu: "0.5"
        memory: "1G"
    
    integration:
      parallel: false
      timeout: "15m"
      resources:
        cpu: "1.0"
        memory: "2G"
    
    performance:
      parallel: false
      timeout: "30m"
      resources:
        cpu: "2.0"
        memory: "4G"
    
    e2e:
      parallel: false
      timeout: "60m"
      resources:
        cpu: "4.0"
        memory: "8G"
  
  # Test data management
  data_management:
    setup_before: true
    cleanup_after: true
    backup_on_failure: true
    isolation: true
"""
        
        with open(test_env_file, 'w') as f:
            f.write(test_env_config)
        
        logger.info(f"Created test environment configuration: {test_env_file}")
        return str(test_env_file)
    
    async def _create_metrics_dashboard(self) -> str:
        """Create test metrics dashboard configuration"""
        metrics_file = self.config_dir / "test_metrics.yaml"
        
        metrics_config = f"""# Test Metrics Dashboard Configuration
# Generated on: {datetime.utcnow().isoformat()}

metrics:
  # Test execution metrics
  execution:
    - name: "Test Execution Time"
      type: "duration"
      unit: "seconds"
      aggregation: "average"
    
    - name: "Test Success Rate"
      type: "percentage"
      unit: "percent"
      aggregation: "average"
    
    - name: "Test Failure Rate"
      type: "percentage"
      unit: "percent"
      aggregation: "average"
    
    - name: "Test Coverage"
      type: "percentage"
      unit: "percent"
      aggregation: "average"
  
  # Performance metrics
  performance:
    - name: "API Response Time"
      type: "duration"
      unit: "milliseconds"
      aggregation: "percentile_95"
    
    - name: "Database Query Time"
      type: "duration"
      unit: "milliseconds"
      aggregation: "percentile_95"
    
    - name: "Memory Usage"
      type: "memory"
      unit: "MB"
      aggregation: "peak"
    
    - name: "CPU Usage"
      type: "percentage"
      unit: "percent"
      aggregation: "peak"
  
  # Quality metrics
  quality:
    - name: "Code Quality Score"
      type: "score"
      unit: "points"
      aggregation: "average"
    
    - name: "Security Score"
      type: "score"
      unit: "points"
      aggregation: "average"
    
    - name: "Maintainability Index"
      type: "index"
      unit: "points"
      aggregation: "average"

# Dashboard configuration
dashboard:
  title: "LLM Multimodal Stack Test Metrics"
  refresh_interval: "30s"
  time_range: "24h"
  
  # Widgets
  widgets:
    - title: "Test Execution Summary"
      type: "summary"
      metrics:
        - "Test Success Rate"
        - "Test Failure Rate"
        - "Test Coverage"
    
    - title: "Performance Trends"
      type: "line_chart"
      metrics:
        - "API Response Time"
        - "Database Query Time"
        - "Memory Usage"
    
    - title: "Quality Metrics"
      type: "gauge"
      metrics:
        - "Code Quality Score"
        - "Security Score"
        - "Maintainability Index"
    
    - title: "Test Categories"
      type: "pie_chart"
      metrics:
        - "Unit Tests"
        - "Integration Tests"
        - "Performance Tests"
        - "E2E Tests"

# Alerting configuration
alerting:
  rules:
    - name: "High Test Failure Rate"
      condition: "Test Failure Rate > 10%"
      severity: "warning"
      duration: "5m"
    
    - name: "Low Test Coverage"
      condition: "Test Coverage < 80%"
      severity: "warning"
      duration: "10m"
    
    - name: "High API Response Time"
      condition: "API Response Time > 2000ms"
      severity: "critical"
      duration: "2m"
    
    - name: "High Memory Usage"
      condition: "Memory Usage > 8GB"
      severity: "warning"
      duration: "5m"

# Reporting configuration
reporting:
  # Report types
  types:
    - name: "Daily Test Report"
      schedule: "0 8 * * *"
      recipients: ["team@example.com"]
      format: "html"
    
    - name: "Weekly Quality Report"
      schedule: "0 9 * * 1"
      recipients: ["management@example.com"]
      format: "pdf"
    
    - name: "Performance Report"
      schedule: "0 10 * * 1"
      recipients: ["performance@example.com"]
      format: "html"
  
  # Report templates
  templates:
    daily:
      title: "Daily Test Execution Report"
      sections:
        - "Test Summary"
        - "Failed Tests"
        - "Performance Metrics"
        - "Recommendations"
    
    weekly:
      title: "Weekly Quality Report"
      sections:
        - "Quality Trends"
        - "Coverage Analysis"
        - "Performance Analysis"
        - "Action Items"
"""
        
        with open(metrics_file, 'w') as f:
            f.write(metrics_config)
        
        logger.info(f"Created test metrics configuration: {metrics_file}")
        return str(metrics_file)
    
    async def generate_allure_report(self) -> Dict[str, Any]:
        """Generate comprehensive Allure implementation report"""
        logger.info("Generating Allure implementation report")
        
        report = {
            'allure_timestamp': datetime.utcnow().isoformat(),
            'allure_summary': {
                'framework_setup': 'completed',
                'pytest_integration': 'completed',
                'docker_setup': 'completed',
                'test_scripts': 'completed',
                'cicd_integration': 'completed',
                'test_management': 'completed'
            },
            'allure_configuration': {
                'version': self.allure_config['allure']['version'],
                'results_dir': self.allure_config['allure']['results_dir'],
                'report_dir': self.allure_config['allure']['report_dir'],
                'server_port': self.allure_config['allure']['server_port']
            },
            'pytest_integration': {
                'allure_dir': self.allure_config['pytest']['allure_dir'],
                'allure_clean': self.allure_config['pytest']['allure_clean'],
                'allure_attach': self.allure_config['pytest']['allure_attach'],
                'allure_links': self.allure_config['pytest']['allure_links']
            },
            'test_management_features': {
                'test_data_management': 'configured',
                'test_environment_management': 'configured',
                'test_metrics_dashboard': 'configured',
                'ci_cd_integration': 'configured'
            },
            'reporting_capabilities': {
                'web_based_reports': True,
                'historical_reports': True,
                'trend_analysis': True,
                'test_categorization': True,
                'attachment_support': True,
                'link_integration': True
            },
            'recommendations': [
                'Install Allure CLI for local report generation',
                'Set up Allure server for centralized reporting',
                'Configure test data management for consistent testing',
                'Implement test environment provisioning',
                'Set up automated test execution in CI/CD',
                'Create custom Allure plugins for specific metrics',
                'Implement test result notifications',
                'Set up test trend monitoring and alerting'
            ],
            'next_steps': [
                'Install Allure CLI and dependencies',
                'Run initial test execution with Allure integration',
                'Generate and review first Allure report',
                'Set up Allure server for team access',
                'Configure CI/CD pipelines for automated reporting',
                'Create custom test categories and markers',
                'Implement test data management workflows',
                'Set up test metrics monitoring and alerting'
            ]
        }
        
        # Save report
        report_file = self.reports_dir / "allure_implementation_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Allure implementation report generated: {report_file}")
        return report

# Global Allure integration instance
allure_integration = AllureIntegration()