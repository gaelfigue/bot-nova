"""
NOVA_CORE — Procesador de Audio ASIR
Normalización a -14 LUFS con peak limiting a -1.0 dBTP.
Diseñado para evitar clipping en cabina de DJ.

Pipeline:
  WAV (lossless de yt-dlp) → Normalización LUFS → Peak Limit → MP3 320kbps
  Solo un encode a MP3 en toda la cadena = máxima calidad.
"""

import asyncio
import numpy as np
import pyloudnorm as pyln
from pathlib import Path
from pydub import AudioSegment

from bot_engine.config import TARGET_LUFS, PEAK_LIMIT_DBTP, MP3_BITRATE
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.audio")


class AudioProcessingError(Exception):
    """Error durante el procesado de audio."""
    pass


def _get_numpy_from_audio(audio: AudioSegment) -> np.ndarray:
    """
    Convierte un AudioSegment de pydub a un numpy array float64
    normalizado al rango [-1.0, 1.0].
    """
    samples = np.array(audio.get_array_of_samples(), dtype=np.float64)

    # Normalizar según bit depth
    bit_depth = audio.sample_width * 8
    max_val = float(2 ** (bit_depth - 1))
    samples /= max_val

    # Reshape para multi-canal: (num_samples, channels)
    if audio.channels > 1:
        samples = samples.reshape((-1, audio.channels))
    else:
        samples = samples.reshape((-1, 1))

    return samples


def _numpy_to_audio(samples: np.ndarray, frame_rate: int, channels: int) -> AudioSegment:
    """
    Convierte un numpy array float64 [-1.0, 1.0] de vuelta
    a un AudioSegment de pydub (16-bit PCM).
    """
    # Clip para evitar overflow
    samples = np.clip(samples, -1.0, 1.0)

    # Convertir a int16
    output = (samples * 32767).astype(np.int16)

    # Flatten para pydub (intercalado de canales)
    output = output.flatten()

    return AudioSegment(
        output.tobytes(),
        frame_rate=frame_rate,
        sample_width=2,  # 16-bit
        channels=channels,
    )


def _process_sync(input_path: Path, output_path: Path) -> dict:
    """
    Procesado síncrono del audio:
    1. Carga WAV con pydub
    2. Mide LUFS actual con pyloudnorm
    3. Normaliza a TARGET_LUFS (-14 LUFS)
    4. Aplica peak limiting a PEAK_LIMIT_DBTP (-1.0 dBTP)
    5. Exporta como MP3 320kbps
    """
    logger.info(f"🎛  Cargando audio: {input_path.name}")

    try:
        audio = AudioSegment.from_file(str(input_path))
    except Exception as e:
        raise AudioProcessingError(f"No se pudo cargar el audio: {e}") from e

    # Info del audio original
    duration_sec = len(audio) / 1000.0
    logger.info(
        f"   Formato: {audio.channels}ch, {audio.frame_rate}Hz, "
        f"{audio.sample_width * 8}bit, {duration_sec:.1f}s"
    )

    # Convertir a numpy
    samples = _get_numpy_from_audio(audio)

    # ─── Medir loudness actual ───────────────────────────
    meter = pyln.Meter(audio.frame_rate)

    try:
        current_lufs = meter.integrated_loudness(samples)
    except Exception as e:
        raise AudioProcessingError(f"Error midiendo loudness: {e}") from e

    # Manejar audio silencioso (loudness = -inf)
    if np.isinf(current_lufs):
        logger.warning("   ⚠ Audio silencioso detectado, saltando normalización")
        audio.export(str(output_path), format="mp3", bitrate=f"{MP3_BITRATE}k")
        return {
            "original_lufs": float("-inf"),
            "final_lufs": float("-inf"),
            "peak_dbtp": float("-inf"),
            "gain_applied_db": 0.0,
        }

    logger.info(f"   LUFS original: {current_lufs:.1f}")

    # ─── Normalizar a TARGET_LUFS ────────────────────────
    try:
        normalized = pyln.normalize.loudness(
            samples, current_lufs, TARGET_LUFS
        )
    except Exception as e:
        raise AudioProcessingError(f"Error normalizando LUFS: {e}") from e

    gain_applied = TARGET_LUFS - current_lufs
    logger.info(f"   Ganancia aplicada: {gain_applied:+.1f} dB → {TARGET_LUFS} LUFS")

    # ─── Peak Limiting ───────────────────────────────────
    # Calcular peak actual después de normalización
    peak_linear = np.max(np.abs(normalized))
    peak_dbfs = 20 * np.log10(peak_linear + 1e-10)

    if peak_dbfs > PEAK_LIMIT_DBTP:
        logger.info(
            f"   ⚠ Peak {peak_dbfs:.1f} dBFS excede límite {PEAK_LIMIT_DBTP} dBTP"
        )
        # Aplicar peak normalization para llevar el pico al límite
        normalized = pyln.normalize.peak(normalized, PEAK_LIMIT_DBTP)

        # Recalcular LUFS final (será ligeramente menor que -14)
        final_lufs = meter.integrated_loudness(normalized)
        logger.info(
            f"   Peak limitado → LUFS final: {final_lufs:.1f} "
            f"(ajustado por protección anti-clipping)"
        )
    else:
        final_lufs = TARGET_LUFS
        logger.info(f"   ✓ Peak {peak_dbfs:.1f} dBFS dentro del límite seguro")

    # ─── Exportar MP3 320kbps ────────────────────────────
    processed_audio = _numpy_to_audio(
        normalized, audio.frame_rate, audio.channels
    )

    try:
        processed_audio.export(
            str(output_path),
            format="mp3",
            bitrate=f"{MP3_BITRATE}k",
            parameters=["-q:a", "0"],  # Máxima calidad de encoder
        )
    except Exception as e:
        raise AudioProcessingError(f"Error exportando MP3: {e}") from e

    # Peak final
    final_peak = np.max(np.abs(normalized))
    final_peak_db = 20 * np.log10(final_peak + 1e-10)

    logger.info(
        f"   ✓ Exportado: {output_path.name} "
        f"(MP3 {MP3_BITRATE}kbps, {final_lufs:.1f} LUFS, "
        f"peak {final_peak_db:.1f} dBTP)"
    )

    return {
        "original_lufs": round(current_lufs, 1),
        "final_lufs": round(final_lufs, 1),
        "peak_dbtp": round(final_peak_db, 1),
        "gain_applied_db": round(gain_applied, 1),
    }


async def process_audio(input_path: Path, output_path: Path) -> dict:
    """
    Procesa audio de forma asíncrona.
    Retorna dict con métricas del procesado.
    """
    return await asyncio.to_thread(_process_sync, input_path, output_path)
