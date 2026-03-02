#!/bin/sh
set -e

reflex run --env prod &
caddy run --config /app/Caddyfile --adapter caddyfile