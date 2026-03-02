#!/bin/sh
set -e

reflex run --env prod &
caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
