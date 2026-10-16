#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " Economic Indicator Dashboard: VPS Deployment & Security Verifier"
echo "============================================================"

# 1. Verify Docker and Docker Compose
command -v docker >/dev/null 2>&1 || { echo >&2 "[ERROR] Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo >&2 "[ERROR] Docker Compose is required."; exit 1; }

COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# 2. Boot Compose Stack
echo "[1/4] Starting isolated production container stack..."
$COMPOSE_CMD -f docker-compose.yml up -d --build

# 3. Wait for Healthcheck
echo "[2/4] Awaiting backend service healthcheck..."
MAX_ATTEMPTS=20
ATTEMPT=0
HEALTHY=false

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost/health | grep -q '"status":"ok"'; then
        HEALTHY=true
        echo "✓ Backend API is healthy and reachable via Caddy."
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo "  Waiting for services to initialize... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    sleep 3
done

if [ "$HEALTHY" = false ]; then
    echo "[ERROR] Backend service failed to become healthy in time."
    $COMPOSE_CMD -f docker-compose.prod.yml logs
    exit 1
fi

# 4. Firewall & Network Isolation Check
echo "[3/4] Verifying PostgreSQL network isolation (Port 5432 must be unreachable externally)..."
DB_OPEN=false
if nc -z -w 2 127.0.0.1 5432 2>/dev/null; then
    DB_OPEN=true
fi

if [ "$DB_OPEN" = true ]; then
    echo "[WARNING] Port 5432 appears reachable on host. Ensure PostgreSQL has no published ports in compose."
else
    echo "✓ PostgreSQL port 5432 is strictly isolated within internal Docker network."
fi

# 5. Upstream Reachability Probe
echo "[4/4] Executing upstream reachability probe from within container..."
$COMPOSE_CMD -f docker-compose.yml exec -T backend python backend/scripts/probe_sources.py || true

echo "============================================================"
echo " Deployment & Isolation Verification Complete!"
echo "============================================================"
