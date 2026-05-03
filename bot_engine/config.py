"""
NOVA_CORE — Configuración centralizada
Carga variables de entorno y define constantes del sistema.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ─── Cargar .env ─────────────────────────────────────────────
# Busca .env en la raíz del proyecto (NOVA_CORE/)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ─── Añadir carpeta bin local (ffmpeg/ffprobe) al PATH ───────
BIN_DIR: Path = BASE_DIR / "bin"
if BIN_DIR.exists():
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")

# ─── Telegram ────────────────────────────────────────────────
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")

# ─── Spotify API (Para Playlists) ───────────────────────────
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "2ba362cb6fa645dda37315d6b68c59bb")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "9452eb3637fa4e22b5a72751952553b6")

# ─── IA - Google Gemini ─────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")


# ─── Rutas ───────────────────────────────────────────────────
DOWNLOAD_DIR: Path = BASE_DIR / "downloads"
LOG_DIR: Path = BASE_DIR / "logs"

# Crear directorios si no existen
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── Procesado de Audio ─────────────────────────────────────
TARGET_LUFS: float = float(os.getenv("TARGET_LUFS", "-14.0"))
PEAK_LIMIT_DBTP: float = float(os.getenv("PEAK_LIMIT_DBTP", "-1.0"))
MP3_BITRATE: str = os.getenv("MP3_BITRATE", "320")

# ─── Límites de Telegram ────────────────────────────────────
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

# ─── Logging ─────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ─── Rate Limiting ──────────────────────────────────────────
MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
