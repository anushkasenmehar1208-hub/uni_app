FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install reflex

# Build the frontend
RUN reflex init
RUN reflex export --env prod

# Install Caddy
RUN apt-get update && apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
RUN curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
RUN curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
RUN apt-get update && apt-get install -y caddy

EXPOSE 8080

CMD ["sh", "-c", "reflex run --env prod & sleep 5 && caddy run --config /app/Caddyfile --adapter caddyfile"]