#!/usr/bin/env bash
# Sync N8N_ENCRYPTION_KEY in your .env to match the key stored
# inside n8n's settings file at /home/node/.n8n/config.
#
# This prevents the "Mismatching encryption keys" error in n8n.
#
# Usage:
#   scripts/sync_n8n_encryption_key.sh [-c multimodal-n8n] [-e .env] [--restart]
#
# -c|--container   Name of the n8n container (default: multimodal-n8n)
# -e|--env-file    Path to the env file to update (default: .env)
# -r|--restart     Restart the container after syncing the key
# -h|--help        Show help

set -Eeuo pipefail

CONTAINER_NAME=${CONTAINER_NAME:-multimodal-n8n}
ENV_FILE=${ENV_FILE:-.env}
RESTART=${RESTART:-false}

usage() {
  cat <<EOF
Sync N8N_ENCRYPTION_KEY to match key stored in /home/node/.n8n/config

Usage: $0 [options]

Options:
  -c, --container  Container name (default: multimodal-n8n)
  -e, --env-file   Env file to update (default: .env)
  -r, --restart    Restart the container after syncing
  -h, --help       Show this help
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--container)
      [[ $# -lt 2 ]] && { echo "Missing value for $1"; exit 1; }
      CONTAINER_NAME="$2"; shift 2;;
    -e|--env-file)
      [[ $# -lt 2 ]] && { echo "Missing value for $1"; exit 1; }
      ENV_FILE="$2"; shift 2;;
    -r|--restart)
      RESTART=true; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown argument: $1"; usage; exit 1;;
  esac
done

# Ensure docker is available
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ docker command not found. Please run this on the host with Docker installed."
  exit 1
fi

# Try to read settings file from a running container first
CONFIG_CONTENT=""
if docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
  CONFIG_CONTENT=$(docker exec "$CONTAINER_NAME" sh -lc 'cat /home/node/.n8n/config 2>/dev/null || true') || true
fi

# If not running or content empty, try reading via the container's named volume
if [[ -z "$CONFIG_CONTENT" ]]; then
  # Attempt to discover the volume that backs /home/node/.n8n
  VOLUME_NAME=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/home/node/.n8n"}}{{.Name}}{{end}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || true)
  if [[ -n "${VOLUME_NAME:-}" ]]; then
    CONFIG_CONTENT=$(docker run --rm -v "${VOLUME_NAME}:/data" alpine sh -lc 'cat /data/config 2>/dev/null || true') || true
  fi
fi

if [[ -z "$CONFIG_CONTENT" ]]; then
  echo "❌ Could not read /home/node/.n8n/config from container or volume."
  echo "   - Ensure the container '$CONTAINER_NAME' exists (docker ps -a)"
  echo "   - If it is running, confirm the path /home/node/.n8n/config exists"
  exit 1
fi

# Extract encryptionKey from the JSON settings
ENCRYPTION_KEY=""
if command -v jq >/dev/null 2>&1; then
  ENCRYPTION_KEY=$(printf '%s' "$CONFIG_CONTENT" | jq -r '.encryptionKey // .encryption_key // empty') || true
fi
if [[ -z "$ENCRYPTION_KEY" ]]; then
  # Fallback to sed-based extraction
  ENCRYPTION_KEY=$(printf '%s' "$CONFIG_CONTENT" | sed -nE 's/.*"encryption(Key|_key)"[[:space:]]*:[[:space:]]*"([^"]+)".*/\2/p' | head -n1)
fi

if [[ -z "$ENCRYPTION_KEY" ]]; then
  echo "❌ Failed to extract encryptionKey from settings file."
  echo "   Content preview:" && printf '%s\n' "$CONFIG_CONTENT" | head -n 20
  exit 1
fi

echo "🔑 Found existing n8n encryption key: [${#ENCRYPTION_KEY} chars]"

# Backup and update the env file
if [[ -f "$ENV_FILE" ]]; then
  cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Update or append N8N_ENCRYPTION_KEY
if [[ -f "$ENV_FILE" ]] && grep -qE '^N8N_ENCRYPTION_KEY=' "$ENV_FILE"; then
  # Use sed with a safe delimiter since key may (rarely) contain '/'
  sed -i.bak "s|^N8N_ENCRYPTION_KEY=.*$|N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
else
  printf '\nN8N_ENCRYPTION_KEY=%s\n' "$ENCRYPTION_KEY" >> "$ENV_FILE"
fi

echo "✅ Updated $ENV_FILE with N8N_ENCRYPTION_KEY (length ${#ENCRYPTION_KEY})."

if [[ "$RESTART" == "true" ]]; then
  echo "♻️  Restarting container $CONTAINER_NAME ..."
  if docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
    docker restart "$CONTAINER_NAME" >/dev/null
  else
    # If container exists but is stopped, try starting via compose (best effort)
    if command -v docker compose >/dev/null 2>&1; then
      docker compose up -d n8n >/dev/null || true
    else
      echo "ℹ️  docker compose not available; please start the container manually."
    fi
  fi
  echo "✅ Container restart issued."
else
  echo "ℹ️  Skipping restart. To restart now: docker restart $CONTAINER_NAME"
fi

echo "🎉 Done. n8n should start without the mismatched encryption key error."
