"""
NOVA_CORE — Sistema de Logging
Logger con salida a consola y archivo rotativo.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from bot_engine.config import LOG_DIR, LOG_LEVEL


def setup_logger(name: str = "nova") -> logging.Logger:
    """Configura y retorna un logger con output a consola y archivo."""
    logger = logging.getLogger(name)

    # Evitar handlers duplicados si se llama varias veces
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # ─── Consola ─────────────────────────────────────────
    console_fmt = logging.Formatter(
        "\033[90m%(asctime)s\033[0m │ %(levelname)-8s │ \033[36m%(name)-18s\033[0m │ %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # ─── Archivo ─────────────────────────────────────────
    file_fmt = logging.Formatter(
        "%(asctime)s │ %(levelname)-8s │ %(name)-18s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        LOG_DIR / "nova_bot.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB por archivo
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger
