FROM python:3.12-slim

WORKDIR /app

# Install unzip + Caddy (this was the missing piece before)
RUN apt-get update && apt-get install -y curl gnupg2 unzip \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update && apt-get install -y caddy && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN reflex init
RUN reflex export --env prod
EXPOSE 8080

CMD sh -c "reflex run --backend-only --env prod & sleep 6 && caddy run --config /app/Caddyfile --adapter caddyfile"