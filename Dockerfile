# ══════════════════════════════════════════════════════════════
# NOVA_CORE — Dockerfile (raíz, para Railway)
# ══════════════════════════════════════════════════════════════

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# ─── Instalar FFmpeg y dependencias del sistema ──────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# ─── Directorio de trabajo ──────────────────────────────────
WORKDIR /app

# ─── Instalar dependencias Python ───────────────────────────
COPY bot_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─── Copiar código fuente y carpetas necesarias ──────────────
COPY bot_engine/ ./bot_engine/
COPY data/ ./data/
COPY shared_assets/ ./shared_assets/

# ─── Crear directorios de datos ─────────────────────────────
RUN mkdir -p /app/downloads /app/logs

# ─── Ejecutar el bot ────────────────────────────────────────
CMD ["python", "-m", "bot_engine.main"]
