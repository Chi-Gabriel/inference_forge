#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PIDS=()

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

port_open() {
  python3 - "$1" <<'PY'
import socket
import sys

sock = socket.socket()
sock.settimeout(0.2)
try:
    sock.connect(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

cleanup() {
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
}

trap cleanup EXIT INT TERM

START_REDIS_VALUE="$(env_value START_REDIS auto)"
REDIS_PORT_VALUE="$(env_value REDIS_PORT 6379)"
WEB_HOST_VALUE="$(env_value WEB_HOST 0.0.0.0)"
WEB_PORT_VALUE="$(env_value WEB_PORT 3000)"

if [ "$START_REDIS_VALUE" != "false" ] && port_open "$REDIS_PORT_VALUE"; then
  echo "Redis already appears to be listening on 127.0.0.1:${REDIS_PORT_VALUE}"
elif [ "$START_REDIS_VALUE" != "false" ] && command -v redis-server >/dev/null 2>&1; then
  REDIS_PORT="$REDIS_PORT_VALUE" scripts/start-redis.sh &
  PIDS+=("$!")
  sleep 1
elif [ "$START_REDIS_VALUE" = "true" ]; then
  echo "START_REDIS=true but redis-server is not installed" >&2
  exit 127
fi

scripts/start-api.sh &
PIDS+=("$!")

WEB_HOST="$WEB_HOST_VALUE" WEB_PORT="$WEB_PORT_VALUE" scripts/start-web.sh &
PIDS+=("$!")

wait -n "${PIDS[@]}"
