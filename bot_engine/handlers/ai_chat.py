"""
NOVA_CORE — Handler de Chat IA
Permite al usuario hacer consultas libres al asistente mentor.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

from bot_engine.services.ai_engine import ai_engine
from bot_engine.utils.logger import setup_logger
from bot_engine.handlers.auth_handler import restricted

logger = setup_logger("nova.ai_chat")

# Estado de la conversación
CHAT_INPUT = 1

@restricted
async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el modo chat con la IA."""
    user = update.effective_user
    logger.info(f"🗨 Chat IA iniciado por {user.first_name}")
    
    await update.message.reply_text(
        "🧠 *MODO MENTOR IA ACTIVADO*\n\n"
        "Hola, soy NOVA. Puedo ayudarte con dudas sobre producción, marketing musical, booking o gestión de tu carrera.\n\n"
        "¿En qué puedo ayudarte hoy?\n"
        "_(Escribe /cancelar para salir)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return CHAT_INPUT

async def handle_chat_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa la pregunta del usuario usando Gemini."""
    query = update.message.text
    
    # Mensaje de "pensando"
    thinking_msg = await update.message.reply_text("🤔 *NOVA está pensando...*", parse_mode=ParseMode.MARKDOWN)
    
    # Obtener respuesta del motor de IA
    response = await ai_engine.get_career_advice(query)
    
    # Editar mensaje con la respuesta real
    await thinking_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
    
    return CHAT_INPUT # Mantener la conversación abierta

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Termina el modo chat."""
    await update.message.reply_text(
        "👋 *Modo Mentor desactivado.* ¡Suerte con esos tracks!",
        parse_mode=ParseMode.MARKDOWN
    )
    return ConversationHandler.END

def get_chat_handler() -> ConversationHandler:
    """Devuelve el handler para integrar en el main."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("mentor", start_chat),
            CallbackQueryHandler(start_chat, pattern="^cb_mentor$")
        ],
        states={
            CHAT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_query)],
        },
        fallbacks=[CommandHandler("cancelar", stop_chat)],
    )
