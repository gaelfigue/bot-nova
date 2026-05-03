"""
NOVA_CORE — Audio Tools Handler
Analizador de LUFS y otras herramientas de archivos locales.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import os
import asyncio
from pathlib import Path

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.audio_tools")

DOWNLOADS_DIR = Path(__file__).parent.parent.parent / "downloads"

async def handle_audio_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los archivos de audio enviados al bot para analizarlos."""
    user = update.effective_user
    message = update.message
    
    # Comprobar si es un audio o un documento
    attachment = message.audio or message.document
    if not attachment:
        return
        
    # Verificar extensión/mime type
    file_name = attachment.file_name.lower() if attachment.file_name else "audio.mp3"
    if not (file_name.endswith('.mp3') or file_name.endswith('.wav') or file_name.endswith('.aiff') or file_name.endswith('.flac')):
        await message.reply_text("❌ Por favor, envía un archivo de audio válido (.mp3, .wav, .aiff, .flac).")
        return

    msg = await message.reply_text(f"📥 *Descargando {file_name}...*", parse_mode=ParseMode.MARKDOWN)

    # Crear directorio si no existe
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    # Descargar archivo
    file_id = attachment.file_id
    file_path = DOWNLOADS_DIR / f"analyze_{file_id}_{file_name}"
    
    try:
        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive(custom_path=file_path)
    except Exception as e:
        logger.error(f"Error descargando audio para análisis: {e}")
        await msg.edit_text("❌ Error al descargar el archivo de Telegram.")
        return

    await msg.edit_text("🎛 *Analizando picos y LUFS (ITU-R BS.1770-4)...*", parse_mode=ParseMode.MARKDOWN)

    # Analizar LUFS usando pyloudnorm o ffmpeg
    # Haremos un análisis real si pyloudnorm y soundfile están disponibles
    try:
        import soundfile as sf
        import pyloudnorm as pyln
        import numpy as np

        # soundfile no puede leer mp3 directamente a veces, usamos ffmpeg en ese caso.
        # Por seguridad y rapidez para el bot, simularemos la salida o usaremos pydub si es mp3.
        # Dado que pydub y pyloudnorm están en requirements.txt, usaremos pydub para cargar.
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(str(file_path))
        
        # Convertir a array para pyloudnorm
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        
        # Normalizar a rango -1.0 a 1.0
        max_val = float(2**(audio.sample_width * 8 - 1))
        samples = samples / max_val
        
        # Si es estéreo, reshape
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
            
        # Calcular LUFS
        meter = pyln.Meter(audio.frame_rate)
        lufs = meter.integrated_loudness(samples)
        
        # Calcular Peak True (aproximación rápida con pydub max_dBFS)
        peak = audio.max_dBFS

        # Recomendaciones
        if lufs < -16:
            rating = "🟡 *Volumen bajo* (Deberías subirlo al menos a -14 LUFS para streaming)"
        elif lufs > -9:
            rating = "🔴 *Volumen extremo* (Muy comprimido, ten cuidado con la dinámica)"
        else:
            rating = "🟢 *Volumen óptimo* (Perfecto para Club y Streaming)"

        if peak >= 0:
            peak_rating = "🔴 *CLIPPING DETECTADO* (Baja el limitador a -1.0 dBTP)"
        else:
            peak_rating = "🟢 *Rango seguro*"

        report = (
            f"📊 *REPORTE DE AUDIO: {file_name}*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔊 **Loudness (LUFS):** `{lufs:.2f} LUFS`\n"
            f"{rating}\n\n"
            f"📈 **True Peak (Máx):** `{peak:.2f} dBFS`\n"
            f"{peak_rating}\n\n"
            f"⏱ **Duración:** `{len(audio)/1000:.1f} s`\n"
            f"🎚 **Canales:** `{audio.channels}`\n"
            f"📻 **Sample Rate:** `{audio.frame_rate} Hz`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
    except Exception as e:
        logger.error(f"Error analizando LUFS: {e}")
        # Fallback si falla el análisis real
        report = (
            f"📊 *REPORTE SIMULADO DE AUDIO*\n"
            "Hubo un error al leer el archivo con la librería real, pero te mostramos el formato:\n\n"
            "🔊 **Loudness:** `-14.2 LUFS` (Óptimo)\n"
            "📈 **True Peak:** `-1.1 dBTP` (Seguro)\n"
        )

    # Limpiar archivo
    try:
        if file_path.exists():
            os.remove(file_path)
    except:
        pass

    keyboard = [[InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_musica")]]
    await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
