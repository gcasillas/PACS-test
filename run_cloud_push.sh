#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"
REQ_HASH_FILE="$VENV_DIR/.requirements.sha256"

created_venv=false

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
  created_venv=true
fi

source "$VENV_DIR/bin/activate"

current_hash="$(sha256sum "$REQUIREMENTS_FILE" | awk '{print $1}')"
cached_hash=""

if [[ -f "$REQ_HASH_FILE" ]]; then
  cached_hash="$(cat "$REQ_HASH_FILE")"
fi

if [[ "$created_venv" == "true" || "$current_hash" != "$cached_hash" ]]; then
  python -m pip install --upgrade pip
  python -m pip install -r "$REQUIREMENTS_FILE"
  printf '%s\n' "$current_hash" > "$REQ_HASH_FILE"
else
  echo "✅ Dependencies unchanged, skipping install"
fi

python "$ROOT_DIR/cloud_push.py"