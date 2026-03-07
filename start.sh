#!/bin/sh
set -e

reflex export --frontend-only --no-zip
reflex run --env prod --backend-only --backend-host 127.0.0.1 --backend-port 8000 &
caddy run --config /app/Caddyfile --adapter caddyfile
