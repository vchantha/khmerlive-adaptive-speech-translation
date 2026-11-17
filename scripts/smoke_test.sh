#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

HTTPS_PORT="${HTTPS_PORT:-8443}"
CA="$ROOT/infra/tls/generated/ca.crt"

test -f "$CA" || { echo "Missing TLS CA. Run: make tls"; exit 1; }

echo "== HTTPS gateway / API readiness =="
curl --fail --silent --show-error --cacert "$CA" "https://localhost:$HTTPS_PORT/health/ready"
echo

echo "== Generate a small test audio file in API container =="
docker compose exec -T api sh -lc   'ffmpeg -hide_banner -loglevel error -y -f lavfi -i sine=frequency=440:duration=3 -ac 1 -ar 16000 /tmp/khmerlive-smoke.wav'

echo "== Submit through TLS-enabled API =="
docker compose exec -T api sh -lc   'curl --fail --silent --show-error --cacert /etc/khmerlive/tls/ca.crt -F file=@/tmp/khmerlive-smoke.wav https://localhost:8443/api/v1/ingest/upload'
echo

sleep 8

echo "== Recent jobs via HTTPS dashboard gateway =="
curl --fail --silent --show-error --cacert "$CA"   "https://localhost:$HTTPS_PORT/api/v1/jobs?limit=5"
echo

echo "Smoke test submitted successfully. Confirm the newest job reaches success and SILO contains raw/ and processed/ objects."
