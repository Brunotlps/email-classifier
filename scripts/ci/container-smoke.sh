#!/usr/bin/env bash
set -euo pipefail

image=${1:?Usage: bash scripts/ci/container-smoke.sh IMAGE}
container_id=''
cleanup() {
  status=$?
  if [[ -n "$container_id" ]]; then
    if [[ "$status" -ne 0 ]]; then
      docker logs "$container_id" || true
    fi
    docker rm -f "$container_id" >/dev/null
  fi
  exit "$status"
}
trap cleanup EXIT

# Sem portas publicadas, volumes, secrets ou acesso a provedores externos.
container_id=$(docker run --detach --network none \
  --env AI_PROVIDER=ollama --env OPENAI_API_KEY= --env ENVIRONMENT=test \
  "$image")

for attempt in {1..30}; do
  if docker exec "$container_id" python -c '
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
    assert response.status == 200
    assert json.load(response) == {"status": "healthy"}
' 2>/dev/null; then
    echo 'Container /health returned HTTP 200 and {"status":"healthy"}'
    exit 0
  fi
  if [[ "$(docker inspect --format '{{.State.Running}}' "$container_id")" != true ]]; then
    echo 'Container exited before becoming healthy' >&2
    exit 1
  fi
  sleep 1
done

echo 'Container did not become healthy within the retry budget' >&2
exit 1
