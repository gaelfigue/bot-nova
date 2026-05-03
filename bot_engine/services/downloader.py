"""
NOVA_CORE — Servicio de Descarga
Estrategia multi-fuente:
  - Spotify → oEmbed API (artista+titulo) → busca en YouTube Music
  - Todo lo demás → yt-dlp directo
"""

import asyncio
import json
import re
import uuid
import urllib.request
import yt_dlp
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from bot_engine.config import DOWNLOAD_DIR, BASE_DIR
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.downloader")

SPOTIFY_PATTERN = re.compile(
    r"https?://open\.spotify\.com/(intl-[a-z]{2}/)?track/([A-Za-z0-9]+)",
    re.IGNORECASE,
)


@dataclass
class DownloadResult:
    file_path: Path
    title: str
    artist: str
    duration: int
    thumbnail_path: Optional[Path]
    temp_dir: Path
    extra_info: dict = field(default_factory=dict)


class DownloadError(Exception):
    pass


def _is_spotify_url(url: str) -> bool:
    return bool(SPOTIFY_PATTERN.search(url))


def _find_thumbnail(temp_dir: Path) -> Optional[Path]:
    for ext in ["*.jpg", "*.png", "*.webp"]:
        files = list(temp_dir.glob(ext))
        if files:
            return files[0]
    return None


def _build_ytdlp_opts(temp_dir: Path) -> dict:
    return {
        "format": "bestaudio/best",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "wav"}
        ],
        "outtmpl": str(temp_dir / "%(title).80s.%(ext)s"),
        "writethumbnail": True,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 30,
        "ffmpeg_location": str(BASE_DIR / "bin"),
    }


# ══════════════════════════════════════════════════════════════
#  SPOTIFY — oEmbed metadata + YouTube Music search
# ══════════════════════════════════════════════════════════════

def _get_spotify_metadata(url: str) -> tuple[str, str, str]:
    """
    Usa el endpoint oEmbed de Spotify (público, sin auth)
    para obtener título del track y artista.
    Retorna (title, artist, thumbnail_url).
    """
    # Limpiar URL (quitar parámetros y prefijos de idioma)
    match = SPOTIFY_PATTERN.search(url)
    if not match:
        return "", "", ""

    track_id = match.group(2)
    clean_url = f"https://open.spotify.com/track/{track_id}"
    oembed_url = f"https://open.spotify.com/oembed?url={clean_url}"

    try:
        req = urllib.request.Request(
            oembed_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # oEmbed retorna: title = "Nombre Track", por ejemplo "Paseo"
        # Y el HTML contiene el artista en el iframe title
        raw_title = data.get("title", "")
        thumbnail = data.get("thumbnail_url", "")

        # El campo html contiene algo como:
        # <iframe ... title="Paseo">...</iframe>
        # Pero no tiene artista directo. Usamos "description" si existe
        description = data.get("description", "")

        # Intentar sacar artista del HTML o description
        artist = ""
        html = data.get("html", "")
        # A veces el provider_name no es útil pero veamos
        # Intentar extraer del título del iframe
        iframe_match = re.search(r'title="([^"]+)"', html)
        if iframe_match:
            iframe_title = iframe_match.group(1)
            # Puede ser "Artista · Cancion" formato Spotify embed
            if " · " in iframe_title:
                parts = iframe_title.split(" · ")
                # El primer campo suele ser el nombre del track
                raw_title = parts[0].strip()

        return raw_title, artist, thumbnail

    except Exception as e:
        logger.warning(f"oEmbed fallido: {e}")
        return "", "", ""


def _download_spotify_thumbnail(thumb_url: str, temp_dir: Path) -> Optional[Path]:
    """Descarga la portada de Spotify."""
    if not thumb_url:
        return None
    try:
        thumb_path = temp_dir / "cover.jpg"
        urllib.request.urlretrieve(thumb_url, str(thumb_path))
        return thumb_path
    except Exception:
        return None


def _download_spotify_sync(url: str) -> DownloadResult:
    """
    1. Obtiene título/artista de Spotify via oEmbed (gratis, sin API key)
    2. Busca en YouTube Music con "ytsearch1:artista título"
    3. Descarga el audio via yt-dlp
    """
    download_id = uuid.uuid4().hex[:8]
    temp_dir = DOWNLOAD_DIR / download_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"[{download_id}] SPOTIFY: Obteniendo metadata via oEmbed...")

    # Paso 1: Metadata de Spotify
    sp_title, sp_artist, sp_thumb = _get_spotify_metadata(url)

    if sp_title:
        search_query = f"ytsearch1:{sp_title} {sp_artist} audio".strip()
        logger.info(f"[{download_id}] Spotify track: {sp_title} {sp_artist}")
    else:
        # Si oEmbed falla, extraer track_id y buscar genéricamente
        match = SPOTIFY_PATTERN.search(url)
        track_id = match.group(2) if match else "unknown"
        search_query = f"ytsearch1:spotify track {track_id}"
        logger.warning(f"[{download_id}] oEmbed sin resultado, buscando por ID")

    # Descargar portada de Spotify
    sp_thumb_path = _download_spotify_thumbnail(sp_thumb, temp_dir)

    # Paso 2: Buscar y descargar desde YouTube Music
    opts = _build_ytdlp_opts(temp_dir)

    logger.info(f"[{download_id}] Descargando audio...")

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            dl_info = ydl.extract_info(search_query, download=True)
            if dl_info and "entries" in dl_info:
                dl_info = dl_info["entries"][0] if dl_info["entries"] else dl_info
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(f"No se encontro el track en YouTube Music: {e}") from e

    # Buscar archivo WAV
    wav_files = list(temp_dir.glob("*.wav"))
    if not wav_files:
        raise DownloadError("No se genero el archivo de audio.")

    # Preferir metadata de Spotify, fallback a YouTube
    title = sp_title or (dl_info.get("title", "") if dl_info else "")
    artist = sp_artist or (
        dl_info.get("artist") or dl_info.get("uploader") or "Unknown"
    ) if dl_info else "Unknown"
    duration = dl_info.get("duration", 0) if dl_info else 0

    # Preferir thumbnail de Spotify sobre YouTube
    thumb = sp_thumb_path or _find_thumbnail(temp_dir)

    logger.info(f"[{download_id}] SPOTIFY OK: {artist} - {title}")

    return DownloadResult(
        file_path=wav_files[0],
        title=title,
        artist=artist,
        duration=duration,
        thumbnail_path=thumb,
        temp_dir=temp_dir,
        extra_info={"source": "spotify", "webpage_url": url},
    )


# ══════════════════════════════════════════════════════════════
#  GENÉRICO — yt-dlp directo
# ══════════════════════════════════════════════════════════════

def _download_generic_sync(url: str) -> DownloadResult:
    download_id = uuid.uuid4().hex[:8]
    temp_dir = DOWNLOAD_DIR / download_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"[{download_id}] YT-DLP: {url}")
    opts = _build_ytdlp_opts(temp_dir)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(f"No se pudo descargar: {e}") from e

    wav_files = list(temp_dir.glob("*.wav"))
    if not wav_files:
        raise DownloadError("No se genero archivo WAV.")

    title = info.get("title", wav_files[0].stem) if info else wav_files[0].stem
    artist = (
        info.get("artist") or info.get("creator") or info.get("uploader") or "Unknown"
    ) if info else "Unknown"
    duration = info.get("duration", 0) if info else 0

    logger.info(f"[{download_id}] OK: {title} ({duration}s)")

    return DownloadResult(
        file_path=wav_files[0],
        title=title,
        artist=artist,
        duration=duration,
        thumbnail_path=_find_thumbnail(temp_dir),
        temp_dir=temp_dir,
        extra_info={
            "source": info.get("extractor", "unknown") if info else "unknown",
            "webpage_url": info.get("webpage_url", url) if info else url,
        },
    )


# ══════════════════════════════════════════════════════════════
#  API PÚBLICA
# ══════════════════════════════════════════════════════════════

async def download_audio(url: str) -> DownloadResult:
    if _is_spotify_url(url):
        return await asyncio.to_thread(_download_spotify_sync, url)
    else:
        return await asyncio.to_thread(_download_generic_sync, url)
