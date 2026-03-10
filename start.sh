#!/bin/sh
set -e

APP_PORT="${PORT:-8080}"

# Run migrations first
reflex db makemigrations && reflex db migrate

# Run the app once using the correct port
reflex run --env prod --single-port --frontend-port "$APP_PORT" --backend-port "$APP_PORT"