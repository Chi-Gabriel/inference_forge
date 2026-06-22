#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v redis-server >/dev/null 2>&1; then
  echo "redis-server is not installed" >&2
  exit 127
fi

env_value() {
  local key="$1"
  local default="$2"
  local current="${!key:-}"
  if [ -n "$current" ]; then
    echo "$current"
    return
  fi
  if [ -f ".env" ]; then
    local from_file
    from_file="$(grep -E "^${key}=" .env | tail -n 1 | cut -d= -f2- || true)"
    if [ -n "$from_file" ]; then
      echo "$from_file"
      return
    fi
  fi
  echo "$default"
}

REDIS_PORT="$(env_value REDIS_PORT 6379)"
REDIS_DIR="$(env_value REDIS_DIR var/redis)"

mkdir -p "$REDIS_DIR"

exec redis-server \
  --bind 127.0.0.1 \
  --port "$REDIS_PORT" \
  --dir "$REDIS_DIR" \
  --appendonly yes
