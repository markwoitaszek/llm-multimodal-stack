# Makefile for Multimodal LLM Stack
# Unified schema-based Docker Compose management

.PHONY: help generate-compose validate-schema clean-compose test-compose

# Default target
help:
	@echo "Multimodal LLM Stack - Unified Compose Management"
	@echo "=================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  generate-compose    Generate all Docker Compose files from unified schema"
	@echo "  validate-schema     Validate the unified schema for errors"
	@echo "  clean-compose       Remove all generated compose files"
	@echo "  test-compose        Test generated compose files for syntax errors"
	@echo "  setup-secrets       Generate environment files and secrets"
	@echo "  start-dev           Start development environment"
	@echo "  start-staging       Start staging environment"
	@echo "  start-prod          Start production environment"
	@echo "  start-gpu           Start GPU-optimized environment"
	@echo "  start-monitoring    Start monitoring environment with ELK stack"
	@echo "  stop                Stop all services"
	@echo "  logs                View logs for all services"
	@echo "  status              Show status of all services"
	@echo "  clean               Clean up containers, volumes, and networks"
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

# Setup secrets and environment files
setup-secrets:
	@echo "Setting up secrets and environment files..."
	python3 setup_secrets.py
	@echo "✅ Secrets and environment files generated"

# Development environment
start-dev: generate-compose setup-secrets
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
start-staging: generate-compose setup-secrets
	@echo "Starting staging environment..."
	docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d
	@echo "✅ Staging environment started"

# Production environment
start-prod: generate-compose setup-secrets
	@echo "Starting production environment..."
	docker compose -f compose.yml -f compose.production.yml --profile services --profile monitoring up -d
	@echo "✅ Production environment started"

# GPU-optimized environment
start-gpu: generate-compose setup-secrets
	@echo "Starting GPU-optimized environment..."
	docker compose -f compose.yml -f compose.gpu.yml -f compose.production.yml up -d
	@echo "✅ GPU-optimized environment started"

# Monitoring environment with ELK stack
start-monitoring: generate-compose setup-secrets
	@echo "Starting monitoring environment with ELK stack..."
	docker compose -f compose.yml -f compose.elk.yml --profile elk --profile monitoring up -d
	@echo "✅ Monitoring environment started"
	@echo "📊 Services available:"
	@echo "   - Kibana: http://localhost:5601"
	@echo "   - Elasticsearch: http://localhost:9200"
	@echo "   - Logstash: http://localhost:9600"

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
	@if find services/ -name "config.py" -exec grep -l ', "postgres")\|, "minioadmin")' {} \; | grep -q .; then \
		echo "❌ Hardcoded defaults found in service configs"; \
		exit 1; \
	fi
	@echo "✅ Security validation passed"

# Enhanced setup with security validation
setup: validate-schema validate-security generate-compose setup-secrets
	@echo "🎉 Full setup completed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "  make start-dev        # Start development environment"
	@echo "  make start-gpu-auto   # Start GPU environment with auto-detection"
	@echo "  make wipe             # Wipe environment (DESTRUCTIVE)"
	@echo "  make reset            # Reset and regenerate from scratch"
