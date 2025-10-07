FROM python:3.11-slim

# Instalar ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Puerto interno para Render
ENV PORT=10000

# Ejecutar con gunicorn
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app --timeout 600 -w 2"]