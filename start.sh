#!/bin/sh
set -e

APP_PORT="${PORT:-8080}"

# Run Reflex on Railway's assigned public port (single process, no Caddy proxy layer).
reflex run --env prod --single-port --frontend-port "${APP_PORT}" --backend-port "${APP_PORT}"
