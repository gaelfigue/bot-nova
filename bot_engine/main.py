"""
NOVA_CORE v1.2 — Entry Point (Webhooks)
Foco en MVP: Auth, Rider, Contratos, Finanzas y Mánager IA.
"""

import sys
import os
import shutil
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot_engine.config import TELEGRAM_TOKEN, ADMIN_ID
from bot_engine.handlers.start import start_command, help_command
from bot_engine.handlers.community import get_press_kit_handler, get_tech_rider_handler, get_contract_handler
from bot_engine.handlers.finance_handler import get_bolo_handler, finanzas_command, radar_command, coldmail_command
from bot_engine.handlers.ai_chat import get_chat_handler
from bot_engine.handlers.auth_handler import login_command, set_token_command, handle_tos_acceptance

from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.main")

async def post_init(app: Application) -> None:
    """Callback tras inicializar el bot: Configura el menú y descarga el logo."""
    # 1. Configurar comandos
    commands = [
        ("start", "🚀 Panel de Control"),
        ("mentor", "🤖 Mánager IA"),
        ("login", "🔑 Validar Token")
    ]
    await app.bot.set_my_commands(commands)
    
    # 2. Descargar Foto de Perfil como Logo
    try:
        bot_user = await app.bot.get_me()
        photos = await app.bot.get_user_profile_photos(bot_user.id, limit=1)
        if photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            new_file = await app.bot.get_file(file_id)
            
            # Rutas
            logo_path = os.path.join("shared_assets", "logo_nova.png")
            template_logo_path = os.path.join("bot_engine", "utils", "templates", "logo_nova.png")
            
            os.makedirs("shared_assets", exist_ok=True)
            os.makedirs(os.path.dirname(template_logo_path), exist_ok=True)
            
            await new_file.download_to_drive(logo_path)
            shutil.copy(logo_path, template_logo_path)
            logger.info(f"✓ Logo actualizado desde perfil del bot.")
    except Exception as e:
        logger.error(f"Error descargando logo del bot: {e}")

    logger.info("✓ Nova v1.2 Premium Online.")

def main() -> None:
    """Arranca el bot."""
    if not TELEGRAM_TOKEN:
        logger.error("✗ TELEGRAM_TOKEN no configurado.")
        sys.exit(1)

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    # 1. Seguridad y Acceso
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("settoken", set_token_command))
    app.add_handler(MessageHandler(filters.Regex("^ACEPTO$"), handle_tos_acceptance))
    
    # 2. Comandos Core
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("finanzas", finanzas_command))
    app.add_handler(CommandHandler("radar", radar_command))
    app.add_handler(CommandHandler("coldmail", coldmail_command))

    # 3. Conversation Handlers (Riders, Contratos, Bolos, Chat IA)
    app.add_handler(get_chat_handler())
    app.add_handler(get_tech_rider_handler())
    app.add_handler(get_contract_handler())
    app.add_handler(get_bolo_handler())
    app.add_handler(get_press_kit_handler())

    # 4. Callbacks de menú
    from bot_engine.handlers.start import handle_menu_callbacks
    app.add_handler(CallbackQueryHandler(handle_menu_callbacks))

    logger.info("✓ Handlers v1.2 registrados.")

    port = int(os.environ.get("PORT", 8080))
    webhook_url = os.environ.get("WEBHOOK_URL")

    if webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TELEGRAM_TOKEN,
            webhook_url=f"{webhook_url}/{TELEGRAM_TOKEN}",
            drop_pending_updates=True
        )
    else:
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
