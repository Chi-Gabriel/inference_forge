#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

START_AFTER_SETUP=true
INSTALL_SYSTEM_PACKAGES=true

for arg in "$@"; do
  case "$arg" in
    --no-start)
      START_AFTER_SETUP=false
      ;;
    --no-system-packages)
      INSTALL_SYSTEM_PACKAGES=false
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

install_system_packages() {
  if [ "$INSTALL_SYSTEM_PACKAGES" != "true" ]; then
    return
  fi
  if ! command -v apt-get >/dev/null 2>&1; then
    return
  fi
  if [ "$(id -u)" -ne 0 ]; then
    echo "Skipping apt-get because this user is not root"
    return
  fi
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    ffmpeg \
    python3-venv \
    redis-server
}

ensure_env() {
  if [ ! -f ".env" ]; then
    cp .env.example .env
  fi
  python3 - <<'PY'
from pathlib import Path

path = Path(".env")
text = path.read_text()
updates = {
    "APP_HOST": "0.0.0.0",
    "APP_PORT": "8000",
    "WEB_HOST": "0.0.0.0",
    "WEB_PORT": "3000",
    "CORS_ALLOWED_ORIGINS": "[\"*\"]",
    "REDIS_URL": "redis://localhost:6379/0",
    "JOB_STORE_BACKEND": "redis",
    "START_REDIS": "auto",
    "REDIS_PORT": "6379",
    "REDIS_DIR": "var/redis",
    "MEDIA_ROOT": "var/media",
    "HF_HOME": "hf_cache",
    "HF_HUB_DISABLE_XET": "1",
}
seen = set()
lines = []
for line in text.splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        key = line.split("=", 1)[0]
        if key in updates:
            lines.append(f"{key}={updates[key]}")
            seen.add(key)
            continue
    lines.append(line)
for key, value in updates.items():
    if key not in seen:
        lines.append(f"{key}={value}")
path.write_text("\n".join(lines) + "\n")
PY
}

ensure_venv() {
  if [ ! -x ".venv/bin/python" ]; then
    python3 -m venv .venv
  fi
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/pip install -e '.[dev,gpu]'
}

ensure_directories() {
  mkdir -p var/media var/redis hf_cache
  chmod +x scripts/start.sh scripts/start-api.sh scripts/start-web.sh scripts/start-redis.sh
}

verify_requirements() {
  local missing=()
  command -v ffmpeg >/dev/null 2>&1 || missing+=("ffmpeg")
  command -v redis-server >/dev/null 2>&1 || missing+=("redis-server")
  command -v curl >/dev/null 2>&1 || missing+=("curl")
  if [ "${#missing[@]}" -gt 0 ]; then
    echo "Missing required host tools: ${missing[*]}" >&2
    echo "Install them or rerun setup on a host where apt-get can install packages." >&2
    exit 1
  fi
  .venv/bin/python - <<'PY'
import torch

print(f"torch={torch.__version__}")
print(f"cuda_available={torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"cuda_device={torch.cuda.get_device_name(0)}")
PY
}

install_system_packages
ensure_env
ensure_venv
ensure_directories
verify_requirements

echo "Setup complete"
echo "API: http://0.0.0.0:8000"
echo "Web: http://0.0.0.0:3000"

if [ "$START_AFTER_SETUP" = "true" ]; then
  exec scripts/start.sh
fi
