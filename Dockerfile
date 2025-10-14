# ------------------------- Dockerfile -------------------------
FROM python:3.11-slim

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git build-essential ca-certificates wget && \
    rm -rf /var/lib/apt/lists/*

# Instalar yt-dlp
RUN pip install --no-cache-dir yt-dlp==2025.1.1

# Instalar dependencias del proyecto
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Carpeta para cookies persistentes
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]