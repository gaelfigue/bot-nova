"""
NOVA_CORE v1.0 — Entry Point (Webhooks)
Foco en MVP: Auth, Rider, Contratos, Finanzas y Mánager IA.
"""

import sys
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot_engine.config import TELEGRAM_TOKEN, ADMIN_ID
from bot_engine.handlers.start import start_command, help_command, status_command
from bot_engine.handlers.community import get_press_kit_handler, get_tech_rider_handler, get_contract_handler
from bot_engine.handlers.finance_handler import get_bolo_handler, finanzas_command, radar_command, coldmail_command
from bot_engine.handlers.ai_chat import start_chat
from bot_engine.handlers.auth_handler import login_command, set_token_command, handle_tos_acceptance

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.main")

async def post_init(app: Application) -> None:
    """Callback tras inicializar el bot: Configura el menú nativo."""
    commands = [
        ("start", "🚀 Iniciar Nova Core"),
        ("menu", "📱 Panel de Control"),
        ("mentor", "🤖 Hablar con Mánager IA"),
        ("login", "🔑 Validar Token Skool")
    ]
    await app.bot.set_my_commands(commands)
    logger.info("✓ Menú nativo configurado. Nova v1.0 Premium Online.")

def main() -> None:
    """Arranca el bot."""
    if not TELEGRAM_TOKEN:
        logger.error("✗ TELEGRAM_TOKEN no configurado.")
        sys.exit(1)

    # ─── Construir la aplicación ─────────────────────────
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ─── Registrar handlers ──────────────────────────────
    
    # 1. Seguridad y Acceso
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("settoken", set_token_command))
    app.add_handler(MessageHandler(filters.Regex("^ACEPTO$"), handle_tos_acceptance))
    
    # 2. Comandos Core
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("mentor", start_chat))
    app.add_handler(CommandHandler("finanzas", finanzas_command))
    app.add_handler(CommandHandler("radar", radar_command))
    app.add_handler(CommandHandler("coldmail", coldmail_command))

    # 3. Conversation Handlers (Riders, Contratos, Bolos)
    app.add_handler(get_tech_rider_handler())
    app.add_handler(get_contract_handler())
    app.add_handler(get_bolo_handler())
    app.add_handler(get_press_kit_handler())

    # 4. Callbacks de menú
    from bot_engine.handlers.start import handle_menu_callbacks
    app.add_handler(CallbackQueryHandler(handle_menu_callbacks))

    logger.info("✓ Handlers v1.0 registrados.")

    # ─── Modo Webhook para Railway ────────────────────────
    # En Railway, PORT es una variable de entorno obligatoria
    port = int(os.environ.get("PORT", 8080))
    webhook_url = os.environ.get("WEBHOOK_URL") # Debes configurar esto en Railway

    if webhook_url:
        logger.info(f"✓ Arrancando en modo WEBHOOK: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_TOKEN}",
            drop_pending_updates=True
        )
    else:
        logger.info("✓ Arrancando en modo POLLING (WEBHOOK_URL no detectada).")
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
