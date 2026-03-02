FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x start.sh

EXPOSE 3000

CMD ["reflex", "run", "--env", "prod", "--frontend-port", "3000", "--backend-port", "8000"]