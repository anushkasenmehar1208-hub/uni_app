FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install reflex caddy

RUN reflex init

RUN reflex export --env prod --no-zip

EXPOSE 8080

CMD ["sh", "-c", "reflex run --backend-only --env prod & caddy run --config /app/Caddyfile"]