"""
NOVA_CORE — Auth Handlers & Decorators
Implementación del blindaje de acceso asíncrono.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot_engine.services.auth_service import check_access, grant_access, set_current_token, check_tos, accept_tos
from bot_engine.config import ADMIN_ID

def restricted(func):
    """Decorador asíncrono para restringir acceso a usuarios sin suscripción o sin TOS aceptados."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # 1. Verificar TOS
        if not check_tos(user_id):
            msg = (
                "🚨 *AVISO LEGAL OBLIGATORIO*\n\n"
                "Para usar NOVA_CORE v1.0, debes aceptar nuestros términos de servicio y responsabilidad legal.\n\n"
                "👉 Escribe la palabra *ACEPTO* para desbloquear el sistema."
            )
            await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return

        # 2. Verificar Suscripción
        if not check_access(user_id):
            msg = (
                "⛔️ *ACCESO DENEGADO A NOVA_CORE*\n\n"
                "Este módulo requiere una suscripción activa o un token válido de este mes.\n\n"
                "👉 Ve a la comunidad de Skool, copia el token del post fijado y usa el comando:\n"
                "`/login TU-TOKEN`"
            )
            if update.callback_query:
                await update.callback_query.answer("Acceso Denegado", show_alert=True)
                await update.callback_query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped

async def handle_tos_acceptance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para detectar cuando el usuario escribe ACEPTO."""
    text = update.message.text.strip().upper()
    if text == "ACEPTO":
        user_id = update.effective_user.id
        accept_tos(user_id)
        await update.message.reply_text("✅ *TÉRMINOS ACEPTADOS*")
        # Abrir el menú automáticamente
        from bot_engine.handlers.start import start_command
        await start_command(update, context)

async def set_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando administrativo para cambiar el token del mes."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔️ Comando solo disponible para el administrador jefe.")
        return

    if not context.args:
        await update.message.reply_text("Usa: `/settoken NUEVO-TOKEN-123`", parse_mode=ParseMode.MARKDOWN)
        return

    nuevo_token = context.args[0].strip()
    set_current_token(nuevo_token)
    await update.message.reply_text(f"✅ *TOKEN ACTUALIZADO*\n\nEl nuevo token mensual es: `{nuevo_token}`", parse_mode=ParseMode.MARKDOWN)

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para el comando /login."""
    if not context.args:
        await update.message.reply_text("⚠️ Usa: `/login TOKEN-AQUÍ`", parse_mode=ParseMode.MARKDOWN)
        return

    token = context.args[0].strip()
    user = update.effective_user
    
    if grant_access(user.id, user.username, token):
        await update.message.reply_text("✅ *ACCESO CONCEDIDO*")
        # Abrir el menú automáticamente
        from bot_engine.handlers.start import start_command
        await start_command(update, context)
    else:
        await update.message.reply_text("❌ *TOKEN INVÁLIDO*\nConsigue el tuyo en Skool.")
