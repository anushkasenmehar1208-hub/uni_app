FROM caddy:2 AS caddybin

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y unzip curl git && rm -rf /var/lib/apt/lists/*

# node for reflex frontend
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get update && apt-get install -y nodejs \
 && rm -rf /var/lib/apt/lists/*

COPY --from=caddybin /usr/bin/caddy /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "reflex run --env prod & caddy run --config /etc/caddy/Caddyfile --adapter caddyfile"