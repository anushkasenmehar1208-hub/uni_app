FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    VIDEOS_DIR=/data/videos \
    WORK_DIR=/data/work

WORKDIR /app

# System packages required by Manim:
#   - LaTeX (texlive-*) for MathTex / Tex rendering
#   - ffmpeg for video encoding
#   - cairo, pango for vector rasterisation
#   - dvisvgm + ghostscript for LaTeX → SVG conversion
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    ffmpeg \
    dvisvgm \
    ghostscript \
    texlive \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-latex-recommended \
    texlive-science \
    texlive-fonts-recommended \
    fonts-liberation \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p "$VIDEOS_DIR" "$WORK_DIR" && chmod +x start.sh

EXPOSE 8090

CMD ["./start.sh"]
