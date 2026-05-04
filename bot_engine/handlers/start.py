"""
NOVA_CORE — Start Handler
Gestión de menús y bienvenida.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_engine.services.auth_service import check_tos

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bienvenida al bot."""
    user = update.effective_user
    
    # 1. Comprobar TOS primero
    if not check_tos(user.id):
        tos_msg = (
            f"⚡️ *BIENVENIDO A NOVA_CORE v1.0, {user.first_name.upper()}*\n\n"
            "Este es el sistema operativo para DJs y productores que quieren profesionalizar su carrera.\n\n"
            "🛡 *AVISO LEGAL:* Antes de empezar, debes aceptar que el uso de este bot es bajo tu responsabilidad. "
            "NOVA CLUB C.B. no se hace responsable de los contratos o acuerdos generados.\n\n"
            "👉 Escribe la palabra *ACEPTO* para continuar."
        )
        await update.message.reply_text(tos_msg, parse_mode=ParseMode.MARKDOWN)
        return

    # 2. Si ya aceptó TOS, mostrar menú principal
    main_menu = [
        ["📄 Generar Tech Rider", "📜 Generar Contrato"],
        ["💰 Registrar Bolo", "📊 Finanzas"],
        ["⚡️ Mentor IA", "✉️ Cold Mail"]
    ]
    reply_markup = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    
    welcome_msg = (
        f"🎧 *NOVA HUB — ONLINE*\n\n"
        "Todo lo que necesitas para gestionar tu carrera desde el móvil.\n\n"
        "Usa el menú inferior para empezar."
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra los comandos disponibles."""
    help_text = (
        "⚡️ *COMANDOS NOVA_CORE v1.0*\n\n"
        "🔐 `/login TOKEN` - Activa tu suscripción mensual.\n"
        "📄 `/rider` - Genera tu Tech Rider Premium.\n"
        "📜 `/contrato` - Genera un contrato de actuación.\n"
        "💰 `/bolo` - Registra un nuevo bolo y caché.\n"
        "📊 `/finanzas` - Mira tus ingresos acumulados.\n"
        "⚡️ `/mentor` - Habla con el Mánager Tiburón.\n"
        "✉️ `/coldmail` - Genera ataques comerciales."
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el estado del sistema."""
    await update.message.reply_text("✅ NOVA_CORE v1.0 Status: *OPTIMAL*", parse_mode=ParseMode.MARKDOWN)

async def handle_menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los clics en botones inline (legacy)."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Usa el menú inferior para navegar mejor en v1.0.")
