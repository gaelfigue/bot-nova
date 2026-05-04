"""
NOVA_CORE — Start Handler
Gestión de menús y bienvenida.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_engine.services.auth_service import check_tos, check_access

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bienvenida y Dashboard Principal."""
    user = update.effective_user
    
    # 1. Comprobar TOS primero
    if not check_tos(user.id):
        tos_msg = (
            f"⚡️ *NOVA_CORE v1.0 — ACCESO LEGAL*\n\n"
            "Antes de entrar al ecosistema, debes aceptar que eres responsable de tus actos y acuerdos.\n\n"
            "👉 Escribe la palabra *ACEPTO* para desbloquear."
        )
        await update.message.reply_text(tos_msg, parse_mode=ParseMode.MARKDOWN)
        return

    # 2. Lógica de Dashboard Premium
    if check_access(user.id):
        # PANEL VIP (Cuadrícula)
        keyboard = [
            [
                InlineKeyboardButton("🎧 Tech Rider", callback_data="community_rider"),
                InlineKeyboardButton("📜 Contrato", callback_data="community_contract")
            ],
            [
                InlineKeyboardButton("📧 Cold Email", callback_data="cb_email"),
                InlineKeyboardButton("💰 Registrar Bolo", callback_data="cb_bolo")
            ],
            [
                InlineKeyboardButton("🤖 Mentor IA", callback_data="cb_mentor"),
                InlineKeyboardButton("📊 Finanzas", callback_data="cb_finanzas")
            ]
        ]
        msg = "⚡️ *NOVA_CORE ACTIVADO*\nSelecciona una herramienta táctica:"
    else:
        # PANEL RESTRINGIDO
        keyboard = [
            [InlineKeyboardButton("🔑 Introducir Token Skool", callback_data="cb_login_start")]
        ]
        msg = "🔒 *MODO RESTRINGIDO*\nNo tienes una suscripción validada para este mes."

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Relanza el menú principal."""
    await start_command(update, context)

async def handle_menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Orquestador de botones inline."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    if query.data == "cb_login_start":
        await query.message.reply_text("🔑 Escribe tu token mensual ahora:")
    elif query.data == "cb_email":
        await query.message.reply_text("📧 Usa el comando `/coldmail Sala, Género, Info` para generar el ataque.")
    elif query.data == "cb_mentor":
        await query.message.reply_text("🤖 Escribe tu duda de negocio directamente:")
    elif query.data == "cb_bolo":
        # Llamar al inicio de la conversación de bolo
        from bot_engine.handlers.finance_handler import start_bolo
        return await start_bolo(update, context)
    elif query.data == "cb_finanzas":
        from bot_engine.handlers.finance_handler import finanzas_command
        return await finanzas_command(update, context)
    else:
        await query.message.reply_text("Comando en desarrollo o redirigido.")
