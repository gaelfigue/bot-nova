# ══════════════════════════════════════════════════════════════
# NOVA_CORE — Dockerfile
# Bot de descargas para Nova Club
# Optimizado para Ryzen 5 / servidor local
# ══════════════════════════════════════════════════════════════

FROM python:3.11-slim AS base

# Evitar prompts interactivos de apt
ENV DEBIAN_FRONTEND=noninteractive

# ─── Instalar FFmpeg y dependencias del sistema ──────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# ─── Crear usuario no-root ──────────────────────────────────
RUN groupadd -r nova && useradd -r -g nova -m nova

# ─── Directorio de trabajo ──────────────────────────────────
WORKDIR /app

# ─── Instalar dependencias Python ───────────────────────────
COPY bot_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ─── Copiar código fuente ───────────────────────────────────
COPY bot_engine/ ./bot_engine/

# ─── Crear directorios de datos ─────────────────────────────
RUN mkdir -p /app/downloads /app/logs && \
    chown -R nova:nova /app

# ─── Cambiar a usuario no-root ──────────────────────────────
USER nova

# ─── Healthcheck básico ─────────────────────────────────────
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python -c "import bot_engine.config; print('OK')" || exit 1

# ─── Ejecutar el bot ────────────────────────────────────────
CMD ["python", "-m", "bot_engine.main"]
