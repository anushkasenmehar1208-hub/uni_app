#!/bin/sh
reflex export --frontend-only --no-zip
reflex run --env prod --frontend-port 3002 --backend-port 8000 &
caddy run --config /app/Caddyfile --adapter caddyfile
