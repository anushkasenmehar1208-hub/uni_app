#!/bin/sh
reflex run --env prod --frontend-port 3001 --backend-port 8000 &
caddy run --config /app/Caddyfile --adapter caddyfile