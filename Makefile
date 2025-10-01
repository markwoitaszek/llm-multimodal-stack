# Makefile for Multimodal LLM Stack
# Unified schema-based Docker Compose management

.PHONY: help generate-compose validate-schema clean-compose test-compose

# Default target
help:
	@echo "Multimodal LLM Stack - Unified Compose Management"
	@echo "=================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  generate-compose         Generate all Docker Compose files from unified schema"
	@echo "  validate-schema          Validate the unified schema for errors"
	@echo "  validate-security        Validate security configuration (no hardcoded defaults)"
	@echo "  validate-credentials     Validate credentials for deployment (ENV=environment STRICT=true/false)"
	@echo "  validate-credentials-dev Validate credentials for development"
	@echo "  validate-credentials-staging  Validate credentials for staging (strict)"
	@echo "  validate-credentials-prod     Validate credentials for production (strict)"
	@echo "  clean-compose            Remove all generated compose files"
	@echo "  test-compose             Test generated compose files for syntax errors"
	@echo "  setup-secrets            Generate environment files and secrets (development)"
	@echo "  setup-secrets-dev        Generate secrets for development"
	@echo "  setup-secrets-staging    Generate secrets for staging"
	@echo "  setup-secrets-prod       Generate secrets for production"
	@echo "  setup                    Full setup with all validations"
	@echo "  start-dev                Start development environment (with validation)"
	@echo "  start-staging            Start staging environment (with validation)"
	@echo "  start-staging-gpu        Start staging environment with GPU support"
	@echo "  start-prod               Start production environment (with validation)"
	@echo "  start-prod-gpu           Start production environment with GPU support"
	@echo "  start-gpu                Start GPU-optimized environment"
	@echo "  start-monitoring         Start monitoring environment with ELK stack"
	@echo "  start-testing            Start testing environment with Allure and JMeter"
	@echo "  setup-testing            Setup testing environment and dependencies"
	@echo "  test-allure              Run tests with Allure reporting"
	@echo "  test-jmeter              Run JMeter performance tests"
	@echo "  test-unit                Run unit tests only"
	@echo "  test-integration         Run integration tests only"
	@echo "  test-performance         Run performance tests only"
	@echo "  test-api                 Run API tests only"
	@echo "  generate-allure-report   Generate Allure test report"
	@echo "  serve-allure-report      Serve Allure report on localhost:8080"
	@echo "  stop                     Stop all services"
	@echo "  logs                     View logs for all services"
	@echo "  status                   Show status of all services"
	@echo "  clean                    Clean up containers, volumes, and networks"
	@echo ""
	@echo "Stack-based commands:"
	@echo "  start-core               Start core infrastructure stack (postgres, redis, qdrant, minio)"
	@echo "  start-inference          Start inference stack (vllm, litellm)"
	@echo "  start-ai                 Start AI services stack (worker, retrieval, agents, memory, search)"
	@echo "  start-ui                 Start UI and workflow stack (openwebui, n8n, n8n-monitoring, nginx)"
	@echo "  start-testing            Start testing stack (postgres, redis, allure, jmeter)"
	@echo "  start-monitoring         Start monitoring stack (prometheus, grafana, elk)"
	@echo "  stop-core                Stop core infrastructure stack"
	@echo "  stop-inference           Stop inference stack"
	@echo "  stop-ai                  Stop AI services stack"
	@echo "  stop-ui                  Stop UI and workflow stack"
	@echo "  stop-testing             Stop testing stack"
	@echo "  stop-monitoring          Stop monitoring stack"
	@echo "  restart-core             Restart core infrastructure stack (no data loss)"
	@echo "  restart-inference        Restart inference stack (no data loss)"
	@echo "  restart-ai               Restart AI services stack (no data loss)"
	@echo "  restart-ui               Restart UI and workflow stack (no data loss)"
	@echo "  restart-testing          Restart testing stack (no data loss)"
	@echo "  restart-monitoring       Restart monitoring stack (no data loss)"
	@echo "  rebuild-ai               Rebuild AI services stack (force image rebuild)"
	@echo "  logs-core                View logs for core infrastructure stack"
	@echo "  logs-inference           View logs for inference stack"
	@echo "  logs-ai                  View logs for AI services stack"
	@echo "  logs-ui                  View logs for UI and workflow stack"
	@echo "  logs-testing             View logs for testing stack"
	@echo "  logs-monitoring          View logs for monitoring stack"
	@echo "  status-core              Show status of core infrastructure stack"
	@echo "  status-inference         Show status of inference stack"
	@echo "  status-ai                Show status of AI services stack"
	@echo "  status-ui                Show status of UI and workflow stack"
	@echo "  status-testing           Show status of testing stack"
	@echo "  status-monitoring        Show status of monitoring stack"
	@echo ""
	@echo "Network management commands:"
	@echo "  check-network-conflicts  Check for network conflicts before starting stacks"
	@echo "  cleanup-networks         Clean up orphaned networks"
	@echo "  validate-networks        Validate network configuration"
	@echo "  check-network-health     Check network health and connectivity"
	@echo ""

# Generate all compose files from unified schema
generate-compose:
	@echo "Generating Docker Compose files from unified schema..."
	python3 scripts/compose-generator.py
	@echo "✅ Compose files generated successfully"

# Validate the unified schema
validate-schema:
	@echo "Validating unified schema..."
	python3 scripts/compose-generator.py --validate-only
	@echo "✅ Schema validation passed"

# Clean generated compose files
clean-compose:
	@echo "Cleaning generated compose files..."
	rm -f compose*.yml
	@echo "✅ Compose files cleaned"

# Test generated compose files
test-compose: generate-compose
	@echo "Testing generated compose files..."
	@for file in compose*.yml; do \
		echo "Testing $$file..."; \
		docker compose -f $$file config --quiet || (echo "❌ $$file failed validation" && exit 1); \
	done
	@echo "✅ All compose files validated successfully"

# Setup secrets and environment files (default: development)
setup-secrets:
	@echo "Setting up secrets and environment files..."
	python3 setup_secrets.py --environment development
	@if [ -f .env.development ]; then \
		cp .env.development .env; \
		echo "✅ Copied .env.development to .env for Docker Compose"; \
	fi
	@echo "✅ Secrets and environment files generated"

# Environment-specific secret setup
setup-secrets-dev:
	@echo "Setting up secrets for development..."
	python3 setup_secrets.py --environment development
	@if [ -f .env.development ]; then \
		cp .env.development .env; \
		echo "✅ Copied .env.development to .env"; \
	fi

setup-secrets-staging:
	@echo "Setting up secrets for staging..."
	python3 setup_secrets.py --environment staging
	@if [ -f .env.staging ]; then \
		cp .env.staging .env; \
		echo "✅ Copied .env.staging to .env"; \
	fi

setup-secrets-prod:
	@echo "Setting up secrets for production..."
	python3 setup_secrets.py --environment production
	@if [ -f .env.production ]; then \
		cp .env.production .env; \
		echo "✅ Copied .env.production to .env"; \
	fi

# Validate credentials
validate-credentials:
	@echo "🔒 Validating credentials..."
	@./scripts/validate-credentials.sh $(ENV) $(STRICT)
	@echo "✅ Credential validation passed"

# Validate credentials for specific environment
validate-credentials-dev:
	@$(MAKE) validate-credentials ENV=development STRICT=false

validate-credentials-staging:
	@$(MAKE) validate-credentials ENV=staging STRICT=true

validate-credentials-prod:
	@$(MAKE) validate-credentials ENV=production STRICT=true

# Development environment
start-dev: generate-compose setup-secrets-dev validate-credentials-dev
	@echo "Starting development environment..."
	docker compose up -d
	@echo "✅ Development environment started"
	@echo "📊 Services available:"
	@echo "   - LiteLLM: http://localhost:4000"
	@echo "   - Multimodal Worker: http://localhost:8001"
	@echo "   - Retrieval Proxy: http://localhost:8002"
	@echo "   - vLLM: http://localhost:8000"
	@echo "   - Qdrant: http://localhost:6333"
	@echo "   - MinIO Console: http://localhost:9002"

# Staging environment
start-staging: generate-compose setup-secrets-staging validate-credentials-staging
	@echo "Starting staging environment..."
	docker compose -f compose.yml -f compose.staging.yml up -d
	@echo "✅ Staging environment started"

# Staging environment with GPU
start-staging-gpu: generate-compose setup-secrets-staging configure-gpu validate-credentials-staging
	@echo "Starting staging environment with GPU support..."
	@echo "🎮 GPU Configuration:"
	@echo "  CUDA_VISIBLE_DEVICES: $$(grep '^CUDA_VISIBLE_DEVICES=' .env.staging 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
	@echo "  GPU_COUNT: $$(grep '^GPU_COUNT=' .env.staging 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
	docker compose -f compose.yml -f compose.staging.yml up -d
	@echo "✅ Staging environment with GPU started"

# Production environment
start-prod: generate-compose setup-secrets-prod validate-credentials-prod
	@echo "Starting production environment..."
	docker compose -f compose.yml -f compose.production.yml up -d
	@echo "✅ Production environment started"

# Production environment with GPU
start-prod-gpu: generate-compose setup-secrets-prod configure-gpu validate-credentials-prod
	@echo "Starting production environment with GPU support..."
	@echo "🎮 GPU Configuration:"
	@echo "  CUDA_VISIBLE_DEVICES: $$(grep '^CUDA_VISIBLE_DEVICES=' .env.prod 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
	@echo "  GPU_COUNT: $$(grep '^GPU_COUNT=' .env.prod 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
	docker compose -f compose.yml -f compose.production.yml up -d
	@echo "✅ Production environment with GPU started"

# GPU-optimized environment
start-gpu: generate-compose setup-secrets
	@echo "Starting GPU-optimized environment..."
	docker compose -f compose.yml -f compose.gpu.yml up -d
	@echo "✅ GPU-optimized environment started"

# Monitoring environment with ELK stack (legacy - use start-monitoring stack command instead)

# Stop all services
stop:
	@echo "Stopping all services..."
	docker compose down
	@echo "✅ All services stopped"

# View logs
logs:
	@echo "Viewing logs for all services..."
	docker compose logs -f

# Show status
status:
	@echo "Service status:"
	docker compose ps

# Clean up everything
clean:
	@echo "Cleaning up containers, volumes, and networks..."
	docker compose down --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed"

# Full setup from scratch
	@echo ""
	@echo "Next steps:"
	@echo "  make start-dev     # Start development environment"
	@echo "  make start-staging # Start staging environment"
	@echo "  make start-prod    # Start production environment"
# Enhanced GPU Detection and Configuration
detect-gpu:
	@echo "🔍 Detecting GPU configuration..."
	@scripts/configure-gpu.sh detect

configure-gpu:
	@echo "🎮 Configuring GPU for optimal performance..."
	@scripts/configure-gpu.sh auto

# Enhanced GPU start with auto-detection
start-gpu-auto: detect-gpu configure-gpu start-gpu
	@echo "✅ GPU environment started with auto-configuration"

# Comprehensive Environment Management
wipe:
	@scripts/wipe-environment.sh

# Nuclear reset option
reset: wipe setup
	@echo "🎉 Environment reset and regenerated from scratch"

# Security validation
validate-security:
	@echo "🔒 Validating security configuration..."
	@if grep -q ":-postgres\|:-minioadmin" schemas/compose-schema.yaml; then \
		echo "❌ Hardcoded defaults found in schema"; \
		exit 1; \
	fi
	@if find services/ -name "config.py" -exec grep -l 'POSTGRES_PASSWORD.*,.*"postgres"\|POSTGRES_USER.*,.*"postgres"\|MINIO.*PASSWORD.*,.*"minioadmin"\|MINIO.*USER.*,.*"minioadmin"' {} \; | grep -q .; then \
		echo "❌ Hardcoded defaults found in service configs"; \
		exit 1; \
	fi
	@echo "✅ Security validation passed"

# Enhanced setup with security and credential validation
setup: validate-schema validate-security generate-compose setup-secrets validate-credentials-dev
	@echo "🎉 Full setup completed successfully with credential validation!"
	@echo ""
	@echo "Next steps:"
	@echo "  make start-dev        # Start development environment"
	@echo "  make start-gpu-auto   # Start GPU environment with auto-detection"
	@echo "  make wipe             # Wipe environment (DESTRUCTIVE)"
	@echo "  make reset            # Reset and regenerate from scratch"

# Testing Environment Setup
setup-testing: generate-compose
	@echo "🧪 Setting up testing environment..."
	@mkdir -p allure-results allure-report test-results
	@echo "✅ Testing environment setup completed"

# Start Testing Environment (legacy - use start-testing stack command instead)

# Run Tests with Allure Reporting
test-allure: setup-testing
	@echo "🧪 Running tests with Allure reporting..."
	@python3 -m pytest tests/ --alluredir=allure-results --allure-clean -v
	@echo "✅ Tests completed with Allure reporting"

# Run JMeter Performance Tests
test-jmeter: setup-testing
	@echo "⚡ Running JMeter performance tests..."
	@docker run --rm -v $(PWD)/jmeter:/tests -v $(PWD)/test-results:/results justb4/jmeter:latest -n -t /tests/api_load_test.jmx -l /results/results.jtl -e -o /results/html-report
	@echo "✅ JMeter performance tests completed"
	@echo "📊 Results available in test-results/ directory"

# Run Unit Tests
test-unit: setup-testing
	@echo "🔬 Running unit tests..."
	@python3 -m pytest tests/ -m unit --alluredir=allure-results --allure-clean -v
	@echo "✅ Unit tests completed"

# Run Integration Tests
test-integration: setup-testing
	@echo "🔗 Running integration tests..."
	@python3 -m pytest tests/ -m integration --alluredir=allure-results --allure-clean -v
	@echo "✅ Integration tests completed"

# Run Performance Tests
test-performance: setup-testing
	@echo "⚡ Running performance tests..."
	@python3 -m pytest tests/ -m performance --alluredir=allure-results --allure-clean -v
	@echo "✅ Performance tests completed"

# Run API Tests
test-api: setup-testing
	@echo "🌐 Running API tests..."
	@python3 -m pytest tests/ -m api --alluredir=allure-results --allure-clean -v
	@echo "✅ API tests completed"

# Generate Allure Report
generate-allure-report:
	@echo "📊 Generating Allure report..."
	@if [ -d "allure-results" ]; then \
		allure generate allure-results -o allure-report --clean; \
		echo "✅ Allure report generated in allure-report/ directory"; \
	else \
		echo "❌ No test results found. Run tests first with 'make test-allure'"; \
		exit 1; \
	fi

# Serve Allure Report
serve-allure-report: generate-allure-report
	@echo "🌐 Serving Allure report on http://localhost:8080..."
	@allure open allure-report --port 8080 --host 0.0.0.0

# =============================================================================
# Stack-based Commands
# =============================================================================

# Stack Start Commands
start-core: generate-compose
	@echo "🚀 Starting core infrastructure stack..."
	@docker compose -f compose.core.yml up -d
	@echo "✅ Core infrastructure stack started"

start-inference: generate-compose
	@echo "🚀 Starting inference stack..."
	@docker compose -f compose.inference.yml up -d
	@echo "✅ Inference stack started"

start-ai: generate-compose
	@echo "🚀 Starting AI services stack..."
	@docker compose -f compose.ai.yml up -d
	@echo "✅ AI services stack started"

start-ui: generate-compose
	@echo "🚀 Starting UI and workflow stack..."
	@docker compose -f compose.ui.yml up -d
	@echo "✅ UI and workflow stack started"

start-testing: generate-compose
	@echo "🚀 Starting testing stack..."
	@docker compose -f compose.testing.yml up -d
	@echo "✅ Testing stack started"

start-monitoring: generate-compose
	@echo "🚀 Starting monitoring stack..."
	@docker compose -f compose.monitoring.yml up -d
	@echo "✅ Monitoring stack started"

# Stack Stop Commands
stop-core:
	@echo "🛑 Stopping core infrastructure stack..."
	@docker compose -f compose.core.yml down
	@echo "✅ Core infrastructure stack stopped"

stop-inference:
	@echo "🛑 Stopping inference stack..."
	@docker compose -f compose.inference.yml down
	@echo "✅ Inference stack stopped"

stop-ai:
	@echo "🛑 Stopping AI services stack..."
	@docker compose -f compose.ai.yml down
	@echo "✅ AI services stack stopped"

stop-ui:
	@echo "🛑 Stopping UI and workflow stack..."
	@docker compose -f compose.ui.yml down
	@echo "✅ UI and workflow stack stopped"

stop-testing:
	@echo "🛑 Stopping testing stack..."
	@docker compose -f compose.testing.yml down
	@echo "✅ Testing stack stopped"

stop-monitoring:
	@echo "🛑 Stopping monitoring stack..."
	@docker compose -f compose.monitoring.yml down
	@echo "✅ Monitoring stack stopped"

# Stack Restart Commands (no data loss)
restart-core:
	@echo "🔄 Restarting core infrastructure stack..."
	@docker compose -f compose.core.yml restart
	@echo "✅ Core infrastructure stack restarted"

restart-inference:
	@echo "🔄 Restarting inference stack..."
	@docker compose -f compose.inference.yml restart
	@echo "✅ Inference stack restarted"

restart-ai:
	@echo "🔄 Restarting AI services stack..."
	@docker compose -f compose.ai.yml restart
	@echo "✅ AI services stack restarted"

restart-ui:
	@echo "🔄 Restarting UI and workflow stack..."
	@docker compose -f compose.ui.yml restart
	@echo "✅ UI and workflow stack restarted"

restart-testing:
	@echo "🔄 Restarting testing stack..."
	@docker compose -f compose.testing.yml restart
	@echo "✅ Testing stack restarted"

restart-monitoring:
	@echo "🔄 Restarting monitoring stack..."
	@docker compose -f compose.monitoring.yml restart
	@echo "✅ Monitoring stack restarted"

# Stack Rebuild Commands (force image rebuild)
rebuild-ai:
	@echo "🔨 Rebuilding AI services stack..."
	@docker compose -f compose.ai.yml down
	@docker compose -f compose.ai.yml build --no-cache
	@docker compose -f compose.ai.yml up -d
	@echo "✅ AI services stack rebuilt"

# Stack Logs Commands
logs-core:
	@echo "📋 Viewing logs for core infrastructure stack..."
	@docker compose -f compose.core.yml logs -f

logs-inference:
	@echo "📋 Viewing logs for inference stack..."
	@docker compose -f compose.inference.yml logs -f

logs-ai:
	@echo "📋 Viewing logs for AI services stack..."
	@docker compose -f compose.ai.yml logs -f

logs-ui:
	@echo "📋 Viewing logs for UI and workflow stack..."
	@docker compose -f compose.ui.yml logs -f

logs-testing:
	@echo "📋 Viewing logs for testing stack..."
	@docker compose -f compose.testing.yml logs -f

logs-monitoring:
	@echo "📋 Viewing logs for monitoring stack..."
	@docker compose -f compose.monitoring.yml logs -f

# Stack Status Commands
status-core:
	@echo "📊 Status of core infrastructure stack:"
	@docker compose -f compose.core.yml ps

status-inference:
	@echo "📊 Status of inference stack:"
	@docker compose -f compose.inference.yml ps

status-ai:
	@echo "📊 Status of AI services stack:"
	@docker compose -f compose.ai.yml ps

status-ui:
	@echo "📊 Status of UI and workflow stack:"
	@docker compose -f compose.ui.yml ps

status-testing:
	@echo "📊 Status of testing stack:"
	@docker compose -f compose.testing.yml ps

status-monitoring:
	@echo "📊 Status of monitoring stack:"
	@docker compose -f compose.monitoring.yml ps

# =============================================================================
# Network Management Commands
# =============================================================================

# Check for network conflicts
check-network-conflicts:
	@echo "🌐 Checking for network conflicts..."
	@./scripts/check-network-conflicts.sh check

# Clean up orphaned networks
cleanup-networks:
	@echo "🧹 Cleaning up orphaned networks..."
	@./scripts/check-network-conflicts.sh cleanup

# Validate network configuration
validate-networks:
	@echo "✅ Validating network configuration..."
	@./scripts/check-network-conflicts.sh check

# Check network health and connectivity
check-network-health:
	@echo "🏥 Checking network health and connectivity..."
	@echo "📊 Docker network status:"
	@docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}\t{{.CreatedAt}}"
	@echo ""
	@echo "🔍 Network connectivity tests:"
	@echo "Testing core services connectivity..."
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-postgres"; then \
		echo "✅ PostgreSQL: $(docker exec multimodal-postgres pg_isready -U ${POSTGRES_USER:-postgres} 2>/dev/null && echo 'Ready' || echo 'Not ready')"; \
	else \
		echo "❌ PostgreSQL: Not running"; \
	fi
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-redis"; then \
		echo "✅ Redis: $(docker exec multimodal-redis redis-cli ping 2>/dev/null || echo 'Not responding')"; \
	else \
		echo "❌ Redis: Not running"; \
	fi
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-qdrant"; then \
		echo "✅ Qdrant: $(curl -s http://localhost:6333/health 2>/dev/null | grep -q 'ok' && echo 'Healthy' || echo 'Not responding')"; \
	else \
		echo "❌ Qdrant: Not running"; \
	fi
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-minio"; then \
		echo "✅ MinIO: $(curl -s http://localhost:9000/minio/health/live 2>/dev/null | grep -q 'ok' && echo 'Healthy' || echo 'Not responding')"; \
	else \
		echo "❌ MinIO: Not running"; \
	fi
