#!/bin/bash

# Generate LiteLLM configuration with environment variables
echo "🔧 Generating LiteLLM configuration with current environment..."

# Source environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Generate the configuration file
cat > configs/litellm_config_generated.yaml << EOF
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: openai/gpt-3.5-turbo
      api_base: http://vllm:8000/v1
      api_key: dummy-key
      
  - model_name: local-llm
    litellm_params:
      model: openai/local-model
      api_base: http://vllm:8000/v1
      api_key: dummy-key

router_settings:
  routing_strategy: simple-shuffle
  model_group_alias:
    gpt-3.5-turbo: local-llm

litellm_settings:
  drop_params: true
  set_verbose: false
  json_logs: true

general_settings:
  completion_model: local-llm
  master_key: ${LITELLM_MASTER_KEY:-sk-1234}
  database_url: postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-multimodal}
EOF

echo "✅ Generated configs/litellm_config_generated.yaml"
echo "🔧 Database URL: postgresql://${POSTGRES_USER}:***@postgres:5432/${POSTGRES_DB}"
