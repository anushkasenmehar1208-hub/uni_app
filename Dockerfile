FROM python:3.11-slim

WORKDIR /app

ENV REFLEX_DIR=/app/.reflex
ENV REFLEX_USE_NPM=true

RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    gcc \
    libpq-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p "$REFLEX_DIR" \
    && reflex export --frontend-only --no-zip --env prod

RUN chmod +x start.sh

EXPOSE 3000

CMD ["./start.sh"]
