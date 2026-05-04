"""
NOVA_CORE — Entry Point
Nova Promo Hub para Telegram.
Modo Polling para servidores con IP dinámica.
"""

import sys
import os

# Fix encoding para consola Windows
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot_engine.config import TELEGRAM_TOKEN
from bot_engine.handlers.start import start_command, help_command, status_command
from bot_engine.handlers.download import handle_download
from bot_engine.handlers.invoice_handler import get_invoice_conversation
from bot_engine.handlers.community import get_press_kit_handler, get_budget_handler, get_tech_rider_handler, get_visual_identity_handler, get_contract_handler
from bot_engine.handlers.landing import get_landing_handler
from bot_engine.handlers.ai_chat import get_chat_handler

from bot_engine.web_server import start_web_server
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.main")

# ─── Banner ──────────────────────────────────────────────────
BANNER = """
 +===============================================+
 |                                               |
 |   N   N  OOO  V   V  AAA                     |
 |   NN  N O   O V   V A   A                    |
 |   N N N O   O V   V AAAAA                    |
 |   N  NN O   O  V V  A   A                    |
 |   N   N  OOO    V   A   A                    |
 |                                               |
 |           P R O M O   H U B            |
 |            --- Nova Club ---                  |
 |                                               |
 +===============================================+
"""

async def post_init(app: Application) -> None:
    """Callback que se ejecuta tras inicializar el bot pero antes de empezar el polling."""
    logger.info("Iniciando mini-servidor web (aiohttp)...")
    import asyncio
    # Lanzar el servidor web como tarea de fondo (usará el puerto de la variable de entorno PORT)
    asyncio.create_task(start_web_server(host='0.0.0.0'))



def main() -> None:
    """Arranca el bot en modo Polling."""
    print(BANNER)

    # Verificar token
    if not TELEGRAM_TOKEN:
        logger.error(
            "✗ TELEGRAM_TOKEN no configurado. "
            "Crea un archivo .env con tu token de @BotFather"
        )
        sys.exit(1)

    logger.info("Inicializando Nova Download Engine...")

    # ─── Construir la aplicación ─────────────────────────
    # Timeout alto para subir archivos grandes a Telegram
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .read_timeout(120)
        .write_timeout(120)
        .connect_timeout(30)
        .post_init(post_init)
        .build()
    )

    # ─── Registrar handlers ──────────────────────────────
    # 1. Comandos
    from bot_engine.handlers.auth_handler import login_command, set_token_command
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("settoken", set_token_command))
    app.add_handler(get_chat_handler()) # Mentor IA


    # 2. Conversation Handlers (deben ir antes que los genéricos)
    from bot_engine.handlers.invoice_handler import get_invoice_conversation
    app.add_handler(get_invoice_conversation())
    app.add_handler(get_press_kit_handler())
    app.add_handler(get_budget_handler())
    app.add_handler(get_landing_handler())
    app.add_handler(get_tech_rider_handler())
    app.add_handler(get_visual_identity_handler())
    app.add_handler(get_contract_handler())

    # 3. Callbacks para el Menú Interactivo (Inline)
    from bot_engine.handlers.start import handle_menu_callbacks
    app.add_handler(CallbackQueryHandler(handle_menu_callbacks, pattern="^(menu_|music_track|music_lufs|coming_soon)"))

    # 4. Herramientas de teclado (ReplyKeyboard)
    from bot_engine.handlers.start import music_track_command, lufs_command
    app.add_handler(MessageHandler(filters.Regex("^📥 Descargar Track Sencillo$"), music_track_command))
    app.add_handler(MessageHandler(filters.Regex("^🎛 Analizar LUFS$"), lufs_command))

    # 4. Archivos de audio (para analizar LUFS)
    from bot_engine.handlers.audio_tools import handle_audio_file
    app.add_handler(
        MessageHandler(
            filters.AUDIO | filters.Document.AUDIO | filters.Document.MimeType("audio/mpeg") | filters.Document.MimeType("audio/wav"),
            handle_audio_file,
        )
    )

    # 5. Mensajes genéricos con URLs → pipeline de descarga
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_download,
        )
    )

    logger.info("✓ Handlers registrados (menú inferior activo)")
    logger.info("✓ Modo: POLLING (IP dinámica compatible)")
    logger.info("✓ Nova Promo Hub ONLINE")

    # ─── Arrancar en modo Polling ────────────────────────
    # run_polling() maneja el event loop internamente
    # drop_pending_updates=True evita procesar mensajes acumulados
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
