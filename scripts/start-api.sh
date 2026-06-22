#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

if [ ! -x ".venv/bin/uvicorn" ]; then
  .venv/bin/pip install -e '.[dev,gpu]'
fi

read_env() {
  .venv/bin/python - "$1" "$2" <<'PY'
import sys
from dotenv import dotenv_values

key, default = sys.argv[1], sys.argv[2]
print(dotenv_values(".env").get(key) or default)
PY
}

APP_HOST_VALUE="$(read_env APP_HOST 0.0.0.0)"
APP_PORT_VALUE="$(read_env APP_PORT 8000)"
export HF_HOME="$(read_env HF_HOME hf_cache)"
export HF_HUB_DISABLE_XET="$(read_env HF_HUB_DISABLE_XET 1)"

mkdir -p var/media "$HF_HOME"

exec .venv/bin/uvicorn app.main:app --host "$APP_HOST_VALUE" --port "$APP_PORT_VALUE"
