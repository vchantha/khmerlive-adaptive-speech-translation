#!/usr/bin/env bash
set -euo pipefail
curl -fsS http://localhost:8000/health/ready
echo
docker compose exec -T api sh -lc 'ffmpeg -hide_banner -loglevel error -y -f lavfi -i sine=frequency=440:duration=3 -ac 1 -ar 16000 /tmp/khmerlive-smoke.wav'
docker compose exec -T api sh -lc 'curl -fsS -F file=@/tmp/khmerlive-smoke.wav http://localhost:8000/api/v1/ingest/upload'
echo
sleep 8
curl -fsS 'http://localhost:8000/api/v1/jobs?limit=5'
echo
