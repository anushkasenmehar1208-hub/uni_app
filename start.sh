#!/bin/sh
set -e

APP_PORT="${PORT:-8080}"

reflex run --env prod --single-port --frontend-port "$APP_PORT" --backend-port "$APP_PORT"