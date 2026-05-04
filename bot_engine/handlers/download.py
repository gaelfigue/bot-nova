"""
NOVA_CORE — Handler de Descarga
Pipeline completo: URL → Descarga → LUFS → Metadata → Envío.
Incluye rate limiting por usuario y limpieza de temporales.
"""

import re
import shutil
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction

from bot_engine.config import MAX_FILE_SIZE_BYTES, MAX_CONCURRENT_DOWNLOADS
from bot_engine.services.downloader import download_audio, DownloadError, _is_spotify_url
from bot_engine.services.audio_processor import process_audio, AudioProcessingError
from bot_engine.services.metadata_fixer import fix_metadata
from bot_engine.services.playlist_extractor import extract_playlist, is_playlist
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.download")

# ─── Rate Limiting ───────────────────────────────────────────
# Set de user_ids con descargas activas
_active_downloads: set[int] = set()
_download_count: int = 0

# Regex para detectar URLs
URL_PATTERN = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}"
    r"\b[-a-zA-Z0-9()@:%_\+.~#?&/=]*",
    re.IGNORECASE,
)


def _format_duration(seconds: int) -> str:
    """Formatea duración en mm:ss."""
    if not seconds:
        return "??:??"
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"


def _format_filesize(path: Path) -> str:
    """Formatea tamaño de archivo."""
    size_mb = path.stat().st_size / (1024 * 1024)
    return f"{size_mb:.1f} MB"


async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler principal de descarga.
    Detecta URLs en mensajes y ejecuta el pipeline completo.
    """
    global _download_count

    message = update.message
    if not message or not message.text:
        return

    # Extraer URL del mensaje
    match = URL_PATTERN.search(message.text)
    if not match:
        return  # No es una URL, ignorar silenciosamente

    url = match.group(0)
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name

    # Detectar fuente
    is_spotify = _is_spotify_url(url)
    source_label = "Spotify" if is_spotify else "yt-dlp"

    logger.info(f"[{source_label}] Solicitud de {user_name} ({user_id}): {url}")

    # ─── Rate limiting ───────────────────────────────────
    if user_id in _active_downloads:
        await message.reply_text(
            "Ya tienes una descarga en proceso. Espera a que termine.",
        )
        return

    if len(_active_downloads) >= MAX_CONCURRENT_DOWNLOADS:
        await message.reply_text(
            "Servidor ocupado. Intentalo en unos segundos.",
        )
        return

    # Detectar si es una playlist
    if is_playlist(url):
        status_msg = await message.reply_text("🔎 *Analizando playlist...*\nEsto puede tardar unos segundos.", parse_mode=ParseMode.MARKDOWN)
        tracks = extract_playlist(url)
        if not tracks:
            await status_msg.edit_text("❌ No se pudieron extraer tracks de la playlist. (¿Es una cuenta gratuita de Spotify?)")
            _active_downloads.discard(user_id)
            return
        await status_msg.edit_text(f"🎵 *Playlist detectada: {len(tracks)} canciones.*\nAñadiendo a la cola de descarga...", parse_mode=ParseMode.MARKDOWN)
    else:
        tracks = [url]
        status_msg = None

    total_tracks = len(tracks)

    for idx, track_url in enumerate(tracks, 1):
        try:
            await _process_single_track(track_url, message, user_name, context, idx, total_tracks, status_msg if total_tracks == 1 else None)
        except Exception as e:
            logger.error(f"Error en track {idx}/{total_tracks}: {e}")
            await message.reply_text(f"❌ Error procesando pista {idx}/{total_tracks}")
    
    if total_tracks > 1:
        await message.reply_text(f"✅ *Playlist completada* ({total_tracks} canciones descargadas).", parse_mode=ParseMode.MARKDOWN)

    # Limpieza final
    _active_downloads.discard(user_id)


async def _process_single_track(url: str, message, user_name: str, context, idx: int, total_tracks: int, existing_status_msg=None) -> None:
    """Procesa una única URL (descarga, LUFS, ID3, envío)."""
    global _download_count
    
    is_spotify = _is_spotify_url(url)
    
    if existing_status_msg:
        status_msg = existing_status_msg
    else:
        prefix = f"[{idx}/{total_tracks}] " if total_tracks > 1 else ""
        source = "Spotify" if is_spotify else "YouTube/Genérico"
        status_msg = await message.reply_text(
            f"{prefix}*Descargando desde {source}...*\nExtrayendo audio en máxima calidad.",
            parse_mode=ParseMode.MARKDOWN,
        )

    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
    temp_dir = None

    try:
        # FASE 1: Descarga
        result = await download_audio(url)
        temp_dir = result.temp_dir

        await status_msg.edit_text(
            f"✅ Descarga completa: *{result.title}*\n"
            f"⏱ Duración: `{_format_duration(result.duration)}`\n\n"
            f"🎛 *Procesando audio ASIR...*\n"
            f"Normalizando a −14 LUFS con peak limiting.",
            parse_mode=ParseMode.MARKDOWN,
        )

        # FASE 2: Procesado LUFS
        await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)
        mp3_output = result.temp_dir / f"{result.file_path.stem}.mp3"
        audio_stats = await process_audio(result.file_path, mp3_output)

        await status_msg.edit_text(
            f"✅ Audio procesado\n"
            f"📊 LUFS: `{audio_stats['original_lufs']}` → `{audio_stats['final_lufs']}`\n"
            f"📈 Peak: `{audio_stats['peak_dbtp']} dBTP`\n\n"
            f"🏷 *Fijando metadata ID3...*",
            parse_mode=ParseMode.MARKDOWN,
        )

        # FASE 3: Metadata
        meta_info = await fix_metadata(
            mp3_path=mp3_output,
            title=result.title,
            artist=result.artist,
            thumbnail_path=result.thumbnail_path,
        )

        # FASE 4: Envío
        file_size = mp3_output.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            await status_msg.edit_text(
                f"❌ El archivo pesa *{_format_filesize(mp3_output)}* y supera el límite de Telegram (50 MB).",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await status_msg.edit_text("📤 *Enviando archivo...*", parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)

        cover_icon = "🖼" if meta_info["cover_embedded"] else ""
        caption = (
            f"🎧 *{meta_info['title']}*\n"
            f"🎤 {meta_info['artist']}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 {audio_stats['final_lufs']} LUFS │ Peak {audio_stats['peak_dbtp']} dBTP\n"
            f"💿 MP3 320kbps │ {_format_filesize(mp3_output)} {cover_icon}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ _Nova Promo Hub_"
        )

        with open(mp3_output, "rb") as audio_file:
            await message.reply_audio(
                audio=audio_file,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                title=meta_info["title"],
                performer=meta_info["artist"],
                duration=result.duration,
            )

        await status_msg.delete()
        _download_count += 1
        logger.info(f"✓ Enviado a {user_name}: {meta_info['title']} [Total: {_download_count}]")

    except DownloadError as e:
        logger.error(f"✗ Error descarga: {e}")
        error_text = f"❌ *Error al descargar*\n\n`{str(e)[:200]}`"
        await status_msg.edit_text(error_text, parse_mode=ParseMode.MARKDOWN)
    except AudioProcessingError as e:
        logger.error(f"✗ Error audio: {e}")
        await status_msg.edit_text(f"❌ *Error al procesar audio*\n\n`{str(e)[:200]}`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"✗ Error inesperado: {e}", exc_info=True)
        await status_msg.edit_text("❌ *Error inesperado*\nRevisa los logs del servidor.", parse_mode=ParseMode.MARKDOWN)
    finally:
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
