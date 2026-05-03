"""
NOVA_CORE — Metadata Fixer
Limpieza y corrección de tags ID3v2.4 para archivos MP3.
Elimina basura de YouTube, extrae Artista/Título e incrusta portada.
"""

import asyncio
import re
from pathlib import Path
from typing import Optional

from mutagen.mp3 import MP3
from mutagen.id3 import (
    ID3,
    ID3NoHeaderError,
    TIT2,   # Título
    TPE1,   # Artista
    TALB,   # Álbum
    APIC,   # Portada
    TDRC,   # Año
    TCON,   # Género
    COMM,   # Comentarios
)

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.metadata")

# ─── Patrones de basura a limpiar del título ──────────────────
CLEAN_PATTERNS = [
    r"\s*\[Official\s*(Music\s*)?Video\]",
    r"\s*\(Official\s*(Music\s*)?Video\)",
    r"\s*\[Official\s*Audio\]",
    r"\s*\(Official\s*Audio\)",
    r"\s*\[Official\s*Lyric\s*Video\]",
    r"\s*\(Official\s*Lyric\s*Video\)",
    r"\s*\[Lyrics?\s*(Video)?\]",
    r"\s*\(Lyrics?\s*(Video)?\)",
    r"\s*\[Visuali[sz]er\]",
    r"\s*\(Visuali[sz]er\)",
    r"\s*\[Audio\]",
    r"\s*\(Audio\)",
    r"\s*\[HD\]",
    r"\s*\[HQ\]",
    r"\s*\(HD\)",
    r"\s*\(HQ\)",
    r"\s*\[4K\]",
    r"\s*\(4K\)",
    r"\s*\[Extended\s*Mix\]",
    r"\s*\[Original\s*Mix\]",
    r"\s*【.*?】",
    r"\s*\|\s*[A-Z].*$",       # " | Algo Records" al final
    r"\s*\/\/\s*Free\s*Download",
    r"\s*\(Free\s*Download\)",
    r"\s*\[Free\s*Download\]",
]


def clean_title(raw_title: str) -> str:
    """Elimina sufijos típicos de video de YouTube del título."""
    cleaned = raw_title.strip()
    for pattern in CLEAN_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    # Limpiar espacios múltiples
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def split_artist_title(raw: str) -> tuple[str, str]:
    """
    Intenta separar 'Artista - Título' de un string.
    Retorna (artista, título). Si no puede separar, retorna ('', raw).
    """
    separators = [" - ", " – ", " — ", " ~ "]
    for sep in separators:
        if sep in raw:
            parts = raw.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    return "", raw


def _get_mime_type(file_path: Path) -> str:
    """Determina MIME type de una imagen por extensión."""
    ext = file_path.suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


def _fix_sync(
    mp3_path: Path,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    thumbnail_path: Optional[Path] = None,
) -> dict:
    """
    Limpia y establece tags ID3v2.4 en el archivo MP3.
    
    1. Limpia el título de basura de YouTube
    2. Intenta separar Artista/Título del formato "Artista - Título"
    3. Establece tags limpios
    4. Incrusta portada desde thumbnail
    """
    logger.info(f"🏷  Procesando metadata: {mp3_path.name}")

    # Cargar o crear tags ID3
    try:
        audio = MP3(str(mp3_path), ID3=ID3)
    except ID3NoHeaderError:
        audio = MP3(str(mp3_path))
        audio.add_tags()

    # Limpiar todos los tags existentes y empezar limpio
    audio.tags.delete(str(mp3_path))
    audio = MP3(str(mp3_path))
    audio.add_tags()

    # ─── Procesar título ─────────────────────────────────
    final_title = title or mp3_path.stem
    final_artist = artist or ""

    # Limpiar basura del título
    clean = clean_title(final_title)

    # Intentar extraer artista del formato "Artista - Título"
    detected_artist, detected_title = split_artist_title(clean)

    if detected_artist:
        final_title = detected_title
        # Solo sobrescribir artista si no tenemos uno mejor
        if not final_artist or final_artist == "Unknown":
            final_artist = detected_artist
    else:
        final_title = clean

    # ─── Establecer tags ─────────────────────────────────
    if final_title:
        audio.tags.add(TIT2(encoding=3, text=final_title))
    if final_artist:
        audio.tags.add(TPE1(encoding=3, text=final_artist))

    # Álbum: usar "Nova Club" como sello
    audio.tags.add(TALB(encoding=3, text="Nova Club"))

    # Género
    audio.tags.add(TCON(encoding=3, text="Electronic"))

    # Comentario con crédito
    audio.tags.add(
        COMM(encoding=3, lang="eng", desc="", text="Processed by Nova Download Engine")
    )

    logger.info(f"   Título: {final_title}")
    logger.info(f"   Artista: {final_artist}")

    # ─── Incrustar portada ───────────────────────────────
    cover_embedded = False
    if thumbnail_path and thumbnail_path.exists():
        try:
            with open(thumbnail_path, "rb") as f:
                cover_data = f.read()

            mime = _get_mime_type(thumbnail_path)

            audio.tags.add(
                APIC(
                    encoding=3,
                    mime=mime,
                    type=3,  # Cover (front)
                    desc="Cover",
                    data=cover_data,
                )
            )
            cover_embedded = True
            logger.info(f"   ✓ Portada incrustada ({mime})")
        except Exception as e:
            logger.warning(f"   ⚠ No se pudo incrustar portada: {e}")
    else:
        logger.info("   ⓘ Sin thumbnail disponible")

    # Guardar
    audio.save()

    logger.info(f"   ✓ Metadata guardada correctamente")

    return {
        "title": final_title,
        "artist": final_artist,
        "cover_embedded": cover_embedded,
    }


async def fix_metadata(
    mp3_path: Path,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    thumbnail_path: Optional[Path] = None,
) -> dict:
    """Fix metadata de forma asíncrona."""
    return await asyncio.to_thread(
        _fix_sync, mp3_path, title, artist, thumbnail_path
    )
