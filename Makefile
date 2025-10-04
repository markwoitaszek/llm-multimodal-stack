# Comprehensive Makefile for LLM Multimodal Stack
# Combines streamlined essential commands with all extended options

.PHONY: help help-essential help-extended setup start-dev start-staging start-dev-gpu start-staging-gpu stop stop-all stop-dev stop-staging stop-prod stop-gpu force-stop wipe wipe-confirm reset status logs clean

# Default target - shows essential commands
help:
	@echo "🚀 LLM Multimodal Stack - Essential Commands"
	@echo "============================================="
	@echo ""
	@echo "📋 Essential Commands:"
	@echo "  setup              Complete setup from scratch"
	@echo "  start-dev          Start development environment"
	@echo "  start-staging      Start staging environment"
	@echo "  start-dev-gpu      Start development with GPU support"
	@echo "  start-staging-gpu  Start staging with GPU support"
	@echo ""
	@echo "🔧 Management Commands:"
	@echo "  stop               Stop main services (basic)"
	@echo "  stop-all           Stop ALL services from ALL compose files"
	@echo "  stop-dev           Stop development environment"
	@echo "  stop-staging       Stop staging environment"
	@echo "  stop-prod          Stop production environment"
	@echo "  wipe-nuclear       💥 NUCLEAR wipe (complete destruction - type 'NUKE')"
	@echo "  reset              Nuclear reset (wipe + setup)"
	@echo "  status             Show service status"
	@echo "  logs               View service logs"
	@echo ""
	@echo "🎮 GPU Commands:"
	@echo "  detect-gpu         Detect GPU configuration"
	@echo "  configure-gpu      Configure GPU settings"
	@echo ""
	@echo "📚 Extended Options:"
	@echo "  help-extended      Show all extended commands"
	@echo "  help-essential     Show this essential commands list"
	@echo ""

# Extended help - shows all available commands
help-extended:
	@echo "🚀 LLM Multimodal Stack - All Commands"
	@echo "======================================"
	@echo ""
	@echo "📋 Essential Commands:"
	@echo "  setup              Complete setup from scratch"
	@echo "  start-dev          Start development environment"
	@echo "  start-staging      Start staging environment"
	@echo "  start-dev-gpu      Start development with GPU support"
	@echo "  start-staging-gpu  Start staging with GPU support"
	@echo ""
	@echo "🔧 Management Commands:"
	@echo "  stop               Stop main services (basic)"
	@echo "  stop-all           Stop ALL services from ALL compose files"
	@echo "  stop-dev           Stop development environment"
	@echo "  stop-staging       Stop staging environment"
	@echo "  stop-prod          Stop production environment"
	@echo "  wipe-nuclear       💥 NUCLEAR wipe (complete destruction - type 'NUKE')"
	@echo "  reset              Nuclear reset (wipe + setup)"
	@echo "  status             Show service status"
	@echo "  logs               View service logs"
	@echo "  clean              Clean up containers, volumes, and networks"
	@echo ""
	@echo "🎮 GPU Commands:"
	@echo "  detect-gpu         Detect GPU configuration"
	@echo "  configure-gpu      Configure GPU settings"
	@echo ""
	@echo "📄 Schema & Compose Commands:"
	@echo "  generate-compose   Generate all Docker Compose files from unified schema"
	@echo "  validate-schema    Validate the unified schema for errors"
	@echo "  validate-security  Validate security configuration (no hardcoded defaults)"
	@echo "  clean-compose      Remove all generated compose files"
	@echo "  test-compose       Test generated compose files for syntax errors"
	@echo ""
	@echo "🔐 Secret Management Commands:"
	@echo "  setup-secrets      Generate environment files and secrets (development)"
	@echo "  setup-secrets-dev  Generate secrets for development"
	@echo "  setup-secrets-staging Generate secrets for staging"
	@echo "  setup-secrets-prod Generate secrets for production"
	@echo ""
	@echo "🔒 Credential Validation Commands:"
	@echo "  validate-credentials Validate credentials for deployment (ENV=environment STRICT=true/false)"
	@echo "  validate-credentials-dev Validate credentials for development"
	@echo "  validate-credentials-staging Validate credentials for staging (strict)"
	@echo "  validate-credentials-prod Validate credentials for production (strict)"
	@echo ""
	@echo "🌍 Extended Environment Commands:"
	@echo "  start-prod         Start production environment (with validation)"
	@echo "  start-prod-gpu     Start production environment with GPU support"
	@echo "  start-monitoring   Start monitoring environment with ELK stack"
	@echo "  start-testing      Start testing environment with Allure and JMeter"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  setup-testing      Setup testing environment and dependencies"
	@echo "  test-allure        Run tests with Allure reporting"
	@echo "  test-jmeter        Run JMeter performance tests"
	@echo "  test-unit          Run unit tests only"
	@echo "  test-integration   Run integration tests only"
	@echo "  test-api           Run API tests only"
	@echo "  generate-allure-report Generate Allure test report"
	@echo "  serve-allure-report Serve Allure report on localhost:8080"
	@echo ""
	@echo "🏗️ Stack-based Commands:"
	@echo "  start-core         Start core infrastructure stack (postgres, redis, qdrant, minio)"
	@echo "  start-inference    Start inference stack (vllm, litellm)"
	@echo "  start-ai           Start AI services stack (worker, retrieval, agents, memory, search)"
	@echo "  start-ui           Start UI and workflow stack (openwebui, n8n, n8n-monitoring, nginx)"
	@echo ""
	@echo "🛑 Stack Management Commands:"
	@echo "  stop-core          Stop core infrastructure stack"
	@echo "  stop-inference     Stop inference stack"
	@echo "  stop-ai            Stop AI services stack"
	@echo "  stop-ui            Stop UI and workflow stack"
	@echo "  stop-testing       Stop testing stack"
	@echo "  stop-monitoring    Stop monitoring stack"
	@echo ""
	@echo "🔄 Stack Restart Commands:"
	@echo "  restart-core       Restart core infrastructure stack (no data loss)"
	@echo "  restart-inference  Restart inference stack (no data loss)"
	@echo "  restart-ai         Restart AI services stack (no data loss)"
	@echo "  restart-ui         Restart UI and workflow stack (no data loss)"
	@echo "  restart-testing    Restart testing stack (no data loss)"
	@echo "  restart-monitoring Restart monitoring stack (no data loss)"
	@echo "  rebuild-ai         Rebuild AI services stack (force image rebuild)"
	@echo ""
	@echo "📋 Stack Logs & Status Commands:"
	@echo "  logs-core          View logs for core infrastructure stack"
	@echo "  logs-inference     View logs for inference stack"
	@echo "  logs-ai            View logs for AI services stack"
	@echo "  logs-ui            View logs for UI and workflow stack"
	@echo "  status-core        Show status of core infrastructure stack"
	@echo "  status-inference   Show status of inference stack"
	@echo "  status-ai          Show status of AI services stack"
	@echo "  status-ui          Show status of UI and workflow stack"
	@echo ""
	@echo "🌐 Network Management Commands:"
	@echo "  check-network-conflicts Check for network conflicts before starting stacks"
	@echo "  cleanup-networks   Clean up orphaned networks"
	@echo "  validate-networks  Validate network configuration"
	@echo "  check-network-health Check network health and connectivity"
	@echo ""
	@echo "🧹 Granular Wipe/Reset Commands:"
	@echo "  wipe-core          Wipe core infrastructure stack (containers + data)"
	@echo "  wipe-inference     Wipe inference stack (containers + data)"
	@echo "  wipe-ai            Wipe AI services stack (containers + data)"
	@echo "  wipe-ui            Wipe UI and workflow stack (containers + data)"
	@echo "  wipe-db            Wipe database volumes only"
	@echo "  wipe-cache         Wipe cache volumes only"
	@echo "  wipe-models        Wipe model cache only"
	@echo "  wipe-logs          Wipe log volumes only"
	@echo "  wipe-test-results  Wipe test results only"
	@echo "  wipe-dev           Wipe development environment"
	@echo "  wipe-staging       Wipe staging environment"
	@echo "  wipe-prod          Wipe production environment"
	@echo "  system-status      Show current system status"
	@echo ""
	@echo "📊 Data Retention & Backup Commands:"
	@echo "  retention-status [env] Show retention status for environment"
	@echo "  retention-cleanup [env] Run retention cleanup for environment"
	@echo "  retention-test [env] Test retention cleanup (dry run)"
	@echo "  backup-status [env] Show backup status for environment"
	@echo "  backup-full [env] Run full backup for environment"
	@echo "  backup-list [env] List available backups for environment"
	@echo ""
	@echo "🧪 Enterprise Testing Commands:"
	@echo "  test-stack-operations Test stack-based operations (start, stop, restart, status)"
	@echo "  test-network-operations Test network management and isolation"
	@echo "  test-data-operations Test data retention and backup operations"
	@echo "  test-granular-operations Test granular wipe/reset operations"
	@echo "  test-comprehensive Run comprehensive test suite for all enterprise features"
	@echo "  test-quick Run quick tests (non-destructive)"
	@echo "  test-report Generate comprehensive test report"
	@echo "  test-monitoring Test monitoring and alerting system"
	@echo ""

# Essential commands help
help-essential:
	@$(MAKE) help

# =============================================================================
# ESSENTIAL COMMANDS (Streamlined)
# =============================================================================

# Complete setup from scratch
setup:
	@echo "🎯 Setting up LLM Multimodal Stack..."
	@$(MAKE) validate-schema
	@$(MAKE) generate-compose
	@$(MAKE) setup-secrets-dev
	@$(MAKE) validate-credentials-dev
	@echo "✅ Setup complete! Use 'make start-dev' or 'make start-dev-gpu' to begin"

# Development environment
start-dev: generate-compose setup-secrets-dev validate-credentials-dev
	@echo "🚀 Starting development environment..."
	docker compose up -d
	@echo "✅ Development environment started"
	@echo "📊 Services available:"
	@echo "   - LiteLLM: http://localhost:4000"
	@echo "   - vLLM: http://localhost:8000"
	@echo "   - Multimodal Worker: http://localhost:8001"
	@echo "   - Retrieval Proxy: http://localhost:8002"
	@echo "   - Qdrant: http://localhost:6333"
	@echo "   - MinIO Console: http://localhost:9002"

# Staging environment
start-staging: generate-compose setup-secrets-staging validate-credentials-staging
	@echo "🚀 Starting staging environment..."
	docker compose -f compose.yml -f compose.staging.yml up -d
	@echo "✅ Staging environment started"

# Development with GPU support
start-dev-gpu: configure-gpu start-dev
	@echo "🎮 GPU-enabled development environment started"
	@echo "📊 GPU Configuration:"
	@echo "   CUDA_VISIBLE_DEVICES: $$(grep '^CUDA_VISIBLE_DEVICES=' .env 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
	@echo "   GPU_COUNT: $$(grep '^GPU_COUNT=' .env 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"

# Staging with GPU support
start-staging-gpu: configure-gpu
	@echo "🚀 Starting staging environment with GPU support..."
	@$(MAKE) generate-compose
	@$(MAKE) setup-secrets-staging
	@$(MAKE) validate-credentials-staging
	docker compose -f compose.yml -f compose.staging.yml up -d
	@echo "✅ Staging environment with GPU started"
	@echo "📊 GPU Configuration:"
	@echo "   CUDA_VISIBLE_DEVICES: $$(grep '^CUDA_VISIBLE_DEVICES=' .env 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
	@echo "   GPU_COUNT: $$(grep '^GPU_COUNT=' .env 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"

# GPU detection
detect-gpu:
	@echo "🔍 Detecting GPU configuration..."
	@scripts/configure-gpu.sh detect

# GPU configuration
configure-gpu:
	@echo "🎮 Configuring GPU for optimal performance..."
	@scripts/configure-gpu.sh auto

# Stop all services (basic - only main compose file)
stop:
	@echo "🛑 Stopping main services..."
	docker compose down
	@echo "✅ Main services stopped"

# Stop ALL services from ALL compose files (comprehensive)
stop-all:
	@echo "🛑 Stopping ALL services from ALL compose files..."
	@echo "📋 Stopping main services..."
	@docker compose down 2>/dev/null || true
	@echo "📋 Stopping staging services..."
	@docker compose -f compose.yml -f compose.staging.yml down 2>/dev/null || true
	@echo "📋 Stopping production services..."
	@docker compose -f compose.yml -f compose.production.yml down 2>/dev/null || true
	@echo "📋 Stopping development services..."
	@docker compose -f compose.yml -f compose.development.yml down 2>/dev/null || true
	@echo "📋 Stopping GPU services..."
	@docker compose -f compose.yml -f compose.gpu.yml down 2>/dev/null || true
	@echo "📋 Stopping monitoring services..."
	@docker compose -f compose.monitoring.yml down 2>/dev/null || true
	@docker compose -f compose.elk.yml down 2>/dev/null || true
	@docker compose -f compose.logging.yml down 2>/dev/null || true
	@echo "📋 Stopping testing services..."
	@docker compose -f compose.testing.yml down 2>/dev/null || true
	@echo "📋 Stopping stack-based services..."
	@docker compose -f compose.core.yml down 2>/dev/null || true
	@docker compose -f compose.inference.yml down 2>/dev/null || true
	@docker compose -f compose.ai.yml down 2>/dev/null || true
	@docker compose -f compose.ui.yml down 2>/dev/null || true
	@docker compose -f compose.services.yml down 2>/dev/null || true
	@docker compose -f compose.n8n-monitoring.yml down 2>/dev/null || true
	@echo "🧹 Cleaning up orphaned containers..."
	@docker container prune -f 2>/dev/null || true
	@echo "🧹 Cleaning up orphaned networks..."
	@docker network prune -f 2>/dev/null || true
	@echo "✅ ALL services stopped and cleaned up"
	@echo "💡 Use 'make status' to verify all services are stopped"

# Force stop all containers (emergency - kills everything)
force-stop:
	@echo "🚨 FORCE STOPPING ALL CONTAINERS..."
	@echo "⚠️  This will forcefully kill ALL containers without graceful shutdown"
	@echo "📋 Force killing all multimodal containers..."
	@docker ps -q --filter "name=multimodal" | xargs -r docker kill 2>/dev/null || true
	@echo "📋 Force killing all containers from compose files..."
	@docker ps -q --filter "label=com.docker.compose.project=llm-multimodal-stack" | xargs -r docker kill 2>/dev/null || true
	@echo "📋 Removing all containers..."
	@docker ps -aq --filter "name=multimodal" | xargs -r docker rm -f 2>/dev/null || true
	@docker ps -aq --filter "label=com.docker.compose.project=llm-multimodal-stack" | xargs -r docker rm -f 2>/dev/null || true
	@echo "🧹 Cleaning up networks..."
	@docker network prune -f 2>/dev/null || true
	@echo "✅ FORCE STOP completed"
	@echo "💡 Use 'make status' to verify all services are stopped"

# Nuclear wipe with interactive confirmation - COMPLETE ENVIRONMENT DESTRUCTION
wipe-nuclear:
	@echo "💥 NUCLEAR ENVIRONMENT WIPE"
	@echo "==========================="
	@echo ""
	@echo "🚨 DANGER: This will COMPLETELY DESTROY your entire environment!"
	@echo ""
	@echo "📋 What will be NUKED:"
	@echo "   • ALL multimodal containers and services"
	@echo "   • ALL PostgreSQL database volumes (DATA LOSS!)"
	@echo "   • ALL MinIO object storage volumes (DATA LOSS!)"
	@echo "   • ALL Redis cache volumes (DATA LOSS!)"
	@echo "   • ALL multimodal networks"
	@echo "   • ALL orphaned containers and volumes"
	@echo "   • Generated compose files"
	@echo ""
	@echo "🔍 Current system status:"
	@echo "   Running containers: $$(docker ps --format '{{.Names}}' | grep multimodal | wc -l)"
	@echo "   Multimodal volumes: $$(docker volume ls --format '{{.Name}}' | grep multimodal | wc -l)"
	@echo "   Multimodal networks: $$(docker network ls --format '{{.Name}}' | grep multimodal | wc -l)"
	@echo ""
	@echo "💡 For detailed preview, use: ./scripts/wipe-environment-fixed.sh preview"
	@echo "💡 For targeted fixes, use: make wipe-ui, make wipe-core, etc."
	@echo ""
	@bash -c 'read -p "Type '\''NUKE'\'' to confirm nuclear wipe: " -r; \
	if [ "$$REPLY" = "NUKE" ]; then \
		echo ""; \
		echo "💥 Executing nuclear wipe..."; \
		./scripts/wipe-environment-fixed.sh force; \
		echo "✅ Nuclear wipe completed"; \
		echo ""; \
		echo "💡 Next steps:"; \
		echo "   make setup     # Set up fresh environment"; \
		echo "   make reset     # Nuclear reset (wipe + setup)"; \
	else \
		echo ""; \
		echo "❌ Nuclear wipe cancelled by user"; \
	fi'

# Confirmation wipe (after preview)
wipe-confirm:
	@echo "🧹 Starting wipe process..."
	@docker compose down --volumes --remove-orphans 2>/dev/null || true
	@docker container prune -f 2>/dev/null || true
	@docker volume prune -f 2>/dev/null || true
	@docker network prune -f 2>/dev/null || true
	@echo "✅ Environment wiped successfully"
	@echo ""
	@echo "💡 Next steps:"
	@echo "   make setup     # Set up fresh environment"
	@echo "   make reset     # Nuclear reset (wipe + setup)"

# Legacy alias for backward compatibility
wipe: wipe-nuclear
	@echo "⚠️  DEPRECATED: 'make wipe' is deprecated. Use 'make wipe-nuclear' instead."

# Nuclear reset (wipe + setup)
reset: wipe-nuclear setup
	@echo "🎉 Nuclear reset complete!"
	@echo "✅ Fresh environment ready"

# Show service status
status:
	@echo "📊 Service Status:"
	@echo "=================="
	@docker compose ps

# View service logs
logs:
	@echo "📋 Viewing service logs..."
	@docker compose logs -f

# =============================================================================
# EXTENDED COMMANDS (All Original Functionality)
# =============================================================================

# Generate all compose files from unified schema
generate-compose:
	@echo "📄 Generating Docker Compose files..."
	python3 scripts/compose-generator.py
	@echo "✅ Compose files generated"

# Validate the unified schema
validate-schema:
	@echo "🔍 Validating schema..."
	python3 scripts/compose-generator.py --validate-only
	@echo "✅ Schema validation passed"

# Clean generated compose files
clean-compose:
	@echo "🧹 Cleaning generated compose files..."
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

# Enhanced GPU start with auto-detection
start-gpu-auto: detect-gpu configure-gpu start-gpu
	@echo "✅ GPU environment started with auto-configuration"

# Monitoring environment with ELK stack
start-monitoring: generate-compose
	@echo "Starting monitoring environment with ELK stack..."
	docker compose -f compose.yml -f compose.elk.yml up -d
	@echo "✅ Monitoring environment started"

# Testing Environment Setup
setup-testing: generate-compose
	@echo "🧪 Setting up testing environment..."
	@mkdir -p allure-results allure-report test-results
	@echo "✅ Testing environment setup completed"

# Start Testing Environment
start-testing: setup-testing
	@echo "Starting testing environment..."
	docker compose -f compose.yml -f compose.testing.yml up -d
	@echo "✅ Testing environment started"

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
# STACK-BASED COMMANDS
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

# Stack Stop Commands
stop-core:
	@echo "🛑 Stopping core infrastructure stack..."
	@docker compose -f compose.core.yml down 2>/dev/null || true
	@echo "✅ Core infrastructure stack stopped"

stop-inference:
	@echo "🛑 Stopping inference stack..."
	@docker compose -f compose.inference.yml down 2>/dev/null || true
	@echo "✅ Inference stack stopped"

stop-ai:
	@echo "🛑 Stopping AI services stack..."
	@docker compose -f compose.ai.yml down 2>/dev/null || true
	@echo "✅ AI services stack stopped"

stop-ui:
	@echo "🛑 Stopping UI and workflow stack..."
	@docker compose -f compose.ui.yml down 2>/dev/null || true
	@echo "✅ UI and workflow stack stopped"

stop-testing:
	@echo "🛑 Stopping testing stack..."
	@docker compose -f compose.testing.yml down 2>/dev/null || true
	@echo "✅ Testing stack stopped"

stop-monitoring:
	@echo "🛑 Stopping monitoring stack..."
	@docker compose -f compose.monitoring.yml down 2>/dev/null || true
	@docker compose -f compose.elk.yml down 2>/dev/null || true
	@docker compose -f compose.logging.yml down 2>/dev/null || true
	@docker compose -f compose.n8n-monitoring.yml down 2>/dev/null || true
	@echo "✅ Monitoring stack stopped"

# Environment-specific stop commands
stop-dev:
	@echo "🛑 Stopping development environment..."
	@docker compose -f compose.yml -f compose.development.yml down 2>/dev/null || true
	@echo "✅ Development environment stopped"

stop-staging:
	@echo "🛑 Stopping staging environment..."
	@docker compose -f compose.yml -f compose.staging.yml down 2>/dev/null || true
	@echo "✅ Staging environment stopped"

stop-prod:
	@echo "🛑 Stopping production environment..."
	@docker compose -f compose.yml -f compose.production.yml down 2>/dev/null || true
	@echo "✅ Production environment stopped"

stop-gpu:
	@echo "🛑 Stopping GPU services..."
	@docker compose -f compose.yml -f compose.gpu.yml down 2>/dev/null || true
	@echo "✅ GPU services stopped"

# Stack Restart Commands
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

# Stack Rebuild Commands
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
# NETWORK MANAGEMENT COMMANDS
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
		echo "✅ PostgreSQL: $$(docker exec multimodal-postgres pg_isready -U $${POSTGRES_USER:-postgres} 2>/dev/null && echo 'Ready' || echo 'Not ready')"; \
	else \
		echo "❌ PostgreSQL: Not running"; \
	fi
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-redis"; then \
		echo "✅ Redis: $$(docker exec multimodal-redis redis-cli ping 2>/dev/null || echo 'Not responding')"; \
	else \
		echo "❌ Redis: Not running"; \
	fi
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-qdrant"; then \
		echo "✅ Qdrant: $$(curl -s http://localhost:6333/health 2>/dev/null | grep -q 'ok' && echo 'Healthy' || echo 'Not responding')"; \
	else \
		echo "❌ Qdrant: Not running"; \
	fi
	@if docker ps --format "{{.Names}}" | grep -q "multimodal-minio"; then \
		echo "✅ MinIO: $$(curl -s http://localhost:9000/minio/health/live 2>/dev/null | grep -q 'ok' && echo 'Healthy' || echo 'Not responding')"; \
	else \
		echo "❌ MinIO: Not running"; \
	fi

# =============================================================================
# GRANULAR WIPE/RESET COMMANDS
# =============================================================================

# Stack Wipe Commands (containers + data)
wipe-core:
	@echo "🧹 Wiping core infrastructure stack..."
	@./scripts/wipe-environment.sh wipe-stack core

wipe-inference:
	@echo "🧹 Wiping inference stack..."
	@./scripts/wipe-environment.sh wipe-stack inference

wipe-ai:
	@echo "🧹 Wiping AI services stack..."
	@./scripts/wipe-environment.sh wipe-stack ai

wipe-ui:
	@echo "🧹 Wiping UI and workflow stack..."
	@./scripts/wipe-environment.sh wipe-stack ui

wipe-testing:
	@echo "🧹 Wiping testing stack..."
	@./scripts/wipe-environment.sh wipe-stack testing

wipe-monitoring:
	@echo "🧹 Wiping monitoring stack..."
	@./scripts/wipe-environment.sh wipe-stack monitoring

# Data-Specific Wipe Commands
wipe-db:
	@echo "🗑️  Wiping database volumes..."
	@./scripts/wipe-environment.sh wipe-db

wipe-cache:
	@echo "🗑️  Wiping cache volumes..."
	@./scripts/wipe-environment.sh wipe-cache

wipe-models:
	@echo "🗑️  Wiping model cache..."
	@./scripts/wipe-environment.sh wipe-models

wipe-logs:
	@echo "🗑️  Wiping log volumes..."
	@./scripts/wipe-environment.sh wipe-logs

wipe-test-results:
	@echo "🗑️  Wiping test results..."
	@./scripts/wipe-environment.sh wipe-test-results

# Environment-Specific Wipe Commands
wipe-dev:
	@echo "🗑️  Wiping development environment..."
	@./scripts/wipe-environment.sh wipe-dev

wipe-staging:
	@echo "🗑️  Wiping staging environment..."
	@./scripts/wipe-environment.sh wipe-staging

wipe-prod:
	@echo "🗑️  Wiping production environment..."
	@./scripts/wipe-environment.sh wipe-prod

# System Status
system-status:
	@echo "📊 Showing system status..."
	@./scripts/wipe-environment.sh status

# =============================================================================
# DATA RETENTION MANAGEMENT COMMANDS
# =============================================================================

# Show retention status for environment
retention-status:
	@echo "📊 Showing retention status..."
	@./scripts/manage-retention.sh status $(ENVIRONMENT)

# Run retention cleanup for environment
retention-cleanup:
	@echo "🧹 Running retention cleanup..."
	@./scripts/manage-retention.sh cleanup $(ENVIRONMENT)

# Test retention cleanup (dry run)
retention-test:
	@echo "🔍 Testing retention cleanup (dry run)..."
	@./scripts/manage-retention.sh test $(ENVIRONMENT)

# Cleanup specific service
retention-cleanup-service:
	@echo "🧹 Cleaning up specific service..."
	@./scripts/manage-retention.sh cleanup-service $(SERVICE) $(ENVIRONMENT)

# Show retention schedules
retention-schedule:
	@echo "📅 Showing retention schedules..."
	@echo "Development: Daily at 1 AM"
	@echo "Staging: Daily at 2 AM"
	@echo "Production: Weekly on Sunday at 3 AM"
	@echo "Testing: Daily at midnight"

# Create backups before cleanup
retention-backup:
	@echo "💾 Creating backups before cleanup..."
	@echo "This would create backups of all data before running cleanup"
	@echo "Implementation depends on backup strategy configuration"

# =============================================================================
# MULTI-TIER BACKUP SYSTEM COMMANDS
# =============================================================================

# Show backup status for environment
backup-status:
	@echo "📊 Showing backup status..."
	@./scripts/manage-backups.sh status $(ENVIRONMENT)

# Run full backup for environment
backup-full:
	@echo "💾 Running full backup..."
	@./scripts/manage-backups.sh backup $(ENVIRONMENT)

# Backup specific service
backup-service:
	@echo "💾 Backing up specific service..."
	@./scripts/manage-backups.sh backup-service $(SERVICE) $(ENVIRONMENT) $(BACKUP_TYPE)

# List available backups for environment
backup-list:
	@echo "📋 Listing available backups..."
	@./scripts/manage-backups.sh list $(ENVIRONMENT)

# Verify backup integrity
backup-verify:
	@echo "🔍 Verifying backup integrity..."
	@echo "This would verify the integrity of all backups"
	@echo "Implementation depends on backup verification strategy"

# Show backup schedules
backup-schedule:
	@echo "📅 Showing backup schedules..."
	@echo "Development: Daily at 2 AM"
	@echo "Staging: Daily at 3 AM"
	@echo "Production: Daily at 1 AM"
	@echo "Testing: Daily at 4 AM"

# Restore from backup
backup-restore:
	@echo "🔄 Restoring from backup..."
	@echo "This would restore from a specific backup file"
	@echo "Implementation depends on restore strategy configuration"

# =============================================================================
# ENTERPRISE TESTING COMMANDS
# =============================================================================

# Test stack operations
test-stack-operations:
	@echo "🧪 Testing stack operations..."
	@./scripts/test-stack-operations.sh

# Test network operations
test-network-operations:
	@echo "🌐 Testing network operations..."
	@./scripts/test-network-operations.sh

# Test data operations
test-data-operations:
	@echo "💾 Testing data operations..."
	@./scripts/test-data-operations.sh

# Test granular operations
test-granular-operations:
	@echo "🔧 Testing granular operations..."
	@./scripts/test-granular-operations.sh

# Run comprehensive test suite
test-comprehensive:
	@echo "🧪 Running comprehensive test suite..."
	@./scripts/test-comprehensive.sh

# Run quick tests (non-destructive)
test-quick:
	@echo "🚀 Running quick tests (non-destructive)..."
	@./scripts/test-comprehensive.sh --quick

# Generate comprehensive test report
test-report:
	@echo "📊 Generating comprehensive test report..."
	@./scripts/test-comprehensive.sh --report

# Test monitoring and alerting system
test-monitoring:
	@echo "📊 Testing monitoring and alerting system..."
	@./scripts/test-monitoring.sh init
	@./scripts/test-monitoring.sh status

# Test documentation
test-documentation:
	@echo "📚 Testing documentation..."
	@./scripts/test-documentation.sh

# =============================================================================
# SECURITY AND VALIDATION COMMANDS
# =============================================================================

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

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

# Clean up everything
clean:
	@echo "Cleaning up containers, volumes, and networks..."
	docker compose down --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed"
