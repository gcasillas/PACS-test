#!/usr/bin/env bash
set -euo pipefail

wait_for_port() {
  local host="$1"
  local port="$2"
  local label="$3"
  local timeout_secs="${4:-180}"
  local start
  start=$(date +%s)

  while true; do
    if timeout 1 bash -lc "cat < /dev/null > /dev/tcp/${host}/${port}" 2>/dev/null; then
      echo "✅ ${label} is reachable on ${host}:${port}"
      return 0
    fi

    local now elapsed
    now=$(date +%s)
    elapsed=$((now - start))
    if (( elapsed >= timeout_secs )); then
      echo "❌ Timed out waiting for ${label} on ${host}:${port} after ${timeout_secs}s"
      return 1
    fi

    sleep 2
  done
}

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ docker CLI not found in this shell."
  echo "Run this from a Docker-enabled terminal (or use Codespaces Rebuild Container)."
  exit 1
fi

echo "▶ Starting PACS-test demo stack..."
docker compose up -d

echo "▶ Waiting for services..."
wait_for_port 127.0.0.1 8042 "Orthanc" 180
wait_for_port 127.0.0.1 8080 "OpenEMR" 300

echo
echo "🎉 Demo stack is ready"
echo "Orthanc: http://127.0.0.1:8042"
echo "  user: orthanc_user"
echo "  pass: orthanc_secure_pass"
echo
echo "OpenEMR: http://127.0.0.1:8080/interface/login/login.php?site=default"
echo "  user: admin"
echo "  pass: AdminPass123!"
